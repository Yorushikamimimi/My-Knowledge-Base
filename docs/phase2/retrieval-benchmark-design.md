# Phase 2A-3a Retrieval Benchmark Design Report

> 本轮只读 + 设计，未实现 evaluator，未启动服务，未修改 Baseline，未 commit。
> 全部结论基于对 `apps/rag/` 真实代码的重新读取 + 12 篇 Corpus 的真实静态分析（脚本运行于 Vault 只读，未写入仓库）。

---

## 1. 当前 Parser / Chunker 真实行为

### parsers.py（Markdown）

```python
if normalized_content_type.startswith("text/") or "markdown" in normalized_content_type:
    return ParsedDocument(text=data.decode("utf-8", errors="replace"))
if extension in TEXT_EXTENSIONS:  # .txt/.md/.markdown
    return ParsedDocument(text=data.decode("utf-8", errors="replace"))
```

**确认：Markdown 以原始文本形式进入 pipeline——不剥离 Markdown 标记、不改 heading、不改空白**。`## 3. MVCC`、`**答:**`、表格 `|`、代码块都原样保留在 `text` 中。

### chunking.py（精确行为，已逐行核对）

```python
normalized = re.sub(r"\s+", " ", text or "").strip()   # 所有连续空白（含换行）→ 单个空格
words = normalized.split()                               # 按空白切分
chunks = []
start = 0
while start < len(words):
    end = min(start + chunk_size, len(words))
    chunks.append(TextChunk(index=len(chunks), text=" ".join(words[start:end])))
    if end == len(words): break
    start = end - overlap
```

精确事实：

- **tokenization**：`str.split()`，即按任意空白切分。**单位是"空白分隔的词"，不是字符、不是中文字符**。
- **中文影响（关键）**：中文句子内部没有空格，因此一个连续中文片段（如 `多版本并发控制，让读写更少互相阻塞。普通`）在遇到英文/数字/标点+空格前会**粘连成一个 token**。实测 D07（130 行 Markdown）只有 402 个 token。
- **chunk_size 单位**：token 数（450 = 450 个空白分隔词）。
- **chunk_overlap 单位**：token 数（80）。
- **step 计算**：`start = end - overlap`，即滑动窗口，步长 = `chunk_size - overlap`。
- **重新 join**：chunk 文本 = `" ".join(words[start:end])`，即窗口内 token 用单空格重连（原始换行/表格竖线/多空格全部丢失）。
- **heading 是否保留**：保留为普通 token（如 `##`、`3.`、`MVCC` 各是一个 token），但**与正文粘连在同一 token 流中**，换行信息丢失。
- **chunk 是否跨 section**：**是**。窗口按 token 滑动，不感知 heading 边界（见 §3 实测数据）。

### 实测：Corpus V1 在 chunk_size=450/overlap=80 下的 chunk 数

| Doc | tokens | chunks@450/80 |
|-----|--------|---------------|
| D01 | 391 | **1** |
| D02 | 359 | **1** |
| D03 | 463 | 2 |
| D04 | 243 | **1** |
| D05 | 372 | **1** |
| D06 | 413 | **1** |
| D07 | 402 | **1** |
| D08 | 333 | **1** |
| D09 | 628 | 2 |
| D10 | 165 | **1** |
| D11 | 370 | **1** |
| D12 | 236 | **1** |

**重要发现**：当前 Baseline（450/80）下，12 篇中 10 篇是**单 chunk**。这意味着在 Baseline 参数下 section attribution 几乎退化——整篇文档就是 1 个 chunk，命中即整篇。**Section-level 判定只有在更小 chunk 参数下才有区分力**（这也是 Phase 2B 要实验 chunk_size 的直接动机之一）。

## 2. 当前 Retrieval 返回结构

`repository.search()` SQL：

```sql
select document_id, document_name, chunk_index, content,
       1 - (embedding <=> %s::vector) as score
from rag_document_chunks
where knowledge_base_id = %s
order by embedding <=> %s::vector
limit %s
```

返回 `RetrievedChunk(document_id, document_name, chunk_index, content, score)`。

**确认：返回结构没有 section / heading / metadata 字段**。`V7__rag_chunks.sql` 表结构也只有 `content text`，无 heading 列、无 metadata JSON 列。因此 Gold 的 `section` 无法从 DB 直接取，必须靠 §4 的动态 attribution 从源 Markdown 计算。

## 3. Gold Section 与 Chunk 的 Gap

