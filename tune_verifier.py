"""Finds a safe setting for the two-stage cache check.
Negatives = your LLM-written near-misses  +  every pair of DIFFERENT eval questions from the
same company (real questions that look alike). Goal: zero false hits, as many true hits as possible."""
import json
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

import config
import verifier
from cache import guard_ok, normalize
from embeddings import embed


def main():
    pairs = json.loads(Path("data/cache_pairs.json").read_text(encoding="utf-8"))
    qs = json.loads(Path("eval/questions.json").read_text(encoding="utf-8"))

    pos = [(p["original"], p["paraphrase"]) for p in pairs]
    neg = [(p["original"], p["near_miss"]) for p in pairs]
    by_tenant = {}
    for q in qs:
        by_tenant.setdefault(q["tenant_id"], []).append(q["question"])
    nat = [pair for v in by_tenant.values() for pair in combinations(v, 2)]
    print(f"{len(pos)} paraphrase pairs, {len(neg)} near-miss pairs, {len(nat)} natural different-question pairs")

    def vec_sim(pair_list):
        a = np.array(embed([normalize(x) for x, _ in pair_list]))
        b = np.array(embed([normalize(y) for _, y in pair_list]))
        return (a * b).sum(axis=1)

    ct = config.CACHE_THRESHOLD
    sims = {"pos": vec_sim(pos), "neg": vec_sim(neg), "nat": vec_sim(nat)}
    sets = {"pos": pos, "neg": neg, "nat": nat}

    # Stage 1 only (what you ran before)
    s1 = {k: sims[k] >= ct for k in sets}
    print(f"\nStage 1 only (vector >= {ct}):  paraphrase hits {s1['pos'].mean():.1%}, "
          f"false hits: near-miss {s1['neg'].sum()}/{len(neg)}, natural {s1['nat'].sum()}/{len(nat)}")

    # Stage 1 + number guard
    g = {k: np.array([guard_ok(a, b) for a, b in sets[k]]) for k in sets}
    s2 = {k: s1[k] & g[k] for k in sets}
    print(f"+ number guard:                paraphrase hits {s2['pos'].mean():.1%}, "
          f"false hits: near-miss {s2['neg'].sum()}/{len(neg)}, natural {s2['nat'].sum()}/{len(nat)}")

    # Stage 1 + guard + verifier (only score pairs that survived, to save time)
    print("\nScoring candidate pairs with the verifier model (first run downloads it)...")
    scores = {}
    for k in sets:
        idx = np.where(s2[k])[0]
        sc = np.zeros(len(sets[k]))
        if len(idx):
            sc[idx] = verifier.same_question_scores([sets[k][i] for i in idx])
        scores[k] = sc

    rows = []
    for vt in [0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99]:
        keep = {k: s2[k] & (scores[k] >= vt) for k in sets}
        rows.append({
            "verify_threshold": vt,
            "paraphrase_hit_rate": round(float(keep["pos"].mean()), 3),
            "false_hits_near_miss": int(keep["neg"].sum()),
            "false_hits_natural": int(keep["nat"].sum()),
        })
    df = pd.DataFrame(rows)
    df.to_csv("eval/verifier_sweep.csv", index=False)
    print(df.to_string(index=False))

    safe = df[(df.false_hits_near_miss == 0) & (df.false_hits_natural == 0)]
    if safe.empty:
        print("\nNo verify threshold gives zero false hits. Look at the pairs below and tell me what you see.")
    else:
        best = safe.iloc[0]
        print(f"\nLowest verify threshold with ZERO false hits: {best.verify_threshold} "
              f"(paraphrase hit rate {best.paraphrase_hit_rate})")
        print(f"Put this in .env:  VERIFY_THRESHOLD={best.verify_threshold}")

    # Show what still slips through, to help you inspect the pairs by hand
    vt = float(safe.iloc[0].verify_threshold) if not safe.empty else 0.5
    leftovers = [(sets[k][i], k) for k in ("neg", "nat") for i in np.where(s2[k] & (scores[k] >= vt))[0]]
    for (a, b), k in leftovers[:5]:
        print(f"  still matches [{k}]: {a!r}  <->  {b!r}")


if __name__ == "__main__":
    main()
