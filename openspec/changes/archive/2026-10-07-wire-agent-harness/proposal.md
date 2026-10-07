# Proposal

## Why

一年级出题现在在 `_bailian_generator` 里用 OpenAI SDK 直接打一次百炼补全，既不是需求里的方式 A 固定图，也没有方式 B 的 harness。`create_agent` 是带工具循环的轻量 harness，不适合替换这一步：课文已由 Python 按单元取出，出题必须一次返回固定题量的 JSON，模型不该自己决定调用工具。Harness 应按需求放在方式 B。

## What Changes

- 方式 A 保持一次结构化出题，不改成 `create_agent` 的工具循环。`POST /api/quizzes` 改为在进程内跑一张 LangGraph 固定图，图里只有「用已取出的课文生成题目」这一个模型节点。模型仍是 `.env` 里的 `qwen3.7-plus`，密钥仍是 `bailian_api_key`。家长看到的题目 JSON、题量和缺密钥错误不变。
- 抽出共用的百炼对话模型工厂，方式 A 和方式 B 都用它，不再在出题函数里直接构造 OpenAI 客户端。
- 方式 B 在 `agents/chat` 用 DeepAgents 的 `create_deep_agent` 作为 harness，同一模型，只挂出题工具。Harness 不得获得宿主机 shell 或任意写文件能力。对话页仍显示尚未开放，本期不把 harness 接到家长入口。
- 本变更没有 HITL 中断，因此不为这两次调用挂 Checkpointer，也不使用内存 Checkpointer。

## Capabilities

### New Capabilities

- `agent-runtime`: 方式 A 用固定图做一次结构化出题；方式 B 的 DeepAgents harness 只在进程内可调用，且不能操作宿主机。

### Modified Capabilities

- （无）`bailian-models` 仍要求一年级出题使用 `qwen3.7-plus` 与 `bailian_api_key`，缺密钥时不编造题目。本变更只换调用路径，不改这些要求。

## Impact

- 前端：不改。对话卡片仍不可进入出题。
- FastAPI：`POST /api/quizzes` 仍是一次同步请求，不新增 SSE。超时沿用现有长请求约定。不新增对话 HTTP 接口，不单独部署 Agent。
- Agent A：`agents/textbook` 的 `build_graph()` 返回可运行的出题图，`generate_questions` 走这张图。
- Agent B：`agents/chat` 的 `build_agent()` 返回受限 harness。
- 共用：新增百炼对话模型工厂。依赖增加 LangChain、LangGraph、DeepAgents。
- 数据与存储：不改表，不改向量模型，不写 Checkpointer。

## Non-goals

- 不开放对话出题页面，不做多轮对话、HITL 确认、Postgres Checkpointer。
- 不把方式 A 改成自主规划的 `create_agent`。
- 不改登录、拍照判分、Jev、PDF 引擎、入库与 embedding。
- 不引入任务队列、独立 Agent 服务或内存 Checkpointer。
