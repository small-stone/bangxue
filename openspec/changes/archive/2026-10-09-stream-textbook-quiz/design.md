# Design

## Context

见 `proposal.md` — Why。现状：`POST /api/quizzes` 同步调用 `run_textbook_quiz` → `_bailian_generator` 的 `model.invoke`，前端 `Config.tsx` 假文案轮播。对话路径已有 SSE/打字机；教材路径没有。部署上 `docker-compose-deploy` 已要求长请求超时，但教材 SSE 需显式纳入 nginx `proxy_read_timeout`。

## Goals / Non-Goals

**Goals:**

- 家长 UI 出题主路径走 SSE，有真实进度反馈。
- 后端流式调用百炼（`stream=True` / LangChain `.stream`/`.astream`），边收边尝试解析完整 `questions` 数组项并推送。
- 完成时仍落库 `save_quiz`，结果页/PDF 契约不变。

**Non-Goals:**

- 不改对话 harness 协议；不换模型；不做 WebSocket；不把题量改成任意值。

## Decisions

1. **端点形态**  
   - 新增 `POST /api/quizzes/stream`（body 与现 `QuizRequest` 相同），响应 `text/event-stream`。  
   - 保留 `POST /api/quizzes`：内部调用同一生成核心后一次性返回（便于调试/兼容），家长前端改打 stream。  
   - 备选：把原 POST 改成仅 SSE——破坏性更大，不采用。

2. **SSE 事件**（JSON `data:`）  
   - `status`：`{ "phase": "load_units"|"generating"|"validating"|"saving", "message": "...", "done"?: number, "total"?: number }`  
   - `question`：`{ "index": n, "question": { ... } }`（可选；解析到完整题且校验通过时发）  
   - `done`：`{ "id", "title", "questions": [...] }`  
   - `error`：`{ "detail": "...", "status_code"?: number }`  
   - 事件名用 `event:` 字段或统一包在 `{ "type": "..." }`；实现任选一种并在前后端对齐。

3. **生成策略（优先可落地）**  
   - **主方案**：对百炼 `stream` 累积 token，用增量 JSON 解析（或在流结束后 parse；流中定期发 `status`）。若增量解析成本高，第一期可：**流式收 token + 心跳/进度 status，结束后一次校验再 `done`**，同时把「假文案」换成服务端 `status.message`。  
   - **增强（同 change 若工期允许）**：按小批量（如每次 5 题）循环生成并 `question` 推送，降低单次失败重试成本。  
   - 仍禁止工具循环；`MAX_GENERATE_ATTEMPTS` 保留但每次重试前发 `status`。

4. **前端**  
   - `fetch` + `ReadableStream` 读 SSE（比 `EventSource` 更易 POST + JSON body）。  
   - loading 区绑定最新 `status.message` / `done/total`；`done` 后 `saveQuiz` 并 `navigate`。  
   - 中止：组件卸载时 `AbortController.abort()`。

5. **代理超时**  
   - `apps/web` nginx：`location /api/` 设 `proxy_read_timeout` / `proxy_send_timeout` ≥ 180s（或与现对话配置取更大者）。

## Risks / Trade-offs

- [增量 JSON 解析脆弱] → 第一期允许「只流式 status + 结束一次 parse」；单题事件作增强。  
- [重试仍慢] → status 标明「正在重试」；后续可分批。  
- [东京→百炼延迟不消失] → 流式改善体感，不承诺墙钟时间数量级下降。

## Migration Plan

- 先上 API stream + nginx 超时，再切 Config。  
- 回滚：Config 改回同步 POST，保留 stream 端点无害。

## Open Questions

- （无）第一期以 status 流式 + 结束交付完整卷为必达；单题增量为同 change 内尽力项，tasks 中分开勾选。
