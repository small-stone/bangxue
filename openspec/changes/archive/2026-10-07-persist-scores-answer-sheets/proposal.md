# Proposal

## Why

成绩 attempt 与答卷照片目前落在 `apps/api/data/scores.json` 与本地 `uploads/`，进程换机或重启多副本时会丢数据，也无法与 Postgres Checkpointer / 教材库同一套运维。上线前必须把确认成绩与答卷引用持久化到数据库。

## What Changes

- 将判分 attempt（含逐题结果、确认态、家长邮箱、出题元数据）写入 **PostgreSQL**，替代 JSON 文件读写。
- 答卷照片：**二进制仍存对象/本地磁盘**；库中 MUST 保存可追溯的路径或对象键，并与 attempt 关联；确认后成绩查询 MUST 能指向这些答卷引用。
- 保持现有 HTTP 契约（`/api/grading/attempts`、confirm、`/api/scores`、`/api/wrong-questions`）对外行为不变；前端演示夹具逻辑不变。
- 启动时 ensure schema（与 `textbook_chunks` 同类）；可选一次性从 `scores.json` 导入已有数据（失败不阻断服务）。
- **Non-goals**：JWT/SMTP 鉴权升级、S3 生产切换（本期可继续本地盘，仅把路径写入库）、错题组卷、把照片二进制塞进 Postgres BYTEA。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `score-records`: 已确认成绩 MUST 持久化在 PostgreSQL；按家长邮箱查询 MUST 来自数据库而非本地 JSON。
- `photo-grading`: 上传答卷后 MUST 持久化答卷引用与 attempt；确认后写入成绩库；未确认 attempt 亦须可从库按 id 读取（进程重启后仍可确认）。

## Impact

- **FastAPI**：重写/替换 `app/score_store.py`（或新增 Postgres 实现并切换）；`grading_routes` 调用面尽量不变；依赖已有 `DATABASE_URL`。
- **前端**：原则上无改；演示态仍走 `demoShowcase`。
- **Agent**：判分图不变；只改落库层。
- **数据与存储**：新表（如 `grade_attempts` + items JSONB 或子表 + `photo_refs`）；答卷文件仍在 `data/uploads`（或后续 S3 key）。
- **运维**：无 `DATABASE_URL` 时 API 相关写成绩路径 MUST 失败明确，禁止静默回退 JSON（避免双存储漂移）。
