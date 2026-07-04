# 启动文档

## 项目简介

智能知识库（My Knowledge Base）—— AI 驱动的文档管理与 RAG 问答平台。上传文档，AI 自动处理，然后可以针对文档内容提问。

### 技术栈

| 模块 | 语言 | 框架 |
|------|------|------|
| 后端 | Java 21 | Spring Boot 3.3 + JPA + Flyway |
| RAG 服务 | Python 3.12 | FastAPI + pgvector + Ollama |
| 前端 | JavaScript (React) | React 18 + Vite 5 + Tailwind CSS |
| 数据库 | PostgreSQL 16 | Docker (pgvector 镜像) |
| OCR 服务 | Python 3.12 | FastAPI + RapidOCR（可选） |

---

## 前置条件

- Docker Desktop（已安装）
- Java 21（`java -version`）
- Node.js 24（`node -v`）
- Maven（`mvn -v`）
- Python 3.12（`python3 --version`）
- Ollama（本地模型服务，后续联调时需要）

---

## 第一次启动

### 1. 启动依赖服务（Docker）

```bash
# PostgreSQL
docker run -d \
  --name mykb-pg \
  -e POSTGRES_DB=mykb \
  -e POSTGRES_USER=mykb \
  -e POSTGRES_PASSWORD=mykb \
  -p 5432:5432 \
  pgvector/pgvector:pg16

# Redis（项目暂时没用到，但有容器在跑）
docker start redis-local
```

### 2. 配置环境变量

项目根目录已有 `.env.example`，复制一份：

```bash
cp .env.example .env
```

默认值可以直接用，不需要改。如果 PostgreSQL 端口或密码不同，修改 `.env` 里的对应项。

### 3. 准备 Ollama 模型

```bash
ollama pull nomic-embed-text
ollama pull qwen2.5:7b
```

当前代码默认使用：

- Embedding：`nomic-embed-text`
- Chat：`qwen2.5:7b`

> 本轮先完成代码落地；Ollama 连通性、真实 embedding 和真实问答启动验收放到后续执行。

### 4. 启动 RAG 服务

```bash
cd apps/rag
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

PYTHONPATH=. \
RAG_DATABASE_URL=postgresql://mykb:mykb@127.0.0.1:5432/mykb \
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8091
```

健康检查：

```bash
curl http://localhost:8091/healthz
```

### 5. 编译后端

```bash
cd apps/server
mvn package -DskipTests -q
```

编译产物：`apps/server/target/server-0.1.0-SNAPSHOT.jar`

### 6. 启动后端

```bash
cd /Users/yang/Workspace/SelfProject/CodexProject/My_KnowledgeBase

env \
  DB_HOST=127.0.0.1 DB_PORT=5432 DB_NAME=mykb DB_USERNAME=mykb DB_PASSWORD=mykb \
  APP_JWT_SECRET=this-is-a-very-long-secret-key-for-local-development-min-32-bytes \
  APP_ALLOWED_ORIGINS=http://localhost:3001 \
  APP_STORAGE_TYPE=LOCAL \
  RAG_BASE_URL=http://127.0.0.1:8091 \
  OCR_ENABLED=false \
  nohup java -jar apps/server/target/server-0.1.0-SNAPSHOT.jar \
  > .runtime/server.log 2>&1 &
```

验证：`curl http://localhost:8081/actuator/health` → 返回 `{"status":"UP"}`

### 7. 启动前端

```bash
cd apps/web
pnpm install
npx vite --port 3001
```

浏览器打开 `http://localhost:3001`

### 8. 创建测试账号

直接插数据库（DBeaver 连 `127.0.0.1:5432`，库 `mykb`，用户/密码 `mykb`）：

```sql
-- 先生成 BCrypt 哈希（密码 12345678）
-- 用 python3 -c "import bcrypt; print(bcrypt.hashpw(b'12345678', bcrypt.gensalt()).decode())"

INSERT INTO user_accounts (id, username, email, password_hash, created_at, updated_at)
VALUES (
  gen_random_uuid(),
  '12345678',
  '12345678@mykb.local',
  -- 下面这行换成上面命令生成的哈希
  '$2b$10$evJE4xziUF816XRyL.pW4O.eA.MotuQ5yue8VYn7t4T7IHcmMCV9O',
  now(),
  now()
);
```

---

## 日常启动（服务已经在跑）

通常 Docker 容器和项目服务都在后台运行。检查状态：

```bash
# 检查服务端口
curl -s http://localhost:8081/actuator/health   # 后端
curl -s http://localhost:8091/healthz            # RAG 服务
curl -s -o /dev/null -w "%{http_code}" http://localhost:3001  # 前端
docker exec mykb-pg pg_isready -U mykb           # 数据库
docker exec redis-local redis-cli -a local_dev_only ping  # Redis
```

---

## 运行测试

```bash
# 后端 Java 测试（13 个集成测试）
cd apps/server
mvn test

# RAG 服务测试
cd apps/rag
PYTHONPATH=. .venv/bin/python -m pytest tests -q

# 前端 E2E 测试（Playwright）
cd apps/web
pnpm test:e2e
```

---

## 当前功能

- ✅ 用户注册/登录（JWT + BCrypt）
- ✅ 知识库创建、分享
- ✅ 文档上传（PDF / DOCX / TXT / MD）
- ✅ 本地文件存储
- ✅ OCR 文本提取（需启动 Python OCR 服务）
- ✅ 文档列表、任务状态追踪
- ✅ RAG 入库（上传后自动调用 FastAPI RAG 服务切片、Embedding、写入 pgvector）
- ✅ Q&A 问答 JSON 接口（答案、拒答标记、命中数、耗时、Sources）
- ✅ 前端问答结果展示（答案、来源片段、score、耗时）
- ⚠️ `.doc` 旧格式暂不进入 RAG 解析；建议使用 `.docx` / `.pdf` / `.txt` / `.md`
- ⚠️ 真实 Ollama 连通和端到端服务启动验收待后续执行

---

## 常用端口

| 服务 | 端口 | 说明 |
|------|------|------|
| 后端 API | 8081 | Spring Boot |
| RAG 服务 | 8091 | FastAPI |
| 前端页面 | 3001 | Vite dev server |
| PostgreSQL | 5432 | Docker `mykb-pg` |
| Redis | 6379 | Docker `redis-local` |
| MinIO API | 19000 | Docker `minio-local`（暂未使用） |
| MinIO 控制台 | 19001 | Web 管理界面 |

---

## 目录结构

```
My_KnowledgeBase/
├── apps/
│   ├── server/          # Java 后端
│   │   ├── src/main/java/com/mykb/server/
│   │   │   ├── auth/        # 认证模块
│   │   │   ├── common/      # 公共组件（安全、存储、异常）
│   │   │   ├── document/    # 文档管理
│   │   │   ├── knowledgebase/ # 知识库 CRUD
│   │   │   ├── ocr/         # OCR 客户端
│   │   │   └── qa/          # 问答（暂不可用）
│   │   └── src/main/resources/db/migration/  # Flyway 迁移脚本
│   ├── web/             # React 前端
│   │   └── src/
│   │       ├── App.jsx      # 主应用（单文件）
│   │       ├── main.jsx     # 入口
│   │       └── styles.css   # 少量全局样式
│   ├── rag/             # Python RAG 微服务
│   └── ocr/             # Python OCR 微服务
├── docs/                # 项目文档
│   ├── WORKLOG.md       # 工作日志
│   └── STARTUP.md       # 本文件
├── .runtime/            # 运行时数据（不提交 git）
└── .env.example         # 环境变量模板
```
