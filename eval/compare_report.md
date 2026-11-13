| Metric | Baseline (always large model) | Optimized (cache + routing) |
|---|---|---|
| Requests | 90 | 90 |
| Cache hit rate | 0.0% | 56.7% |
| Avg cost / request ($) | 0.00051 | 0.00016 |
| Total cost ($) | 0.04582 | 0.01447 |
| p50 latency (s) | 20.43 | 0.07 |
| p95 latency (s) | 34.25 | 22.37 |
| Answer correctness | 83.3% | 85.6% |

Cost reduction: 68.4%
p95 latency change: -34.7%
p50 latency change: -99.7%
Quality change: +2.2 points
Route split (non-cached requests): {'simple': 39}
Simple-route answers escalated to the large model: 21%
