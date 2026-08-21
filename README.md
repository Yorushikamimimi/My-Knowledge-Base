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
- 已完成 OCR 服务接入开关和 PDF OCR 处理骨架
- 已移除 `Dify dataset/document API`、Dify 配置和 Dify 数据库字段
- 已完成本地 RAG 最小闭环：文档解析、切片、Embedding、向量检索、问答生成、`Sources`（来源，中文解释：答案引用依据）展示
- 已完成 Java 后端到 Python RAG 服务的 HTTP 集成，上传后自动入库，问答接口返回 JSON
- 已完成真实 `Ollama` 模型连通与全服务联调验收（`nomic-embed-text` + `qwen2.5:7b`），并经受控实验将生产切片配置评估为 `chunk 200/40`
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

本仓库采用 `Hybrid Dev`（混合开发，中文解释：前后端本地跑，基础依赖可本地或容器化）的方式。

### 启动顺序

1. 启动基础依赖：

```bash
docker start mykb-pg
docker start redis-local
```

如果本机还没有容器，参考 [STARTUP.md](docs/STARTUP.md) 创建 `mykb-pg` 和 `redis-local`。

2. 准备本地模型：

```bash
ollama pull nomic-embed-text
ollama pull qwen2.5:7b
```

> 说明：当前代码已落地本地 RAG，但真实模型连通和全服务联调还需要后续单独验收。

3. 启动 Python RAG 服务：

```bash
cd apps/rag
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

PYTHONPATH=. \
RAG_DATABASE_URL=postgresql://mykb:mykb@127.0.0.1:5432/mykb \
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8091
```

4. 编译并启动后端：

```bash
cd apps/server
mvn package -DskipTests -q

cd ../..
env \
  DB_HOST=127.0.0.1 DB_PORT=5432 DB_NAME=mykb DB_USERNAME=mykb DB_PASSWORD=mykb \
  APP_JWT_SECRET=this-is-a-very-long-secret-key-for-local-development-min-32-bytes \
  APP_ALLOWED_ORIGINS=http://localhost:3001 \
  APP_STORAGE_TYPE=LOCAL \
  RAG_BASE_URL=http://127.0.0.1:8091 \
  OCR_ENABLED=false \
  java -jar apps/server/target/server-0.1.0-SNAPSHOT.jar
```

5. 启动前端：

```bash
cd apps/web
./node_modules/.bin/vite --host 0.0.0.0 --port 3001
```

6. 打开页面：

- 前端：`http://localhost:3001`
- 后端健康检查：`http://127.0.0.1:8081/actuator/health`
- RAG 健康检查：`http://127.0.0.1:8091/healthz`

### 关闭顺序

1. 关闭后端 `java -jar` 窗口：按 `Ctrl + C`
2. 关闭前端 Vite 窗口：按 `Ctrl + C`
3. 如需停止依赖容器：`docker stop mykb-pg redis-local`

完整说明见：
- [STARTUP.md](docs/STARTUP.md)

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

- 跑通 `Ollama`、FastAPI RAG、Spring Boot、React 的真实本地联调（已完成）
- 刷新本地 RAG 问答截图和演示数据
- 执行 `Linux` 宿主机部署演练
