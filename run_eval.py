"""Usage: python run_eval.py baseline
Scores retrieval hit rate + answer correctness and saves eval/results_<label>.csv"""
import json
import sys
import time
from pathlib import Path
import pandas as pd
from rag import answer_question
from llm import generate

JUDGE = """Question: {q}
Reference answer: {ref}
Model answer: {ans}

Does the model answer agree with the reference answer on the key facts?
Reply with exactly one word: CORRECT or INCORRECT."""


def main():
    label = sys.argv[1] if len(sys.argv) > 1 else "baseline"
    questions = json.loads(Path("eval/questions.json").read_text(encoding="utf-8"))
    rows = []
    for i, q in enumerate(questions, 1):
        start = time.time()
        result = answer_question(q["question"])
        latency = time.time() - start
        hit = q["doc_id"] in {s["doc_id"] for s in result["sources"]}
        verdict = generate(JUDGE.format(
            q=q["question"], ref=q["reference_answer"], ans=result["answer"]
        )).strip().upper()
        rows.append({
            "question": q["question"],
            "doc_id": q["doc_id"],
            "retrieval_hit": hit,
            "correct": verdict.startswith("CORRECT"),
            "latency_s": round(latency, 2),
            "answer": result["answer"],
        })
        print(f"{i}/{len(questions)} hit={hit} correct={rows[-1]['correct']}")
        time.sleep(2)
        if len(sys.argv) > 2:
            questions = questions[:int(sys.argv[2])]
    df = pd.DataFrame(rows)
    df.to_csv(f"eval/results_{label}.csv", index=False)
    print("\n=== SUMMARY ===")
    print("Retrieval hit rate:", round(df.retrieval_hit.mean(), 3))
    print("Answer correctness:", round(df.correct.mean(), 3))
    print("Avg latency (s):", round(df.latency_s.mean(), 2))


if __name__ == "__main__":
    main()
