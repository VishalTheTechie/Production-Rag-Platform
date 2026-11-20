| Metric | Baseline (always large model) | Optimized (cache + routing) |
|---|---|---|
| Requests | 90 | 90 |
| Cache hit rate | 0.0% | 28.9% |
| Avg cost / request ($) | 0.00051 | 0.00026 |
| Total cost ($) | 0.04626 | 0.02356 |
| p50 latency (s) | 1.71 | 1.74 |
| p95 latency (s) | 3.97 | 3.86 |
| Answer correctness | 83.3% | 83.3% |

Cost reduction: 49.1%
p95 latency change: -2.6%
p50 latency change: +1.8%
Quality change: +0.0 points
Route split (non-cached requests): {'simple': 63, 'complex': 1}
Simple-route answers escalated to the large model: 19%
