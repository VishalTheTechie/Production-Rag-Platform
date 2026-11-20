import json

import numpy as np

from graphrag import build_corpus, resolve
from graphrag.extract import parse_extraction
from graphrag.linking import build_entity_index, link_entities
from graphrag.textutils import exact_match, f1_score, norm_name, normalize_answer


def test_norm_name():
    assert norm_name("The Beatles") == "beatles"
    assert norm_name("Beyoncé!") == "beyonce"
    assert norm_name("  Ed   Wood, Jr. ") == "ed wood jr"


def test_answer_metrics():
    assert normalize_answer("The Eiffel Tower.") == "eiffel tower"
    assert exact_match("the eiffel tower", "Eiffel Tower") == 1.0
    assert abs(f1_score("Eiffel Tower in Paris", "Eiffel Tower") - 2 / 3) < 1e-9   # precision 0.5, recall 1.0
    assert f1_score("yes", "no") == 0.0
    assert f1_score("", "x") == 0.0


def test_parse_extraction_is_lenient():
    raw = '''```json
    {"entities": [{"name": "Ed Wood", "type": "person"}, {"name": "Plan 9", "type": "MOVIE"}, {"type": "PERSON"}],
     "relations": [{"source": "Ed Wood", "type": "directed", "target": "Plan 9"},
                   {"source": "Ed Wood", "type": "INVENTED_BY", "target": "Bela Lugosi"},
                   {"source": "X", "target": ""}]}
    ```'''
    ex = parse_extraction(raw, "Plan 9 from Outer Space")
    names = {e.name: e.type for e in ex.entities}
    assert names["Ed Wood"] == "PERSON"             # type upper-cased
    assert names["Plan 9"] == "OTHER"                # invented type -> OTHER
    assert "Plan 9 from Outer Space" in names        # subject always added
    assert "Bela Lugosi" in names                    # relation endpoint added
    assert {r.type for r in ex.relations} == {"DIRECTED", "OTHER"}
    assert len(ex.relations) == 2                    # the broken relation was dropped


def test_should_merge_rules():
    assert resolve.should_merge("j smith", "john smith", 0.75)                       # initial match
    assert resolve.should_merge("anne emily bergl", "emily bergl", 0.85)             # extra given name
    assert not resolve.should_merge("paris", "paris hilton", 0.85)                   # one-word subset: no
    assert not resolve.should_merge("apollo 11", "apollo 12", 0.97)                  # different numbers
    assert resolve.should_merge("beatles", "beetles", 0.95, "ORG")                   # spelling variant
    assert not resolve.should_merge("john smith", "jane smith", 0.80)                # different first names
    assert not resolve.should_merge("ian paisley", "ian paisley jr", 0.97)           # father vs son
    assert not resolve.should_merge("john jacob astor iii", "john jacob astor iv", 0.98)
    assert not resolve.should_merge("new york", "new york city", 0.97, "LOCATION")   # state vs city
    assert not resolve.should_merge("las vegas", "las vegas boulevard", 0.96, "LOCATION")
    assert not resolve.should_merge("leeds city f c", "leeds united f c", 0.96, "ORG")
    assert not resolve.should_merge("football league", "national football league nfl", 0.9, "ORG")
    assert resolve.should_merge("cambridge university", "university of cambridge", 0.90, "ORG")
    assert resolve.should_merge("futuresex lovesound", "futuresex lovesounds", 0.97, "WORK")


def test_resolve_merges_and_maps(monkeypatch):
    def fake_embed(names):                       # same first token -> identical vectors
        vocab = {}
        out = []
        for n in names:
            v = np.zeros(32)
            v[hash(n.split()[-1]) % 32] = 1.0    # vector depends on the LAST token only
            out.append(v.tolist())
        return out
    monkeypatch.setattr(resolve, "embed", fake_embed)
    ex = [
        {"chunk_id": "p1", "entities": [{"name": "John Smith", "type": "PERSON"}, {"name": "Paris", "type": "LOCATION"}],
         "relations": [{"source": "John Smith", "target": "Paris", "type": "BORN_IN"}]},
        {"chunk_id": "p2", "entities": [{"name": "J. Smith", "type": "PERSON"}, {"name": "the Paris", "type": "LOCATION"}],
         "relations": [{"source": "J. Smith", "target": "the Paris", "type": "LIVES"}]},
    ]
    graph, merged = resolve.resolve(ex)
    assert graph["stats"]["entities_after_merging"] == 2          # 'J. Smith'+'John Smith' merged; both Paris forms match exactly
    assert merged == [["j smith", "john smith"]]                  # only fuzzy merges are listed for hand-checking
    assert {m["chunk_id"] for m in graph["mentions"]} == {"p1", "p2"}
    assert len(graph["relations"]) == 2                           # one per chunk (different chunk ids)


def test_link_entities_prefers_longest_name():
    index = build_entity_index([
        {"id": "e1", "name": "Ed Wood", "aliases": []},
        {"id": "e2", "name": "Wood", "aliases": []},
        {"id": "e3", "name": "Plan 9 from Outer Space", "aliases": ["Plan 9"]},
        {"id": "e4", "name": "UK", "aliases": []},                # too short, ignored
    ])
    ids = link_entities("Who directed Plan 9 from Outer Space, and was Ed Wood the UK director?", index)
    assert set(ids) == {"e1", "e3"}


def test_select_builds_corpus_and_questions():
    rows = []
    for i in range(6):
        ctx = [(f"Gold{i}A", ["Sentence one.", "Two."]), (f"Gold{i}B", ["Other."])] + \
              [(f"Dist{i}_{j}", ["Filler."]) for j in range(6)]
        rows.append({"id": f"q{i}", "question": f"Question {i}?", "answer": f"A{i}", "type": "bridge" if i < 5 else "comparison",
                     "context": ctx, "support_titles": [f"Gold{i}A", f"Gold{i}B"]})
    corpus, questions = build_corpus.select(rows, n_questions=3, n_distractors=2, seed=1)
    assert len(questions) == 3 and all(q["type"] == "bridge" for q in questions)
    assert len(corpus) == 3 * (2 + 2)                              # 2 gold + 2 distractors each
    titles = {c["title"] for c in corpus}
    for q in questions:
        assert set(q["support_titles"]) <= titles
    assert all(c["text"].startswith(c["title"] + ": ") for c in corpus)


def test_truncated_json_is_salvaged():
    cut = ('{"entities": [{"name": "Ian Paisley Jr", "type": "PERSON"}, {"name": "Ulster", "type": "LOCATION"}], '
           '"relations": [{"source": "Ian Paisley Jr", "type": "BORN_IN", "target": "Ulster"}, '
           '{"source": "Ian Paisley Jr", "type": "MEMBER_OF", "target": "Democrat')
    ex = parse_extraction(cut, "Ian Paisley Jr")
    assert {e.name for e in ex.entities} >= {"Ian Paisley Jr", "Ulster"}
    assert len(ex.relations) == 1                    # the cut-off relation is dropped, the complete one kept


def test_empty_answer_still_raises():
    import pytest
    with pytest.raises(Exception):
        parse_extraction("", "Anything")
