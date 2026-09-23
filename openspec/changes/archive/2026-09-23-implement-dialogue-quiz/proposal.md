# Proposal

## Why

首页「对话出题」仍提示尚未开放，`agents/chat` 只有占位，家长无法用自然语言多轮出题。方式 A 已能按单元出题，需要把方式 B 做成可演示的垂直切片：对话 → 追问/出题 → 确认 → 沿用现有练习卷与 PDF。

## What Changes

- **选型确认（写入本变更设计，不再悬空）**：
  - 方式 B 用 **DeepAgents**（`create_deep_agent`）做多轮对话 harness，不用裸 `StateGraph` 手写整张对话图，也不用 `create_agent` 替代 DeepAgents。
  - 方式 A 仍用 LangGraph 固定图（不在本期改；与已有 `wire-agent-harness` 规划一致）。
  - **Jev** 接在方式 B「是否已够信息可以出题」的流程判断上：不足则追问，足够才调用出题工具；Jev 不写题干、不看图、不替代家长确认。
- 开放首页「对话出题」入口，新增移动端对话页（多轮消息、追问、出题中进度）。
- FastAPI 增加对话会话接口（创建会话、发消息、确认题目）；Agent 在进程内 `ainvoke` / `astream`，不单独部署。
- 确认后的题目写入现有 quiz 存储，结果页与 PDF 下载与方式 A 共用。
- 一期对话 **不强制** 绑定教材 RAG；家长提到的年级/科目写入练习元数据作约束。缺 `bailian_api_key` 或 Jev 密钥时明确报错，不编造题目。

## Capabilities

### New Capabilities

- `chat-generation`: 方式 B 对话出题——多轮意图澄清、DeepAgents harness 出题、家长确认后进入共用结果/PDF。
- `flow-judgment`: 出题流程中的封闭判断；本期实现方式 B「信息是否足够」；方式 A 范围校验与判分 Jev 仍属其他变更，本变更不展开。

### Modified Capabilities

- （无）`primary-math-quiz` / `bailian-models` / `textbook-ingest` 的行为要求不变；出题模型仍为百炼 `qwen3.7-plus`。

## Impact

- **前端**：`Home` 可进入对话；新增对话页；确认后跳转现有 `Result`（或等价结果路由）。流式/长回复需进度或逐步展示。
- **FastAPI**：新增 `/api/chat/...`（名称以实现为准）；SSE 或分块流式用于助手回复与出题进度；超时沿用长请求约定。Agent 仍嵌在 FastAPI 进程内。
- **Agent B**：实现 `agents/chat.build_agent()`（DeepAgents）；共用百炼对话模型工厂（若 `wire-agent-harness` 已落地则复用，否则本变更补齐工厂与 chat harness）。
- **Jev**：`agents/shared` 客户端；方式 B 每轮出题前做 completeness 判断。密钥仅环境变量。
- **数据**：对话会话用 LangGraph Checkpointer 持久化（开发可用 Postgres checkpointer；**禁止**生产用纯内存）。业务侧练习记录标记来源为「对话」，并保存对话摘要。
- **依赖**：LangChain / LangGraph / DeepAgents；TypeSafe Jev API。
- **与在途变更关系**：吸收 `wire-agent-harness` 中「方式 B harness」与 `add-jev-decisions` 中「方式 B 信息足够」部分；方式 A 固定图、方式 A 范围 Jev、判分 Jev 仍留给对应变更。

## Non-goals

- 不做「对话 + 指定教材/单元」RAG（二期）。
- 不改方式 A 出题图、入库、embedding。
- 不做拍照判分、成绩表、登录。
- 不引入任务队列、独立 Agent 服务、Next.js。
- 不把 Jev 用于出题正文或 Vision 识图。
