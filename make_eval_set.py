"""Uses Gemini to draft questions + reference answers for each document.
CHECK THE OUTPUT BY HAND - this file is the most valuable part of the repo."""
import json
import time
from pathlib import Path
from llm import generate

PROMPT = """Read this document and write 3 factual questions that can be answered from it,
with short reference answers. Each question must be self-contained and mention the company
name. Return ONLY a JSON list like:
[{{"question": "...", "answer": "..."}}]

Document:
{text}"""


def main():
    manifest = json.loads(Path("data/manifest.json").read_text(encoding="utf-8"))
    out = []
    for doc in manifest:
        raw = generate(PROMPT.format(text=Path(doc["path"]).read_text(encoding="utf-8")), json_mode=True)
        for item in json.loads(raw):
            out.append({
                "question": item["question"],
                "reference_answer": item["answer"],
                "doc_id": doc["doc_id"],
                "tenant_id": doc["tenant_id"],
                "classification": doc["classification"],
            })
        print("done", doc["doc_id"])
        time.sleep(4)
    Path("eval/questions.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Saved {len(out)} questions to eval/questions.json")


if __name__ == "__main__":
    main()
