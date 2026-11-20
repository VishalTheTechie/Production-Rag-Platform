"""Step 5. Loads chunks, entities and relations into Neo4j and builds the vector index.
Graph: (:Chunk)-[:MENTIONS]->(:Entity)   (:Entity)-[:REL {type, chunk_id}]->(:Entity)
Usage: python -m graphrag.load_graph"""
import json

from neo4j import GraphDatabase

from embeddings import embed
from graphrag import settings


def batches(items, n=200):
    for i in range(0, len(items), n):
        yield items[i:i + n]


def main():
    corpus = json.loads(settings.CORPUS_FILE.read_text(encoding="utf-8"))
    graph = json.loads(settings.GRAPH_FILE.read_text(encoding="utf-8"))
    print("Embedding paragraphs...")
    vectors = embed([c["text"] for c in corpus])
    rows = [dict(c, embedding=v) for c, v in zip(corpus, vectors)]

    driver = GraphDatabase.driver(settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD))
    with driver.session() as s:
        s.run("MATCH (n) DETACH DELETE n").consume()
        s.run("CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (c:Chunk) REQUIRE c.id IS UNIQUE").consume()
        s.run("CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE").consume()
        s.run(
            "CREATE VECTOR INDEX chunk_embedding IF NOT EXISTS FOR (c:Chunk) ON (c.embedding) "
            "OPTIONS {indexConfig: {`vector.dimensions`: %d, `vector.similarity_function`: 'cosine'}}"
            % settings.EMBED_DIM
        ).consume()

        for b in batches(rows):
            s.run("UNWIND $rows AS r CREATE (c:Chunk {id: r.chunk_id, title: r.title, text: r.text, "
                  "embedding: r.embedding})", {"rows": b}).consume()
        for b in batches(graph["entities"]):
            s.run("UNWIND $rows AS r CREATE (e:Entity {id: r.id, name: r.name, type: r.type, "
                  "aliases: r.aliases})", {"rows": b}).consume()
        for b in batches(graph["mentions"]):
            s.run("UNWIND $rows AS r MATCH (c:Chunk {id: r.chunk_id}), (e:Entity {id: r.entity_id}) "
                  "MERGE (c)-[:MENTIONS]->(e)", {"rows": b}).consume()
        for b in batches(graph["relations"]):
            s.run("UNWIND $rows AS r MATCH (a:Entity {id: r.source_id}), (b:Entity {id: r.target_id}) "
                  "CREATE (a)-[:REL {type: r.type, chunk_id: r.chunk_id}]->(b)", {"rows": b}).consume()
        s.run("CALL db.awaitIndexes(300)").consume()
        counts = s.run("MATCH (c:Chunk) WITH count(c) AS chunks MATCH (e:Entity) WITH chunks, count(e) AS entities "
                       "MATCH ()-[r:REL]->() RETURN chunks, entities, count(r) AS relations").data()
        print("Loaded:", counts)
    driver.close()


if __name__ == "__main__":
    main()
