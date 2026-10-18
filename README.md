# My Knowledge Base | AI 知识库工程底座

<p align="center">
  <img src="https://img.shields.io/badge/Spring%20Boot-3.3-brightgreen?style=flat-square" />
  <img src="https://img.shields.io/badge/React%20%2B%20Vite-Frontend-blue?style=flat-square" />
  <img src="https://img.shields.io/badge/PostgreSQL%20%2B%20pgvector-RAG%20Base-orange?style=flat-square" />
  <img src="https://img.shields.io/badge/Java-21-lightgrey?style=flat-square" />
</p>

> 基于 `Spring Boot + FastAPI + React/Vite + PostgreSQL/pgvector + Ollama` 的 AI 知识库工程底座。当前已打通 `登录 -> 创建知识库 -> 上传文档 -> 文件存储 -> 文档切片/向量入库 -> RAG 问答 -> Sources 展示` 的最小闭环。

## 项目定位

这是一个面向面试展示和工程能力讲解的 `AI engineering`（AI 工程化，中文解释：围绕真实业务流程构建的工程项目）项目，不是简单聊天壳。

- 面向场景：个人/团队知识库、文档管理、本地 RAG 问答
- 核心价值：展示一个从业务后端到 AI 检索生成链路的完整工程闭环
- 当前状态：`Dify` 路线已移除；改为 Java 业务服务 + Python RAG 服务 + PostgreSQL/pgvector + Ollama 的本地方案

## 当前进度

- 已完成 `Auth`、知识库管理、文档上传、任务状态跟踪
- 已完成 `LOCAL / MinIO` 存储抽象和文档异步处理框架
- 已实现可选 OCR 服务接入与 PDF OCR 处理代码；本轮联调关闭 OCR，未验证识别效果
- 已移除 `Dify dataset/document API`、Dify 配置和 Dify 数据库字段
- 已完成本地 RAG 最小闭环：文档解析、切片、Embedding、向量检索、问答生成、`Sources`（来源，中文解释：答案引用依据）展示
- 已完成 Java 后端到 Python RAG 服务的 HTTP 集成，上传后自动入库，问答接口返回 JSON
- 2026-09-23 隔离联调验证了合成 TXT / MD / DOCX / 文本层 PDF 从 Java 上传、FastAPI 切片与向量入库到本地 Ollama 问答的链路；扫描件 PDF 在 OCR 关闭时未产生切片。这不代表已在干净机器或 Docker Compose 下完成首次启动验收。切片参数实验结果仍见 [Phase 2 报告](docs/phase2/final-evaluation.md)，本轮未重跑基准
- 已完成 `Langfuse` RAG 可观测性接入（Phase 1）与 Retrieval Evaluation 基准（Phase 2，详见 `docs/phase2/final-evaluation.md`）
- 仍待完成：`Linux` 真实宿主机部署演练

## 功能预览

### 1. 创建知识库

![创建知识库](docs/picture/page-2026-03-24T09-11-25-334Z.png)

### 2. 工作台总览

![工作台总览](docs/picture/page-2026-03-24T09-11-35-284Z.png)

### 3. 上传入库

![上传入库](docs/picture/element-2026-03-24T09-11-40-010Z.png)

### 4. 问答与 Sources 截图

![问答与 Sources](docs/picture/element-2026-03-24T09-11-45-298Z.png)

> 说明：早期截图来自 Dify 方案阶段。当前 Dify 已移除，代码已改为本地 RAG 方案；截图后续需要在新链路联调后刷新。

### 5. 完整验收页

![完整验收页](docs/picture/page-2026-03-24T09-10-06-130Z.png)

## 核心能力

- `JWT auth`：登录注册和接口鉴权
- 知识库创建、列表、详情、共享
- 文档上传到 `LOCAL / MinIO` 存储
- 异步入库任务流转与状态展示
- 普通文件上传和基础处理状态闭环
- `PDF -> OCR` 扫描件处理骨架
- 失败任务重试、失败文档删除
- 本地 RAG：`parse -> chunk -> embedding -> pgvector -> retrieve -> generate -> sources`
- 检索增强策略：chunk overlap、score threshold、无命中拒答、来源片段预览、命中数量和耗时指标

## 技术栈

