# Deploy (Docker Compose, single VPS)

海外小 VPS 一期拓扑：同机 **web**（Nginx 静态 + `/api` 反代）+ **api**（FastAPI，Agent 进程内）+ **db**（Postgres + pgvector）。**没有**独立 Agent 容器。

## 前置

- Docker Engine + Compose v2
- 复制环境变量：`cp .env.example .env`，填入 `bailian_api_key` 与数据库密码
- 域名可用 Cloudflare / Namecheap 的 `.com` 等；TLS 建议用 Cloudflare 代理或主机上的 Caddy 终止 HTTPS，再反代到本机 `WEB_PORT`（默认 8080）

## 启动

```bash
# 仓库根目录
docker compose up -d --build
```

- 家长端：`http://<host>:8080/`
- 健康检查（经 Nginx）：`http://<host>:8080/health` → `{"status":"ok"}`
- API 不对外映射端口，仅容器网络内由 web 访问

```bash
docker compose config --services   # 应为 db api web
docker compose ps
docker compose logs -f api
```

## 数据卷

| Volume | 用途 |
|--------|------|
| `pgdata` | PostgreSQL 数据（成绩、会话、练习卷、checkpointer、教材向量等） |
| `api_data` | 挂载为容器内 `/app/data`（答卷上传等） |

重启 compose **保留** volume 则库与上传不丢；`docker compose down -v` 会删卷。

## 教材入库（两种方式）

Docker 镜像**不含**本机 Postgres 里的教材与向量。`pgdata` 卷首次是空的，需要二选一：

1. **本机导出 → 服务器导入**（推荐：省 embedding 费用与时间）——见下一节  
2. **在服务器上重新 ingest**（要有 PDF + 能调通百炼 embedding）

### 在服务器上重新入库

```bash
docker compose exec api python -m ingest ingest-primary-math
# 或指定 PDF：
# docker compose exec api python -m ingest ingest --pdf /path/in/container/...
```

需先把 PDF 拷进 api 容器或挂载只读目录（按需改 compose）。

## 本机导出数据库 → 服务器导入

适用：本机已有 `textbook_chunks`（及可选的成绩/会话等），部署到 VPS 后不想重新算向量。

约定（与 `.env.example` / 本地开发一致）：

- 库名 / 用户 / 密码默认：`bangxue` / `bangxue` / `bangxue`
- 本机：`DATABASE_URL=postgresql://bangxue:bangxue@127.0.0.1:5432/bangxue`
- 服务器 compose：`db` 服务内同一套账号，API 用 `...@db:5432/bangxue`

**注意**

- 导出库与服务器使用的 **embedding 模型 / 向量维度必须一致**（改模型后需重入库，不能只迁旧表）。
- 自定义格式（`-Fc`）更稳妥，可带上 pgvector 列。
- 首次上线建议先起 `db`，导入后再起 `api` / `web`；或导入后 `docker compose restart api`。

### A. 本机导出

本机已安装 `pg_dump`（或用本机 Postgres 容器）：

```bash
# 在仓库外任意目录生成 dump 文件（勿提交到 git）
export PGPASSWORD=bangxue

# 方案 1：整库（含教材向量 + 成绩/会话/checkpointer 等，若已有）
pg_dump -h 127.0.0.1 -p 5432 -U bangxue -d bangxue \
  -Fc --no-owner --no-acl \
  -f bangxue.dump

# 方案 2：只迁教材向量表（体积更小；其他表由 API 启动时 bootstrap）
pg_dump -h 127.0.0.1 -p 5432 -U bangxue -d bangxue \
  -Fc --no-owner --no-acl \
  -t textbook_chunks \
  -f textbook_chunks.dump
```

若本机 Postgres 也在 Docker 里，可改为：

```bash
docker exec <本地 postgres 容器名> \
  pg_dump -U bangxue -d bangxue -Fc --no-owner --no-acl \
  > bangxue.dump
```

确认非空：

