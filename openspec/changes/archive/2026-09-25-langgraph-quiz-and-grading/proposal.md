# Proposal

## Why

架构约定方式 A 为 LangGraph 固定 StateGraph、判分应落在 `agents/shared` 可编排子图，但现状是：教材出题仍是普通函数直调百炼（`build_graph()` 返回 `None`），判分为同步函数流水线。家长路径已打通，现在需要把「出题 + 判分」真正接到进程内 LangGraph，便于后续 HITL、节点级重试与 Jev 接入，并与方式 B（已用 DeepAgents/Checkpointer）对齐运行时模型。

## What Changes

- **方式 A（教材出题）**：实现可编译的 LangGraph StateGraph；`POST /api/quizzes` 经 `ainvoke`/`invoke` 跑图；节点覆盖取课文上下文 → 结构化出题（复用现有百炼出题逻辑）；`build_graph()` 不再返回 `None`
- **判分**：将现有 `grade_questions` 升为 shared 判分 StateGraph（节点：解析题目/答卷 → Vision 或演示回退 → 组装 draft）；`POST /api/grading/attempts` 改为跑该图
- FastAPI 仍进程内调用，不拆独立 Agent 服务；家长可见的题目 JSON、判分结果字段与确认落库 API **保持兼容**
- 吸收并落实 `wire-agent-harness` 中「方式 A 固定图」意图；判分侧补齐此前刻意推迟的图编排
- **Non-goals**：不把方式 B 改写成另一张固定 StateGraph（保持 DeepAgents）；本期不做家长确认的 graph interrupt/`resume`（确认仍走现有 REST）；不接 Jev 节点；不上 LangGraph Platform；不改前端路由与 mockup；不做独立 worker 队列；不引入 MemorySaver 作为生产默认

## Capabilities

### New Capabilities

- `langgraph-runtime`: 方式 A 出题与共用判分必须以进程内 LangGraph StateGraph 执行；约定图边界、调用方式与 Checkpointer 使用条件

### Modified Capabilities

- （无）`primary-math-quiz` / `chat-generation` / `bailian-models` 的家长可观察需求不变；本变更改运行时路径。`photo-grading` 尚未归档进 main specs，行为契约仍以已实现 API 为准，本期不另开 delta 改对外字段

## Impact

- **前端**：无强制变更（响应形状保持）；可选后续再接图事件流式进度
- **FastAPI**：出题与判分路由改为调用 graph；超时策略不变（出题/判分仍为同步长请求，判分约 60s）
- **Agent A**：`agents/textbook` 提供真实 `build_graph` + 薄封装 `generate_questions`
- **Agent B**：不改 harness 结构
- **Shared**：新增判分图；复用 `bailian` 工厂与现有 `grading`/`generate` 逻辑作节点实现
- **Checkpointer / 数据**：一期出题与判分图为无 interrupt 的一次调用，可不挂 Checkpointer；若节点需跨请求恢复，MUST 用现有 Postgres Checkpointer，禁止 MemorySaver 作为默认。成绩落库仍用现有 `score_store`
- **与在途变更**：与未归档的 `photo-grade-scores`、`wire-agent-harness` 相关；实现时以当前代码为准，避免重复造第二套判分入口
