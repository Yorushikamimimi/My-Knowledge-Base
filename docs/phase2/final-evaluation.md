# My Knowledge Base RAG Evaluation Final Report

> Phase 2B 最终总结。本轮 RAG 进阶优化的正式实验结论与验收记录。
> Status: CLOSED / ACCEPTED

## Baseline

```text
原始配置: chunk = 450/80, TopK = 5, min_score = 0.35, embedding = nomic-embed-text, LLM = qwen2.5:7b
```

问题（production-faithful 验证）：

```text
- 10/12 Corpus 文档可 ingest
- D06 / D09 因 embedding context overflow 失败（chunk ≈4651 / 3410+2387 chars）
- 10/12 文档单 chunk
- section metric degeneracy（Section Hit 恒等于 Document Hit）
```

## Controlled Chunk Experiment（Phase 2B-1）

```text
Candidates（whitespace chunker 不变，仅 chunk_size/overlap）:
  450/80  INVALID（D06/D09 context overflow）
  300/50  INVALID（D06 仍 overflow）
  200/40  SELECTED
  120/24  VIABLE（DEV Section MRR 更低）

Selected: 200/40
Selection basis: DEV only（Hard Gate 12/12 ingest + Section MRR primary）

DEV（20 cases）:
  Section MRR = 0.4856

held-out TEST（10 cases，selection freeze 后运行一次）:
  Section MRR = 0.7000
  Section Hit@5 = 1.0
  Wrong-Context = 0.0
  Section granularity 从严重退化（avg 9.375/max 14）恢复到有区分力（avg 4.85/max 9）
```

## Threshold Experiment（Phase 2B-2）

```text
DEV selected: 0.625（Balanced Score 0.8091，pre-registered rule）
Fresh Holdout（threshold-holdout-v1，12 cases，仅在 selection freeze 后运行一次）:
  Conditional Retention = 0.625
  Negative Refusal = 0.25

结论: DEV-selected threshold 未泛化（negative refusal 0.8 → 0.25）
positive/negative cosine distributions 强烈重叠（DEV overlap [0.5399, 0.7133]；
holdout clean negative th-101 竟以 0.7468 命中 Redis 文档）
→ single-stage cosine threshold is insufficient as the sole refusal policy.
```

## Production Decision

```text
Applied:   chunk 200/40（实验验证可 production-faithful ingest 且 ranking/granularity 更优）
Not Applied: threshold 0.625（fresh holdout 未泛化）

Production min_score remains: 0.35
```

依据：450/80 只有 10/12 可 ingest；200/40 12/12 PASS；held-out TEST Section MRR 0.7 / Hit@5 1.0 / Wrong-Context 0；granularity 恢复。

## Remaining Limitations

```text
- whitespace chunker 仍结构性粗糙（200/40 下 avg 4.85 sections/chunk、max 9）
- 无 reranker
- 固定阈值拒答策略弱（single cosine threshold 无法同时满足 retention 与 refusal）
- hard-negative 分数重叠（q-028 fp=0.7133、th-101 fp=0.7468）
- 真实链路 Kafka ISR 查询被放行（score 0.4456 > 0.35；模型靠 prompt 约束拒答，
  非检索层拒绝）—— 已知 limitation，不修改 threshold

Future roadmap（本轮不实现）:
  reranker / hybrid retrieval / confidence policy / query classification
```

## Final Acceptance

```text
Corpus V1 production-faithful ingestion（200/40）: 12/12 PASS, failed = []
  D06（前 context-overflow）: PASS, 3 chunks
  D09（前 context-overflow）: PASS, 4 chunks
  max chunk chars = 2600（D06，仍在 nomic-embed-text context 内）

Tests: 65 passed（apps/rag）

Real end-to-end（React→Spring Boot→FastAPI→Ollama→pgvector）:
  Upload D06 → SUCCEEDED
  Upload D09 → SUCCEEDED
  Positive query  → hit 0.7284, answer correct
  Rewrite query  → hit 0.6634, answer correct
  Should-refuse  → refused=False（known limitation），model refusal via prompt
```

## Langfuse

```text
Phase 1 synthetic trace 已单独验收（rag-query 树、usage mapping）。
Phase 2 真实 Vault 验收全程 LANGFUSE_TRACING_ENABLED=false，
真实 question/context/prompt/answer 未发送 Langfuse Cloud。
```

## 相关文件

```text
docs/phase2/corpus-v1.{md,json}               Corpus V1（FROZEN）
docs/phase2/gold-v1.1.{md,json}               Gold V1.1（FROZEN）
docs/phase2/gold-split-v1.1.{md,json}         DEV/TEST split
docs/phase2/chunk-experiment-v1.md            Chunk 实验选择冻结
docs/phase2/threshold-experiment-design-v1.md Threshold 实验设计
docs/phase2/threshold-experiment-v1.md        Threshold 选择冻结
docs/phase2/threshold-holdout-v1.{md,json}    Fresh holdout
apps/rag/eval/                                Benchmark runner（production-faithful）
```
