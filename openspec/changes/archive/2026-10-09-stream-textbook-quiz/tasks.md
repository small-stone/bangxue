# Tasks

## 1. Backend streaming core

- [x] 1.1 在 `agents/textbook` 抽出可复用的生成流程：加载课文 → 流式调用百炼 → 校验题目；对外提供异步生成器或回调产出 `status` /（可选）`question` / 最终 `questions`；用假 stream 生成器单测或脚本验证事件顺序
- [x] 1.2 新增 `POST /api/quizzes/stream`（`StreamingResponse` + SSE），事件含 status、done（含 save_quiz 后的 id/title/questions）、error；保留原 `POST /api/quizzes` 并改为复用同一核心；用 curl 或 httpx 验证一条成功流与缺密钥错误流
- [x] 1.3 将 `_bailian_generator` 改为走模型 stream（至少 token 流式累积后再 JSON parse，并周期性发 status）；确认 `enable_thinking: false` 仍生效

## 2. Proxy and frontend

- [x] 2.1 更新 web nginx `/api/` 的 `proxy_read_timeout` / `proxy_send_timeout`（≥180s）并在 compose 重建后用长等待请求确认不被 60s 切断
- [x] 2.2 改 `Config.tsx`：POST 消费 `/api/quizzes/stream`，展示服务端 status 文案与可选题数进度；done 后 saveQuiz 跳转；error/abort 结束 busy；本地手测一轮出题体感有进度更新

## 3. Hardening

- [x] 3.1 （尽力）在流式解析稳定时推送 `question` 单题事件；若解析不稳则文档/注释标明仅 status+done，并保证不降低完成路径可靠性
- [x] 3.2 回归：同步 `POST /api/quizzes`、PDF 下载、数学/语文/英语白名单出题仍可用；对话 SSE 未回归
