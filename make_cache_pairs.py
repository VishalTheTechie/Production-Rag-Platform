"""For each eval question, asks the LLM for:
   - a PARAPHRASE (same meaning, different words)  -> should be a cache HIT
   - a NEAR-MISS (looks similar, different answer) -> must NOT be a cache hit
CHECK data/cache_pairs.json BY HAND afterwards and delete or fix bad pairs."""
import json
import time
from pathlib import Path

from llm import generate

PROMPT = """Original question about a company document:
{q}

Write two new questions and return ONLY JSON like
{{"paraphrase": "...", "near_miss": "..."}}

paraphrase: the SAME question in different words. Same meaning, same answer.
near_miss: a question that looks very similar (same company, same sentence structure) but asks for
a DIFFERENT fact, or changes one key detail (level, tier, severity, quarter, number) so that the
correct answer is different."""

OUT = Path("data/cache_pairs.json")


def main():
    questions = json.loads(Path("eval/questions.json").read_text(encoding="utf-8"))
    pairs = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else []
    done = {p["original"] for p in pairs}
    for i, q in enumerate(questions, 1):
        if q["question"] in done:
            continue
        raw = generate(PROMPT.format(q=q["question"]), json_mode=True)
        try:
            item = json.loads(raw)
            pairs.append({
                "original": q["question"],
                "paraphrase": item["paraphrase"],
                "near_miss": item["near_miss"],
                "doc_id": q["doc_id"],
                "tenant_id": q["tenant_id"],
            })
        except Exception as e:
            print("  skipped (bad JSON):", e)
            continue
        OUT.write_text(json.dumps(pairs, indent=2), encoding="utf-8")
        print(f"{i}/{len(questions)} done")
        time.sleep(2)
    print(f"Saved {len(pairs)} pairs to {OUT}")


if __name__ == "__main__":
    main()
