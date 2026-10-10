# Tasks

## 1. Shared wiring

- [x] 1.1 在 `apps/api/requirements.txt` 增加兼容的 `langfuse`（及所需 langchain 集成包若有）；`pip install` / 镜像构建可解析。验证：干净环境安装无冲突报错
- [x] 1.2 新增 `agents/shared` 观测模块：读 `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` / 可选 `LANGFUSE_HOST`；齐全则返回可用 CallbackHandler（或等价），否则 `None`；上报异常不抛到调用方。验证：单测覆盖「双密钥齐全 / 缺一 / 全缺」
- [x] 1.3 改 `build_chat_model`（或统一出口）在 handler 存在时挂上默认 callbacks，并支持 metadata/tags 注入点。验证：假 handler 在一次 `invoke`/`stream` 后被调用

## 2. Call-site coverage

- [x] 2.1 确认教材出题 stream/sync、Supervisor 路由、对话 harness 经 `build_chat_model` 的调用自动带上观测；必要时传 `thread_id` / path 标签。验证：本地或 mock 下三条路径各触发一次可识别标签
- [x] 2.2 （可选）为判分 `vision_grade` 的 OpenAI 直调补显式 span；做不到则在代码注释标明本期仅 ChatOpenAI 路径保证。验证：注释或 span 二选一存在且教材/对话路径仍绿

## 3. Config and docs

- [x] 3.1 更新 `.env.example` 与 `deploy/README.md`（或 `apps/api/README.md`）列出 Langfuse 可选变量与 fail-open 说明；Compose 服务列表仍无强制 langfuse。验证：文档与 example 可对照，无真实密钥
- [x] 3.2 回归：未配置 Langfuse 时教材 SSE / 同步出题 / 对话 SSE 单测或手测仍通过；配置错误的 bailian 仍 fail-closed。验证：相关 pytest 通过

## 4. Smoke（有真实密钥时）

- [x] 4.1 在已配置 Langfuse 的环境跑一轮教材出题与一轮对话草稿，于 Langfuse UI 确认出现对应 trace。验证：截图或记录 trace id；无密钥则跳过并在 PR/说明中标注
  - 本环境无 Langfuse 密钥，已按任务说明跳过；部署后在 `.env` 填入密钥并重建 api 后于 UI 抽查即可
