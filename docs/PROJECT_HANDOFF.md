# My Knowledge Base — Project Handoff

> **START HERE for any new coding agent.**

```text
Last Updated: 2026-08-21

Current Status:
RAG Advanced Optimization V1 — CLOSED / ACCEPTED
```

本项目已经完成一轮完整的 RAG 进阶优化并正式收口。接手时**先读本文档**，再按 §21 的 checklist 确认 Git 状态，不要扫描全部历史。

---

## 1. 项目一句话定位

```text
一个基于 Spring Boot + FastAPI + PostgreSQL/pgvector + Ollama 的本地 RAG
Engineering / Evaluation Playground，包含完整知识库链路、Langfuse
Observability、真实 Corpus / Gold Dataset、production-faithful Retrieval
Benchmark 与受控 Retrieval Experiment。
```

重要背景：

- **日常真实个人知识管理目前并不依赖该 Web RAG 系统**；
- 项目的价值已转向：`RAG Engineering / Observability / Evaluation / Controlled Experiment`；
- 不要把它包装成高频真实生产用户系统。

---

## 2. 当前真实架构

```text
React / Vite (apps/web, :3001)
      ↓
Spring Boot (apps/server, :8081)
      ↓
FastAPI RAG (apps/rag, :8091)
      ├── Parser (parsers.py)
      ├── Chunking (chunking.py)
      ├── Ollama Embedding (providers.py)
      ├── PostgreSQL / pgvector Retrieval (repository.py)
      └── Ollama Generation (providers.py)
```

真实目录：

```text
apps/web       React/Vite 前端
apps/server    Spring Boot 后端
apps/rag       FastAPI RAG 服务（含 eval/ 评测模块）
apps/ocr       OCR 服务（当前关闭）
docs/phase2    Corpus / Gold / 实验设计 / 评估结论
```

注意：`OCR_ENABLED=false`，当前验收路径 OCR 未启用。

---

## 3. 当前 Production Configuration（未来 Agent 最容易误改的地方）

```text
chunk_size = 200
chunk_overlap = 40

embedding = nomic-embed-text
embedding dimension = 768

TopK = 5
min_score = 0.35

reranker = none

LLM = qwen2.5:7b
stream = false
```

### 为什么 chunk 从 450/80 改成 200/40

真实受控实验（production-faithful ingestion）：

```text
450/80  INVALID — D06 / D09 embedding context overflow（chunk ≈4651 / 3410+2387 chars）
300/50  INVALID — D06 仍 context overflow（chunk ≈3686 chars）
200/40  12/12 Corpus production-faithful ingest PASS → DEV selected
120/24  VIABLE — 但 DEV Retrieval ranking 低于 200/40（chunk 过碎语义分散）
```

**200/40 已正式应用到 production**（`apps/rag/app/config.py` 默认值）。

---

## 4. 为什么 min_score 仍然是 0.35（重要历史决策）

曾在 DEV 上通过受控 threshold experiment 选出 **0.625**：

```text
DEV @0.625:
  Conditional Retention = 0.8182
  Negative Refusal      = 0.8000
```

但 Fresh Holdout（threshold-holdout-v1，12 cases，freeze 后运行一次）：

```text
Conditional Retention = 0.625
Negative Refusal      = 0.2500
```

结论：

```text
DEV-selected fixed cosine threshold did not generalize.
```

因此：

- **0.625 没有进入 production**；
- **production min_score = 0.35 保持不变**。

**不要**因为看到历史 negative 被放行，就直接把 min_score 改成 0.5 / 0.6 / 0.625。未来若优化拒答机制，必须做新的受控实验。

---

## 5. 当前已知 Retrieval Limitation

```text
single-stage cosine threshold is insufficient as the sole refusal policy
```

真实现象：

- positive / negative cosine score 明显重叠（DEV overlap [0.5399, 0.7133]）；
- hard negative 可获得很高 similarity（q-028 fp=0.7133、th-101 fp=0.7468）；
- clean negative 也可能因领域词汇相似被高分召回；
- Kafka ISR 等 should-refuse query 仍可能通过 min_score。

最终真实链路 Kafka 验收：

```text
score ≈ 0.4456
min_score = 0.35
refused = false
（模型依赖 Prompt 自行判断资料不足，而非检索层拒绝）
```

Future roadmap（**本轮全部未实现**，见 §23）：reranker / hybrid retrieval / confidence policy / query classification / Chinese-aware chunker。

---

## 6. Phase 0 — Baseline

原始 RAG 全链路已通过真实运行验证：

```text
React upload → Spring Boot → async ingestion → FastAPI → parse → chunk
→ embedding → pgvector → query → retrieval → qwen2.5 → Answer + Sources
```

```text
Baseline was proven to work end-to-end before Langfuse integration.
```