- Gold 锚点：`document + section`（真实 H2 heading，123 个，与源文档 H2 一一对应，已核实无缺失、无重复标题）。
- Retrieval 实际：`document + chunk_index + content`，无 section。
- Gap：**chunk 是 token 窗口，与 section 边界无关**。

### 实测 D07 在 chunk_size=200/overlap=40 下的归属（chunk 跨 section 实证）

```
chunk0 (tok 0-200):   [1. 索引] s=1.0, [2. 事务] s=1.0, [3. MVCC] s=0.6
chunk1 (tok 160-360): [2. 事务] s=0.1, [3. MVCC] s=1.0, [4. InnoDB] s=1.0, ...
chunk2 (tok 320-402): [6. 深分页] s=0.38, [高频对比速记] s=1.0
```

一个 chunk 覆盖 3-6 个 section 是常态。**因此"chunk 命中某 section"必须用 overlap 判定，不能简单"有交集就算"**。

## 4. Section Attribution 推荐算法

### 输入

- 源 Markdown 文本（与生产 `parse_document` 相同：原始文本）
- chunk 参数（chunk_size, overlap）——从 Benchmark 运行时参数传入
- chunk 列表（index, content 或 token range）

### 步骤

**A. Heading 识别（token 级）**

对源文本逐行匹配 `^(#{1,6})\s+(.*)$`。对每个 heading：
- 记录 `(level, title, token_start, token_end)`
- token 定位方法：对 normalized 文本（`re.sub(r"\s+"," ",text).strip()`，与生产完全一致）做 split，记录每个 token 的 char 边界；再用**游标式顺序搜索**（cursor-based）在 normalized 中查找 `'#'*level + ' ' + title` 的字面出现位置，映射为 token 序号。已验证：cursor 搜索修复了 naive `find` 的错位问题（D07 `覆盖索引` 从错误位置 15 修正到正确位置 41）。

**B. Section token range**

对每个目标级别（Gold 使用 H2）heading，section range = `[heading.token_start, next_same_or_higher_heading.token_start)`，最后一个 section 到文档末尾。**子标题（H3）不单独成 section，归属到其父 H2 section**。

> 决策：Gold V1 section = H2。Corpus 中 7 篇有 H3（D02/D03/D04/D05/D06/D07/D08/D09），但锚点层记录的是 H2（`1. 索引` 等），H3（`为什么用 B+Tree` 等）作为 H2 内部子结构不参与 Gold 判定。**不使用 heading path**——因为 Gold V1 已冻结为单层真实 heading，且无重复标题（已核实），H2 足以唯一标识。

**C. Chunk token range**

对 chunk 列表，用**与生产 chunker 完全相同的窗口逻辑**重建每个 chunk 的 `[start, end)` token range（不依赖 DB 中已有 chunk，因为 DB 不存 token 边界；运行时由当前 chunk 参数即时计算）。

**D. Overlap 判定规则（推荐）**

对每个 `(chunk, section)` 对，计算：

```text
overlap_tokens = |chunk_range ∩ section_range|
ratio_of_section = overlap_tokens / section_tokens   （section 被覆盖的比例）
```

**推荐规则（双条件，OR）**：

```text
chunk 归属 section ⟺
    ratio_of_section >= 0.5
    OR
    overlap_tokens >= 30
```

理由（基于实测数据）：
- D07 在 200/40 下，section「2. 事务」99 tokens，chunk0 覆盖其 99/99=1.0 → 归属；「3. MVCC」50 tokens，chunk0 覆盖 30/50=0.6 → 归属（0.5 规则）。
- 短 section（如 D07「深分页」34 tokens 被 chunk1 覆盖 13 tokens，ratio=0.38）若只看 ratio 会漏判——但 13 token 的绝对 overlap 太小、确实不该算 chunk 覆盖了深分页 → 正确排除。
- 但「高频对比速记」69 tokens 被 chunk2 覆盖 69/69=1.0 → 归属，正确（速记节是真实 H2 section，Gold 若引用它应命中）。

**阈值不凭感觉选**：上表是基于 D07/D09 两种 chunk 参数实测后选定的；正式实现时应把这套规则做成纯函数，并在 Phase 2A-3b 用全部 12 篇 × 多组 chunk 参数回归验证后再定稿（若发现边界 case 再微调，规则本身保持"简单、确定、可复现"）。

**E. 多 section chunk 行为**

