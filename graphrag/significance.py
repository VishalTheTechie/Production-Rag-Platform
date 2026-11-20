"""Is the improvement real, or luck with only 60 questions?
Paired bootstrap: re-draws the questions 10,000 times and checks whether the difference stays above zero.
Usage: python -m graphrag.significance"""
import numpy as np
import pandas as pd

from graphrag import settings

PAIRS = [("baseline", "hybrid"), ("baseline", "rerank"), ("rerank", "hybrid")]
METRICS = ["f1", "em", "support_recall"]

def load(method):
    df = pd.read_csv(settings.DATA_DIR / f"results_{method}.csv")
    return df[df["type"] == "bridge"].set_index("id")


def main():
    rng = np.random.default_rng(0)
    for a, b in PAIRS:
        try:
            first, second = load(a), load(b)
        except FileNotFoundError:
            continue
        ids = first.index.intersection(second.index)
        print(f"\n{b} vs {a}  ({len(ids)} multi-hop questions)")
        for metric in METRICS:
            diff = (second.loc[ids, metric] - first.loc[ids, metric]).to_numpy(dtype=float)
            boots = [rng.choice(diff, size=len(diff), replace=True).mean() for _ in range(10000)]
            lo, hi = np.percentile(boots, [2.5, 97.5])
            verdict = "clearly better" if lo > 0 else ("clearly worse" if hi < 0 else "not clearly different")
            print(f"  {metric:15} mean difference {diff.mean():+.3f}   95% CI [{lo:+.3f}, {hi:+.3f}]   {verdict}")


if __name__ == "__main__":
    main()