---

## 7. Phase 1 — Langfuse Observability

Commit: `7e35e13 feat(rag): integrate Langfuse tracing for RAG observability`

Trace：

```text
rag-query
├── query-embedding   (type=embedding)
├── vector-retrieval  (type=retriever)
└── ollama-generation (type=generation)
```

已在 Langfuse Cloud UI 真实验收；Generation usage 已验证（如 185 prompt → 137 completion，Σ322）。

Usage 映射（**不要改回 prompt_tokens/completion_tokens**）：

```text
Ollama prompt_eval_count → Langfuse usage_details["input"]
Ollama eval_count        → Langfuse usage_details["output"]
```

隐私约定：

- 真实 Vault 数据测试时 `LANGFUSE_TRACING_ENABLED=false`；
- `LANGFUSE_SECRET_KEY` 从未进入 Git，**不要保存/回显**；
- 配置项使用官方 `LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY / LANGFUSE_BASE_URL / LANGFUSE_TRACING_ENABLED`。

---

## 8. Corpus V1（FROZEN）

```text
12 documents
领域: Java / Spring / MySQL / Redis / OS / Network
定义: docs/phase2/corpus-v1.md + docs/phase2/corpus-v1.json
```

**不要静默增删**；变更需 version bump。

---

## 9. Anchor Layer（FROZEN）

```text
docs/phase2/anchors/  — 123 sections
Gold 锚点: document + section
NOT chunk_index（chunk 参数会变化，Gold 必须与 chunk strategy 解耦）
```

已知修复历史：`D08 S8 concepts` 中曾误引 "Redisson"（该词只存在于 D09），已删除并冻结。

---

## 10. Gold Dataset（FROZEN）

```text
Gold V1.1: 30 cases
  22 positive
   8 negative（4 clean out-of-corpus + 4 hard negative）
文件: docs/phase2/gold-v1.1.json + gold-v1.1.md
```

规则：

```text
source_match = any
positive: expected_sources >= 1
negative: expected_sources = []
chunk_index forbidden
compound question forbidden
```

Gold V1 → V1.1 唯一 semantic change：

```text
q-001 增加 D06 合法 Spring self-invocation evidence source（D06 §3 AOP + §5 声明式事务）
```

Gold V1 历史文件未被静默修改。

---

## 11. Retrieval Benchmark Runner

```text
apps/rag/eval/
  section_attribution.py   heading 识别 + token range + chunk attribution（纯函数）
  metrics.py               Hit@K / MRR / threshold metrics（纯函数）
  retrieval_benchmark.py   入口：ingest → per-case retrieval → aggregate → JSON/CSV
  threshold_experiment.py  离线 threshold scan / selection（纯函数）
```

设计原则：**production-faithful**

- 不允许 embedding truncation（历史上曾因 D06/D09 overflow 加过 truncation，已彻底删除）；
- ingestion production 失败 → Benchmark 也失败（INGESTION_FAILED surface）；
- 不调用 generation（AST 测试保证）；
- 不初始化 Langfuse（启动断言 `LANGFUSE_TRACING_ENABLED=false`）；
- 真实技术资料只留本地；
- raw ranking 与 threshold filtering 分离。

---

## 12. Chunk Experiment（Phase 2B-1）

```text
450/80  INVALID
300/50  INVALID
200/40  SELECTED
120/24  VIABLE
```

200/40：

```text
DEV:            Section MRR = 0.4856
held-out TEST:  Section MRR = 0.7000
                Section Hit@5 = 1.0
                Wrong-Context = 0
```

Whitespace chunker 仍结构性粗糙（200/40 下 avg sections/chunk ≈ 4.85，max 9）。**200/40 是本轮最优受控配置，不代表中文 chunking 已达到理论最优。**

---

## 13. Threshold Experiment（Phase 2B-2）

```text
DEV grid: 0.35 → 0.75 step 0.025（17 点，预注册）
Selection: Balanced Score = (Conditional Relevant Retention + Negative Refusal Accuracy) / 2
DEV Selected: 0.625
Fresh Holdout generalization: FAILED（Neg Refusal 0.8 → 0.25）
→ 0.625 NOT APPLIED
```

这是未来 Agent 不能重复犯错的重要结论。

---

## 14. Final Production Acceptance

```text
生产配置: 200/40
Corpus V1: 12/12 ingest PASS, 31 chunks, failed = []
真实 UI 链路: D06 + D09 Upload → ingestion → embedding → pgvector → SUCCEEDED
  （此前 450/80 下这两篇 context-overflow）
真实 query:
  positive:        score ≈ 0.7284, correct source
  semantic rewrite: score ≈ 0.6634, correct source
  Kafka ISR:       score ≈ 0.4456, refused = false（known limitation）
```

---

