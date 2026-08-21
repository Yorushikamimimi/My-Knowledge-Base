# Threshold Holdout V1（Fresh Holdout）

```text
Status: FROZEN
Gold Parent: V1.1
Purpose: Fresh threshold holdout — threshold tuning final validation
Total: 12
Positive: 8
Negative: 4
  clean out-of-corpus: 2
  hard negative: 2
Retrieval preview before freeze: NO
```

## 定位

- **不做参数选择**：本 holdout 不参与 threshold 选择（选择只用 Gold V1.1 DEV）。
- **只运行一次**：在 threshold selection freeze 之后，仅对 Selected Threshold 运行一次。
- **禁止 scan**：不在 holdout 上扫 17 个阈值。

## Positive（8，全用未被 Gold V1.1 使用的 frozen anchors）

| ID | 领域 | Source (doc / section) | 难度 | 设计意图 |
|----|------|------------------------|------|----------|
| th-001 | Java | D01 / 3. String / StringBuilder / StringBuffer | easy | 高相关、选型型 |
| th-002 | Java | D03 / 9. 线程池（拒绝策略） | medium | 高相关、表格式 |
| th-003 | Java | D04 / 2. 堆 vs 栈 | medium | 中等相关、含"为什么" |
| th-004 | Spring | D05 / 4. Bean 生命周期 | easy | 高相关、流程型 |
| th-005 | MySQL | D07 / 5. 慢查询排查 | medium | 高相关、字段型 |
| th-006 | Redis | D08 / 4. 过期删除 vs 内存淘汰 | medium | 高相关、区别型 |
| th-007 | Network | D11 / 3. 四次挥手 | medium | 中等相关、原理型 |
| th-008 | OS | D10 / 5. 零拷贝 | medium | 中等相关、与 Kafka 字面相邻 |

覆盖领域：Java×3、Spring×1、MySQL×1、Redis×1、Network×1、OS×1；含高相关（th-001/002/004/005/006）与中等相关（th-003/007/008）。

## Negative（4）

| ID | 类型 | Question | 设计依据 |
|----|------|----------|----------|
| th-101 | clean | Redis Cluster 槽位分配和迁移机制 | Corpus 'cluster/槽/slot' 全零（静态验证） |
| th-102 | clean | ClickHouse 列式存储和 MergeTree | Corpus 'clickhouse/列式/merge tree' 全零 |
| th-103 | hard | Spring Security 过滤器链执行顺序 | 仅 D06 §4 提 SecurityContextHolder；embedding 会命中 |
| th-104 | hard | MySQL 半同步复制机制 | 仅 D07 §3 binlog 主从复制语境；无半同步 |

clean 不复用 Kafka/ZAB/K8s/Prometheus；hard 不复用 G1/AQS/Next-Key/Sentinel。

## 使用规则

1. Holdout Freeze 前**未运行任何 retrieval / embedding / score 预览**（构造仅依据 Corpus evidence + Gold methodology）。
2. Phase 2B-2 正式执行顺序：
   ```text
   1. Freeze threshold-holdout-v1          （本文件）
   2. 不运行 holdout
   3. DEV raw retrieval 一次（200/40）
   4. DEV threshold scan（17 个 grid，离线重算）
   5. 按预注册 selection rule 选 threshold
   6. 写 selection freeze
   7. 第一次运行 Fresh Holdout（仅 Selected Threshold）
   8. 不允许根据 holdout 回头换 threshold
   ```
3. Holdout 表现差 → 报告 generalization failure，不重选 threshold。

## 文件

- 数据：`docs/phase2/threshold-holdout-v1.json`
- Gold 父：`docs/phase2/gold-v1.1.json`
