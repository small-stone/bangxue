# Proposal

## Why

按教材出题目前是同步 `POST /api/quizzes`：前端转圈等到整卷 JSON 一次返回。东京 VPS 调国内百炼时，15～30 题常要数十秒甚至更久，家长只能干等，体感极慢。需要在总耗时未必大幅下降的前提下，用**流式进度与题目增量**缩短「无反馈等待」。

## What Changes

- 教材出题主路径改为 **SSE 流式**：推送阶段进度、已就绪的题目、最终 `quiz id` / 完成或错误事件。
- 出题设置页改吃流式接口：加载态展示真实进度；有题目时尽早展示或进入结果页前先累积；失败时仍有明确错误。
- 后端在进程内对百炼做 **token/增量流式生成**（或等价分批生成并逐题校验推送），不再仅「整包 invoke 结束后才响应」。
- 保留或薄封装原同步 `POST /api/quizzes`（内部可复用同一生成逻辑），避免 PDF/内部调用立刻全断；家长 UI 以流式为准。
- Nginx / compose 超时已按长请求要求核对，避免 SSE 被短超时切断。

## Capabilities

### New Capabilities

- （无）

### Modified Capabilities

- `primary-math-quiz`: 教材出题 API 增加流式契约（进度 / 题目 / 完成），题量与白名单行为不变。
- `textbook-quiz-ui`: 出题设置页的等待与结果进入改为消费 SSE，展示进度而非纯假文案轮播。
- `agent-runtime`: 「一次固定结构化生成」改为允许流式传输与增量校验，仍禁止工具循环与改写题量。
- `docker-compose-deploy`: 明确 web→api 对教材出题 SSE 的代理超时要求（与对话 SSE 同类）。

## Impact

- 前端：`Config.tsx`（及必要时 Result 入场）；`fetch` → `EventSource` 或 `fetch`+stream reader。
- FastAPI：`POST /api/quizzes` 旁路或改造为 stream 端点；`agents/textbook` 生成改为 `astream` / 分批。
- Agent A：仍在 API 进程内；Checkpointer 非必须（一次性出题）。
- 外部：百炼 chat completions stream；密钥仍 `bailian_api_key`。
- 非目标：对话出题打字机改造；换模型/换机房；题量上限变更；WebSocket。
- 超时：SSE 读超时需覆盖完整出题窗口（建议 ≥ 180s，与现有长请求部署要求对齐）。