## 15. Tests

```text
65 passed（apps/rag 全量）
```

**修改 RAG 前必须先跑**：

```bash
apps/rag/.venv/bin/python -m pytest
```

注意 venv shebang 历史问题：`.venv/bin/pytest`、`uvicorn`、`pip` 等 wrapper script 的 shebang 指向旧路径，**优先使用**：

```bash
.venv/bin/python -m pytest
.venv/bin/python -m uvicorn
.venv/bin/python -m pip
```

---

## 16. Git 状态 / Commit History

```text
branch: codex/rag-fastapi-pgvector
working tree: clean
ahead origin: 7 commits（未 push）
```

关键 commits（按时间序）：

```text
7e35e13 feat(rag): integrate Langfuse tracing for RAG observability
b447341 docs(rag): freeze corpus and gold dataset v1
8e7c21a docs(rag): patch gold dataset to v1.1
009519d feat(rag): add production-faithful retrieval benchmark runner
1b64fce feat(rag): add controlled chunk evaluation workflow
594a3a0 feat(rag): add controlled threshold evaluation
cd59350 feat(rag): apply evaluated chunk configuration
```

**不要因为 origin 落后就自动 pull/reset/rebase**。先理解这 7 个本地 commit。

---

## 17. 当前服务状态（收口时全部关闭）

```text
React :3001      STOPPED
Spring Boot :8081 STOPPED
FastAPI :8091    STOPPED
mykb-pg          STOPPED（docker）
Ollama :11434    保留（machine-level service）
通用 Redis       未动（无法确认归属时不要随意 stop）
```

---

## 18. 数据状态

```text
Data Deleted: NO
```

**不要删除**：PostgreSQL volume、Corpus / test DB 数据、Ollama models、Vault。

---

## 19. 恢复开发 Start Checklist

```bash
git status
git branch --show-current
git log --oneline -10
```

确认 working tree / HEAD / ahead-behind，然后阅读：

```text
docs/PROJECT_HANDOFF.md            （本文档）
docs/phase2/final-evaluation.md    （最终评估结论）
docs/phase2/gold-v1.1.md           （Gold 定义）
docs/phase2/chunk-experiment-v1.md （chunk 选择冻结）
docs/phase2/threshold-experiment-v1.md（threshold 选择冻结）
```

不要一上来扫描整个历史。

---

## 20. 重新启动

PostgreSQL：

```bash
docker start mykb-pg
```

FastAPI（因 venv shebang 问题优先）：

```bash
cd apps/rag
.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8091
```

Spring Boot / React：以 README / 当前脚本为准（`apps/server/target/server-0.1.0-SNAPSHOT.jar`、`apps/web` 的 vite）。不要在 handoff 中编造未经仓库确认的命令。

---

## 21. Future Roadmap（Optional，不执行）

```text
P1: reranker / confidence policy experiment
P2: Chinese-aware chunker
P3: hybrid retrieval
P4: Generation evaluation / LLM-as-a-Judge
P5: Langfuse self-host
```

这些是 Optional Future Roadmap，不是 TODO。项目当前 `CLOSED / ACCEPTED`。

---

## 22. Do Not Repeat Without New Evidence

1. **不要把 chunk 改回 450/80** —— Corpus 已证明 D06/D09 context overflow。
2. **不要直接采用 min_score=0.625** —— Fresh Holdout generalization failed（0.8→0.25）。
3. **不要通过截断 embedding input 让 Benchmark 假装成功** —— production-faithful Runner 已明确禁止。
4. **不要把 Gold 绑定 chunk_index** —— Gold 使用 document + section。
5. **不要用已暴露的 Gold TEST 重新宣称 threshold unseen validation** —— Fresh Holdout 已单独建立；TEST 已暴露（q-025/029/030 fp 已知）。
6. **不要用真实 Vault 内容开启 Langfuse Cloud tracing** —— 真实 Corpus 实验一律 `LANGFUSE_TRACING_ENABLED=false`。
7. **不要为了优化简历继续无限增加** reranker / hybrid / tokenizer / 更大 Dataset —— 除非用户明确重新开启研发。

---

## 23. Resume-ready Evidence（全部真实测量数据）

```text
Corpus V1:         12 real technical notes
Gold V1.1:         30 cases（22 positive / 8 negative）
Tests:             65 passed
Langfuse:          embedding / retrieval / generation trace
                   token / latency / source / score observable
Chunk:             450/80 → 200/40，12/12 production-faithful ingest
Held-out chunk TEST: Section MRR 0.700，Section Hit@5 1.0
Threshold:         DEV 0.625 failed Fresh Holdout（Neg Refusal 0.8 → 0.25）
Final:             200/40 applied，min_score remains 0.35
```

不要写夸大的生产用户量或不存在的数据。
