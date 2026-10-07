# Proposal

## Why

仓库一期约定 Docker Compose（Nginx 静态前端 + FastAPI 内嵌 Agent + Postgres/pgvector），但尚未提供可构建的 Dockerfile / compose，无法在海外小 VPS 上一键拉起演示环境。需要补齐最小可部署镜像与编排，降低上线成本，且不引入大陆机房或独立 Agent 服务。

## What Changes

- 增加 **API Dockerfile**（`apps/api` 上下文）：安装 Python 依赖与 PDF/插图所需系统库，以 uvicorn 运行 FastAPI（Agent 仍进程内）。
- 增加 **Web Dockerfile**（`apps/web` 上下文）：多阶段构建 Vite 静态资源，由 Nginx 提供，并将 `/api` 反代到 API 服务（与现有相对路径 `/api/...` 一致）。
- 增加仓库根 **docker-compose.yml**（及示例 env）：`web` + `api` + `db`（带 pgvector 的 Postgres）；持久化卷用于数据库与答卷本地上传目录。
- 补充简短部署文档（README 或 `deploy/` 说明）：构建、环境变量、健康检查、海外单机假设。
- **Non-goals**：不部署独立 Agent 服务；不上 K8s / Fly 专用配置；不做对象存储（S3/R2）切换；不配大陆备案域名；不做 CI 自动发布；不引入 JWT 生产加固；不把教材入库做成 compose 常驻服务（仍可手工 `docker compose run`）。

## Capabilities

### New Capabilities

- `docker-compose-deploy`: 用 Docker Compose 在单机上构建并运行家长端 Web、API（含 Agent）与 Postgres(+pgvector)。

### Modified Capabilities

- `repo-layout`: 明确允许（并期望）仓库根存在面向 `apps/web` / `apps/api` 的 Dockerfile 与 compose，且 MUST NOT 增加独立 Agent 镜像/服务。

## Impact

- **前端**：生产构建仍为静态资源；同源 `/api` 由 Nginx 反代，开发代理不变。
- **FastAPI / Agent**：容器内运行；SSE/出题/判分长超时需在 Nginx 与 uvicorn 配置中保留足够超时；Agent 不单独镜像。
- **数据与存储**：Postgres 容器 + volume；答卷仍本地目录挂载；`DATABASE_URL` / `bailian_api_key` 等经 env 注入。
- **长任务**：对话 SSE 与判分可能超过默认代理超时；compose/Nginx MUST 为 `/api` 配置足够长的读超时（设计中给出建议值）。
