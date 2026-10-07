# Tasks

## 1. API image

- [x] 1.1 Add `apps/api/Dockerfile` (slim Python, install `requirements.txt`, copy app/agents/ingest, uvicorn on 8000, no secrets in image). Verify: `docker build -f apps/api/Dockerfile apps/api` succeeds.
- [x] 1.2 Add `.dockerignore` for API (venv, `__pycache__`, tests caches, local `.env`). Verify: build context excludes `.venv` / `.env`.

## 2. Web image and Nginx

- [x] 2.1 Add `apps/web/Dockerfile` multi-stage (npm build → nginx:alpine with `dist`). Verify: `docker build -f apps/web/Dockerfile apps/web` produces image serving `index.html`.
- [x] 2.2 Add Nginx config: SPA `try_files`, `/api/` reverse proxy to `api:8000`, SSE-friendly (`proxy_buffering off`), read/send timeout ≥ 300s, `client_max_body_size` ≥ 20m. Verify: config file present and referenced by web Dockerfile/compose.
- [x] 2.3 Add `apps/web/.dockerignore` (node_modules, dist). Verify: build does not copy host `node_modules` as sole dependency source.

## 3. Compose stack

- [x] 3.1 Add root `docker-compose.yml` with `db` (pgvector), `api`, `web`; volumes for Postgres and API `data/`; `api` waits on db health; web depends on api. Verify: `docker compose config` validates.
- [x] 3.2 Add `.env.example` (or `deploy/.env.example`) listing `DATABASE_URL`/Postgres creds, `bailian_api_key`, model envs; document that real `.env` is gitignored. Verify: example contains required keys without real secrets.
- [x] 3.3 Ensure compose does **not** define a separate Agent service. Verify: `docker compose config --services` is only web/api/db (plus any explicit helper, not agent).

## 4. Docs and smoke

- [x] 4.1 Document overseas single-VPS bring-up in `apps/api/README.md` or root/deploy README: build, up, health (`/health` via `/api` or direct), ingest note, Bailian-from-abroad caveat. Verify: doc mentions compose services, volumes, and env example path.
- [ ] 4.2 Local smoke: compose up, hit Web `/`, proxy `/api/health` (or API health through nginx). Verify: HTTP 200 from health through the public web entry.
