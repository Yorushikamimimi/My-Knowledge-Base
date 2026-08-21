# Threshold Experiment V1 — Selection Freeze（Phase 2B-2b）

```text
Selected Threshold: 0.625
Selected from: DEV only
Grid: 0.35 → 0.75 step 0.025（17 点）
Selection Rule: Balanced Score
DEV Balanced Score: 0.8091
TEST / Fresh Holdout executed before selection: NO
Status: SELECTION FROZEN
```

## 选择过程（严格按预注册规则）

### DEV 统计

```text
positive: 15     rankable: 11     ranking failures: 4（q-005/q-006/q-008/q-009）
negative: 5
score_overlap = True（min positive relevant 0.5399 < max negative 0.7133）
→ 无完美单阈值（No perfect single cosine threshold exists on DEV）
```

### DEV Threshold Table（17 点，完整见 .runtime/eval/phase2b2/threshold-scan.csv）

| t | CondRet | E2E | FalseRef | WrongCtx | NegRef | Clean | Hard | Balanced |
|-----|---------|------|----------|----------|--------|-------|------|----------|
| 0.350-0.475 | 1.0000 | 0.7333 | 0.0000 | 0.2667 | 0.0000 | 0.0000 | 0.0000 | 0.5000 |
| 0.500 | 1.0000 | 0.7333 | 0.0000 | 0.2667 | 0.2000 | 0.3333 | 0.0000 | 0.6000 |
| 0.525 | 1.0000 | 0.7333 | 0.0000 | 0.2667 | 0.6000 | 1.0000 | 0.0000 | 0.8000 |
| 0.550 | 0.9091 | 0.6667 | 0.0667 | 0.3333 | 0.6000 | 1.0000 | 0.0000 | 0.7546 |
| 0.575 | 0.8182 | 0.6000 | 0.1333 | 0.2667 | 0.6000 | 1.0000 | 0.0000 | 0.7091 |
| 0.600 | 0.8182 | 0.6000 | 0.1333 | 0.2000 | 0.8000 | 1.0000 | 0.5000 | 0.8091 |
| **0.625** | **0.8182** | **0.6000** | **0.1333** | **0.0000** | **0.8000** | **1.0000** | **0.5000** | **0.8091** |
| 0.650 | 0.4545 | 0.3333 | 0.4000 | 0.2000 | 0.8000 | 1.0000 | 0.5000 | 0.6273 |
| 0.675 | 0.4545 | 0.3333 | 0.4000 | 0.0667 | 0.8000 | 1.0000 | 0.5000 | 0.6273 |
| 0.700 | 0.3636 | 0.2667 | 0.4667 | 0.1333 | 0.8000 | 1.0000 | 0.5000 | 0.5818 |
| 0.725 | 0.3636 | 0.2667 | 0.4667 | 0.0667 | 1.0000 | 1.0000 | 1.0000 | 0.6818 |
| 0.750 | 0.2727 | 0.2000 | 0.5333 | 0.0000 | 1.0000 | 1.0000 | 1.0000 | 0.6363 |

### 选择判定

```text
最高 Balanced Score = 0.8091，出现在 0.600 与 0.625。
Tie-break（预注册顺序）：
  1. Negative Refusal: 相同（0.8000）
  2. Wrong-Context: 0.625=0.0000 < 0.600=0.2000  → 0.625 胜出
  3. （未触发）
```

**Selected = 0.625**，Balanced Score = 0.8091。

### Selected 0.625 的 Case-level Tradeoffs

```text
positive_false_refusal_ids:  q-017, q-018
positive_relevant_dropped:   q-005, q-006, q-008, q-009, q-017, q-018
  （q-005/006/008/009 是 ranking failure 或 relevant < 0.625）
positive_wrong_context:      []（0.625 下无错误放行）
negative_refused:            q-023, q-024, q-026, q-027
negative_false_accept:       q-028（hard negative，fp=0.7133）
```

### Pareto Frontier

```text
cond=1.0000 negref=0.6000 t=0.525
cond=0.8182 negref=0.8000 t=0.600 / 0.625
cond=0.3636 negref=1.0000 t=0.725
```

- Zero false-accept point: t=0.725（但 cond_ret 崩到 0.3636、e2e 0.2667、false_refusal 0.4667）→ 代价巨大。
- High retention (cond≥0.90): t=0.525，最大 neg_refusal=0.6。
- **No perfect single cosine threshold exists on DEV**（score_overlap=True）。

## Fresh Holdout 状态

```text
TEST / Fresh Holdout executed before selection: NO
Fresh Holdout（threshold-holdout-v1，12 cases）将在本文件写入后第一次运行，
仅使用 Selected Threshold=0.625，运行一次。
```

## 边界声明

- 0.625 是 experimental threshold；**production config.py（450/80 + 0.35）未修改**。
- 0.625 的代价：牺牲 q-017/q-018（false refusal）与 4 条 ranking-failure positive 无法用阈值修复；换得 negative 4/5 拒答（q-028 hard negative 仍漏）。
