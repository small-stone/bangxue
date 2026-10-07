# Proposal

## Why

代码审查将 agent 链路标为「严重」的四项会直接导致上线不可用或规格失真：对话草稿只在进程内存、多 worker 会话错乱、Supervisor 与 DeepAgent 共用 checkpoint 键、以及 `agent-runtime` 仍要求「对话入口关闭」与产品现状冲突。本期一次性修掉这四项。

## What Changes

- **对话会话持久化**：`messages` / `draft` / `summary` / `meta` 写入 PostgreSQL；`session_exists` / `get_session` 以库为准，不再依赖进程内 `_SESSIONS` 作为权威源（可保留短缓存，但重启后 MUST 能从库恢复）。
- **练习卷短期持久化**：确认前/确认后的 quiz（至少含 `id`、题目、`include_answers`、meta）写入 PostgreSQL，替换进程内 `_QUIZZES` 权威存储，使多实例与重启后仍可下载 PDF、再判分（在合理 TTL 内）。
- **Checkpoint 命名空间隔离**：Supervisor 与 DeepAgents harness 使用同一 `thread_id` 时 MUST 使用不同 `checkpoint_ns`（如 `supervisor` / `chat-agent`），避免状态串台。
- **修正 `agent-runtime`**：删除或改写「Chat entry stays closed」，与 `chat-generation`「对话入口可用」对齐；保留「教材固定图出题」与「harness 不得操作宿主机」。
- **Non-goals**：JWT/限流（属高优先级另案）、判分 demo 开关默认、教材 handoff 题量四档策略、Jev 全量接入、对象存储。

## Capabilities

### New Capabilities

- `agent-session-persistence`: 对话会话与练习卷权威状态落在 PostgreSQL，跨进程/重启可恢复；Checkpointer 命名空间隔离。

### Modified Capabilities

- `chat-generation`: 对话会话与确认后的 quiz 生命周期依赖持久化存储，不再允许「仅内存」作为权威路径。
- `request-supervisor`: 编排图与对话 harness 的 checkpoint 命名空间 MUST 隔离。
- `agent-runtime`: 移除「对话入口关闭」；明确对话可用且 harness 仍进程内、无宿主机能力。

## Impact

- **前端**：契约尽量不变（仍用 `thread_id` / quiz `id`）；重启后旧会话应仍可用（若库中有记录）。
- **FastAPI / Agent**：`agents/chat/harness.py`、`app/quiz_store.py`、`agents/supervisor/graph.py`、可选新建 `agents/shared/session_store.py`；启动时 ensure schema。
- **数据与存储**：新表（如 `chat_sessions`、`quiz_papers`）共用 `DATABASE_URL`；无库时对话写/读与 quiz 读 MUST fail-closed（与成绩库策略一致）。
- **长任务**：不改变 SSE 策略；仅保证状态在库中可恢复。
