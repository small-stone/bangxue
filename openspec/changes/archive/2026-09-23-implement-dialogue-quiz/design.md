# Design

## Context

方式 A 已有 `POST /api/quizzes` + 结果页/PDF；方式 B 首页入口仍关闭，`agents/chat.build_agent()` 返回 `None`。需求与 `openspec/config.yaml` 已约定：方式 A = LangGraph 固定图，方式 B = DeepAgents；Jev 做封闭流程判断。在途变更 `wire-agent-harness` / `add-jev-decisions` 有部分重合规划，本设计以「可演示的对话出题切片」为准，并吸收其中方式 B 相关结论。

## Goals / Non-Goals

**Goals:**

- 家长可走通：首页 → 对话 →（追问）→ 出题 → 确认 → 共用 Result/PDF。
- 明确技术选型：方式 B = DeepAgents；Jev = 出题前 completeness 门闩。
- Checkpointer 绑定 `thread_id`；业务侧保存已确认练习与来源标记。

**Non-Goals:**

- 不做对话绑定教材 RAG、不做判分 Vision/Jev、不改方式 A 图。
- 不引入独立 Agent 服务或任务队列。
- 不在本期实现完整 HITL interrupt 改题循环的全部边角（「再出几道」可作为确认前的继续对话，确认后改题可二期）。

## Decisions

### 1. 方式 B 用 DeepAgents，不用手写 LangGraph 对话图

```
家长消息
  → FastAPI /api/chat/...
  → DeepAgents (create_deep_agent)  in-process
       ├─（门闩）Jev: 信息是否足够？
       │     否 → 追问文本（工具不必出题）
       │     是 → 出题工具 → 百炼 qwen3.7-plus → 题目 JSON
       └─ 流式/增量回复给前端
  → 家长确认
  → save_quiz（source=chat）→ 现有 Result / PDF
```

| 选项 | 结论 |
|------|------|
| 手写 LangGraph `StateGraph` 多节点对话 | 拒绝作为方式 B 主实现。开放对话与追问更适合 harness；固定图留给方式 A。 |
| LangChain `create_agent` | 拒绝作为方式 B 主实现。需求要的是 DeepAgents 层；`create_agent` 无 DeepAgents 默认中间件与子代理模型。 |
| **DeepAgents `create_deep_agent`** | **采用**。工具最少化：出题工具（+ 可选读取会话约束）；**禁止** `LocalShellBackend` / 宿主机 `execute`。 |

方式 A 仍按固定图一次结构化出题；两套并存是有意的学习与产品分层，不是重复造两套完整产品。

### 2. Jev 加在哪里

**加在「调用出题工具之前」**，作为方式 B 的流程判断，而不是：

- 不加在 Vision 识图里（那是判分变更）；
- 不加在 PDF 渲染后；
- 不替代家长确认。

实现形态（择一，优先 A）：

- **A（推荐）**：FastAPI 或 harness 包装层在每轮「准备出题」时先调 `agents/shared` 的 Jev 客户端；不足则只返回追问，不调用出题工具。
- **B**：把「completeness」做成 harness 必须先走的工具，模型不可跳过——需用中间件/策略保证，复杂度更高。

低置信度或 Jev 失败 → 追问或明确错误，不静默出题。

方式 A「题是否在教材范围内」与判分 Jev **不在本期实现**（仍见 `add-jev-decisions`）。

### 3. API 与流式

- `POST /api/chat/sessions` → 创建会话，返回 `thread_id`。
- `POST /api/chat/sessions/{thread_id}/messages` → 家长消息；响应用 **SSE**（或分块）推送助手增量与可选「出题中」事件；结束时带结构化状态（`clarifying` | `draft_ready` | `error`）。
- `POST /api/chat/sessions/{thread_id}/confirm` → 将草稿写入 `save_quiz`，返回 quiz `id`，前端跳转 Result。

长耗时：网关/uvicorn 超时保持宽松；出题阶段必须有进度事件，避免手机端假死。

### 4. Checkpointer / thread_id / 业务存储

```
Checkpointer（Postgres）
  - thread_id → 对话消息、harness 中间态、未确认草稿

业务 / quiz_store（可先沿用进程内字典，与现网方式 A 一致）
  - 确认后的 quiz_id、title、questions
  - meta.source = "chat"
  - meta.summary = 对话主题摘要
  - 可选 grade/subject 约束

禁止：生产用 MemorySaver 冒充持久化。
开发：Postgres checkpointer（与现有 bangxue-pg 一致）；无 Postgres 时启动应失败或明确降级策略写在实现注释/配置，不得默默 Memory。
```

HITL：本期「确认」用显式 `confirm` API，不必上 LangGraph `interrupt`；若后续要图内中断，再挂同一 `thread_id`。

### 5. 模型与密钥

- 出题/对话：`bailian_api_key` + `QUIZ_MODEL`（默认 `qwen3.7-plus`）+ 可选 `BAILIAN_BASE_URL`
- Jev：`TYPESAFE_API_KEY`（或官方文档等价名），仅环境变量
- 不把密钥写入仓库；缺密钥时接口 4xx/5xx 带中文说明

### 6. 前端

- `Home`：对话卡片可导航到 `/chat`（或 `/chat/:threadId`）。
- 新页：消息列表 + 输入框；`draft_ready` 时展示题目预览与「确认出题」。
- 确认后 `navigate` 到现有 Result，带 `quiz_id`。
- 视觉跟随现有 ink-amber / 移动 Web，不新开桌面布局。

### 7. 与在途变更

- 若先 apply `wire-agent-harness`：复用百炼模型工厂与 chat `build_agent` 骨架，本变更补 HTTP、UI、Jev 门闩、确认链路。
- 若未 apply：本变更在 `agents/shared` 补模型工厂，并实现受限 `create_deep_agent`。
- `add-jev-decisions` 的判分 / 方式 A 范围判断仍独立；共享同一 Jev 客户端模块以免分叉。

## Risks / Trade-offs

- **DeepAgents 默认带宿主机工具** → 启动验收工具列表；发现 `execute` 则剥离，不合并。
- **Jev 对中文教学习题意图不稳** → 低置信度一律追问；可用少量样例标定阈值。
- **双通道（A 固定图 / B harness）维护成本** → 出题工具内部尽量复用同一 JSON 生成与校验逻辑。
- **无 interrupt 的确认** → 实现简单，但「确认前改题」靠继续发消息；可接受为一期。

## Migration Plan

- 无历史对话数据。部署后需 Postgres 可写 checkpointer 表/ schema（按 LangGraph 文档初始化）。
- 回滚：关闭 `/chat` 路由与首页入口，不影响方式 A。

## Open Questions

- Jev 具体 SDK 问题 schema 以接入时 TypeSafe 文档为准（不改变「足够 / 不足 + 缺什么」 closure）。
- 确认阈值与「缺什么」枚举在有样例对话后再微调。
