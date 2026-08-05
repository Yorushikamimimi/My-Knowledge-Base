# Predeploy Report

## Current Status Update (2026-07-04)

This report contains the 2026-03 Dify deployment rehearsal history.
It is no longer the current deployment target.

Current deployment baseline:

- Active stack: `server + postgres + redis + minio + ocr`
- Removed dependency: Dify
- Current Q&A state: disabled, returns `503`
- Next deployment target after implementation: local RAG using `pgvector` plus a local or OpenAI-compatible model runtime

Date: 2026-03-20

## Conclusion

The project has reached a deployment-bounded and reviewable state with the core product flow and OCR ingestion flow verified end to end in the local Docker runtime.
It is not yet production-ready because one real Linux host deployment rehearsal is still pending, although the Linux-executable rehearsal package is now included in the repository.

## Deployment Baseline Confirmed

- Deployment mode: `Docker + host Nginx`
- Runtime target: `Java 21`
- Topology: same-host split containers / stacks
- Internal ports: `8081 / 5432 / 6379 / 9000 / 9001 / 8088 / 8090`
- Public ports: only `80 / 443`
- External dependencies bounded:
  - project backend stack
  - Dify self-hosted stack
  - MinIO
- Project stack now directly includes:
  - `server`
  - `postgres`
  - `redis`
  - `minio`
  - `ocr`

## Local Start / Stop Runbook

This repository uses two Docker stacks during local verification:

- project stack: `deploy/docker-compose.yml`
- Dify stack: `D:\services\dify\docker\docker-compose.yaml`

### Start Order

1. Start the Dify stack

```powershell
cd /d D:\services\dify\docker
docker compose up -d --build
```

2. Start the project stack

```powershell
cd /d D:\Workspace\SelfProject\My-Knowledge-Base
docker compose --env-file deploy\.env -f deploy/docker-compose.yml up -d --build
```

3. Start the frontend when you need browser verification

```powershell
cd /d D:\Workspace\SelfProject\My-Knowledge-Base\apps\web
npm install
npm run dev -- --host 0.0.0.0 --port 3001
```

### Stop Order

1. Stop the project stack

```powershell
cd /d D:\Workspace\SelfProject\My-Knowledge-Base
docker compose --env-file deploy\.env -f deploy/docker-compose.yml down
```

2. Stop the Dify stack

```powershell
cd /d D:\services\dify\docker
docker compose down
```

3. Stop the frontend dev server

- press `Ctrl+C` in the `npm run dev` terminal

### Verification Notes

- Backend health: `http://127.0.0.1:8081/actuator/health`
- Frontend: `http://localhost:3001`
- Dify API: `http://127.0.0.1:8088/v1`
- If the backend runs in Docker, `DIFY_BASE_URL` must use `http://host.docker.internal:8088/v1`

## Delivered Scope

- Auth
- Knowledge base management
- Document upload
- Ingestion task tracking
- `Dify dataset/document API` integration
- `QA / chat SSE`
- Frontend business workbench
- Local browser-based workbench validation
- Real OCR adapter service and PDF ingestion validation
- Linux-executable smoke and rehearsal scripts

## Verified Rehearsal Result

- `postgres / redis / minio / server / ocr` are up from [deploy/docker-compose.yml](/D:/Workspace/SelfProject/My-Knowledge-Base/deploy/docker-compose.yml)
- Dify self-hosted stack is reachable on local `8088`
- `http://127.0.0.1:8081/actuator/health` returned `UP`
- `http://127.0.0.1:8090/healthz` returned `UP`
- `./scripts/smoke.ps1 -BaseUrl http://127.0.0.1:8081` passed end to end on 2026-03-19
- `./scripts/smoke.ps1 -BaseUrl http://127.0.0.1:8081 -RunOcrCheck` passed end to end on 2026-03-20
- Frontend workbench on `http://localhost:3001` was manually validated on 2026-03-20
- Linux-executable rehearsal package is available via:
  - [smoke.sh](/D:/Workspace/SelfProject/My-Knowledge-Base/scripts/smoke.sh)
  - [rehearse-linux.sh](/D:/Workspace/SelfProject/My-Knowledge-Base/scripts/rehearse-linux.sh)
- Browser flow verified:
  - login
  - knowledge base selection
  - document upload
  - ingestion task completion
  - failed task retry
  - failed document cleanup for duplicate recovery
  - streamed QA with retrieved source display

## Current Blocking Items

- Real Linux host deployment rehearsal not executed yet

## Risks- Local workstation still validates with mixed host tooling while deployment target is `Java 21`
- OCR currently runs through the in-app async executor, which is enough for MVP but may require a dedicated worker later if OCR load grows
- QA quality still depends on the Dify completion app prompt and retrieval settings
- Duplicate document strategy is strict, although failed-document delete and failed-task retry now cover the main recovery path
- Docker image builds still rely on external package registries and may require stable outbound network on the deployment host
- MinIO backup / retention policy is not refined yet

## Recommended Next Actions

1. Execute `bash scripts/rehearse-linux.sh` on the target Linux host and capture output
2. Decide whether bulk cleanup UX is needed beyond the current single-item delete / retry path
3. If deployment hosts are network-constrained, harden image build caching before release