允许：一个 chunk 可同时归属多个 section（实测 chunk1 覆盖 3 个 section）。attribution 输出为 `chunk_index → [sectionA, sectionB, ...]`。Section Hit 判定 = 该列表是否包含任一 Gold expected section。

**F. Heading 自身归属**

heading token（`##`、`3.`、`MVCC`）落在该 section 的 range 起点，归属**本节**（而非前一节）。因为 section range 定义是 `[heading_start, next_heading_start)`，heading 天然属于本节开头。已验证 D07 `3. MVCC` heading 在 token 170，其后 section「3. MVCC」从 170 开始。

**G. 重复 heading 检查**

已对 12 篇全部 heading 级别做重复标题检查：**无重复**（`dup_titles = none` 全行）。Gold section 无歧义，无需特殊处理。

## 5. Chunk Strategy Independence

- Attribution 是**运行时计算**，输入 = 源 Markdown + 当前 chunk 参数。
- 换 chunk_size=300/overlap=50 时：chunk range 重算、attribution 重算、`chunk_index` 变化，但 **Gold V1 的 `document + section` 不变**。
- 已验证：同一 D07 在 450/80、300/50、200/40、120/24 下 attribution 均能即时生成（§1 表 + §4 模拟）。
- **验收条件满足**：Gold 不绑定任何 chunk 参数；attribution 层是唯一感知 chunk 的组件。

## 6. Corpus Ingestion 方案

- **复用生产链路**：`parse_document → chunk_text → provider.embed → repository.replace_document_chunks`——即直接调用现有 `RagService.ingest()` 的同源组件，不另写 embedding/chunk ingestion。
- Benchmark Runner 不经过 React/Spring Boot/任务系统，直接在 Python 侧构造 `IngestRequest`（knowledgeBaseId、documentId、documentName、contentType=text/markdown、contentBase64）调用 `RagService.ingest()`。
- 若需更底层：可直接调用 `parse_document` + `chunk_text` + `OllamaProvider.embed` + `RagRepository.replace_document_chunks`。**推荐复用 `RagService.ingest()` 以保证与生产完全同路径**。
- Vault 路径：Runner 接受 `--vault-root`（或 `MYKB_VAULT_ROOT` 环境变量），仓库内只存 `Vault/.../xxx.md` 相对路径；运行时拼接绝对路径读取。

## 7. Dedicated Eval KB 设计

- **不污染现有 KB**：新建独立 `knowledge_base_id`，例如确定性的 UUID v5（namespace + "corpus-v1-eval"），或简单固定 UUID（如 `00000000-0000-4000-8000-000000000001` 风格）。**推荐确定性 UUID（v5 或固定值）**，保证可复现。
- **document_id**：对每篇 Corpus 文档，用确定性 UUID v5（namespace + 相对路径），保证跨运行稳定；`replace_document_chunks` 按 `document_id` 先 delete 再 insert，天然幂等，**重复运行会覆盖同一 document 的 chunks，不需要手动清空**。
- **清空策略**：Benchmark 开始前不全局 DELETE；依赖 `replace_document_chunks` 的 delete-by-document_id 幂等性。若需彻底清理：`DELETE FROM rag_document_chunks WHERE knowledge_base_id = <eval-kb-id>`——只删 eval KB，不影响其他 KB。
- **FK 限制**：V7 表中 `knowledge_base_id`/`document_id` 是 `uuid` 类型但**无 FK 约束**（无 REFERENCES 子句），因此不会因其他表约束阻止删除/插入。已核实 migration 全文无外键。
- 知识库表（Spring 侧）需要 eval KB 存在吗？`RagService.ingest()` 只写 `rag_document_chunks`，不检查 knowledge_base 表存在性；但若通过 Spring API 建 KB 则需知识库记录。**Benchmark 直接走 Python 侧可绕过 Spring**——设计上确认 `rag_document_chunks.knowledge_base_id` 无 FK，允许"仅存在 chunk 无 KB 记录"的 eval KB（需在 Phase 2A-3b 验证 psycopg 侧无其他约束）。

## 8. Privacy / Langfuse Policy

- **Benchmark 不进入 Langfuse-traced 路径**：Runner 直接调用 repository + provider，不调用 `RagService.query()`（该函数内嵌 Langfuse observation）。或调用时确保环境 `LANGFUSE_TRACING_ENABLED=false`。
- **双保险**：①代码结构上 Benchmark 用独立的 `benchmark_query()`（只做 embed + search + attribution + filter），无 generation path、无 Langfuse client；②README/启动脚本中写明必须 `LANGFUSE_TRACING_ENABLED=false`。
- **数据边界**：真实 question/context 只存在于 本地 Vault + 本地 Ollama(:11434) + 本地 PostgreSQL(:5432)，不上传 Cloud。Phase 2A 不需要 Langfuse。

