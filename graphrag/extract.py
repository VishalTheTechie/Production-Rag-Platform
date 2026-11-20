"""Step 3. Asks an LLM to pull entities and relations out of every paragraph, using a small FIXED
schema. Results are saved line by line, so you can stop and resume at any time (free-tier limits!).
Usage: python -m graphrag.extract"""
import json
import re
import time
from typing import Literal

from pydantic import BaseModel

import config
from graphrag import settings
from llm import generate_ex

EntityType = Literal["PERSON", "ORG", "LOCATION", "WORK", "EVENT", "DATE", "OTHER"]
RelationType = Literal[
    "BORN_IN", "DIED_IN", "LOCATED_IN", "DIRECTED", "CREATED", "MEMBER_OF", "WORKS_FOR",
    "FOUNDED", "PART_OF", "RELEASED_IN", "SPOUSE_OF", "PARENT_OF", "PLAYED_FOR", "OTHER",
]
ENTITY_TYPES = set(EntityType.__args__)
RELATION_TYPES = set(RelationType.__args__)


class Entity(BaseModel):
    name: str
    type: EntityType = "OTHER"


class Relation(BaseModel):
    source: str
    type: RelationType = "OTHER"
    target: str


class Extraction(BaseModel):
    entities: list[Entity] = []
    relations: list[Relation] = []


PROMPT = """You extract a knowledge graph from a Wikipedia paragraph.
The paragraph is the introduction of the article titled "{title}". That title is the main subject entity.

Return ONLY JSON in exactly this shape:
{{"entities": [{{"name": "...", "type": "..."}}],
  "relations": [{{"source": "...", "type": "...", "target": "..."}}]}}

Entity types (use ONLY these): PERSON, ORG, LOCATION, WORK, EVENT, DATE, OTHER
  (WORK = film, book, album, song, TV show, play)
Relation types (use ONLY these): BORN_IN, DIED_IN, LOCATED_IN, DIRECTED, CREATED, MEMBER_OF,
  WORKS_FOR, FOUNDED, PART_OF, RELEASED_IN, SPOUSE_OF, PARENT_OF, PLAYED_FOR, OTHER

Rules:
- Always include the main subject "{title}" as an entity.
- Use the full name exactly as written in the paragraph. Only entities mentioned in the paragraph.
- Every relation's source and target must also appear in "entities".
- Prefer 5 to 15 entities and the important relations only.

Paragraph:
{text}"""


def load_json_or_salvage(raw: str) -> dict:
    """Parses the model's JSON. If the answer was cut off in the middle, keeps everything that was
    complete (entities/relations are list items, so the last complete '}' is a safe cut point)."""
    raw = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        cuts = [m.start() for m in re.finditer(r"\}", raw)][::-1][:40]
        for pos in cuts:
            try:
                return json.loads(raw[:pos + 1] + "]}")
            except json.JSONDecodeError:
                continue
        raise


def parse_extraction(raw: str, title: str) -> Extraction:
    """Lenient parser: unknown types become OTHER, broken items are dropped, endpoints are added."""
    data = load_json_or_salvage(raw)
    entities, seen = [], set()

    def add_entity(name, etype):
        name = (name or "").strip()
        if not name or name.lower() in seen:
            return
        etype = str(etype or "OTHER").upper()
        entities.append(Entity(name=name, type=etype if etype in ENTITY_TYPES else "OTHER"))
        seen.add(name.lower())

    for e in data.get("entities", []):
        if isinstance(e, dict):
            add_entity(e.get("name"), e.get("type"))
    add_entity(title, "OTHER")                       # the subject is always present

    relations = []
    for r in data.get("relations", []):
        if not isinstance(r, dict):
            continue
        src, tgt = (r.get("source") or "").strip(), (r.get("target") or "").strip()
        if not src or not tgt or src.lower() == tgt.lower():
            continue
        rtype = str(r.get("type") or "OTHER").upper()
        add_entity(src, "OTHER")
        add_entity(tgt, "OTHER")
        relations.append(Relation(source=src, target=tgt, type=rtype if rtype in RELATION_TYPES else "OTHER"))
    return Extraction(entities=entities, relations=relations)


def load_done():
    done = set()
    if settings.EXTRACTIONS_FILE.exists():
        for line in settings.EXTRACTIONS_FILE.read_text(encoding="utf-8").splitlines():
            if line.strip():
                done.add(json.loads(line)["chunk_id"])
    return done


def main():
    corpus = json.loads(settings.CORPUS_FILE.read_text(encoding="utf-8"))
    done = load_done()
    todo = [c for c in corpus if c["chunk_id"] not in done]
    print(f"{len(done)} paragraphs already done, {len(todo)} to go")
    failures = 0
    for i, c in enumerate(todo, 1):
        ex, r = None, None
        for attempt in range(3):                          # empty / broken answers are retried
            try:
                r = generate_ex(PROMPT.format(title=c["title"], text=c["text"]), model=config.SMALL_MODEL,
                                json_mode=True, strict_json=True, reasoning_effort="low")
            except RuntimeError as e:
                print(f"\nStopped: {e}\nProgress is saved. Run the same command again later.")
                return
            try:
                ex = parse_extraction(r["text"], c["title"])
                break
            except Exception as e:
                print(f"  {c['chunk_id']}: unreadable answer ({str(e)[:50]}), attempt {attempt + 1}/3")
        if ex is None:
            failures += 1
            continue
        rec = {"chunk_id": c["chunk_id"], "title": c["title"], "entities": [x.model_dump() for x in ex.entities],
               "relations": [x.model_dump() for x in ex.relations], "input_tokens": r["input_tokens"],
               "output_tokens": r["output_tokens"], "model": r["model"]}
        with open(settings.EXTRACTIONS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
        print(f"{i}/{len(todo)} {c['title'][:40]:40} {len(ex.entities)} entities, {len(ex.relations)} relations")
        time.sleep(1)
    print(f"\nDone. Unreadable answers this run: {failures} (run again to retry them)")


if __name__ == "__main__":
    main()
