"""Semantic cache stored in its own Qdrant collection.
Every entry is tagged with an access 'scope' and a corpus version, so a cached answer is
only ever served to someone who could have received it from the full pipeline."""
import re
import time
import uuid

from qdrant_client import QdrantClient, models

import config
import corpus

client = QdrantClient(url=config.QDRANT_URL)
_personal = {}   # (user_id, corpus_version) -> has personal document grants?


def normalize(query: str) -> str:
    q = query.lower()
    q = re.sub(r"[^\w\s]", " ", q)
    return re.sub(r"\s+", " ", q).strip()


def ensure_collection():
    name = config.CACHE_COLLECTION
    if not client.collection_exists(name):
        client.create_collection(
            collection_name=name,
            vectors_config=models.VectorParams(size=config.EMBED_DIM, distance=models.Distance.COSINE),
        )
        for field in ("scope", "version"):
            client.create_payload_index(
                collection_name=name, field_name=field,
                field_schema=models.PayloadSchemaType.KEYWORD,
            )


def reset():
    if client.collection_exists(config.CACHE_COLLECTION):
        client.delete_collection(config.CACHE_COLLECTION)
    ensure_collection()


def access_scope(user) -> str:
    """Users with the same tenant and roles see the same documents, so they can share
    cache entries. A user who is personally named on a document gets a private scope."""
    key = (user.id, corpus.get_version())
    if key not in _personal:
        n = client.count(
            collection_name=config.COLLECTION,
            count_filter=models.Filter(must=[
                models.FieldCondition(key="allowed_users", match=models.MatchValue(value=user.id))
            ]),
            exact=True,
        ).count
        _personal[key] = n > 0
    scope = f"{user.tenant_id}|{','.join(sorted(user.roles))}"
    if _personal[key]:
        scope += f"|u:{user.id}"
    return scope


def cacheable(answer: str, sources) -> bool:
    """Never cache empty answers, 'I don't know', or answers without sources."""
    a = (answer or "").strip().lower().replace("\u2019", "'")
    if not a or a.startswith("i don't know") or a.startswith("i do not know"):
        return False
    return bool(sources)


def lookup(vec, scope):
    ensure_collection()
    flt = models.Filter(must=[
        models.FieldCondition(key="scope", match=models.MatchValue(value=scope)),
        models.FieldCondition(key="version", match=models.MatchValue(value=str(corpus.get_version()))),
        models.FieldCondition(key="created_at", range=models.Range(gte=time.time() - config.CACHE_TTL_SECONDS)),
    ])
    pts = client.query_points(
        collection_name=config.CACHE_COLLECTION, query=vec, query_filter=flt, limit=1
    ).points
    if pts and pts[0].score >= config.CACHE_THRESHOLD:
        return {"similarity": pts[0].score, **pts[0].payload}
    return None


def store(vec, scope, query, answer, sources):
    ensure_collection()
    sources = [{"chunk_id": s["chunk_id"], "doc_id": s["doc_id"], "score": s["score"]} for s in sources]
    client.upsert(
        collection_name=config.CACHE_COLLECTION,
        points=[models.PointStruct(
            id=str(uuid.uuid4()),
            vector=vec,
            payload={
                "scope": scope,
                "version": str(corpus.get_version()),
                "created_at": time.time(),
                "query": query,
                "answer": answer,
                "sources": sources,
            },
        )],
    )
