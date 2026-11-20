"""Finds which graph entities a question mentions (simple, fast text matching)."""
from graphrag.textutils import norm_name


def build_entity_index(rows):
    """rows: [{'id','name','aliases'}] -> {normalized name: entity id}. Skips very short names."""
    index = {}
    for r in rows:
        for name in [r["name"]] + list(r.get("aliases") or []):
            n = norm_name(name)
            if len(n) >= 3 and not n.isdigit():
                index.setdefault(n, r["id"])
    return index


def link_entities(question, entity_index):
    """Returns ids of entities whose name appears in the question. Longest names win, so
    'Ed Wood' is not also matched as 'Wood'."""
    q = f" {norm_name(question)} "
    matched, ids = [], []
    for name in sorted(entity_index, key=len, reverse=True):
        if f" {name} " in q and not any(name in m for m in matched):
            matched.append(name)
            ids.append(entity_index[name])
    return ids
