"""Chunks every document, embeds it, stores it in Qdrant WITH its access metadata."""
import json
from pathlib import Path
from qdrant_client import QdrantClient, models
import config
from embeddings import embed

def chunk_text(text, size=config.CHUNK_WORDS, overlap=config.CHUNK_OVERLAP):
    words = text.split()
    chunks, start = [], 0
    while start < len(words):
        chunks.append(" ".join(words[start:start + size]))
        if start + size >= len(words):
            break
        start += size - overlap
    return chunks

def main():
    client = QdrantClient(url=config.QDRANT_URL)
    if client.collection_exists(config.COLLECTION):
        client.delete_collection(config.COLLECTION)
    client.create_collection(
        collection_name=config.COLLECTION,
        vectors_config=models.VectorParams(size=config.EMBED_DIM, distance=models.Distance.COSINE),
    )
    # Indexes keep permission filtering fast (used in Project 2)
    for field in ["tenant_id", "allowed_roles", "allowed_users", "doc_id"]:
        client.create_payload_index(
            collection_name=config.COLLECTION,
            field_name=field,
            field_schema=models.PayloadSchemaType.KEYWORD,
        )

    manifest = json.loads(Path("data/manifest.json").read_text(encoding="utf-8"))
    point_id, total = 0, 0
    for doc in manifest:
        if not doc.get("tenant_id"):
            raise ValueError(f"{doc['doc_id']} has no tenant_id - refusing to ingest")
        chunks = chunk_text(Path(doc["path"]).read_text(encoding="utf-8"))
        vectors = embed(chunks)
        points = []
        for i, (text, vec) in enumerate(zip(chunks, vectors)):
            points.append(models.PointStruct(
                id=point_id,
                vector=vec,
                payload={
                    "chunk_id": f"{doc['doc_id']}#{i}",
                    "doc_id": doc["doc_id"],
                    "tenant_id": doc["tenant_id"],
                    "classification": doc["classification"],
                    "allowed_roles": doc["allowed_roles"],
                    "allowed_users": doc["allowed_users"],
                    "text": text,
                },
            ))
            point_id += 1
        client.upsert(collection_name=config.COLLECTION, points=points)
        total += len(points)
        print(f"{doc['doc_id']}: {len(points)} chunks")
    print(f"Done. {total} chunks stored.")


if __name__ == "__main__":
    main()
