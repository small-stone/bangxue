# Design

## Context

- 对话 harness（`agents/chat/harness.py`）把 `messages` / `draft` / `summary` / `meta` 放在进程内 `_SESSIONS`；`session_exists` 在内存未命中时只探测 checkpointer 是否有空 checkpoint，重启后草稿丢失且多 worker 互不可见。
- 练习卷（`app/quiz_store.py`）用进程内 `_QUIZZES`；确认后的 PDF/判分依赖创建该卷的进程。
- Supervisor（`agents/supervisor/graph.py`）与 harness 共用 Postgres checkpointer 与同一 `thread_id`；harness 显式使用 `checkpoint_ns=""`，Supervisor `invoke` 未设 `checkpoint_ns`（亦为空），存在串台风险。
- 主规格 `agent-runtime` 仍含「Chat entry stays closed」，与已开放的对话入口冲突。
- 成绩库（`app/score_store.py`）已建立「`DATABASE_URL` + `ensure_schema` + fail-closed」模式，可复用。

## Goals / Non-Goals

**Goals**

- 会话与练习卷权威状态落 PostgreSQL，多 worker / 重启可恢复。
- Supervisor 与 chat harness 使用不同 `checkpoint_ns`。
- 修正 `agent-runtime` 与对话开放现状一致。
- 保持现有 HTTP/SSE 契约（`thread_id`、quiz `id`）。

**Non-Goals**

- JWT、限流、判分 demo 默认关闭、教材 handoff 题量策略、对象存储、Jev 全量。
- 把 LangGraph checkpoint 本身迁出 Postgres（已有，仅隔离 ns）。
- 长期归档历史会话 UI；本期只需权威读写与合理 TTL。

## Decisions

1. **两张业务表，复用成绩库连接模式**
   - `chat_sessions(thread_id PK, messages jsonb, draft jsonb, summary text, meta jsonb, updated_at, created_at)`
   - `quiz_papers(id PK, payload jsonb, include_answers boolean, meta jsonb, created_at, expires_at)`
   - 连接 / 错误类型对齐 `score_store`（可抽小模块 `app/db.py` 共享 `database_url`/`connect`，非必须；优先少动）。
   - 启动时与成绩一并 `ensure_schema`（API lifespan）。

2. **Harness API 形状不变，换权威源**
   - `create_session`：写库 + 可选写内存缓存；仍 seed checkpointer（`checkpoint_ns=chat-agent`）。
   - `get_session` / `session_exists`：先缓存，未命中读库；库无则 404；读库后回填缓存。
   - 每次消息/草稿更新后 `UPSERT` 写库（同步、与当前请求同线程即可）。
   - 测试可注入 store 或使用 InMemory 替身；现有 supervisor 测试改为 seed 持久化接口而非直接捅 `_SESSIONS`。

3. **`quiz_store` 改为 Postgres 权威**
   - `save_quiz` / `get_quiz` 读写 `quiz_papers`；内存仅缓存。
   - **TTL 默认 7 天**（`expires_at`）；过期 `get_quiz` 返回 `None`。可用环境变量覆盖（如 `QUIZ_PAPER_TTL_DAYS`），记入 README。
   - 教材直出题与对话确认共用同一 store。

4. **Checkpoint 命名空间**
   - Supervisor：`checkpoint_ns="supervisor"`（在 `run_supervisor` / `invoke` config 中显式设置）。
   - Chat harness：`checkpoint_ns="chat-agent"`（替换当前 `""`）。
   - 不迁移旧空 ns 数据（开发期可接受；文档说明旧 thread 需新建会话）。

5. **规格修正**
   - Delta 删除 `agent-runtime`「Chat entry stays closed」，新增「Chat entry is available in-process」；实现侧若仍有「未开放」文案则去掉（若前端已无则仅规格同步）。

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| 每次 turn 写库增加延迟 | 单行 UPSERT；payload 通常不大；可后续异步 |
| TTL 内卷仍占库空间 | 7 天默认；可选后台清理任务本期不做，读时过滤过期即可 |
| 旧空 ns checkpoint 失效 | 文档说明；用户新建会话 |
| 测试依赖真实 PG | 单测用 Memory/假 store；集成测依赖已有 DATABASE_URL |

## Migration Plan

1. 部署前确保 `DATABASE_URL` 可用（与成绩相同）。
2. 首次启动 `CREATE TABLE IF NOT EXISTS`。
3. 无数据迁移：内存态不导入。
4. 回滚：代码回退即可；表可保留。

## Open Questions

无阻塞实现的开放问题。默认：quiz TTL = 7 天；不共享抽 `db.py` 除非重复代码明显。
