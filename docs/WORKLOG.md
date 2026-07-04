# 工作日志

## 2026-07-04 — Codex

### 本地 RAG 最小闭环落地

**做了什么：** 按面试项目口径，把 Dify 移除后的空缺补成 `Java Spring Boot + Python FastAPI + PostgreSQL/pgvector + Ollama` 的本地 RAG 方案。当前重点是代码闭环和可讲清楚的工程结构；真实模型连通、启动后端/RAG 服务、端到端联调按用户要求放到后续。

**具体改了什么：**
- 新增 `apps/rag/` FastAPI RAG 服务：解析 `.txt/.md/.pdf/.docx`、切片、调用模型 provider、写入 pgvector、检索、生成答案
- 新增 `V7__rag_chunks.sql`：创建 `rag_document_chunks` 和 pgvector 索引
- Java 后端新增 `rag` client/config/dto，文档上传成功后自动调用 RAG 入库
- `KnowledgeQaController` 新增 JSON 问答接口，返回 answer、sources、hitCount、latencyMs、refused
- 前端问答页接入新 JSON 接口，展示命中数、耗时、拒答提示和来源片段
- 文档和启动说明同步为本地 RAG 方案，补 RAG 服务端口和环境变量

**已验证：**
- `PYTHONPATH=apps/rag apps/rag/.venv/bin/python -m pytest apps/rag/tests -q`：9 passed
- `mvn -q -Dtest=DocumentModuleIntegrationTest,KnowledgeQaIntegrationTest test`：passed
- `npm run build`：passed
- `npm run test:e2e`：4 passed

**没有做：** 没有启动 Ollama 做真实 embedding / chat 连通测试，没有重启后端/RAG 服务做真实端到端问答，没有 commit。

### 本地真实 RAG 联调

**做了什么：** 按真实链路启动 PostgreSQL、Redis、Ollama、FastAPI RAG、Spring Boot、Vite，并上传 Markdown 样本跑通本地 RAG 问答。

**模型选择：**
- Chat：复用本地已有 `qwen3:14b`
- Embedding：下载 `nomic-embed-text`
- 维度验证：`nomic-embed-text` 输出 768 维，和 `rag_document_chunks.embedding vector(768)` 匹配

**真实链路结果：**
- `POST /api/v1/knowledge-bases/{id}/documents` 上传 `interview-rag-demo.md`
- ingestion task：`status=SUCCEEDED`，`currentStage=COMPLETED`
- PostgreSQL：`rag_document_chunks` 写入 1 条 chunk，`vector_dims(embedding)=768`
- `POST /api/v1/knowledge-bases/{id}/qa` 返回答案、1 条 source、score `0.6762`、`refused=false`

**修复的问题：** RAG 服务调用 Ollama 时被系统代理环境变量影响，`httpx` 尝试走 SOCKS proxy 但 venv 未安装 `socksio`。已在 provider 层设置 `trust_env=False`，避免本地模型调用被系统代理劫持，并新增 provider 单测覆盖。

**已验证：**
- `curl http://127.0.0.1:8091/healthz`：`{"status":"ok"}`
- `curl http://127.0.0.1:8081/actuator/health`：`{"status":"UP"}`
- 前端 `http://localhost:3001`：HTTP 200
- `PYTHONPATH=apps/rag apps/rag/.venv/bin/python -m pytest apps/rag/tests -q`：10 passed
- `mvn -q -Dtest=DocumentModuleIntegrationTest,KnowledgeQaIntegrationTest test`：passed

**没有做：** 没有用浏览器手动点完整上传流程，没有 commit。

### 前端浏览器真实手测

**做了什么：** 用 Playwright 操作真实前端页面完成注册、创建知识库、上传 Markdown、等待文档完成、前端提问、展开来源卡。

**真实页面结果：**
- 注册账号后进入工作台
- 创建知识库 `UI真实联调-1783143812`
- 上传 `/tmp/mykb-ui-rag-demo.md`
- 文档面板显示 `文档 (1)`，文件状态显示 `完成`
- 前端问答显示 `命中 1 · 21706ms`
- 答案正确基于文档内容，回答项目定位是“面向面试展示的本地 RAG 知识库项目”
- 来源卡显示 `mykb-ui-rag-demo.md #0 70%`，展开后能看到 chunk preview
- PostgreSQL 确认该知识库写入 1 条 chunk，`vector_dims(embedding)=768`

**截图：** `output/playwright/ui-rag-flow.png`（local-only，不提交）

**发现的问题：**
- 非阻塞：前端使用 Tailwind CDN，浏览器 console 有 production warning
- 非阻塞：favicon 404 在登录页出现过

**没有做：** 没有 commit。

## 2026-07-04 — Codex

### 项目定位文档校准

