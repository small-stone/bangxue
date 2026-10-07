# Proposal

## Why

首页虽有「按教材 / 对话」双入口，对话侧家长一句话请求目前仍在 `handle_parent_message` 里线性串起 Jev、检索与 DeepAgents，缺少显式的**路由 / 编排层**。要扩展多智能体（教材固定图、对话 harness、后续判分）而不复制两套栈，需要在家长请求进入后先由 Supervisor 决定走哪条能力。

## What Changes

- 在 FastAPI 进程内新增 **Supervisor（编排图）**：家长自然语言请求先经路由，再进入追问、对话出题或教材出题子路径之一。
- **保留首页双入口**：按教材出题仍走现有选题 UI → `POST /api/quizzes`；本期 Supervisor 挂在**对话出题**请求路径上（`/api/chat/...`），不把双入口改成单一输入框。
- Supervisor 可调用现有方式 A 出题能力（进程内 `run_textbook_quiz` / 等价工具）与方式 B 草稿能力，**不**新建独立 Agent HTTP 服务。
- 会话仍用现有 `thread_id` + Postgres Checkpointer；长请求保持现有 SSE / 同步超时约定，不做任务队列。
- **Non-goals**：统一首页为单一「智能入口」、判分 / 拍照路由进 Supervisor、拆微服务、用内存 Checkpointer、替换方式 A 的同步出题 API。

## Capabilities

### New Capabilities

- `request-supervisor`: 家长对话请求进入后的路由与编排——决定追问、对话出题或教材式出题，并在进程内调用对应 Agent。

### Modified Capabilities

- `chat-generation`: 对话消息处理 MUST 经 Supervisor 编排后再追问或出草稿；家长可观察的状态（追问 / 草稿确认）保持兼容。

## Impact

- **前端**：对话页契约基本不变（SSE / 确认 / 结果）；可不改 UI，或仅展示「正在理解意图」类进度文案。
- **FastAPI**：`agents/chat` 入口改为调用 Supervisor；可选 `agents/shared` 或 `agents/supervisor` 新模块；不新增独立端口。
- **Agent**：方式 A / B 图与 harness 仍为被调用方；Supervisor 为上层编排图。
- **数据与存储**：复用 chat `thread_id` 与 Postgres Checkpointer；不新增业务表（除非实现需要记录 route 决策日志，可选）。
- **长任务**：出题仍可能较慢；继续对话 SSE / 等待态；超时沿用现有约定。
