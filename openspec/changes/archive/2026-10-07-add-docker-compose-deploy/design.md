# Design

## Context

- 前端 `apps/web` 全部使用相对路径 `/api/...`；开发态靠 Vite proxy，生产必须同源反代。
- 后端 `apps/api`：FastAPI + 进程内 Agent；依赖 Postgres（成绩、会话、quiz、checkpointer、pgvector 教材）。
- 答卷上传在 `apps/api/data/uploads/`；PDF 用 fpdf2 + Pillow，插图为 SVG/PNG，**无需** Playwright/WeasyPrint 重系统库（当前栈）。
- 仓库尚无 Dockerfile / compose；需求文档已写一期 Compose 拓扑。
- 部署目标：海外单机 VPS（新加坡/东京等），不绑定大陆域名/机房。

## Goals / Non-Goals

**Goals**

- 根目录 `docker-compose.yml` 一键起 `web` + `api` + `db`。
- `apps/api/Dockerfile`、`apps/web/Dockerfile`（多阶段）可重复构建。
- `.env.example`（或 `deploy/.env.example`）列出必需变量；密钥不入库。
- Nginx：静态 + `/api` 反代；SSE/长请求超时放宽。
- 简短部署说明（构建、起停、卷、健康检查）。

**Non-Goals**

- K8s / Fly.toml / 大陆 ICP；独立 Agent 容器；S3/R2；CI CD；TLS 自动证书编排（文档可提 Cloudflare/Caddy 前置）；教材自动入库 job。

## Decisions

1. **三服务 Compose**
   - `db`: 官方或社区 `pgvector/pgvector:pg16`（或等价），volume `pgdata`；健康检查 `pg_isready`。
   - `api`: 构建自 `apps/api`；依赖 `db` healthy；挂载 `api_data` → `/app/data`（或项目内 `data/`）；`DATABASE_URL=postgresql://...@db:5432/...`；暴露仅给内部网络，或仅 8000 给 web。
   - `web`: 构建自 `apps/web`；Nginx 监听 80；`proxy_pass` 到 `http://api:8000`；对外映射 `80:80`（或 `8080:80` 便于本机）。

2. **API 镜像**
   - 基础：`python:3.12-slim`（或与本地一致的 3.13，以 CI/本机可构建为准）。
   - `pip install -r requirements.txt`；WORKDIR 含 `app/`、`agents/`、`ingest/`、`bangxue_env.py`。
   - CMD：`uvicorn app.main:app --host 0.0.0.0 --port 8000`（生产可不 `--reload`）。
   - 系统包：按 Pillow/字体需要最小安装（如 `fonts-dejavu-core` 若 PDF 中文缺字再补中文字体包——实现时以一次 PDF 冒烟为准）。
   - **不**把 `.env` COPY 进镜像；运行时 `env_file` / compose `environment`。

3. **Web 镜像**
   - Stage1：`node:22-alpine` → `npm ci && npm run build` → `dist/`。
   - Stage2：`nginx:alpine` + 自定义 `nginx.conf`：`root` 指向静态；`location /api/` 反代 API；`proxy_buffering off`（利于 SSE）；`proxy_read_timeout` / `proxy_send_timeout` ≥ **300s**（出题/对话）；上传 `client_max_body_size` ≥ **20m**（答卷图）。
   - SPA：`try_files $uri /index.html`。

4. **网络与 CORS**
   - 同源反代后浏览器无跨域；API 无需为 compose 特开宽松 CORS（若已有中间件保持不变即可）。

5. **环境变量清单（示例，非密钥入库）**
   - `DATABASE_URL`、`POSTGRES_USER`/`PASSWORD`/`DB`（compose 内拼 URL）
   - `bailian_api_key`、`QUIZ_MODEL`、`EMBEDDING_MODEL` 等（与现有 `bangxue_env` / README 对齐）
   - 可选：`QUIZ_PAPER_TTL_DAYS`、`GRADING_DISABLE_DEMO`

6. **数据流（家长路径）**

```
浏览器 → web:80 (Nginx)
           ├─ /*        → 静态 SPA
           └─ /api/*    → api:8000 (FastAPI + Agents)
                            └─ db:5432 (Postgres+pgvector)
                            └─ volume ./data uploads
```

7. **Checkpointer / 业务表**
   - 仍用同一 `DATABASE_URL`；容器首次启动走现有 `bootstrap_*` / checkpointer setup；不在 compose 里另起 migration 框架。

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| 百炼从海外 VPS 调用延迟/不稳定 | 文档注明需实测；密钥与 endpoint 可配；失败保持现有错误提示 |
| PDF 中文字体缺失 | 镜像加字体或文档说明限制 |
| 单机磁盘与备份 | volume 路径文档化；本期不做自动备份 |
| 多 worker 与会话 | 一期 api 单进程/单 worker 即可；已有 Postgres 会话权威存储 |

## Migration Plan

1. 新增文件不影响本地 `uvicorn` / `vite` 开发。
2. 首次上线：`cp .env.example` → 填密钥 → `docker compose up -d --build`。
3. 教材入库：`docker compose exec api python -m ingest ...`（或 `run`）。
4. 回滚：停 compose、保留 volume。

## Open Questions

无阻塞项。默认：**对外只暴露 web:80**；API 不映射到公网。TLS 由机房前的 Cloudflare 或主机 Caddy 处理（文档一句带过）。
