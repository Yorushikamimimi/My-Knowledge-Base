# Quality Report

## Current Status Update (2026-07-04)

The 2026-03 Dify quality gate below is historical.
The current codebase has removed Dify integration and the Q&A endpoint returns `503` while local RAG is being rebuilt.

Current verified baseline:

- Backend can start locally against PostgreSQL and Flyway migration version 6.
- Frontend Vite app can start on `3001`.
- Knowledge base management, document upload, storage, ingestion task status, and OCR wiring remain the active product surface.

Current gap:

- `QA / SSE`, vector retrieval, generated answers, and `Sources` are not implemented in the current runtime.

Date: 2026-03-20

## Conclusion

The project quality gate now passes with real self-hosted `Dify` and real `OCR` integration validated.
The backend smoke paths `health -> auth -> knowledge base -> upload -> ingestion -> QA / SSE` and `PDF -> OCR -> ingestion` both passed against the local Docker-based runtime, the frontend workbench was manually validated in the browser, and the Linux rehearsal scripts passed `bash` syntax validation in a Linux container.

## Executed Checks

- `npm run lint` in `apps/web`
  - Result: passed
- `npm run build` in `apps/web`
  - Result: passed
- `mvn -gs .maven-settings.xml -pl apps/server test`
  - Result: passed
- `./scripts/lint.ps1`
  - Result: passed
- `./scripts/build.ps1`
  - Result: passed
- `./scripts/smoke.ps1 -BaseUrl http://127.0.0.1:8081`
  - Result: passed on 2026-03-19
  - Verified scope:
    - `actuator/health`
    - register / login token issue path
    - knowledge base create
    - document upload
    - ingestion task polling
    - `Dify dataset/document` sync
    - `QA / SSE`
- `./scripts/smoke.ps1 -BaseUrl http://127.0.0.1:8081 -RunOcrCheck`
  - Result: passed on 2026-03-20
  - Verified scope:
    - PDF upload
    - OCR extraction service call
    - OCR stage transition
    - OCR-backed Dify ingestion completion
- `docker run --rm -v ... maven:3.9.9-eclipse-temurin-21 bash -n /workspace/scripts/smoke.sh /workspace/scripts/rehearse-linux.sh`
  - Result: passed on 2026-03-20
  - Verified scope:
    - Linux bash syntax for `smoke.sh`
    - Linux bash syntax for `rehearse-linux.sh`
- Browser manual validation on `http://localhost:3001`
  - Result: passed on 2026-03-20
  - Verified scope:
    - login from local frontend after local `CORS` fix
    - knowledge base selection
    - text document upload
    - task status refresh
    - source-backed streamed QA answers

## New Quality Points In This Round

- Added in-repo OCR adapter service under `apps/ocr`
- Added OCR container wiring to [deploy/docker-compose.yml](/D:/Workspace/SelfProject/My-Knowledge-Base/deploy/docker-compose.yml)
- Replaced unstable system-package OCR path with `RapidOCR + opencv-python-headless`
- Fixed OCR multipart request compatibility between backend and OCR service
- Verified the backend can complete `PDF -> OCR -> Dify ingestion`
- Added Linux-executable smoke and rehearsal scripts
- Added owner-only failed document delete and failed ingestion task retry capability across backend and frontend

## Known Limitations

- Real Linux host deployment rehearsal is still pending
- Duplicate upload is currently blocked by `knowledgeBase + originalFilename + sizeBytes`
- Duplicate recovery now relies on owner-only failed document delete or failed task retry
- Historical failed tasks remain visible by design and there is still no bulk cleanup UX
- Docker image builds still depend on external package registries being reachable during build time

## Incremental Addendum (2026-03-23)

### Scope

- Frontend UI structure and interaction refinement only (`apps/web`)
- No backend API contract change in this round

### Checks Executed

- `npm run build` in `apps/web`
  - Result: passed on 2026-03-23

### New Quality Points

- Added dedicated Chat tab to separate QA interaction from document operation panel
- Added 专注对话 jump action from Documents chat card
- Increased dedicated chat workspace area and feed height
- Reduced global typography scale to improve readability and screen fit

### Residual Risks

- Responsive manual validation for all redesigned pages is not yet fully re-run
- UI parity against all target mock screens still requires one final visual pass