```bash
ls -lh bangxue.dump   # 或 textbook_chunks.dump
```

### B. 传到服务器

```bash
# 示例：scp（把 USER、HOST 换成你的 VPS）
scp bangxue.dump USER@HOST:~/bangxue.dump
# 或只传教材表
# scp textbook_chunks.dump USER@HOST:~/textbook_chunks.dump
```

### C. 服务器导入（compose 的 `db`）

在**仓库根目录**（有 `docker-compose.yml` 处）：

```bash
cp .env.example .env   # 若尚未配置；密码需与 dump 来源一致或导入后改应用侧 URL
docker compose up -d db
# 等 healthy
docker compose ps
```

确保扩展存在（pgvector 镜像一般已带；保险执行一次）：

```bash
docker compose exec db \
  psql -U bangxue -d bangxue -c 'CREATE EXTENSION IF NOT EXISTS vector;'
```

把 dump 拷进 `db` 容器并恢复：

```bash
# 整库
docker compose cp ~/bangxue.dump db:/tmp/bangxue.dump
docker compose exec db \
  pg_restore -U bangxue -d bangxue --no-owner --no-acl --clean --if-exists \
  /tmp/bangxue.dump

# 若只用教材表 dump：
# docker compose cp ~/textbook_chunks.dump db:/tmp/textbook_chunks.dump
# docker compose exec db \
#   pg_restore -U bangxue -d bangxue --no-owner --no-acl --clean --if-exists \
#   /tmp/textbook_chunks.dump
```

`--clean --if-exists` 会先删目标中的同名对象再导入；**空库或可覆盖的演示库**再用。生产已有数据时改为不加 `--clean`，或先备份服务器卷。

### D. 启动应用并抽查

```bash
docker compose up -d --build
curl -s http://127.0.0.1:8080/health

# 抽查教材块数量（应 > 0）
docker compose exec db \
  psql -U bangxue -d bangxue -c 'SELECT count(*) FROM textbook_chunks;'
```

浏览器走教材出题：选已入库的年级/册/单元，能列出单元并出题，即迁移成功。

### 常见问题

| 现象 | 处理 |
|------|------|
| `extension "vector" does not exist` | 先 `CREATE EXTENSION vector;` 再 `pg_restore` |
| `vector(N)` 维度不匹配 | 本机与服务器 `EMBEDDING_MODEL` / 维度不一致；需统一后重入库，不能混用旧向量 |
| `pg_restore: error: could not execute query` / 权限 | 加上 `--no-owner --no-acl`；用户用 compose 里的 `POSTGRES_USER` |
| 导入后 API 仍像空库 | 确认 `DATABASE_URL` 指向 compose 的 `db`，且连的是同一个库名；`restart api` |
| 只想更新教材、保留服务器成绩 | 用「只 dump `textbook_chunks`」；或在服务器对该表 `--clean` 后单独 restore |

## 注意

- **百炼从海外调用**：延迟与连通性需实测；密钥只放 `.env`，勿写入 Dockerfile。
- **长请求**：Nginx 对 `/api` 的 `proxy_read_timeout` 为 300s，覆盖常规对话 SSE / 出题。
- **本地开发**仍可用 `vite` + `uvicorn`，不必强制走 compose。
- **Langfuse（可选）**：在 `.env` 设置 `LANGFUSE_PUBLIC_KEY` + `LANGFUSE_SECRET_KEY` + `LANGFUSE_BASE_URL`（如 `https://jp.cloud.langfuse.com`）后，API 用 SDK v4 + LangChain `CallbackHandler` / `langfuse.openai` 上报教材出题、对话、Supervisor、判分视觉调用。未配置或上报失败时**不影响**家长路径（fail-open）。Compose **不**自带 Langfuse 服务。开启后，发给百炼的 prompt（含课文片段）会进入所配置的 Base URL，请自行评估隐私。

## 停止

```bash
docker compose down          # 保留 volume
docker compose down -v       # 连数据一起删（慎用）
```
