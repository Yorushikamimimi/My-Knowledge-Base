# Release Record

## 2026-07-04

### Documentation Status Correction

- Updated project positioning from the old Dify-based knowledge QA platform to the current AI knowledge-base engineering base.
- Marked Dify integration as removed from the current runtime path.
- Documented the active scope: auth, knowledge base management, document upload, storage, ingestion task status, OCR wiring, and frontend workbench.
- Documented the current gap: local RAG, vector retrieval, generated answers, and `Sources` are not implemented yet.
- Set the next technical direction to `Ollama + pgvector`.

## 2026-03-23

### Completed This Round

- Refined frontend information architecture across Workspace / Insights / Collections / Archive / Library
- Added dedicated Chat navigation entry to separate QA from document operations
- Added in-page 专注对话 quick action on Documents page for one-click jump to full chat mode
- Expanded dedicated chat panel area and feed height to improve readability on wide screens
- Reduced overall UI typography scale for better visual density and consistency
- Rebuilt frontend with `npm run build` after the structural and style changes

### Why This Matters

- QA flow is no longer constrained by the two-column document layout
- Workspace now supports both operation mode (Documents) and focused conversation mode (Chat)
- The revised typography and spacing reduce visual fatigue in long sessions

### Current State

- Core QA workflow is stable in both entry points:
  - Workspace -> Documents -> 专注对话
  - Workspace -> Chat
- Frontend build passes after the UI structure update

### Known Gaps

- No in-page hide documents toggle yet; current strategy is dedicated Chat page
- Full responsive manual pass for all redesigned pages is still pending

### Recommended Next Step

- Add one lightweight responsive verification round (desktop + tablet + mobile) for all workspace tabs
- Then decide whether to add optional in-page Hide Docs toggle in Documents view

## 2026-03-20

### Completed This Round

- Passed real local `Dify` smoke for `health -> auth -> knowledge base -> upload -> ingestion -> QA / SSE`
- Manually validated the frontend workbench on `http://localhost:3001`
- Fixed local frontend `CORS` for `localhost:3001 / 127.0.0.1:3001`
- Fixed `Dify Completion API` payload compatibility by sending `query` in both top-level payload and app inputs
- Fixed dataset creation compatibility when knowledge base description is empty
- Added an in-repo OCR adapter service under `apps/ocr`
- Switched OCR runtime to `RapidOCR + opencv-python-headless`
- Wired OCR into [deploy/docker-compose.yml](/D:/Workspace/SelfProject/My-Knowledge-Base/deploy/docker-compose.yml)
- Fixed backend OCR multipart compatibility with the OCR service contract
- Passed real OCR smoke for `PDF -> OCR -> Dify ingestion`
- Added Linux-executable smoke script [smoke.sh](/D:/Workspace/SelfProject/My-Knowledge-Base/scripts/smoke.sh)
- Added Linux deployment rehearsal wrapper [rehearse-linux.sh](/D:/Workspace/SelfProject/My-Knowledge-Base/scripts/rehearse-linux.sh)
- Verified streamed answers and source rendering in the browser
- Verified new ingestion tasks complete successfully after the backend fixes
- Added owner-only failed document delete and failed ingestion task retry in backend APIs
- Added frontend recovery actions for failed document cleanup and failed task retry

### Current State

Core product flow currently provides:

- login / registration
- knowledge base creation and selection
- document upload
- ingestion task tracking
- Dify dataset / document synchronization
- OCR-backed PDF ingestion
- streamed QA with retrieved sources
- Linux-executable smoke / rehearsal package

Still pending:

- real Linux host deployment rehearsal
- bulk cleanup / bulk retry UX for historical failures

### Recommended Next Step

- Execute `bash scripts/rehearse-linux.sh` on the target Linux host
- Then decide whether bulk cleanup UX is needed beyond the current single-item recovery path
- If deployment hosts are network-constrained, harden image build caching before release

## 2026-03-18

### Completed This Round

- Confirmed formal technical baseline: `Java 21`, `Dify self-hosted`, same-host split containers, `MinIO`
- Delivered document upload and ingestion task tracking
- Delivered `Dify dataset/document API` integration
- Delivered `OCR orchestration` for PDF ingestion
- Delivered `QA / chat SSE` with source-return and refusal behavior
- Delivered frontend business workbench with upload, task, and QA panels
- Added deployment smoke script for health, auth, KB, upload, ingestion, and QA validation
- Aligned Docker runtime env forwarding with the delivered Dify/OCR feature set
- Rehearsed the project Docker stack locally and confirmed `actuator/health = UP`
- Captured the real external dependency blocker: Dify connect failure at `http://host.docker.internal:8088/v1/datasets`
- Fixed authenticated SSE handling for async dispatch
- Updated env templates, deployment boundary, and project docs
- Passed frontend `lint / build`
- Re-passed backend `test / lint / build`

### Current State

Backend currently provides:

- Auth
- Knowledge base basic management
- Document upload
- Ingestion task records
- Dify dataset/document synchronization
- PDF OCR ingestion path
- Knowledge-base-scoped streaming QA

Still pending:

- Real external-service smoke tests

### Recommended Next Step

- Run real Dify / OCR smoke tests
- Then do one Linux deployment rehearsal




