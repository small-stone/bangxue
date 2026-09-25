# Design

## Context

参见 `proposal.md`。现状：`agents/textbook/build_graph()` 返回 `None`，`generate_questions` 直调百炼；判分为 `agents/shared/grading.grade_questions` 同步函数，由 `grading_routes` 调用。方式 B 已用 DeepAgents + Postgres Checkpointer。`wire-agent-harness` 曾规划方式 A 固定图但未完全落地；`photo-grade-scores` 已实现判分 API/UI，尚未归档进 main specs。

## Goals / Non-Goals

**Goals:**

- 教材出题、答卷判分均以可测试的 StateGraph 为唯一执行入口（薄封装可保留函数名）
- 对外 HTTP 契约与前端路径尽量不变
- 为后续 Jev / 确认 interrupt 预留节点位，但不在本期实现

**Non-Goals:**

- 重写方式 B 为固定 StateGraph
- 家长确认改成 graph interrupt
- LangGraph Platform、独立 Agent 服务、MemorySaver 默认、Jev 节点

## Decisions

### 1. 两张图，不合成一张端到端巨图

```
[教材出题图]  load_units_text → generate_json_questions → (end)
[判分图]      resolve_questions → grade_vision_or_demo → build_draft → (end)
```

- **选择**：出题与判分生命周期不同（出题在 PDF 前；判分在拍照后），合成一张图会强迫虚假的 `thread_id` 串联与状态膨胀。
- **替代**：端到端「出题→PDF→判分」一张图 → 与现有 REST 切片冲突，HITL 过重。
- **方式 B**：继续 DeepAgents，不在本期改。

### 2. 节点实现复用现有纯函数

- **选择**：图节点调用现有 `load_unit_text` / 百炼出题、`vision_grade` / `demo_grade`；`generate_questions` 与 `grade_questions` 变为 `graph.invoke(...)` 的门面，避免双路径。
- **替代**：在节点内重写 LLM 调用 → 易分叉行为。

### 3. FastAPI 调用方式

- 出题：`POST /api/quizzes` → `textbook_graph.invoke(state)`（或 `ainvoke`）
- 判分：`POST /api/grading/attempts` 存盘后 → `grading_graph.invoke(state)` → `create_attempt`
- 确认成绩：仍 `POST .../confirm`，**不**进图（避免本期改前端与 thread 协议）

### 4. Checkpointer

- 本期两图无 interrupt → **不挂** Checkpointer（与早期 wire-agent-harness「无 HITL 不挂 checkpoint」一致）
- 共用 `get_checkpointer()` 仅留给方式 B 与未来 resume；文档写明若加确认 interrupt 必须 Postgres

### 5. 状态形状（示意）

教材：
`{ meta, units, source_text, count, difficulty, include_answers, questions, error }`

判分：
`{ quiz_id, questions, image_paths, items, correct, total, demo, error }`

错误用节点写入 `error` 并由门面转成现有 `TextbookError` / HTTPException，保持家长文案。

## Risks / Trade-offs

- **[Risk] 双路径**（图与旧函数并存）→ Mitigation：门面强制走图；删除或降级直调
- **[Risk] 与未归档 photo-grade-scores / wire-agent-harness 文档漂移** → Mitigation：实现以当前 `apps/api` 代码为准；归档时对齐
- **[Trade-off] 确认不进 interrupt** → 短期兼容 UI；后续要 resume 时再加节点与 `thread_id`
- **[Trade-off] 同步长请求** → 保持现有超时；流式进度可作为后续增强，不阻塞本期

## Migration Plan

- 先落地教材图并保证 `POST /api/quizzes` 回归；再切判分路由到判分图
- 回滚：门面改回直调函数即可；无 DB 迁移
- 不改 `scores.json` schema

## Open Questions

- 无（确认 interrupt、方式 B 是否改固定图均明确排除）。
