# Threshold Experiment Design V1（Phase 2B-2 实验设计，已预注册）

> 本文件在**任何 threshold scan 结果产生之前**冻结实验设计。
> 状态：DESIGN FROZEN（设计已冻结；scan 未执行）。

## 1. 固定实验条件（唯一变量 = min_score）

```text
Corpus:        V1（FROZEN）
Gold:          V1.1 DEV split（threshold selection 只用 DEV）
Chunk:         200 / 40（Phase 2B-1 selected，production 默认 450/80 未改）
Embedding:     nomic-embed-text, dim 768
raw_top_k:     5
min_score:     唯一变量
reranker:      none
Tokenizer:     production whitespace chunker 不变
```

禁止：改 chunk / overlap / TopK / embedding / tokenizer / reranker / Gold V1.1 / Corpus。

## 2. 已暴露 TEST 的处理

- Gold Split V1.1 TEST（10 cases）已在 Phase 2B-1 运行查看 → **不得作为 threshold final holdout**。
- 已知 exposure：q-025 fp≈0.6058、q-029 fp≈0.7139、q-030 fp≈0.6485。
- 该 TEST 仅保留为 chunk experiment historical evaluation。
- **Threshold validation 使用 Fresh Holdout**（`docs/phase2/threshold-holdout-v1.json`，12 cases）。

## 3. Score 定义（正式 threshold selection 前冻结）

### Positive Relevant Score

```text
对每个 positive DEV case：
  从 raw top5 chunks 中找 document match AND attributed section ∈ expected_sources 的 chunks
  positive_relevant_score = max(relevant chunk scores)
  若 raw top5 无 relevant chunk → positive_relevant_score = null, ranking_failure = true
```

### Negative Max Score

```text
negative_max_score = raw rank1 score
（所有 retrieved chunk 都应不相关，取最有信心的错误证据）
```

## 4. Threshold Filter 精确语义

```text
score >= t → 保留（与生产一致）
negative refused  ⟺ negative_max_score < t（严格 <；score == t 仍保留）
positive relevant survives ⟺ 存在 relevant score >= t
```

## 5. Ranking Failure 隔离

Threshold 无法修复"raw top5 无 relevant chunk"。因此两套 positive metric：

```text
End-to-end Relevant Survival(t) = #(all positive 中 relevant score >= t) / #(all positive)
Conditional Relevant Retention(t) = #(rankable positive 中 relevant score >= t) / #(rankable positive)
   rankable = raw top5 中本来存在 relevant chunk 的 case
```

**Conditional Relevant Retention 用于 threshold selection**（回答"threshold 杀了多少本来检索正确的 evidence"）。

## 6. Score Distribution Analysis（DEV，scan 前准备）

```text
Positive relevant score distribution: min/p25/median/p75/max + 逐 case 排序
Negative max score distribution:     min/p25/median/p75/max + 逐 case 排序
score_overlap = (max negative score >= min positive relevant score)
  true → 不存在单阈值同时 100% retention + 100% refusal（明确报告）
```

## 7. Threshold Grid（预注册，禁止临时插值）

```text
0.350 0.375 0.400 0.425 0.450 0.475 0.500 0.525
0.550 0.575 0.600 0.625 0.650 0.675 0.700 0.725 0.750
（0.35 → 0.75，step 0.025，共 17 点）
```

正式 candidate 只能从 grid 选。unique-score breakpoint 分析仅作诊断。

## 8. Metrics（每 threshold）

```text
Positive: End-to-end Relevant Survival / Conditional Relevant Retention /
          False Refusal Rate / Wrong-Context Acceptance Rate
Negative: Refusal Accuracy / False Acceptance Rate
          Clean Negative Refusal Accuracy / Hard Negative Refusal Accuracy
```

## 9. Selection Objective（预注册）

```text
Threshold Balanced Score(t) = (Conditional Relevant Retention(t) + Negative Refusal Accuracy(t)) / 2
越高越好
```

## 10. Tie Break

```text
1. 更高 Negative Refusal Accuracy
2. 更低 Positive Wrong-Context Acceptance
3. 更高 End-to-end Relevant Survival
4. 更低 threshold（其余相同时优先保守保留 evidence）
```

## 11. Pareto Analysis Plan

```text
- Conditional Relevant Retention vs Negative Refusal Accuracy 的 Pareto frontier
- Zero false-accept threshold: 达到 Negative Refusal=100% 所需最低 t，及此时 positive retention
- High positive-retention threshold: Conditional Retention>=90% 时能达到的最大 Negative Refusal（不存在则如实报告）
```

## 12. No-perfect-threshold Criterion

- 若 score 分布大量重叠 → 允许结论："single-stage cosine threshold 无法同时满足 positive retention 与 negative refusal"。
- 禁止强行"把 0.35 改成 0.X 就解决"。
- 该结论为后续 reranker / margin / confidence policy / query classification 提供数据依据（本轮不实现）。

## 13. Execution Order（Phase 2B-2b）

```text
1. Freeze threshold-holdout-v1（已冻结）
2. 不运行 holdout
3. DEV raw retrieval 一次（200/40）→ 保存 raw top5
4. 离线对 17 个 threshold 重算 filtered metrics（不重复 ingest/embed/search）
5. 按预注册 rule 选 threshold（Balanced Score + tie break）
6. 写 selection freeze（docs/phase2/threshold-selection-v1.md，TEST 未运行）
7. 第一次运行 Fresh Holdout（仅 Selected Threshold）
8. 不允许根据 holdout 回头换 threshold
```

## 14. Fresh Holdout 评价

```text
Positive: relevant survival / conditional retention / false refusal / wrong-context
Negative: refusal / false acceptance
Holdout 表现差 → 报告 generalization failure，不重选 threshold
```

## 15. Production 不变

即使选出 min_score=0.X，本轮仍**不修改** `apps/rag/app/config.py`（生产保持 450/80 + 0.35）。200/40 与 threshold candidate 均为 experimental configuration；升级 production baseline 是后续单独决策。
