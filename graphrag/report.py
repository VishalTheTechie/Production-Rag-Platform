"""Step 7. Compares all methods you have run and writes graphrag/compare_report.md.
Usage: python -m graphrag.report"""
import json

import pandas as pd

from graphrag import settings
from metrics import cost_usd

METHODS = ["baseline", "rerank", "hybrid", "decompose"]
LABELS = {"baseline": "Vector RAG (baseline)", "rerank": "Vector + rerank", "hybrid": "GraphRAG (hybrid)",
          "decompose": "GraphRAG + decomposition"}


def indexing_cost():
    tin = tout = 0
    cost = 0.0
    for line in settings.EXTRACTIONS_FILE.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            tin += r["input_tokens"]
            tout += r["output_tokens"]
            cost += cost_usd(r["model"], r["input_tokens"], r["output_tokens"])
    return tin, tout, cost


def table(frames, subset):
    lines = [f"| Method | Questions | Exact match | F1 | Support recall | All support found | Cost / query ($) |",
             "|---|---|---|---|---|---|---|"]
    for m, df in frames.items():
        d = df[df["type"] == subset]
        if d.empty:
            continue
        lines.append(f"| {LABELS[m]} | {len(d)} | {d.em.mean():.1%} | {d.f1.mean():.3f} | "
                     f"{d.support_recall.mean():.1%} | {d.all_support_found.mean():.1%} | {d.cost_usd.mean():.5f} |")
    return "\n".join(lines)


def main():
    frames = {m: pd.read_csv(settings.DATA_DIR / f"results_{m}.csv") for m in METHODS
              if (settings.DATA_DIR / f"results_{m}.csv").exists()}
    if "baseline" not in frames:
        print("Run: python -m graphrag.evaluate baseline  first")
        return
    stats = json.loads(settings.GRAPH_FILE.read_text(encoding="utf-8"))["stats"]
    tin, tout, cost = indexing_cost()

    out = ["## Multi-hop questions (HotpotQA bridge)", table(frames, "bridge"),
           "", "## Single-hop control questions", table(frames, "single_hop"),
           "", "## One-time indexing cost (GraphRAG only)",
           f"- Paragraphs processed by the LLM: {sum(1 for _ in open(settings.EXTRACTIONS_FILE, encoding='utf-8'))}",
           f"- Tokens: {tin:,} in / {tout:,} out  (simulated cost ${cost:.4f})",
           f"- Graph: {stats['entities_after_merging']} entities after merging "
           f"({stats['names_before_merging']} distinct names before), {stats['relations']} relations, "
           f"{stats['mentions']} chunk-entity links"]
    text = "\n".join(out)
    print(text)
    (settings.DATA_DIR / "compare_report.md").write_text(text, encoding="utf-8")
    print("\nSaved graphrag/data/compare_report.md")


if __name__ == "__main__":
    main()
