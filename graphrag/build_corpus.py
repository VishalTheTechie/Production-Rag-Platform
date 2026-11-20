"""Step 1. Downloads HotpotQA and builds a small corpus + question file.
For each chosen 'bridge' question we keep its 2 gold paragraphs and a few distractor paragraphs.
Usage: python -m graphrag.build_corpus"""
import json
import os
import random
import urllib.request

from graphrag import settings

JSON_URL = "http://curtis.ml.cmu.edu/datasets/hotpot/hotpot_dev_distractor_v1.json"


def rows_from_hf():
    from datasets import load_dataset
    # streaming=True reads only the validation file (a normal load also downloads the huge training files)
    ds = load_dataset("hotpotqa/hotpot_qa", "distractor", split="validation", streaming=True)
    rows = []
    for r in ds:
        rows.append({
            "id": r["id"], "question": r["question"], "answer": r["answer"], "type": r["type"],
            "context": list(zip(r["context"]["title"], r["context"]["sentences"])),
            "support_titles": sorted(set(r["supporting_facts"]["title"])),
        })
    return rows


def rows_from_json():
    print("Downloading the official HotpotQA file (about 45 MB)...")
    with urllib.request.urlopen(JSON_URL, timeout=120) as f:
        data = json.loads(f.read().decode("utf-8"))
    return [{
        "id": r["_id"], "question": r["question"], "answer": r["answer"], "type": r["type"],
        "context": [(t, s) for t, s in r["context"]],
        "support_titles": sorted({t for t, _ in r["supporting_facts"]}),
    } for r in data]


def load_rows():
    if os.getenv("HOTPOT_SOURCE", "").lower() == "json":      # set HOTPOT_SOURCE=json to skip Hugging Face
        return rows_from_json()
    try:
        return rows_from_hf()
    except Exception as e:
        print(f"Hugging Face download failed ({str(e)[:100]}). Trying the official file...")
        return rows_from_json()


def select(rows, n_questions, n_distractors, seed):
    rng = random.Random(seed)
    bridge = [r for r in rows if r["type"] == "bridge"]
    chosen = rng.sample(bridge, min(n_questions, len(bridge)))
    paragraphs, questions = {}, []
    for r in chosen:
        ctx = {title: " ".join(s.strip() for s in sents).strip() for title, sents in r["context"]}
        gold = [t for t in r["support_titles"] if t in ctx]
        others = sorted(t for t in ctx if t not in gold)
        keep = gold + rng.sample(others, min(n_distractors, len(others)))
        for t in keep:
            paragraphs.setdefault(t, ctx[t])
        questions.append({"id": r["id"], "question": r["question"], "answer": r["answer"],
                          "type": "bridge", "support_titles": gold})
    corpus = [{"chunk_id": f"p{i:04d}", "title": t, "text": f"{t}: {p}"}
              for i, (t, p) in enumerate(sorted(paragraphs.items()))]
    return corpus, questions


def main():
    rows = load_rows()
    print(f"Loaded {len(rows)} HotpotQA questions")
    corpus, questions = select(rows, settings.N_MULTIHOP, settings.N_DISTRACTORS, settings.SEED)
    settings.CORPUS_FILE.write_text(json.dumps(corpus, indent=1), encoding="utf-8")
    settings.QUESTIONS_FILE.write_text(json.dumps(questions, indent=1), encoding="utf-8")
    print(f"Saved {len(corpus)} paragraphs and {len(questions)} multi-hop questions to {settings.DATA_DIR}")


if __name__ == "__main__":
    main()
