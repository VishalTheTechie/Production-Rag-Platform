"""Replays the same traffic through the BASELINE and the OPTIMIZED pipeline.
Traffic = N questions asked 3 ways: original, paraphrased, original again (shuffled).
Usage: python run_compare.py [N]      (default N=30; resumes if it stops)"""
import json
import os
import random
import sys
import time
import uuid
from pathlib import Path

import auth
import cache
import metrics
import pipeline
from llm import generate
from run_eval import JUDGE

PAUSE_S = float(os.getenv("COMPARE_PAUSE_S", "4"))   # gap between requests, to avoid free-tier throttling


def build_workload(n):
    questions = json.loads(Path("eval/questions.json").read_text(encoding="utf-8"))
    pairs = {p["original"]: p["paraphrase"]
             for p in json.loads(Path("data/cache_pairs.json").read_text(encoding="utf-8"))}
    questions = [q for q in questions if q["question"] in pairs]
    questions = random.Random(7).sample(questions, min(n, len(questions)))
    originals = [(q["question"], q["reference_answer"], q["tenant_id"]) for q in questions]
    paraphrased = [(pairs[q], ref, t) for q, ref, t in originals]
    repeats = originals[:]
    random.Random(42).shuffle(repeats)
    return originals + paraphrased + repeats


def run(mode, workload):
    label = f"compare_{mode}"
    done = metrics.count_rows(label)
    if done == 0 and mode == "optimized":
        cache.reset()                      # start with a cold cache
    if done:
        print(f"[{mode}] resuming from request {done + 1}")
    for i, (q, ref, tenant) in enumerate(workload[done:], done + 1):
        user = auth.get_user(f"{tenant}_admin")
        res = pipeline.answer(user, q, str(uuid.uuid4()), mode=mode, run_label=label)
        verdict = generate(JUDGE.format(q=q, ref=ref, ans=res["answer"])).strip().upper()
        metrics.set_quality(res["metrics_id"], verdict.startswith("CORRECT"))
        print(f"[{mode}] {i}/{len(workload)} cache_hit={res['cache_hit']} route={res['route']} "
              f"cost=${res['cost_usd']:.5f} {res['latency_ms'] / 1000:.1f}s "
              f"correct={verdict.startswith('CORRECT')}")
        time.sleep(PAUSE_S)


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    workload = build_workload(n)
    print(f"Workload: {len(workload)} requests ({len(workload) // 3} questions x 3)")
    run("baseline", workload)
    run("optimized", workload)
    print("\nDone. Now run: python report.py")


if __name__ == "__main__":
    main()