## 9. Metric Definitions（严格）

### Ranking Metrics（在 raw retrieval results 上，即 min_score 过滤前）

```text
Document Hit@K   = 前 K 个 raw results 中，是否存在 document ∈ expected_sources.document
Section Hit@K    = 前 K 个 raw results 中，是否存在 (document, section) 满足
                   document ∈ expected_sources 且 chunk 的 attributed sections ∋ expected_sources.section
Section MRR      = 1 / first_relevant_rank，其中 relevant = Section Hit（any 语义下命中任一 Gold source）
```

- `source_match=any`：命中任意一个 Gold source 即 relevant。
- raw results = `repository.search()` 返回的 TopK（**不过滤**）。

### Threshold Metrics（在 filtered results 上，即 min_score 过滤后）

```text
Positive False Refusal Rate = #(should answer 且 filtered hits = 0) / #(should answer)
  补充记录: filtered 结果中是否仍存在 relevant section（即"被阈值误杀但检索其实对"）
Refusal Accuracy      = #(should refuse 且 filtered hits = 0) / #(should refuse)
False Acceptance Rate = #(should refuse 且 filtered hits > 0) / #(should refuse)
  Kafka ISR (Q023) 应计入 False Acceptance（历史 score=0.4781 > 0.35）
```

### Raw 与 Filtered 分离原则

Raw ranking metric 回答"embedding + pgvector 排序能力"；Threshold metric 回答"min_score=0.35 是否合理"。**两者分别输出，不混合**。Phase 2B 调阈值时只重算 Threshold 部分，Raw 部分不变。

## 10. Per-case Result Schema

```json
{
  "id": "q-001",
  "question": "...",
  "expected_behavior": "answer | refuse",
  "expected_sources": [{"document": "...", "section": "..."}],
  "raw_top5": [
    {"rank": 1, "document": "...", "chunk_index": 3, "attributed_sections": ["2. 事务", "3. MVCC"], "score": 0.72}
  ],
  "filtered_hits": [{"rank": 1, "document": "...", "chunk_index": 3, "attributed_sections": ["..."], "score": 0.72}],
  "first_relevant_rank": 2,
  "max_score": 0.72,
  "refused": false,
  "document_hit@1": true,
  "document_hit@3": true,
  "section_hit@1": false,
  "section_hit@3": true,
  "diagnostic_reason": "...",
  "highest_false_positive_score": null,
  "likely_false_positive_doc": null,
  "likely_false_positive_section": null
}
```

negative 必填 `highest_false_positive_score` + `likely_false_positive_*`；positive 必填 `first_relevant_rank` 与 `section_hit@K`。

## 11. Aggregate Result Schema

```json
{
  "meta": {"corpus_version": "v1", "gold_version": "v1", "embedding_model": "nomic-embed-text",
           "chunk_size": 450, "overlap": 80, "topK": 5, "min_score": 0.35,
           "timestamp": "...", "git_commit": "..."},
  "raw": {
    "document_hit@1": 0.0, "document_hit@3": 0.0, "document_hit@5": 0.0,
    "section_hit@1": 0.0, "section_hit@3": 0.0, "section_hit@5": 0.0,
    "section_mrr": 0.0
  },
  "threshold": {
    "positive_false_refusal_rate": 0.0,
    "refusal_accuracy": 0.0,
    "false_acceptance_rate": 0.0
  },
  "per_case": [ ...§10 数组... ]
}
```

Raw 聚合只统计 positive（22 条）；Refusal Accuracy / False Acceptance 只统计 negative（8 条）；Positive False Refusal Rate 只统计 positive。

## 12. Runtime Output

- 输出目录：**`.runtime/eval/`**（`.runtime/` 已存在且含 `*.pid`/`*.log` 均被 gitignore；但当前 `.gitignore` 只忽略 `.runtime/storage/`，**`.runtime/eval/` 尚未被忽略——Phase 2A-3b 实现前需在 `.gitignore` 增加 `.runtime/eval/`**，或复用已被忽略的 `.runtime/storage/eval/`）。
- 文件：`retrieval-baseline-v1.json`（完整诊断）+ `retrieval-baseline-v1.csv`（快速比较）。
- 本轮不创建这些文件。

