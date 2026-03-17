# Technical Setup

## Prerequisites

- Node.js and npm
- Python 3.12+
- `uv`

## Install

```bash
npm run setup
```

This installs frontend dependencies and syncs backend dependencies.

## Run Locally

```bash
npm run dev
```

Default endpoints:

- Web: `http://localhost:3200`
- API: `http://localhost:8100`

## Environment

Create local API configuration in `apps/api/.env`:

```bash
HT_DB_URL=sqlite:///./app/data/healthtwin.db
HT_UPLOAD_DIR=./app/data/uploads
HT_DOMAIN_CONTRACT_PATH=../../packages/domain-healthcare/domain.json
HT_LLM_API_KEY=...
HT_LLM_BASE_URL=https://openrouter.ai/api/v1
HT_LLM_MODEL=openai/gpt-oss-120b:free
```

LLM integration is optional for local use. The bundled demo flow works deterministically without provider access.

## Demo Import

```bash
curl -X POST http://localhost:8100/api/demo/import
```

This endpoint creates a fresh project and run from the bundled MetroCare package and returns all primary artifacts.

## Verification

Backend tests:

```bash
cd apps/api
uv run pytest -q
```

Frontend build:

```bash
cd apps/web
npm run build
```
