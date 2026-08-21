# Chunk Experiment V1 — Selection Freeze（Phase 2B-1 结果固化）

```text
Selected: 200 / 40
Selection Basis: DEV only
Held-out TEST: run after selection freeze
Production default changed: NO
Status: FROZEN（实验结论已接受）
```

## 预注册选择规则（Phase 2B-1 实验协议 §14）

```text
Hard Gate:  12/12 ingestion PASS + zero_section_chunks = 0
Primary:    DEV positive Section MRR（越高越好）
Secondary:  Section Hit@3
Tertiary:   Section Hit@1
再参考:     avg_sections_per_chunk / total_chunks（granularity 清晰且无 chunk explosion）
```

## DEV 结果（仅 DEV 20 cases，min_score=0.35 固定）

### Candidate Feasibility（production-faithful）

| Config | Ingest | Chunks | single-chunk docs | avg sec/chunk | max | Hard Gates | Status |
|--------|--------|--------|-------------------|---------------|-----|------------|--------|
| 450/80 | 10/12 | 11 | 10 | 9.375* | 14 | G1 FAIL (D06/D09) | INVALID |
| 300/50 | 11/12 | 20 | 3 | ~5.6 | 13 | G1 FAIL (D06) | INVALID |
| **200/40** | **12/12** | **31** | **1** | **4.85** | **9** | **G1+G2 PASS** | **VIABLE** |
| 120/24 | 12/12 | 49 | 0 | ~3.0 | 7 | G1+G2 PASS | VIABLE |

（*450/80 的 avg 为 3a/3b 时期估算值；本轮 feasibility 中 450/80 未跑 retrieval。）

### DEV Ranking（viable candidates，raw top-5，chunk rank）

| Config | Doc H@1 | Doc H@3 | Sec H@1 | Sec H@3 | Sec H@5 | Sec MRR |
|--------|---------|---------|---------|---------|---------|---------|
| **200/40** | 0.5333 | 0.7333 | 0.3333 | **0.6000** | 0.7333 | **0.4856** |
| 120/24 | **0.6000** | 0.6000 | 0.3333 | 0.5333 | 0.6000 | 0.4389 |

### 选择判定（按预注册规则）

```text
Hard Gate:  两个 candidate 均通过
Primary:    Section MRR → 200/40 (0.4856) > 120/24 (0.4389)   → 200/40
Secondary:  Section Hit@3 → 200/40 (0.6000) > 120/24 (0.5333) → 200/40
Tertiary:   Section Hit@1 持平 (0.3333)
Granularity: 120/24 更细（avg ~3 vs 4.85），但 200/40 的 ranking 更好且
             chunks 更少（31 vs 49），无 chunk explosion
```

**Selected = 200 / 40**

选择只基于 DEV。120/24 的 granularity 更优但 ranking 明显更差（chunk 过碎导致语义分散，document 检索也受影响——Doc H@3 从 0.7333 掉到 0.6）。

## 固化指标（Selected 200/40）

```text
200/40:
  12/12 production-faithful ingestion PASS
  DEV Section MRR = 0.4856
  TEST Section MRR = 0.7000
  section granularity:
    31 chunks
    1 single-chunk document
    avg sections/chunk = 4.85
    max = 9
```

## Reproducibility

Selected candidate（200/40）DEV Run1 vs Run2：见实验报告 §9（rank stable + aggregate identical）。

## TEST 状态（已执行）

```text
TEST has been executed: YES（selection freeze 之后，仅 200/40，--allow-test 显式开启）
TEST 结果: 见 Phase 2B-1 实验报告 §10
TEST positive: Section MRR 0.7000 / Sec Hit@5 1.0 / Wrong-Context 0.0
TEST negative: Refusal Accuracy 0.0（3/3 全被放行）
```

## TEST Exposure Note（重要）

```text
Phase 2B-1 TEST（gold-split-v1.1 TEST，10 cases）已经运行并查看结果。
因此：

1. 该 TEST 以后仍可用于 chunk experiment historical evaluation。
2. 但不能再作为完全未见的 threshold-tuning final holdout。
3. 已知 exposure：
     q-025 fp ≈ 0.6058
     q-029 fp ≈ 0.7139
     q-030 fp ≈ 0.6485

后续 Phase 2B-2 threshold selection 必须只使用 DEV。
如果需要最终 unbiased threshold evaluation，
应新增 fresh holdout，而不是复用这 10 条并称其为 unseen test。
（本轮不创建 fresh holdout，仅记录 methodology rule。）
```

## 边界声明

- 本选择**不修改生产配置**（config.py 默认 450/80 保持）。
- 200/40 是 experimental candidate；是否升级生产 Baseline 由下一阶段单独决定。
- **whitespace chunker 仍存在结构性粗糙问题，200/40 只是当前候选中最优，不代表中文 chunking 问题已经彻底解决。**

