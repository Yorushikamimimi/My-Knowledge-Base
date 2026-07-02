# 工作日志

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
