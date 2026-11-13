"""Checks how accurate the router is on ~100 labelled queries.
   simple  = your 54 eval questions (each asks for one fact)
   complex = data/complex_queries.json (40 multi-part questions)
Usage: python eval_router.py          (rules only)
       python eval_router.py --llm    (also tests the tiny-LLM classifier)
CHECK THE LABELS BY HAND: open the files and change any label you disagree with."""
import json
import sys
import time
from pathlib import Path

import config
from rag import retrieve
from router import classify_llm, classify_rules


def load():
    simple = [q["question"] for q in json.loads(Path("eval/questions.json").read_text(encoding="utf-8"))]
    complex_ = json.loads(Path("data/complex_queries.json").read_text(encoding="utf-8"))
    return [(q, "simple") for q in simple] + [(q, "complex") for q in complex_]


def accuracy(items, scores, gap):
    ok = sum(classify_rules(q, scores[q], gap) == label for q, label in items)
    return ok / len(items)


def main():
    items = load()
    print(f"{len(items)} labelled queries")
    scores = {q: [c["score"] for c in retrieve(q)] for q, _ in items}

    print("\nRules accuracy by retrieval-spread setting (FLAT_GAP):")
    for gap in (0.0, 0.05, 0.10, 0.15, 0.20):
        print(f"  FLAT_GAP={gap:<5} accuracy={accuracy(items, scores, gap):.3f}"
              + ("   (spread rule off)" if gap == 0.0 else ""))

    gap = config.FLAT_GAP
    wrong = [(q, label) for q, label in items if classify_rules(q, scores[q], gap) != label]
    tp = sum(1 for q, l in items if l == "complex" and classify_rules(q, scores[q], gap) == "complex")
    fn = sum(1 for q, l in items if l == "complex" and classify_rules(q, scores[q], gap) == "simple")
    fp = sum(1 for q, l in items if l == "simple" and classify_rules(q, scores[q], gap) == "complex")
    tn = sum(1 for q, l in items if l == "simple" and classify_rules(q, scores[q], gap) == "simple")
    print(f"\nAt FLAT_GAP={gap}: complex caught={tp}, complex missed={fn}, simple wrongly escalated={fp}, simple ok={tn}")
    print(f"Accuracy: {(tp + tn) / len(items):.3f}")
    for q, label in wrong[:10]:
        print(f"  WRONG (true={label}): {q}")

    if "--llm" in sys.argv:
        ok, tin, tout = 0, 0, 0
        for q, label in items:
            route, r = classify_llm(q)
            ok += route == label
            tin += r["input_tokens"]
            tout += r["output_tokens"]
            time.sleep(1)
        print(f"\nLLM classifier accuracy: {ok / len(items):.3f}  (tokens used: {tin} in / {tout} out)")
        print("Compare with the rules above: the LLM costs tokens and time on EVERY request.")


if __name__ == "__main__":
    main()
