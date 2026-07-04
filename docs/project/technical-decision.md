# Technical Decision

日期：2026-03-18
当前修订：2026-07-04

## 1. 项目类型

- 结论：采用 `Type C`
- 原因：项目包含多用户、知识库管理、文件上传、异步任务、外部 AI 平台集成和共享访问，已经明显超过工具脚本或单页 Demo 范围。

## 2. 技术路线

### 前端

- React + Vite
- 当前阶段保留 skeleton，后续再补业务页与生产构建

### 后端

- Spring Boot 3.3
- Spring MVC
- 模块化单体，中文解释：单服务部署、内部按业务模块拆分
- 正式运行时目标：`Java 21`
- 当前本地验证：`JDK 17`

### 数据与基础设施

- PostgreSQL：业务数据
- Redis：缓存、限流和后续任务辅助
- MinIO：文档对象存储
- PostgreSQL / pgvector：计划承接本地向量索引
- Ollama 或 OpenAI-compatible 本地模型：计划承接 Embedding / 生成能力
- OCR 独立容器：扫描件识别与后续文档预处理

## 3. RAG 决策

- 结论：移除 Dify，改成本地 RAG
- 原因：
  - Dify 运行成本过高，需要额外容器和内存，不适合当前本地/轻量部署目标
  - 项目更需要展示 `parse -> chunk -> embedding -> retrieve -> generate` 的工程能力
  - 本地 RAG 更容易控制数据、部署和面试讲述边界
- 当前状态：
  - Dify Java 包、配置项和数据库关联字段已移除
  - Q&A 接口暂时返回 `503`
  - 文档摄入目前完成到文件读取、可选 OCR 和处理状态落库
- 下一步：
  - 新增 chunk / embedding / vector schema
  - 接入 `pgvector`
  - 接入 Ollama 或 OpenAI-compatible 本地模型
  - 恢复问答、拒答和 sources 引用

## 4. 部署拓扑

- 结论：采用“同机单服务器 + 分容器隔离”
- 说明：
  - 本项目 compose：`server + postgres + redis + minio`
  - OCR：同机独立容器或独立 worker
  - 公网入口只保留 `Nginx 80/443`

## 5. 本地开发模式

- 结论：采用 `Hybrid Dev`
- 说明：
  - 前端本地启动
  - 后端本地启动
  - PostgreSQL / Redis / MinIO 用 Docker
  - OCR 在本地容器或独立进程接入

## 6. 端口规划

- Frontend: `3001`
- Backend API: `8081`
- PostgreSQL: `5432`
- Redis: `6379`
- MinIO API: `9000`
- MinIO Console: `9001`
- Ollama API: `11434`，可选本地访问
- OCR Service: `8090`，内部访问

说明：最终项目按部署标准统一使用 `3001/8081`，不再沿用草稿中的 `3000/8080`。

## 7. 当前未决项

- OCR 最终是 `PaddleOCR` 还是 `OCRmyPDF + OCR Engine` 组合
- 异步任务首版是否继续使用数据库任务表，还是补 `Redis Stream`
- 文档解析器选型：直接 Java 解析、Apache Tika，还是独立解析 worker
- Embedding 模型选型和维度
- chunk 粒度、重叠策略、引用定位策略
