"""Usage: python run_eval_secure.py project2 [limit]
Same questions, same judge as the baseline, but through the permission-aware pipeline.
Each question is asked as the ADMIN of its own company, so it is allowed to see the answer.
Goal: show that security did not reduce answer quality."""
import json
import sys
import time
import uuid
from pathlib import Path

import pandas as pd

import auth
from llm import generate
from rag import secure_answer
from run_eval import JUDGE


def main():
    label = sys.argv[1] if len(sys.argv) > 1 else "project2"
    out_path = Path(f"eval/results_{label}.csv")
    questions = json.loads(Path("eval/questions.json").read_text(encoding="utf-8"))
    if len(sys.argv) > 2:
        questions = questions[: int(sys.argv[2])]

    rows, done = [], set()
    if out_path.exists():
        old = pd.read_csv(out_path)
        rows, done = old.to_dict("records"), set(old["question"])
        print(f"Resuming: {len(done)} done")

    for i, q in enumerate(questions, 1):
        if q["question"] in done:
            continue
        user = auth.get_user(f"{q['tenant_id']}_admin")
        start = time.time()
        res = secure_answer(user, q["question"], str(uuid.uuid4()))
        latency = time.time() - start
        hit = q["doc_id"] in {s["doc_id"] for s in res["sources"]}
        verdict = generate(JUDGE.format(
            q=q["question"], ref=q["reference_answer"], ans=res["answer"]
        )).strip().upper()
        rows.append({
            "question": q["question"], "doc_id": q["doc_id"], "retrieval_hit": hit,
            "correct": verdict.startswith("CORRECT"), "latency_s": round(latency, 2),
            "answer": res["answer"],
        })
        pd.DataFrame(rows).to_csv(out_path, index=False, encoding="utf-8")
        print(f"{i}/{len(questions)} hit={hit} correct={rows[-1]['correct']}")
        time.sleep(2)

    df = pd.DataFrame(rows)
    print("\n=== SUMMARY ===")
    print("Retrieval hit rate:", round(df.retrieval_hit.mean(), 3))
    print("Answer correctness:", round(df.correct.mean(), 3))
    print("Avg latency (s):", round(df.latency_s.mean(), 2))


if __name__ == "__main__":
    main()