## 13. Reproducibility Metadata

- 记录：`corpus_version, gold_version, embedding_model, chunk_size, overlap, topK, min_score, timestamp, git_commit`。
- **确定性要求**：同一组参数连续运行两次，结果应一致——①UUID 确定性（v5）保证 document_id/chunk 稳定；②embedding 用同一 Ollama 模型（nomic-embed-text 确定性）；③`replace_document_chunks` 幂等覆盖；④`ORDER BY embedding <=> %s` 对同分数 tie 可能有顺序抖动——**建议在结果中保留完整 score 序列并在聚合时对 tie 容差**（Phase 2A-3b 验证）。

## 14. 推荐文件结构（Minimal）

```text
apps/rag/eval/
  __init__.py
  section_attribution.py   # heading 识别 + token range + chunk attribution（纯函数，可单测）
  metrics.py               # Hit@K / MRR / threshold metrics（纯函数，可单测）
  retrieval_benchmark.py   # 入口：ingest corpus → for each gold: embed+search+attribution+filter → aggregate → 输出 JSON/CSV
```

3 个模块足够。attribution 与 metrics 为纯函数（无 DB/网络），benchmark 入口负责编排。`LANGFUSE_TRACING_ENABLED=false` 断言 + 无 generation path 是 benchmark 入口的结构性保证。

## 15. 需要新增哪些 Tests

```text
tests/test_section_attribution.py
  - heading token 定位（H2/H3、cursor 搜索、heading 归属本节）
  - chunk range 与生产 chunker 完全一致（同一 text+参数 → 同一 range）
  - overlap 判定（0.5 ratio / 30 token 双条件）
  - 换 chunk 参数后 attribution 重算且 Gold 不变

tests/test_metrics.py
  - Document/Section Hit@K 计算（any 语义）
  - Section MRR
  - Positive False Refusal Rate / Refusal Accuracy / False Acceptance Rate
  - raw 与 filtered 分离（同 case 两种结果各自统计）

tests/test_benchmark_never_generates.py
  - 断言 benchmark 模块 import 后不存在 provider.generate 调用路径（结构断言）
```

## 16. 风险 / 未决问题

1. **Baseline 450/80 下 10/12 篇单 chunk**：section attribution 在 Baseline 参数下几乎无区分力 → section-level metric 在 450/80 下会退化为 document-level。**这不是 bug，是数据事实**；Phase 2B 的 chunk 实验将直接受益（120/24 或 200/40 下 D07/D09 有 3-4 chunks）。Gold V1 无需修改。
2. **中文 tokenization 粗糙**：当前 split() 把中文长句粘成单 token，导致 token 数远小于"语义词数"。attribution 与生产 chunker 保持一致即可（设计目标就是镜像生产），但**如 Phase 2B 引入中文感知 chunker，attribution 必须同步更换 tokenizer**——本设计将 tokenizer 作为可注入参数，已预留。
3. **overlap 阈值 0.5/30 是实测初值**：需在 3b 用 12 篇 × 多组参数回归定稿；若出现边界 case 只调阈值，不换规则形态。
4. **eval KB 无知识库主记录**：`rag_document_chunks.knowledge_base_id` 无 FK，允许"chunk-only" eval KB；但若未来 Spring 侧有查询假设 KB 存在，需注意。3b 验证。
5. **score tie 顺序抖动**：同分 chunk 排序可能不稳定，聚合时需处理 tie（如加 document_id 次级排序或容差）。
6. **H3 不参与判定**：Gold 锚定 H2；若未来 Gold 需引用 H3 级证据（如 D09「Lua 能保证什么」），需 Gold version bump（V1.1）并改用 heading path。当前不处理。

## 17. 下一步

**Phase 2A-3b：实现 Retrieval Benchmark Runner**——按 §14 文件结构创建 `apps/rag/eval/`（attribution/metrics 纯函数 + benchmark 入口），先写 §15 的 attribution/metrics 单测，再在本地 PostgreSQL + Ollama 上：①建 deterministic eval KB、②用生产 `RagService.ingest()` 导入 12 篇 Corpus、③跑 30 条 Gold 的 retrieval-only benchmark（embed + search + attribution + filter，**无 generation**）、④输出 `.runtime/eval/retrieval-baseline-v1.json/csv` 并补 `.gitignore` 忽略该目录。本轮不执行。
