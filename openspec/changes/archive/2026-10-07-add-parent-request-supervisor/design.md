# Design

## Context

见 `proposal.md` 的 Why。现状：对话路径在 `agents/chat/harness.py` 的 `handle_parent_message` 内线性执行完整性判断 → 混合检索 → DeepAgents `draft_quiz`；教材路径由 UI 驱动 `POST /api/quizzes` → `run_textbook_quiz`。二者已在进程内，缺显式编排节点。首页双入口与 `chat-generation`「入口可用」以产品现状为准（`agent-runtime` 中「入口关闭」为历史冲突项，本期不回退对话入口）。

## Goals / Non-Goals

**Goals:**

- 对话请求先经封闭路由再执行子路径。
- 复用现有教材图与对话 harness，不复制出题栈。
- 会话状态继续落在 Postgres Checkpointer + 现有 session 字典。

**Non-Goals:**

- 改造首页为单一输入框；判分 / 上传进 Supervisor；独立 Supervisor 服务；内存 Checkpointer。

## Decisions

### 1. Supervisor = LangGraph 固定编排图（非自由规划聊天群）

```
家长消息 (chat thread_id)
        │
        ▼
   [route] ── clarify ──► 返回追问文案
        │
        ├─ chat_draft ──► 现有检索 + DeepAgents / 等价草稿逻辑
        │
        └─ textbook_quiz ──► 解析单元元数据 → run_textbook_quiz（或包装工具）
                │
                ▼
        ChatTurnResult（clarifying | draft_ready | error）
```

- **为何**：路由集合封闭、可测；符合「方式 A 少自主规划」的整体取向。
- **备选**：纯 DeepAgents Supervisor 自由选工具——否决为本期默认（难约束、易碰宿主机工具）；可作二期增强。
- **备选**：仅 if/else 无图——可作过渡，但缺少后续挂 HITL / 日志节点的落点；本期仍落成可 compile 的图。

### 2. 挂载点：对话 API，不改 `POST /api/quizzes`

- `handle_parent_message`（或薄封装）改为 `supervisor.invoke(...)`。
- 按教材 UI 继续直连方式 A，满足「双入口仍可用」。
- **为何**：最小破坏；家长在对话里说「按某单元出」时才交叉调用教材图。

### 3. 路由信号

一期优先级：

1. 结构化路由调用（百炼 `qwen3.7-plus` + JSON：`route` + 可选 `units` / `grade` / `count`），`enable_thinking=false`。
2. 若 `add-jev-decisions` 已提供封闭判断客户端，可将「是否足够 / 是否教材单元意图」委托 Jev；**不**阻塞本 change——无 Jev 时用 LLM JSON 或规则回退，失败则 `clarify`，不得静默出题。

### 4. 状态存放

| 存储 | 用途 |
|------|------|
| Postgres Checkpointer | Supervisor / chat agent 的 `thread_id` 消息与中断恢复 |
| `_SESSIONS`（现有） | draft 题目、summary、meta（确认后写 quiz store） |
| `textbook_chunks` | 只读；教材路径出题前校验单元存在 |

禁止为本编排引入内存-only Checkpointer。

### 5. 流式与超时

- 保持现有 chat SSE：长计算阶段可发进度，token 打字机在有文案后开始。
- 教材子调用为同步 `invoke`，超时与 `POST /api/quizzes` 同类；失败映射为可展示中文错误，不编造题目。

## Risks / Trade-offs

- [路由误判把对话意图送进教材路径] → 单元不存在则回退 clarify；不编造块。
- [与 add-jev-decisions 并行] → 预留 Jev 适配点，默认 LLM JSON。
- [出题变慢] → 前端等待态 / SSE；不做队列。
- [agent-runtime「对话关闭」与现状冲突] → 本期遵循 `chat-generation` 入口可用，不在本 change 回退。

## Migration Plan

- 部署后对话请求走 Supervisor；无数据迁移。
- 回滚：`handle_parent_message` 恢复直连旧线性逻辑。

## Open Questions

- 教材式对话出题的 `source` 元数据最终标 `chat` 还是 `textbook`：规格允许实现二选一，建议默认 `chat` + meta 记 `via=textbook_quiz`，避免成绩页来源混乱。