**做了什么：** 把项目文档从旧的 Dify 问答平台口径，校准为当前真实状态：AI 知识库工程底座，Dify 已移除，Q&A 暂时不可用，下一步走 `Ollama + pgvector` 本地 RAG。

**具体改了什么：**
- `README.md`：重写项目定位、当前进度、核心能力、技术栈和本地启动说明
- `docs/project/requirements-summary.md`：补当前口径，标明 Dify 相关描述只属于历史方案
- `docs/project/mvp-boundary.md`：把 MVP 边界改为本地 RAG 最小闭环
- `docs/project/technical-decision.md`：把 Dify 决策改为移除记录，补 `pgvector` / 本地模型方向
- `deployment.md` / `deployment-checklist.md`：去掉 Dify API key 和 Dify app 前置项
- `quality-report.md` / `predeploy-report.md` / `release-record.md`：保留 3 月验收历史，同时加 2026-07-04 当前状态说明

**没有做：** 没有改任何代码，没有恢复 Q&A，没有新增 RAG schema，没有 commit。

## 2026-07-03 — Claude Code (deepseek-v4-pro-max)

### Dify 模块完全删除

**做了什么：** 把项目里所有跟 Dify 有关的东西全删了。Dify 是个外部 AI 服务，之前负责文档向量化和 RAG 问答。但它太重了——需要 6 个容器、至少 4-6G 内存，服务器跑不动，本地也占资源。以后我们手搓这部分的 RAG 功能（用 Ollama + pgvector）。

**具体改了什么：**
- 删了整个 `dify/` Java 包（11 个文件：配置类、HTTP 客户端、DTO 等）
- 删了 `KnowledgeBase` 和 `KnowledgeDocument` 实体的 Dify 关联字段
- 删了 `DocumentIngestionTask` 的 `externalBatchId`，把枚举 `DIFY_UPLOAD` 改名 `UPLOAD`
- 重写了 `DocumentIngestionWorkflowService`，去掉 Dify 上传和索引轮询，现在摄入流程就是 OCR → 标记完成
- 重写了 `KnowledgeQaService`，Q&A 端点临时返回 503 "建设中"
- 删了 `DocumentService` 里所有 Dify 安全检查（之前删文档要判断是否已关联 Dify）
- 删了 `application.yml` / `application-test.yml` / `.env.example` / `.env` 所有 Dify 配置项
- 新增 Flyway V6 迁移脚本，删掉 DB 里 `dify_dataset_id`、`dify_document_id`、`external_batch_id` 列
- 前端 `App.jsx` 的 `STAGE_LABELS` 里 `DIFY_UPLOAD` 改成 `UPLOAD`

**测试结果：** 全部 13 个集成测试通过，BUILD SUCCESS

### 前端全中文改造

**做了什么：** 把整个前端的 UI 文案全从英文改成中文。大概 80 处替换，覆盖了登录页、导航栏、侧边栏、仪表盘、工作区、对话页、洞察、合集、归档、弹窗等所有页面。

### 前端 UI 重构：极简画板式布局

**做了什么：** 参考确定的方案三 UI 设计，把整个前端从多页面仪表盘布局重写为极简画板式单页布局。

**具体改动：**
- `index.html`：引入 Tailwind CDN + Material Symbols + Deep Blue Enterprise 设计系统色板
- `styles.css`：从 1600 行削到 30 行，只剩动画和骨架屏
- `App.jsx`：完全重写（~350 行），只保留核心功能

**新架构：**
- Header：智能知识库 logo + 对话/文档 tab + KB 选择器 + 新建按钮 + 头像
- 主画布：对话流 + 空状态 + 输入区
- 文档面板：点击"文档"tab 展开，含自定义上传组件 + 文档列表 + 失败重试
- 移动端：底部 tab bar（对话/文档/上传/新建）

**删掉的旧页面：** Dashboard / Insights / Collections / Archive / Library

### 上传区域 UI 优化

**问题：** 文档面板之前用浏览器原生 `<input type="file">`，显示"选择文件 未选择任何文件"，跟整体圆角卡片风格完全不搭。

**修复：** 替换为自定义 dropzone 组件——
- 空文档时：显示虚线边框卡片，云图标 + "拖拽或点击上传文档" + "支持 PDF、DOCX、TXT、MD"
- 选择文件后：显示文件名 + 大小 + 取消/上传按钮
- 有文档时：dropzone 消失，header 右侧显示紧凑 `+ 上传文档` 按钮

### 右侧悬浮按钮去重

**问题：** 文档页右侧有两个重叠的圆形悬浮按钮（上传+新增），跟文档面板内已有上传入口功能重复。

**修复：** 直接删掉这两个按钮，只保留文档面板里的上传入口。

### 其他小修小补

- 项目本地环境拉起（Docker PostgreSQL + Redis + 后端 + 前端）
- 配置和启动文档整理
- Header KB 选择器样式修复（原生箭头和文字重叠问题）
