# Gold Schema V1（冻结）

> Phase 2A-2a/2b 冻结产物。后续 Gold Draft 必须严格遵守本 schema。
> 状态：**已冻结**（用户确认：单一行为字段、不支持 chunk_index、negative 无 source、keywords 仅作 Generation 辅助、`source_match=any`）。

## 1. Schema 定义

```json
{
  "id": "q-001",
  "question": "...",
  "expected_behavior": "answer",
  "expected_sources": [
    {
      "document": "Vault/.../xxx.md",
      "section": "真实 heading"
    }
  ],
  "source_match": "any",
  "expected_keywords": [],
  "category": "positive",
  "difficulty": "easy | medium | hard",
  "cluster": "optional cluster id",
  "notes": ""
}
```

negative 模板：

```json
{
  "id": "q-xxx",
  "question": "...",
  "expected_behavior": "refuse",
  "expected_sources": [],
  "source_match": "any",
  "expected_keywords": [],
  "category": "negative",
  "difficulty": "easy | medium | hard",
  "cluster": null,
  "notes": "说明为什么 Corpus 不足以回答"
}
```

## 2. 字段规则（冻结）

1. `expected_sources` 允许多个（跨文档 cluster 场景）。
2. **不允许 `chunk_index`** 出现在任何字段中；证据只按 document + section。
3. `positive` 必须至少有一个 expected source（否则不合法）。
4. `negative` 默认 `expected_sources = []`；如确有参考源也允许填写，但判定以 refuse 为准。
5. `expected_keywords` 只作为未来 Generation Evaluation 的辅助字段，**不参与 Phase 2A Retrieval 判定**。
6. Retrieval Benchmark 正确性**只依据 document/section evidence**：命中即对、漏命即错，不看关键词。
7. Gold 只以 Vault 实际内容为准，不用模型常识补答案。
8. **`source_match` 固定为 `"any"`**：expected_sources 多个时是 OR / ANY 关系——TopK 中命中任意一个 expected source 即 Retrieval Hit。V1 禁止 `source_match=all`（不创建"必须联合两个文档才能回答"的 compound question），未来需要时再扩展。

## 3. 判定语义（Retrieval 阶段）

- `expected_behavior = answer`：
  - 正确 = 返回的 sources 中至少命中一个 expected (document, section) 对。
  - 多 source 问题：命中任一即算正确（Recall 判定），全部命中更优（后续可计 Source Accuracy 加权）。
- `expected_behavior = refuse`：
  - 正确 = 检索结果无任何 source 达到 min_score（refused=true）或返回的 sources 不含与问题语义匹配的证据。
  - 注意：refuse 判定的实现细节（min_score 阈值）由 Phase 2B 实验决定，本 schema 只定义"应该 refuse"。

## 4. 题目类型约定（辅助字段，非 schema 字段）

- `category` 与 `expected_behavior` 的映射：
  - positive → 期望 answer，必须带 source(s)
  - negative → 期望 refuse，默认无 source
- `difficulty`（**表示 retrieval difficulty / confusion difficulty，而不是问题本身的知识难度**）：
  - easy：答案集中于单一 section 的事实/定义题
  - medium：需要区别型推理或跨 section 整合
  - hard：跨文档 cluster 区分、边界场景、noise 干扰（含 D12）题
- `difficulty` 对 negative 的含义：hard negative 表示"与 Corpus 概念高度相似、极容易被 Retriever 误放行"（如 Q023 Kafka 对当前 Retriever 是真实 hard，因为历史 score=0.4781 > min_score 0.35 曾被放行），不是指问题本身难。

## 5. 分布计划（Gold Draft V1 目标，30~40 题）

| 维度 | 目标 | 说明 |
|------|------|------|
| 总题数 | 30~40 | 第一版控制，可人工复核 |
| positive : negative | 约 26~30 : 6~10（≈ 75% : 25%） | negative 偏少但必须含 Kafka ISR |
| easy : medium : hard | 约 12 : 14 : 8 | hard 覆盖 cluster 区分与 noise |

### 按 cluster 分配（30 题方案示例）

| Cluster | 题数 | 主题 |
|---------|------|------|
| A Spring Proxy/Tx | 5 | @Transactional 失效、REQUIRED vs REQUIRES_NEW、AOP 代理、D05↔D06 区分 |
| B Redis Cache/Lock | 5 | 缓存三问、分布式锁、缓存一致性、D08↔D09 深度区分 |
| C MySQL 内部 | 5 | 索引/回表/覆盖、隔离级别、MVCC、日志 |
| D Java 并发/集合 | 4 | CHM、CAS/ABA、synchronized vs Lock、ThreadLocal |
| E JVM/线程 | 3 | 堆vs栈、Minor vs Full GC、类加载 |
| F 并发/OS | 3 | 进程vs线程（Java vs OS 视角）、IO 多路复用、零拷贝 |
| 跨域/其他 HIGH | 3 | NPE 场景、MQ、分布式事务 |
| negative（含 Kafka ISR） | 2~4 | 库外主题 + 库内错位 |

（实际以 Gold Draft 为准，以上为计划示例。）

## 6. 优先出题 anchor（来自 anchor-audit §4.1）

D05 S9、D07 S1、D03 S9、D08 S7/S8、D09 S8、D07 S2/S3、D05 S3/S10、D08 S5↔D09 S7、D03 S5/S6/S11、D01 S13、D06 S4/S5/S6。

## 7. Kafka ISR negative（必须保留）

```text
question: Kafka ISR 的工作机制是什么？
expected_behavior: refuse
category: negative
sources: []
```

历史 baseline：Corpus 只有 Spring synthetic doc 时 score=0.4781 > min_score 0.35 → 被错误放行。加入真实 Corpus 后重新观测（预计仍应 refuse，因四大领域+后端基础无 Kafka 内容）。
