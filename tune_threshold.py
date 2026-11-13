"""Sweeps the similarity threshold and shows the trade-off:
   paraphrase hit rate (higher is better) vs false hits on near-miss pairs (must be 0)."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from cache import normalize
from embeddings import embed


def main():
    pairs = json.loads(Path("data/cache_pairs.json").read_text(encoding="utf-8"))
    a = np.array(embed([normalize(p["original"]) for p in pairs]))
    b = np.array(embed([normalize(p["paraphrase"]) for p in pairs]))
    c = np.array(embed([normalize(p["near_miss"]) for p in pairs]))
    para_sim = (a * b).sum(axis=1)       # vectors are normalized -> dot product = cosine
    near_sim = (a * c).sum(axis=1)

    rows = []
    for t in np.arange(0.80, 0.995, 0.01):
        rows.append({
            "threshold": round(float(t), 2),
            "paraphrase_hit_rate": round(float((para_sim >= t).mean()), 3),
            "false_hits": int((near_sim >= t).sum()),
            "false_hit_rate": round(float((near_sim >= t).mean()), 3),
        })
    df = pd.DataFrame(rows)
    df.to_csv("eval/threshold_sweep.csv", index=False)
    print(df.to_string(index=False))
    print(f"\nParaphrase similarity: min {para_sim.min():.3f}, median {np.median(para_sim):.3f}")
    print(f"Near-miss similarity:  median {np.median(near_sim):.3f}, max {near_sim.max():.3f}")

    safe = df[df.false_hits == 0]
    if safe.empty:
        print("\nNo threshold in this range gives zero false hits. Raise the range or fix the pairs.")
        return
    best = safe.iloc[0]
    print(f"\nLowest threshold with ZERO false hits: {best.threshold} "
          f"(paraphrase hit rate {best.paraphrase_hit_rate})")
    print(f"Put this in .env:  CACHE_THRESHOLD={best.threshold}")


if __name__ == "__main__":
    main()
