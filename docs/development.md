# Development Guide

This document explains how to set up a local development environment, run the project, and complete the first development tasks for the AI Course Prerequisite Validator.

---

## Prerequisites

- **Git** 2.30+  
- **Python** 3.10+ (use pyenv or virtualenv)  
- **Node.js** 16+ (for frontend work)  
- **Docker** (optional, recommended for local DB or services)  
- **Make** or a small script runner (optional but helpful)

---

## Repository layout

```
.
├─ app/                    # backend application (FastAPI)
├─ frontend/               # React dashboard (Cytoscape/D3)
├─ parsers/                # catalog parsers and parser tests
├─ samples/                # sample catalogs and fixtures
├─ tests/                  # unit and integration tests
├─ docs/                   # documentation (this file, API specs)
├─ .github/workflows/      # CI workflows
├─ requirements.txt
├─ package.json
└─ README.md
```

---

## Clone and create virtual environment

Run these commands from your project root (VS Code terminal is fine):

```bash
git clone https://github.com/<your-org>/<repo>.git
cd <repo>
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

For frontend:

```bash
cd frontend
npm install
cd ..
```

---

## Environment variables

Create a `.env` file in the repo root with required variables. Example minimal values for local dev:

```
FLASK_ENV=development
DATABASE_URL=sqlite:///dev.db
SECRET_KEY=dev-secret
```

Adjust for FastAPI or your chosen backend framework.

---

## Run the backend locally

Example for FastAPI:

```bash
uvicorn app.main:app --reload --port 8000
# or using Makefile
make run-backend
```

Visit `http://localhost:8000/docs` for OpenAPI UI if enabled.

---

## Run the frontend locally

```bash
cd frontend
npm start
# default: http://localhost:3000
```

The frontend should be configured to proxy API requests to the backend (see `frontend/.env` or package proxy).

---

## Tests and linters

Run unit tests:

```bash
pytest -q
```

Run formatters and linters:

```bash
# Python
black .
flake8

# Frontend
cd frontend
npx prettier --check "src/**/*"
npx eslint "src/**/*"
```

---

## Pre-commit hooks

Install pre-commit hooks to enforce formatting and checks:

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

---

## Common developer scripts

Add helpful scripts under `scripts/` or a `Makefile`:

- `make run-backend` — start backend with reload  
- `make run-frontend` — start frontend dev server  
- `make test` — run tests  
- `make lint` — run linters and formatters  
- `make ingest-sample` — run ingestion on `samples/` data

Example `make` targets should be included in the repo for consistency.

---

## Adding a new parser

1. Create a new parser module under `parsers/` (e.g., `parsers/courseleaf.py`).  
2. Add unit tests under `tests/parsers/test_courseleaf.py` with sample HTML/JSON in `samples/`.  
3. Ensure parser outputs normalized course records: `course_id`, `title`, `prereq_text`, `level`, `terms_offered`.  
4. Run tests and linting locally. Commit with a clear message.

---

## Running an analysis locally

1. Ingest sample catalog into a local snapshot: `python scripts/ingest.py --source samples/sample-catalog.html`  
2. Build graph: `python scripts/build_graph.py --snapshot snapshots/latest.json`  
3. Run validator: `python scripts/validate_graph.py --graph data/graph.json --report reports/latest.json`  
4. Open the frontend and load the `reports/latest.json` for visualization.

Provide small CLI wrappers to make these steps one-command for developers.

---

## CI and GitHub Actions

- Ensure workflows run tests, linters, and the DCO check on PRs.  
- Add a job to run parser unit tests and a smoke test that ingests a tiny sample and runs cycle detection.  
- Add an artifacts job to publish OpenAPI spec validation results.

---

## Local data and fixtures

- Keep sample catalogs small and representative in `samples/`.  
- Add a `samples/README.md` describing each sample and how to regenerate it.  
- Avoid committing sensitive data.

---

## Deployment notes

- Containerize backend and frontend with Docker.  
- Use managed Postgres for production and S3 for snapshots.  
- Use a job queue (Celery + Redis) for heavy ingestion/analysis tasks.  
- Start with a single-tenant pilot deployment before multi-tenant architecture.

---

## Troubleshooting

- If tests fail, run `pytest -k <testname> -vv` to isolate.  
- If the frontend cannot reach the backend, confirm proxy or CORS settings.  
- If ingestion fails on a new catalog, add a parser or extend the NLP fallback.

---

## Useful links and references

- OpenAPI spec location `docs/api/openapi.yaml`  
- Sample ingestion command `scripts/ingest.py --help`  
- Developer contact `MAINTAINERS.md` for who to ping on issues

```

---
