"""Compares the two runs and writes eval/compare_report.md (paste it into your README)."""
import metrics


def summarize(df):
    return {
        "Requests": len(df),
        "Cache hit rate": df.cache_hit.mean(),
        "Avg cost / request ($)": df.cost_usd.mean(),
        "Total cost ($)": df.cost_usd.sum(),
        "p50 latency (s)": df.latency_ms.quantile(0.50) / 1000,
        "p95 latency (s)": df.latency_ms.quantile(0.95) / 1000,
        "Answer correctness": df.correct.dropna().mean(),
    }


def pct(new, old):
    return (new - old) / old * 100 if old else float("nan")


def main():
    base = metrics.load("compare_baseline")
    opt = metrics.load("compare_optimized")
    if base.empty or opt.empty:
        print("Run python run_compare.py first.")
        return
    b, o = summarize(base), summarize(opt)

    lines = ["| Metric | Baseline (always large model) | Optimized (cache + routing) |", "|---|---|---|"]
    for k in b:
        fmt = (lambda v: f"{v:.1%}") if k in ("Cache hit rate", "Answer correctness") else \
              (lambda v: f"{v:.5f}") if "cost" in k.lower() else \
              (lambda v: f"{v:.2f}") if "latency" in k else (lambda v: f"{v:.0f}")
        lines.append(f"| {k} | {fmt(b[k])} | {fmt(o[k])} |")
    table = "\n".join(lines)

    non_cached = opt[opt.cache_hit == 0]
    split = non_cached.route.value_counts().to_dict()
    esc = non_cached[non_cached.route == "simple"].escalated.mean() if "simple" in split else 0

    summary = (
        f"\nCost reduction: {-pct(o['Total cost ($)'], b['Total cost ($)']):.1f}%\n"
        f"p95 latency change: {pct(o['p95 latency (s)'], b['p95 latency (s)']):+.1f}%\n"
        f"p50 latency change: {pct(o['p50 latency (s)'], b['p50 latency (s)']):+.1f}%\n"
        f"Quality change: {(o['Answer correctness'] - b['Answer correctness']) * 100:+.1f} points\n"
        f"Route split (non-cached requests): {split}\n"
        f"Simple-route answers escalated to the large model: {esc:.0%}\n"
    )
    print(table)
    print(summary)
    open("eval/compare_report.md", "w", encoding="utf-8").write(table + "\n" + summary)
    print("Saved eval/compare_report.md")


if __name__ == "__main__":
    main()
