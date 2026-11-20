"""Step 2. Creates single-hop control questions (answerable from ONE paragraph), so you can show
the graph does not hurt easy questions. CHECK graphrag/data/questions.json BY HAND afterwards.
Usage: python -m graphrag.make_single_hop"""
import json
import random
import time

from graphrag import settings
from llm import generate

PROMPT = """Paragraph:
{text}

Write ONE factual question that can be answered using ONLY this paragraph.
Rules: name the subject explicitly (never say "the film" or "he"); the answer must be a short phrase
of 1 to 5 words. Return ONLY JSON like {{"question": "...", "answer": "..."}}"""


def main():
    corpus = {c["title"]: c for c in json.loads(settings.CORPUS_FILE.read_text(encoding="utf-8"))}
    questions = json.loads(settings.QUESTIONS_FILE.read_text(encoding="utf-8"))
    questions = [q for q in questions if q["type"] != "single_hop"]          # allows re-running
    gold_titles = sorted({t for q in questions for t in q["support_titles"]})
    random.Random(settings.SEED).shuffle(gold_titles)

    made = 0
    for title in gold_titles:
        if made >= settings.N_SINGLE_HOP:
            break
        raw = generate(PROMPT.format(text=corpus[title]["text"]), json_mode=True)
        try:
            item = json.loads(raw)
            questions.append({"id": f"single_{made:03d}", "question": item["question"],
                              "answer": item["answer"], "type": "single_hop",
                              "support_titles": [title]})
            made += 1
            print(f"{made}/{settings.N_SINGLE_HOP}  {item['question']}  ->  {item['answer']}")
        except Exception as e:
            print("  skipped (bad JSON):", e)
        time.sleep(1)
    settings.QUESTIONS_FILE.write_text(json.dumps(questions, indent=1), encoding="utf-8")
    print(f"Saved. Total questions: {len(questions)}")


if __name__ == "__main__":
    main()
