import logging

from qdrant_client import QdrantClient

import audit
import config
from acl import build_filter, enforce_acl
from embeddings import embed_one
from llm import generate

log = logging.getLogger("rag")
client = QdrantClient(url=config.QDRANT_URL)

PROMPT = """You are a helpful assistant. Answer the question using ONLY the context below.
Cite the chunk ids you used in square brackets, like [acme_corp__handbook#0].
If the context does not contain the answer, say "I don't know."

Context:
{context}

Question: {question}
Answer:"""


def retrieve(question, query_filter=None, k=config.TOP_K):
    hits = client.query_points(
        collection_name=config.COLLECTION,
        query=embed_one(question),
        query_filter=query_filter,
        limit=k,
    ).points
    return [
        {
            "chunk_id": h.payload["chunk_id"],
            "doc_id": h.payload["doc_id"],
            "text": h.payload["text"],
            "score": h.score,
            "tenant_id": h.payload.get("tenant_id"),
            "allowed_roles": h.payload.get("allowed_roles"),
            "allowed_users": h.payload.get("allowed_users"),
        }
        for h in hits
    ]


def _answer_from_chunks(question, chunks, model):
    context = "\n\n".join(f"[{c['chunk_id']}]\n{c['text']}" for c in chunks)
    return generate(PROMPT.format(context=context, question=question), model=model)


def answer_question(question, query_filter=None, model=config.LARGE_MODEL):
    """Baseline (no user, no permissions). Kept so Phase 1 results stay reproducible."""
    chunks = retrieve(question, query_filter)
    return {"answer": _answer_from_chunks(question, chunks, model), "sources": chunks}


def secure_answer(user, question, request_id, model=config.LARGE_MODEL, k=config.TOP_K):
    """Permission-aware answer: pre-filter -> second check -> LLM -> audit log."""
    # 1) Pre-filter: Qdrant never even sees chunks this user may not read
    chunks = retrieve(question, build_filter(user), k)

    # 2) Defense in depth: re-check every chunk in code before building the prompt
    allowed, blocked = enforce_acl(user, chunks)
    if blocked:
        log.error(
            "ACL VIOLATION: filter returned %d forbidden chunk(s) for user=%s: %s",
            len(blocked), user.id, [b["chunk_id"] for b in blocked],
        )

    # 3) No permitted context -> don't call the LLM at all
    if allowed:
        answer = _answer_from_chunks(question, allowed, model)
        used_model = model
    else:
        answer = "I don't know."
        used_model = None

    # 4) Audit trail: who asked what, and which chunks were released
    audit.log_retrieval(request_id, user, question, allowed, used_model, len(blocked))
    return {"answer": answer, "sources": allowed, "blocked": len(blocked)}
