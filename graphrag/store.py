"""Retrieval on top of Neo4j.
   vector_search  = plain vector RAG (the BASELINE)
   hybrid_retrieve = vector search + graph expansion + cross-encoder rerank (GRAPHRAG)"""
from neo4j import GraphDatabase

from embeddings import embed_one
from graphrag import settings
from graphrag.linking import build_entity_index, link_entities

_reranker = None


def get_reranker():
    global _reranker
    if _reranker is None:
        from sentence_transformers import CrossEncoder
        _reranker = CrossEncoder(settings.RERANK_MODEL)
    return _reranker


def rerank(question, chunks):
    """Re-scores chunks by reading the question and each chunk together."""
    if not chunks:
        return []
    scores = get_reranker().predict([(question, c["text"]) for c in chunks])
    ranked = []
    for c, s in zip(chunks, scores):
        ranked.append(dict(c, score=float(s)))
    return sorted(ranked, key=lambda c: -c["score"])


class GraphStore:
    def __init__(self):
        self.driver = GraphDatabase.driver(settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD))
        rows = self.run("MATCH (e:Entity) RETURN e.id AS id, e.name AS name, e.aliases AS aliases")
        self.entity_index = build_entity_index(rows)

    def run(self, query, params=None):
        with self.driver.session() as s:
            return s.run(query, params or {}).data()

    # ---- baseline ----
    def vector_search(self, question, k):
        return self.run(
            "CALL db.index.vector.queryNodes('chunk_embedding', $k, $vec) YIELD node, score "
            "RETURN node.id AS id, node.title AS title, node.text AS text, score",
            {"k": k, "vec": embed_one(question)},
        )

    # ---- graph pieces ----
    def entities_of_chunks(self, chunk_ids):
        rows = self.run("MATCH (c:Chunk)-[:MENTIONS]->(e:Entity) WHERE c.id IN $ids RETURN DISTINCT e.id AS id",
                        {"ids": list(chunk_ids)})
        return {r["id"] for r in rows}

    def expand(self, seed_ids, limit):
        """Walk up to MAX_HOPS relations away from the seed entities and collect the chunks that
        mention the entities found. More paths = more relevant."""
        return self.run(
            "MATCH (e:Entity) WHERE e.id IN $seed_ids "
            f"MATCH (e)-[:REL*0..{settings.MAX_HOPS}]-(n:Entity)<-[:MENTIONS]-(c:Chunk) "
            "RETURN c.id AS chunk_id, count(*) AS paths ORDER BY paths DESC LIMIT $limit",
            {"seed_ids": list(seed_ids), "limit": limit},
        )

    def chunks_by_ids(self, ids):
        if not ids:
            return []
        return self.run("MATCH (c:Chunk) WHERE c.id IN $ids RETURN c.id AS id, c.title AS title, c.text AS text",
                        {"ids": list(ids)})

    def triples(self, chunk_ids, limit=25):
        rows = self.run(
            "MATCH (a:Entity)-[r:REL]->(b:Entity) WHERE r.chunk_id IN $ids AND r.type <> 'OTHER' "
            "RETURN a.name AS source, r.type AS type, b.name AS target LIMIT $limit",
            {"ids": list(chunk_ids), "limit": limit},
        )
        return [f"{r['source']} -[{r['type']}]-> {r['target']}" for r in rows]

    # ---- the two retrieval strategies ----
    def hybrid_retrieve(self, question, k=settings.TOP_K):
        vec_hits = self.vector_search(question, settings.VECTOR_CANDIDATES)
        seeds = set(link_entities(question, self.entity_index))           # entities named in the question
        seeds |= self.entities_of_chunks([h["id"] for h in vec_hits[:3]])  # entities in the best chunks
        graph_rows = self.expand(seeds, settings.GRAPH_CANDIDATES) if seeds else []

        candidates = {h["id"]: h for h in vec_hits}
        missing = [r["chunk_id"] for r in graph_rows if r["chunk_id"] not in candidates]
        for c in self.chunks_by_ids(missing):
            candidates[c["id"]] = dict(c, score=0.0)
        return rerank(question, list(candidates.values()))[:k]

    def close(self):
        self.driver.close()
