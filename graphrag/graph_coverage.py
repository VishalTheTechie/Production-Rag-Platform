"""How many multi-hop questions have their two key paragraphs connected in your graph?
If this number is low, GraphRAG cannot help much. Usage: python graph_coverage.py"""
import json

from graphrag import settings

corpus = {c["title"]: c["chunk_id"] for c in json.loads(settings.CORPUS_FILE.read_text(encoding="utf-8"))}
graph = json.loads(settings.GRAPH_FILE.read_text(encoding="utf-8"))
ents = {}
for m in graph["mentions"]:
    ents.setdefault(m["chunk_id"], set()).add(m["entity_id"])
rel = {(r["source_id"], r["target_id"]) for r in graph["relations"]}
rel |= {(b, a) for a, b in rel}
questions = [q for q in json.loads(settings.QUESTIONS_FILE.read_text(encoding="utf-8")) if q["type"] == "bridge"]

shared = linked = 0
for q in questions:
    a, b = (ents.get(corpus[t], set()) for t in q["support_titles"][:2])
    if a & b:
        shared += 1
    elif any((x, y) in rel for x in a for y in b):
        linked += 1
total = len(questions)
print(f"{total} multi-hop questions")
print(f"  key paragraphs share an entity:       {shared}  ({shared / total:.0%})")
print(f"  connected by a relation (1 hop):      {linked}  ({linked / total:.0%})")
print(f"  NOT connected in the graph:           {total - shared - linked}  ({(total - shared - linked) / total:.0%})")
