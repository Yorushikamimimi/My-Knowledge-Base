# Gold V1

```text
Status: FROZEN
Total: 30
Positive: 22
Negative: 8

Out-of-corpus negative: 4
Hard negative: 4

Source Match: ANY
Evidence Anchor: document + section
Chunk-independent: YES
Compound Questions: NO
```

## Purpose

这是：

```text
My Knowledge Base
Retrieval Benchmark V1
```

用于测：

```text
Embedding
→ pgvector Retrieval
→ min_score filtering
```

不是 Generation benchmark。

## Metrics planned

```text
Hit@1
Hit@3
Hit@5
MRR
Source Accuracy
Refusal Accuracy
```

这里只记录计划，尚未实现。

## Dataset 文件

- 正式数据：`docs/phase2/gold-v1.json`（30 cases，与已批准的 `gold-draft-v1.json` questions 完全一致，哈希验证通过）
- Draft 历史：`docs/phase2/gold-draft-v1.json`
- Review 历史：`docs/phase2/gold-draft-v1-review.md`
- Schema：`docs/phase2/gold-schema-v1.md`

## Negative Case 设计

### Clean out-of-corpus（4）

```text
Q023 Kafka ISR
Q024 ZooKeeper ZAB
Q025 Kubernetes Pod Scheduling
Q026 Prometheus
```

### Hard negative（4）

```text
Q027 G1 SATB / RSet
Q028 ReentrantLock / AQS fair lock
Q029 Next-Key Lock
Q030 Redis Sentinel
```

### 特别记录：Q023 Kafka ISR

历史 Baseline（Phase 0，Corpus 仅 Spring synthetic doc 时）：

```text
score = 0.4781
min_score = 0.35

expected = refuse
actual = accepted
```

这是后续 Retrieval Benchmark 的已知 regression / negative baseline case：当前阈值下 Kafka 问题会被错误放行，应在 Phase 2B 阈值实验中重点观测（先建立足够 positive/negative Dataset，不凭单 case 调阈值）。

## 版本约定

以下变更**不能静默修改 Gold V1**，必须升级版本（Gold V1.1 或 Gold V2）：

```text
增加题目
删除题目
改变 expected source
改变 expected behavior
改变 Corpus
```

- 纯 typo / formatting 修复：可视情况 patch，不升版本。
- 影响评测语义的修改（题目、source、behavior、Corpus 变更）：必须 version bump。
- Anchor 层（docs/phase2/anchors/）同样冻结：发现真正错误必须通过明确的 Gold version change 处理，不静默修改。

## Freeze 边界

- Corpus V1 = D01-D12（12 篇），`docs/phase2/corpus-v1.md` 为定义；后续 Phase 2B 测试不同 chunk strategy 时 document set 不变。
- Anchor 层 = D01-D12 共 123 section，`docs/phase2/anchors/` 冻结；已知并已修复 D08 S8 Redisson contamination。
- 本轮不实现 evaluator，metrics 仅为计划。
