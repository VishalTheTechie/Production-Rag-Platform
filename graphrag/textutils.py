"""Text helpers: entity-name cleaning and the standard HotpotQA answer metrics (EM and F1)."""
import re
import string
import unicodedata
from collections import Counter


def norm_name(name: str) -> str:
    """'The Beatles', 'beatles' and 'Beatles.' all become 'beatles'."""
    s = unicodedata.normalize("NFKD", name or "")
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return re.sub(r"^(the|a|an)\s+", "", s)


def normalize_answer(s: str) -> str:
    s = (s or "").lower()
    s = "".join(ch for ch in s if ch not in set(string.punctuation))
    s = re.sub(r"\b(a|an|the)\b", " ", s)
    return " ".join(s.split())


def exact_match(prediction: str, gold: str) -> float:
    return float(normalize_answer(prediction) == normalize_answer(gold))


def f1_score(prediction: str, gold: str) -> float:
    p, g = normalize_answer(prediction), normalize_answer(gold)
    special = ("yes", "no", "noanswer")
    if (p in special or g in special) and p != g:
        return 0.0
    p_tokens, g_tokens = p.split(), g.split()
    same = sum((Counter(p_tokens) & Counter(g_tokens)).values())
    if same == 0:
        return 0.0
    precision, recall = same / len(p_tokens), same / len(g_tokens)
    return 2 * precision * recall / (precision + recall)
