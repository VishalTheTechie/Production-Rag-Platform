import json
import verifier
from cache import guard_ok

pairs = json.load(open("data/cache_pairs.json", encoding="utf-8"))
scores = verifier.same_question_scores([(p["original"], p["near_miss"]) for p in pairs])
for p, s in sorted(zip(pairs, scores), key=lambda x: -x[1])[:8]:
    print(f"{s:.2f} guard_ok={guard_ok(p['original'], p['near_miss'])}\n  A: {p['original']}\n  B: {p['near_miss']}\n")