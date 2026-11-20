"""Step 6. Runs every question through one method and scores it.
Usage: python -m graphrag.evaluate baseline      (then: rerank, hybrid, decompose)
Saves after every question; run the same command again to resume."""
import json
import sys
import time

import pandas as pd

from graphrag import pipeline, settings
from graphrag.store import GraphStore
from graphrag.textutils import exact_match, f1_score
from metrics import cost_usd


def main():
    method = sys.argv[1] if len(sys.argv) > 1 else "baseline"
    questions = json.loads(settings.QUESTIONS_FILE.read_text(encoding="utf-8"))
    out_path = settings.DATA_DIR / f"results_{method}.csv"
    rows, done = [], set()
    if out_path.exists():
        old = pd.read_csv(out_path)
        rows, done = old.to_dict("records"), set(old["id"])
        print(f"Resuming: {len(done)} questions done")

    store = GraphStore()
    for i, q in enumerate(questions, 1):
        if q["id"] in done:
            continue
        try:
            res = pipeline.run(store, method, q["question"])
        except RuntimeError as e:
            print(f"\nStopped: {e}\nProgress is saved. Run the same command again later.")
            break
        gold = set(q["support_titles"])
        found = {c["title"] for c in res["chunks"]}
        recall = len(gold & found) / len(gold)
        first_model = res["models"].split(",")[0] if res["models"] else ""
        rows.append({
            "id": q["id"], "type": q["type"], "question": q["question"], "gold": q["answer"],
            "pred": res["pred"], "em": exact_match(res["pred"], q["answer"]),
            "f1": round(f1_score(res["pred"], q["answer"]), 4), "support_recall": round(recall, 3),
            "all_support_found": float(recall == 1.0), "latency_s": round(res["latency_s"], 2),
            "input_tokens": res["input_tokens"], "output_tokens": res["output_tokens"],
            "cost_usd": cost_usd(first_model, res["input_tokens"], res["output_tokens"]),
        })
        pd.DataFrame(rows).to_csv(out_path, index=False, encoding="utf-8")
        print(f"{i}/{len(questions)} [{q['type']}] EM={rows[-1]['em']:.0f} F1={rows[-1]['f1']:.2f} "
              f"support={recall:.1f}  pred={res['pred'][:40]!r} gold={q['answer'][:40]!r}")
        time.sleep(1)
    store.close()


if __name__ == "__main__":
    main()