- 前端：`React + Vite`
- 后端：`Spring Boot 3.3`
- RAG 服务：`Python + FastAPI`
- 运行时：`Java 17`
- 数据库：`PostgreSQL`
- 向量检索：`pgvector`
- 缓存：`Redis`
- 对象存储：`MinIO`
- AI 核心：`Ollama`（默认 `nomic-embed-text` + `qwen2.5:7b`）
- OCR：独立 OCR service
- 部署：`Docker + host Nginx`

## 本地启动

先准备 Docker、JDK 17 或 21、Maven、Python 3.12、Node.js 24（含 npm）和 Ollama。
完整的首次安装、模型准备、各终端工作目录及停止方式见 [启动指南](docs/STARTUP.md#第一次启动)；前端在 `apps/web` 中先运行 `npm ci`，再运行 `npm run dev -- --host 127.0.0.1 --port 3001`。

默认只用于本机：浏览器打开 `http://localhost:3001`，通过 Java API 使用知识库。**FastAPI RAG 是后端内部服务，未实现用户认证或知识库权限校验**，启动时必须绑定 `127.0.0.1:8091`；不能直接向局域网或公网发布、转发 RAG 端口。回环绑定不是认证，同一主机上的其他程序仍可访问。

Java 与 RAG 分机或分容器时，先按[访问边界说明](docs/STARTUP.md#rag-访问边界与跨机部署)配置专用内部网络与服务认证，不能仅把监听地址改为 `0.0.0.0`。仓库历史 Compose 不含完整 RAG 链路，尚不能当作一键启动方案。

## 验证范围（2026-09-23）

- 本批定向回归：隔离源码副本中的 RAG Python 选定测试集 47 项通过；Java RAG 客户端错误映射 2 项及文档失败任务状态集成测试 1 项通过（集成测试使用 H2 和 stub RAG 客户端）。Java 后端其余测试未在本批重跑。前端生产构建和 4 项 mock API Playwright 结果来自此前验证，不属于本批回归。
- 真实服务链路：在临时 PostgreSQL/pgvector 和已安装的本地 Ollama 模型上，合成 TXT、MD、DOCX、文本层 PDF 各写入 1 个切片；问答返回合成标记及来源。无可提取文本的 PDF 在 `OCR_ENABLED=false` 时报告 RAG 入库失败，不再记为成功任务；同一文档 ID 的旧切片保持不变。
- 未覆盖：干净机器首次启动、Docker Compose 全服务启动、OCR 识别、MinIO、浏览器直连真实后端，以及托管模型服务。此次没有下载模型或发送外部模型请求。

## 目录说明

```text
.
|-- apps/
|   |-- server/          # Spring Boot API
|   |-- web/             # React frontend workbench
|   |-- rag/             # FastAPI RAG service
|   `-- ocr/             # OCR adapter service
|-- deploy/              # deployment files and Nginx config
|-- docs/project/        # project docs, reports, decisions
|-- docs/picture/        # Playwright verification screenshots
|-- scripts/             # local dev, test, build, rehearsal scripts
|-- standards/           # delivery and deployment standards
`-- .runtime/            # local runtime data
```

## 文档链接

- [Project Handoff / 当前工程状态](docs/PROJECT_HANDOFF.md)
- [RAG Evaluation Final Report](docs/phase2/final-evaluation.md)
- [requirements-summary.md](docs/project/requirements-summary.md)
- [mvp-boundary.md](docs/project/mvp-boundary.md)
- [technical-decision.md](docs/project/technical-decision.md)
- [quality-report.md](docs/project/quality-report.md)
- [predeploy-report.md](docs/project/predeploy-report.md)
- [release-record.md](docs/project/release-record.md)

## 下一步

- 在干净环境按首次启动指南复验依赖和服务顺序；本轮完成的是隔离环境下的真实后端 / RAG / 本地模型联调，浏览器测试仍使用 mock API
- 刷新本地 RAG 问答截图和演示数据
- 执行 `Linux` 宿主机部署演练

## 许可证

本项目自有代码与自有说明采用 [MIT](LICENSE)。第三方依赖、模型、商标和截图中的第三方内容不因本仓库的 MIT 声明而改变原许可，见[第三方说明](THIRD_PARTY_NOTICES.md)。
