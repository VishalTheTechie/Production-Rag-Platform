"""The full request flow.
   mode="baseline":  secure retrieval -> large model (Project 2 behaviour, but measured)
   mode="optimized": semantic cache -> router -> small/large model -> escalation -> cache store"""
import logging
import re
import time

import audit
import cache
import config
import metrics
import router
from acl import build_filter, enforce_acl
from embeddings import embed_one
from llm import generate_ex
from rag import PROMPT, retrieve

log = logging.getLogger("pipeline")
CITE = re.compile(r"[\[\u3010][^\]\u3011]*#\d+[\]\u3011]")


def needs_escalation(answer: str) -> bool:
    """A weak small-model answer: empty, 'I don't know', or no citation."""
    a = (answer or "").strip().lower().replace("\u2019", "'")
    if not a or a.startswith("i don't know") or a.startswith("i do not know"):
        return True
    return not CITE.search(answer)


def _ask_model(question, chunks, model):
    context = "\n\n".join(f"[{c['chunk_id']}]\n{c['text']}" for c in chunks)
    return generate_ex(PROMPT.format(context=context, question=question), model=model)


def answer(user, query, request_id, mode="optimized", run_label="live"):
    start = time.perf_counter()
    tokens_in = tokens_out = 0
    cost = 0.0
    waited_total = 0.0     # time spent waiting out free-tier rate limits (not model speed)
    models_used = []
    use_cache = mode == "optimized"

    def tally(r):
        nonlocal tokens_in, tokens_out, cost, waited_total
        waited_total += r.get("waited_s", 0.0)
        tokens_in += r["input_tokens"]
        tokens_out += r["output_tokens"]
        cost += metrics.cost_usd(r["model"], r["input_tokens"], r["output_tokens"])
        models_used.append(r["model"])

    # ---- 1. semantic cache (scoped to the user's access level) ----
    cache_vec = scope = None
    if use_cache:
        scope = cache.access_scope(user)
        cache_vec = embed_one(cache.normalize(query))
        hit = cache.lookup(cache_vec, scope, query)
        if hit:
            sources = hit["sources"]
            audit.log_retrieval(request_id, user, query, sources, "cache", 0)
            latency_ms = max((time.perf_counter() - start - waited_total) * 1000, 0.0)
            row = metrics.log_request(run_label, request_id, user, query, True, None, "cache",
                                      False, 0, 0, 0.0, latency_ms)
            return {"answer": hit["answer"], "sources": sources, "cache_hit": True, "route": None,
                    "escalated": False, "cost_usd": 0.0, "latency_ms": latency_ms, "metrics_id": row}

    # ---- 2. permission-aware retrieval (Project 2) ----
    chunks = retrieve(query, build_filter(user))
    allowed, blocked = enforce_acl(user, chunks)
    if blocked:
        log.error("ACL VIOLATION: user=%s chunks=%s", user.id, [b["chunk_id"] for b in blocked])

    route, escalated, final_answer = "large", False, "I don't know."
    if allowed:
        # ---- 3. route ----
        if mode == "optimized":
            if config.ROUTER_MODE == "llm":
                route, r_route = router.classify_llm(query)
                tally(r_route)
            else:
                route = router.classify_rules(query, [c["score"] for c in allowed])
            model = config.SMALL_MODEL if route == "simple" else config.LARGE_MODEL
        else:
            model = config.LARGE_MODEL

        r = _ask_model(query, allowed, model)
        tally(r)
        final_answer = r["text"]

        # ---- 4. escalate weak small-model answers to the large model ----
        if mode == "optimized" and route == "simple" and needs_escalation(final_answer):
            r2 = _ask_model(query, allowed, config.LARGE_MODEL)
            tally(r2)
            final_answer, escalated = r2["text"], True

    audit.log_retrieval(request_id, user, query, allowed, ",".join(models_used) or None, len(blocked))

    # ---- 5. store in cache (only good answers) ----
    if use_cache and cache.cacheable(final_answer, allowed):
        cache.store(cache_vec, scope, query, final_answer, allowed)

    latency_ms = max((time.perf_counter() - start - waited_total) * 1000, 0.0)
    row = metrics.log_request(run_label, request_id, user, query, False,
                              route if allowed else None, ",".join(models_used) or "none",
                              escalated, tokens_in, tokens_out, cost, latency_ms)
    return {"answer": final_answer, "sources": allowed, "cache_hit": False, "route": route,
            "escalated": escalated, "cost_usd": cost, "latency_ms": latency_ms, "metrics_id": row}
