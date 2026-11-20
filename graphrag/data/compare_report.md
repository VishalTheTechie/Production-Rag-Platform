## Multi-hop questions (HotpotQA bridge)
| Method | Questions | Exact match | F1 | Support recall | All support found | Cost / query ($) |
|---|---|---|---|---|---|---|
| Vector RAG (baseline) | 60 | 50.0% | 0.592 | 82.5% | 66.7% | 0.00019 |
| Vector + rerank | 60 | 55.0% | 0.687 | 90.8% | 81.7% | 0.00019 |
| GraphRAG (hybrid) | 60 | 61.7% | 0.764 | 96.7% | 93.3% | 0.00025 |

## Single-hop control questions
| Method | Questions | Exact match | F1 | Support recall | All support found | Cost / query ($) |
|---|---|---|---|---|---|---|
| Vector RAG (baseline) | 30 | 76.7% | 0.916 | 100.0% | 100.0% | 0.00015 |
| Vector + rerank | 30 | 76.7% | 0.919 | 100.0% | 100.0% | 0.00015 |
| GraphRAG (hybrid) | 30 | 80.0% | 0.935 | 100.0% | 100.0% | 0.00020 |

## One-time indexing cost (GraphRAG only)
- Paragraphs processed by the LLM: 300
- Tokens: 136,736 in / 339,890 out  (simulated cost $0.1122)
- Graph: 2573 entities after merging (2593 distinct names before), 2230 relations, 3045 chunk-entity links