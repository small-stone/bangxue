# Design

## Context

现状：`app/score_store.py` 用文件锁读写 `data/scores.json`，答卷写入 `data/uploads/`，仅存相对路径字符串。教材侧已用 `DATABASE_URL` + `psycopg`（`ingest/store.py`）。方式 B Checkpointer 亦依赖同一 Postgres。动机见 proposal.md。

本期不改鉴权（仍 `X-Parent-Email`），不引入 SQLAlchemy 亦可——与 ingest 一致用 psycopg 即可。

## Goals / Non-Goals

**Goals:**

- attempt 全生命周期（创建未确认 → 确认 → 列表/错题聚合）权威在 Postgres。
- 答卷文件仍落盘（或日后 S3）；库存 `photo_paths text[]`（或等价 JSON）。
- API 形状与前端契约不变；无 `DATABASE_URL` 时写/读真实成绩 fail closed。

**Non-Goals:**

- JWT、SMTP、S3 SDK
- 照片 BYTEA
- 强制迁移历史 JSON（可选脚本，失败不阻塞）
- 游客演示夹具入库

## Decisions

### 1. 表结构（单表 + JSONB items）

```
grade_attempts (
  id text PRIMARY KEY,
  email text NULL,              -- set on confirm
  confirmed boolean NOT NULL DEFAULT false,
  demo boolean NOT NULL DEFAULT false,
  quiz_id text NULL,
  source text,
  subject text,
  title text,
  correct int NOT NULL,
  total int NOT NULL,
  items jsonb NOT NULL DEFAULT '[]',
  photo_paths text[] NOT NULL DEFAULT '{}',
  created_at timestamptz NOT NULL,
  confirmed_at timestamptz NULL
)
CREATE INDEX grade_attempts_email_confirmed_idx
  ON grade_attempts (email, confirmed, confirmed_at DESC);
```

- **备选**：`grade_items` 子表 → 查询更规范但改动大；一期 JSONB 足够（与现 JSON 同形）。
- **理由**：与现 `create_attempt` 字段一一对应，迁移成本低。

### 2. 存储实现替换

- 保留 `score_store` 公共函数签名（`create_attempt` / `get_attempt` / `confirm_attempt` / `list_*` / `save_upload`）。
- 内部改为 psycopg；`save_upload` 仍写本地盘，返回 `uploads/...`，写入 `photo_paths`。
- `ensure_schema()` 在 FastAPI startup 调用（已有 `ensure_data_dirs` 处扩展）。

### 3. Fail closed

- 无 `DATABASE_URL`：成绩相关 API 返回 503/明确错误；**不**回退 JSON。
- 开发文档标明必须起 Postgres（可与教材/Checkpointer 共用）。

### 4. 可选 JSON 导入

- 启动或一次性 CLI：若 `scores.json` 存在则 upsert 入表；冲突以 id 为准跳过或覆盖（实现时选 skip）。不作为验收硬条件。

```
Upload photos → save_upload (disk)
            → create_attempt (Postgres, confirmed=false, photo_paths)
Confirm      → UPDATE email/confirmed/confirmed_at
List scores  → SELECT WHERE email AND confirmed
Wrong book   → 同上 + 展开 items 中 correct=false
```

Checkpointer / textbook_chunks 表不动；业务成绩与 Agent 状态分离。

## Risks / Trade-offs

- [双写窗口] 切换期若有人仍写 JSON → 单一实现后消除；导入只读一次。
- [邮箱头可伪造] 已知一期限制；JWT 另 change，本设计不假装已解决。
- [本地盘与多实例] 多副本需共享卷或后续 S3；本期单机假设与现状一致，库只存路径。

## Migration Plan

1. 部署带新 schema 的 API，配置 `DATABASE_URL`。
2. （可选）导入旧 `scores.json`。
3. 验证 confirm → list → wrong-book。
4. 回滚：保留旧 JSON 代码分支成本高；宜用 DB 备份回滚表，或短暂 dual-read（不推荐默认实现）。
