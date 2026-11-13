"""Decides whether a question is 'simple' (small model) or 'complex' (large model)."""
import re

import config
from llm import generate_ex

COMPLEX_WORDS = [
    "compare", "comparison", "difference", "differences", "versus", "vs", "why", "explain",
    "summarize", "summarise", "summary", "relationship", "impact", "implications", "analyze",
    "analyse", "contrast", "both", "between", "overall", "how does", "how do", "trade-off",
]


def features(query, scores, flat_gap=None):
    flat_gap = config.FLAT_GAP if flat_gap is None else flat_gap
    q = query.lower()
    return {
        "n_words": len(re.findall(r"\w+", q)),
        "and_count": len(re.findall(r"\band\b", q)),
        "keyword": any(re.search(rf"\b{re.escape(w)}\b", q) for w in COMPLEX_WORDS),
        "multi_q": query.count("?") >= 2,
        # flat retrieval scores = no clear best chunk = harder question
        "flat": len(scores) >= 2 and (scores[0] - scores[-1]) < flat_gap,
    }


def classify_rules(query, scores, flat_gap=None):
    f = features(query, scores, flat_gap)
    points = (
        (1 if f["n_words"] > 22 else 0)
        + (1 if f["and_count"] >= 2 else 0)
        + (2 if f["keyword"] else 0)
        + (1 if f["multi_q"] else 0)
        + (1 if f["flat"] else 0)
    )
    return "complex" if points >= 2 else "simple"


def classify_llm(query):
    """Tiny-LLM classifier. Returns (route, llm_result) so its cost can be counted."""
    prompt = (
        "Classify this question about company documents.\n"
        "SIMPLE = asks for one fact that sits in one place.\n"
        "COMPLEX = needs comparing, explaining, or combining several facts.\n"
        f"Question: {query}\nReply with exactly one word: SIMPLE or COMPLEX."
    )
    r = generate_ex(prompt, model=config.SMALL_MODEL)
    return ("complex" if "COMPLEX" in r["text"].upper() else "simple"), r
