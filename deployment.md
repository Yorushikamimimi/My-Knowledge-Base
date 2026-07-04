# Deployment Guide

## Conclusion

Formal deployment uses `Docker + host Nginx`, meaning containers run the project stack, while the host Nginx exposes only `80/443`.
The repository-managed stack currently includes `server + postgres + redis + minio + ocr`.
`Dify` has been removed from the current runtime path; local RAG with `pgvector` and a local model runtime is the next target.

## Deployment Topology

- Host `Nginx`: public entry, only `80/443`
- Project stack: `server + postgres + redis + minio + ocr`
- Optional future model runtime: Ollama or another OpenAI-compatible local service

## Suggested Directory Layout

```text
/srv/apps/my-knowledge-base/
|-- app/
|   |-- current/
|   `-- releases/
|-- deploy/
|   |-- docker-compose.yml
|   |-- .env
|   `-- nginx/
|-- logs/
`-- backup/
```

## Port Plan

- Public: `80/443`
- Backend API: `8081`
- PostgreSQL: `5432`
- Redis: `6379`
- MinIO API: `9000`
- MinIO Console: `9001`
- Ollama API: `11434`, optional future local model runtime
- OCR Service: `8090`, internal access

## Environment Variables

Use [deploy/.env](/D:/Workspace/CodexProject/My_KnowledgeBase/deploy/.env) for runtime variables.

Key variables:

- `APP_VERSION`
- `SERVER_PORT`
- `DB_HOST` / `DB_PORT` / `DB_NAME` / `DB_USERNAME` / `DB_PASSWORD`
- `REDIS_HOST` / `REDIS_PORT`
- `APP_JWT_SECRET`
- `APP_STORAGE_TYPE`
- `APP_STORAGE_BUCKET`
- `MINIO_ENDPOINT` / `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY`
- `OCR_BASE_URL`
- `OCR_ENABLED` / `OCR_TIMEOUT` / `OCR_PDF_CONTENT_TYPE`

## OCR Service Contract

The in-repo OCR service listens on `8090` and exposes:

- `GET /healthz`
- `POST /api/v1/ocr/extract`

The extraction endpoint accepts multipart field `file` and returns JSON:

- `text`
- `engine`

## QA Status

The streaming QA endpoint is currently disabled and returns `503`.
The next implementation should use local RAG:

- parse uploaded documents
- split text into chunks
- create embeddings
- persist vectors in `pgvector`
- retrieve chunks within the selected knowledge base
- generate an answer with sources and refusal behavior

## First Deployment

1. Put the code at `/srv/apps/my-knowledge-base/app/releases/<version>/`
2. Copy `deploy/` to the deployment directory
3. Adjust `deploy/.env`
4. Start the project stack

```bash
docker compose --env-file deploy/.env -f deploy/docker-compose.yml up -d --build
```

5. Check backend and OCR health

```bash
curl http://127.0.0.1:8081/actuator/health
curl http://127.0.0.1:8090/healthz
```

6. Make Linux scripts executable

```bash
chmod +x scripts/smoke.sh scripts/rehearse-linux.sh
```

7. Execute smoke tests

```bash
bash scripts/smoke.sh --base-url http://127.0.0.1:8081
bash scripts/smoke.sh --base-url http://127.0.0.1:8081 --run-ocr-check
```

Or run the full rehearsal wrapper:

```bash
bash scripts/rehearse-linux.sh
```

8. Validate and reload Nginx

```bash
nginx -t && systemctl reload nginx
```

## Logs And Status

- Container status

```bash
docker compose --env-file deploy/.env -f deploy/docker-compose.yml ps
```

- API logs

```bash
docker compose --env-file deploy/.env -f deploy/docker-compose.yml logs -f server
```

- OCR logs

```bash
docker compose --env-file deploy/.env -f deploy/docker-compose.yml logs -f ocr
```

- MinIO logs

```bash
docker compose --env-file deploy/.env -f deploy/docker-compose.yml logs -f minio
```

## Update Steps

1. Back up the current `deploy/.env`
2. Record the current image tag and release directory
3. Upload the new release
4. Run `docker compose up -d --build`
5. Execute both smoke commands or `bash scripts/rehearse-linux.sh`
6. Observe for 15 to 30 minutes

## Rollback Steps

1. Switch back to the previous release or image tag
2. Run `docker compose up -d`
3. Verify `actuator/health`
4. Verify `OCR /healthz`
5. Verify `bash scripts/smoke.sh`

## Current Limits

- Q&A is not production-ready in the current codebase; Dify has been removed and local RAG is not implemented yet
- Real Linux host rehearsal is still pending in this workspace; what is delivered here is the Linux-executable rehearsal package
- Docker image builds rely on outbound access to package registries during build time
