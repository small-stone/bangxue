# Design

## Context

见 `proposal.md` 的 Why。现状：`agents/textbook/generate.py` 的 `_bailian_generator` 用 OpenAI SDK 调百炼兼容接口；`build_graph()` 与 `agents/chat.build_agent()` 都返回 `None`。课文在进模型前已由 `load_unit_text` 按单元名从 `textbook_chunks` 取出。`POST /api/quizzes` 同步调用 `generate_questions`。

## Goals / Non-Goals

**Goals:**

- 方式 A 的出题调用收进一张没有工具循环的固定图。
- 方式 A 与方式 B 共用百炼对话模型工厂。
- 方式 B 有一个可在进程内调用的 DeepAgents harness，且没有宿主机执行能力。

**Non-Goals:**

- 不在本期做检索节点、HITL、流式、对话 HTTP 或 Checkpointer。这些留到真正要中断恢复时再做。

## Decisions

### 方式 A 不用 `create_agent`

`create_agent` 实现的是「模型 → 工具 → 再问模型」循环。当前出题的输入已经是课文文本，输出必须是固定题量的 JSON。改成工具循环会让题量和时延不稳定，也和需求里「方式 A 步骤固定、少依赖模型自主规划」相反。

方式 A 用 LangGraph `StateGraph`：一个 `generate` 节点，`START → generate → END`。节点内用共用模型做一次 JSON 输出（沿用现在的 `response_format=json_object`，并关闭百炼思考，避免思考过程进 `content`）。`generate_questions` 改为 `invoke` 这张图，校验题量和题干的逻辑留在图外。`compile()` 不传 checkpointer。

备选：继续直接用 OpenAI SDK。能出题，但方式 A 仍然没有图，后续 HITL 节点没有落点。不选。

### 方式 B 用 DeepAgents harness，且默认后端不是宿主机

三层关系：LangGraph 是运行时，`create_agent` 是轻量 harness，`create_deep_agent` 是带默认中间件的 harness。需求里的方式 B 用最后这一层。

`build_agent()` 调用 `create_deep_agent`：模型来自共用工厂；工具只有一个「按已给课文参数起草题目」，内部复用 `generate_questions`；不传入 `LocalShellBackend` 或任何带 `execute` 的宿主机后端。默认的进程内状态后端可以保留。实现后必须检查工具列表里没有宿主机执行工具；若当前版本的默认栈带了该工具，用中间件替换掉它。不为此改回裸的 OpenAI 调用。

对话页和 `POST /api/quizzes` 都不调用 `build_agent()`。验证方式是进程内直接 `invoke` 一条消息。

### 共用模型工厂

放在 `agents/shared`。读取已有环境变量，不新增密钥名，不把密钥写入仓库：

- `bailian_api_key`
- `QUIZ_MODEL`（默认 `qwen3.7-plus`）
- `BAILIAN_BASE_URL`（默认百炼 OpenAI 兼容地址）

用 LangChain 的 OpenAI 兼容聊天模型构造，关闭思考。向量模型 `qwen3.7-text-embedding` 仍只给入库用，不进这张对话模型。

### 状态各存什么

```
POST /api/quizzes
  load_unit_text（按单元名读 textbook_chunks）
       │
       ▼
  方式 A 图：generate 节点 ──一次──► 百炼 qwen3.7-plus
       │
       ▼
  现有进程内 quiz id 字典 + PDF 路由

方式 B harness（本期无 HTTP）
  create_deep_agent ──工具──► 同上出题函数
  无 Checkpointer，无 thread_id
```

- Checkpointer：本期不创建、不写入。没有 interrupt，就没有 `thread_id`。禁止用内存 Checkpointer 占位。
- 业务侧：现有 quiz id 字典只保存已生成的卷，重启即失效。它不是 Checkpointer。
- `textbook_chunks`：只读课文，不改向量列。

出题仍是一次同步 HTTP，不改成 SSE。超时沿用现有长请求。

## Risks / Trade-offs

- [DeepAgents 默认栈随版本带上宿主机执行] → 用工具列表验收；有 `execute` 就替换中间件，不合并。
- [图多一次封装，出题变慢或 JSON 更不稳] → 节点内仍是一次补全，校验失败仍返回 502，不自动重试成多轮。
- [百炼思考内容混进 JSON] → 继续关闭思考，只解析正式内容。
- [REQUIREMENTS 仍写 OpenAI / Claude，实现已是百炼] → 本变更不改 REQUIREMENTS。模型名以 `bailian-models` 规格和 `.env` 为准。

## Migration Plan

安装 LangChain、LangGraph、DeepAgents 后重启 API 进程。没有数据迁移。回滚时让 `generate_questions` 重新直接调用百炼补全，并让 `build_agent()` 回到返回空。

## Open Questions

无。对话页何时接上 harness、以及那时的 Postgres Checkpointer，属于后续变更。
