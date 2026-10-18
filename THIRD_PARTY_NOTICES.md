# 第三方依赖与许可边界

根目录 [MIT 许可证](LICENSE)适用于本项目维护者拥有版权的代码与说明，不将第三方内容重新授权为 MIT。没有发现单独随源码分发的第三方字体或模型权重；依赖由各自包管理器安装。本次发布不包含 `node_modules`、JAR、Python虚拟环境、前端构建包或模型文件。

## 使用的主要依赖

| 范围 | 版本依据与上游入口 | 使用与分发边界 |
|---|---|---|
| React、Vite及前端开发工具 | `apps/web/package.json`、`apps/web/package-lock.json`；[React](https://github.com/facebook/react)、[Vite](https://github.com/vitejs/vite) | 各依赖保留所用版本的许可证；本机已核 React、Vite、ESLint及其所用插件的包元数据为 MIT，Playwright为 Apache-2.0。生成可分发构建包时，还须保留其中打入的第三方版权与许可。 |
| Spring Boot及Java依赖 | `apps/server/pom.xml`；[Spring Boot](https://github.com/spring-projects/spring-boot)、[JJWT](https://github.com/jwtk/jjwt)、[MinIO Java SDK](https://github.com/minio/minio-java) | 不把这些依赖的许可覆盖为本项目 MIT；分发JAR时按实际打包依赖携带相应 LICENSE／NOTICE。 |
| FastAPI、Langfuse、Uvicorn、Psycopg、pypdf、python-docx等 | `apps/rag/requirements.txt`；[FastAPI](https://github.com/fastapi/fastapi)、[Langfuse](https://github.com/langfuse/langfuse-python)、[Psycopg](https://github.com/psycopg/psycopg) | 各依赖适用自己的版本许可，包括与 MIT 不同的许可证；本仓库不提供这些依赖的副本。 |
| OCR服务依赖 | `apps/ocr/requirements.txt`；[RapidOCR](https://github.com/RapidAI/RapidOCR) | OCR为可选功能，库、识别模型与其运行时需分别遵守原许可；本轮未下载、打包或重新授权模型。 |
| PostgreSQL／pgvector、Redis、MinIO、JDK等运行服务与镜像 | `deploy/docker-compose.yml`、`apps/server/Dockerfile`；[pgvector](https://github.com/pgvector/pgvector)、[Redis](https://github.com/redis/redis)、[MinIO](https://github.com/minio/minio) | 服务、镜像与不同版本可能适用各自的许可及使用条件；本文不是容器镜像的再许可或完整软件物料清单。 |
| Ollama及模型 | [Ollama](https://github.com/ollama/ollama)、[nomic-embed-text](https://ollama.com/library/nomic-embed-text)、[qwen2.5](https://ollama.com/library/qwen2.5) | 运行工具与模型权重的许可分别核对；`ollama pull` 由使用者执行，本项目不分发或将模型授权为 MIT。 |

## 图片、商标与使用者资料

- `docs/picture/` 与前端测试快照用于说明项目界面，其中可能出现的第三方名称、商标与产品界面元素仍归各自权利人；本项目 MIT 不授予这些第三方权利。历史截图属于旧 Dify 阶段，不能证明当前本地 RAG 界面或完整流程已验收。
- 使用者上传的文档、私人笔记及数据库不属于本项目许可证范围，不应提交到源码仓库。已确认的测试运行输出不再随当前源码跟踪；这不改写既有 Git 历史。
- 新增或替换第三方源码、字体、图片、模型或发布安装包前，应核对对应版本的实际许可与署名义务；此文件不是对未来依赖版本的统一许可保证。
