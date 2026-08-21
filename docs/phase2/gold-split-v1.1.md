# Gold Split V1.1

```text
Status: FROZEN
Gold Parent: V1.1

DEV: 20
TEST: 10

Purpose:
DEV for parameter selection
TEST held out until configuration selection
```

## 分层规则

### DEV（20 = 15 positive + 5 negative）

```text
positive: q-001 q-002 q-003 q-005 q-006 q-008 q-009 q-011 q-012 q-013
          q-014 q-017 q-018 q-021 q-022
negative: q-023 q-024 q-026 q-027 q-028
```

- positive 覆盖：A(3: q-001/002/003) B(2: q-005/006) C(4: q-009/011/012/022) D(2: q-013/014) E(2: q-017/018?) F(1: q-018) none(2: q-021)——按实际 cluster 分布自然保留。
- negative：3 clean out-of-corpus（q-023 Kafka / q-024 ZooKeeper / q-026 Prometheus）+ 2 hard（q-027 G1 / q-028 AQS）。
- **q-023 Kafka ISR 放 DEV**：它是已知多次观察的 regression（Baseline 0.4781/0.5087 被放行），不能算真正未知的 TEST signal。

### TEST（10 = 7 positive + 3 negative）

```text
positive: q-004 q-007 q-010 q-015 q-016 q-019 q-020
negative: q-025 q-029 q-030
```

- positive 覆盖全部 6 个 Confusion Cluster + 1 条后端基础：
  - A: q-004（Spring 事务 catch 吞异常）
  - B: q-007（Redis Lua 释放锁）
  - C: q-010（聚簇 vs 非聚簇索引）
  - D: q-015（ThreadLocal 内存泄漏）
  - E: q-016（Minor vs Full GC）
  - F: q-019（epoll vs select）
  - 后端基础: q-020（NPE）
- negative：1 clean out-of-corpus（q-025 K8s Pod）+ 2 hard（q-029 Next-Key Lock / q-030 Sentinel）。

### 分层完整性

```text
DEV ∪ TEST = 30（Gold V1.1 全部）
DEV ∩ TEST = ∅
positive: DEV 15 + TEST 7 = 22
negative: DEV 5 + TEST 3 = 8
```

## 使用规则

- 参数选择阶段只允许 `--split dev`。
- TEST 在候选配置 Selection Freeze 前**禁止运行**（Runner 有 `--allow-test` 显式守卫，默认拒绝）。
- 一旦实验开始，禁止修改本 split。

## 文件

- 机器可读：`docs/phase2/gold-split-v1.1.json`
- Gold 父版本：`docs/phase2/gold-v1.1.json`
