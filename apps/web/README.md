# Web App

This package contains the React + Vite frontend for `My Knowledge Base`.
It is the browser-facing workbench for knowledge base selection, document
upload, ingestion tracking, and streaming QA.

## Scope

- workspace shell and navigation
- knowledge base document management
- QA/chat workspace
- responsive product UI and visual parity

## Local Run

从仓库根目录开始（新终端），先安装锁定依赖，再启动本机开发服务：

```bash
cd apps/web
npm ci
npm run dev -- --host 127.0.0.1 --port 3001
```

## Verification

- `npm run lint`
- `npm run build`
- `npm run test:e2e`

## Environment

- frontend reads backend base URL from `VITE_API_BASE_URL`
- default local frontend port: `3001`

完整依赖、后端/RAG启动顺序及内部服务边界见 [启动指南](../../docs/STARTUP.md)。无需 pnpm；不要直接运行尚未安装的 `node_modules` 中的文件。
