"""Step 4. ENTITY RESOLUTION: merges duplicates such as 'J. Smith' / 'John Smith' / 'the Beatles',
then writes graphrag/data/graph_data.json. A graph full of duplicates cannot connect anything.
Usage: python -m graphrag.resolve"""
import json
from collections import Counter, defaultdict
from difflib import SequenceMatcher

import numpy as np

from embeddings import embed
from graphrag import settings
from graphrag.textutils import norm_name

NO_FUZZY = {"DATE", "OTHER"}      # dates and untyped things are only merged on exact name match


def initial_match(ta, tb):
    """['j','smith'] vs ['john','smith']"""
    if len(ta) != len(tb) or len(ta) < 2 or ta[-1] != tb[-1]:
        return False
    a, b = ta[0], tb[0]
    return (len(a) == 1 and b.startswith(a)) or (len(b) == 1 and a.startswith(b))


SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "v", "vi"}
STOP = {"of", "the", "and", "in", "at", "for", "f", "c", "fc", "inc", "llc", "ltd", "co", "corp",
        "company", "group", "academy"}          # words that do not change which entity it is
# if the only difference between two names is one of these words, they are different things
DISTINCT = {"city", "county", "state", "boulevard", "street", "avenue", "road", "airport", "league",
            "playoff", "semifinal", "song", "album", "film", "district", "region", "hospital"}


def should_merge(a: str, b: str, cos: float, etype: str = "PERSON") -> bool:
    ta, tb = a.split(), b.split()
    digits = lambda toks: [t for t in toks if any(ch.isdigit() for ch in t)]
    if digits(ta) != digits(tb):
        return False                                   # 'Apollo 11' is not 'Apollo 12'
    if {t for t in ta if t in SUFFIXES} != {t for t in tb if t in SUFFIXES}:
        return False                                   # 'John Astor III' is not 'John Astor IV'; 'Ian Paisley' is not 'Ian Paisley Jr'
    if etype == "PERSON" and initial_match(ta, tb) and cos >= 0.70:
        return True                                    # 'J. Smith' = 'John Smith'
    diff_a, diff_b = [t for t in ta if t not in tb], [t for t in tb if t not in ta]
    if diff_a and diff_b and SequenceMatcher(None, " ".join(diff_a), " ".join(diff_b)).ratio() < 0.8:
        return False                                   # each name has its own different word: 'Leeds City' vs 'Leeds United'
    if etype != "PERSON" and (set(diff_a) | set(diff_b)) & DISTINCT:
        return False                                   # 'New York' vs 'New York City', 'Las Vegas' vs 'Las Vegas Boulevard'
    if {t for t in ta if t not in STOP} == {t for t in tb if t not in STOP}:
        return True                                    # 'University of Cambridge' = 'Cambridge University'
    if cos >= 0.95:
        return True
    if etype == "PERSON":
        shorter, longer = (ta, tb) if len(ta) <= len(tb) else (tb, ta)
        return len(shorter) >= 2 and set(shorter) <= set(longer) and shorter[-1] == longer[-1] and cos >= 0.80
    return False


def resolve(extractions):
    surface, types = defaultdict(Counter), defaultdict(Counter)
    for ex in extractions:
        for e in ex["entities"]:
            n = norm_name(e["name"])
            if n:
                surface[n][e["name"].strip()] += 1
                types[n][e["type"]] += 1
    names = sorted(surface)
    typ = {n: types[n].most_common(1)[0][0] for n in names}
    parent = list(range(len(names)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    if names:
        vecs = np.array(embed(names))
        sims = vecs @ vecs.T
        ii, jj = np.where(np.triu(sims >= 0.70, k=1))
        for i, j in zip(ii, jj):
            if typ[names[i]] == typ[names[j]] and typ[names[i]] not in NO_FUZZY:
                if should_merge(names[i], names[j], float(sims[i, j]), typ[names[i]]):
                    parent[find(i)] = find(j)

    groups = defaultdict(list)
    for i, n in enumerate(names):
        groups[find(i)].append(n)
    entities, norm_to_id = [], {}
    for k, (root, members) in enumerate(sorted(groups.items())):
        surf, tcount = Counter(), Counter()
        for m in members:
            surf.update(surface[m])
            tcount.update(types[m])
        canonical = max(surf.items(), key=lambda kv: (kv[1], len(kv[0])))[0]
        eid = f"e{k:05d}"
        entities.append({"id": eid, "name": canonical, "type": tcount.most_common(1)[0][0],
                         "aliases": sorted(set(surf) - {canonical})})
        for m in members:
            norm_to_id[m] = eid

    mentions, relations = set(), set()
    for ex in extractions:
        for e in ex["entities"]:
            n = norm_name(e["name"])
            if n:
                mentions.add((ex["chunk_id"], norm_to_id[n]))
        for r in ex["relations"]:
            s, t = norm_name(r["source"]), norm_name(r["target"])
            if s in norm_to_id and t in norm_to_id and norm_to_id[s] != norm_to_id[t]:
                relations.add((norm_to_id[s], norm_to_id[t], r["type"], ex["chunk_id"]))

    merged_groups = [sorted(m) for m in groups.values() if len(m) > 1]
    stats = {"names_before_merging": len(names), "entities_after_merging": len(entities),
             "merged_groups": len(merged_groups), "mentions": len(mentions), "relations": len(relations)}
    return {
        "entities": entities,
        "mentions": [{"chunk_id": c, "entity_id": e} for c, e in sorted(mentions)],
        "relations": [{"source_id": s, "target_id": t, "type": ty, "chunk_id": c} for s, t, ty, c in sorted(relations)],
        "stats": stats,
    }, merged_groups


def main():
    extractions = [json.loads(line) for line in
                   settings.EXTRACTIONS_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
    graph, merged = resolve(extractions)
    settings.GRAPH_FILE.write_text(json.dumps(graph), encoding="utf-8")
    settings.MERGES_FILE.write_text("\n".join(" | ".join(g) for g in merged), encoding="utf-8")
    print(json.dumps(graph["stats"], indent=2))
    print(f"\nOpen {settings.MERGES_FILE} and check the merges by hand. Wrong merges hurt accuracy.")


if __name__ == "__main__":
    main()
