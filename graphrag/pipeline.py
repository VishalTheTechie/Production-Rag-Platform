"""Answers a question with one of four methods:
   baseline   plain vector search -> LLM
   rerank     vector search + cross-encoder rerank -> LLM        (isolates the effect of reranking)
   hybrid     vector + graph expansion + rerank + graph facts -> LLM   (GraphRAG)
   decompose  split into sub-questions, retrieve for each, then answer   (extension)"""
import json
import time

import config
from graphrag import settings
from graphrag.store import rerank
from llm import generate_ex

ANSWER_PROMPT = """Answer the question using ONLY the context.
Reply with the shortest possible answer: a name, date, number, place or yes/no.
No explanation and no full sentence. If the context does not contain the answer, reply: unknown

Context:
{context}
{facts}
Question: {question}
Answer:"""

DECOMPOSE_PROMPT = """Break this multi-hop question into exactly two simple sub-questions.
The second sub-question must contain the placeholder [ANSWER] where the answer to the first goes.
Return ONLY JSON: {{"sub_questions": ["first question", "second question with [ANSWER]"]}}

Question: {question}"""


def _clean(text):
    return (text or "").strip().strip(".").strip()


def ask_llm(question, chunks, triples):
    context = "\n\n".join(f"[{i}] {c['text']}" for i, c in enumerate(chunks, 1))
    facts = ("\nKnown facts from a knowledge graph:\n" + "\n".join(f"- {t}" for t in triples) + "\n") if triples else ""
    r = generate_ex(ANSWER_PROMPT.format(context=context, facts=facts, question=question),
                    model=config.LARGE_MODEL)
    return dict(r, text=_clean(r["text"]))


def _result(pred, chunks, usage, started):
    return {
        "pred": pred, "chunks": chunks,
        "input_tokens": sum(u["input_tokens"] for u in usage),
        "output_tokens": sum(u["output_tokens"] for u in usage),
        "models": ",".join(sorted({u["model"] for u in usage})),
        "latency_s": max(time.perf_counter() - started - sum(u.get("waited_s", 0.0) for u in usage), 0.0),
    }


def run(store, method, question):
    started = time.perf_counter()
    if method == "decompose":
        return run_decompose(store, question, started)
    if method == "baseline":
        chunks, triples = store.vector_search(question, settings.TOP_K), []
    elif method == "rerank":
        chunks = rerank(question, store.vector_search(question, settings.VECTOR_CANDIDATES))[:settings.TOP_K]
        triples = []
    elif method == "hybrid":
        chunks = store.hybrid_retrieve(question)
        triples = store.triples([c["id"] for c in chunks])
    else:
        raise ValueError(f"unknown method {method}")
    r = ask_llm(question, chunks, triples)
    return _result(r["text"], chunks, [r], started)


def run_decompose(store, question, started):
    usage = []
    d = generate_ex(DECOMPOSE_PROMPT.format(question=question), model=config.LARGE_MODEL, json_mode=True,
                    strict_json=True, reasoning_effort="low")
    usage.append(d)
    try:
        subs = json.loads(d["text"])["sub_questions"]
        assert len(subs) >= 2
    except Exception:                                  # could not split: fall back to the one-shot method
        res = run(store, "hybrid", question)
        res["input_tokens"] += d["input_tokens"]
        res["output_tokens"] += d["output_tokens"]
        return res

    first = store.hybrid_retrieve(subs[0], k=3)
    a1 = ask_llm(subs[0], first, store.triples([c["id"] for c in first]))
    usage.append(a1)
    second = store.hybrid_retrieve(subs[1].replace("[ANSWER]", a1["text"]), k=3)

    merged = {}
    for c in first + second:
        merged.setdefault(c["id"], c)
    chunks = list(merged.values())[:settings.TOP_K + 1]
    final = ask_llm(question, chunks, store.triples([c["id"] for c in chunks]))
    usage.append(final)
    return _result(final["text"], chunks, usage, started)
