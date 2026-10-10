# Proposal

## Why

一期 Agent 出题（教材 SSE、对话 harness、Supervisor 路由、判分视觉）已在 FastAPI 进程内跑通，但调用百炼时**没有统一 LLM 可观测性**：延迟、失败、token、prompt/输出链路只能靠容器日志拼。调试东京 VPS → 百炼慢请求、重试与路由分支时成本高。需要以 **可选接入 Langfuse** 补齐 trace，且缺配置时不得影响家长路径。

## What Changes

- 新增进程内 Langfuse 集成（SDK / LangChain Callback）：在已配置密钥时自动上报 LLM / Agent 调用。
- 覆盖主路径：教材出题（含 stream 累积）、对话 harness、Supervisor 路由；判分视觉调用尽量纳入同一会话或同标签。
- `.env.example` / 部署文档补充 `LANGFUSE_*`（公钥、密钥、可选 Host）；**不**把密钥写入仓库。
- 未配置 Langfuse 时行为与现网一致（fail-open：不出错、不上报）。
- **非目标**：Compose 内自建 Langfuse 服务；改家长 UI；改出题语义 / 白名单 / SSE 协议；独立 Agent 服务；全量 embedding ingest 强制上屏（MAY 后续）；把课文全文以外的家长 PII 额外外发策略产品化。

## Capabilities

### New Capabilities

- `llm-observability`: 规定进程内 LLM/Agent 调用的可选观测（Langfuse）：配置存在时 MUST 产生可查询 trace；缺失时 MUST NOT 阻断出题/对话/判分。

### Modified Capabilities

- `agent-runtime`: 明确观测为可选旁路，MUST NOT 改变「进程内、不得操作宿主机、缺 bailian 密钥仍 fail-closed」等既有边界。
- `docker-compose-deploy`: 文档/示例环境变量列出 Langfuse 可选项；一期 MUST NOT 强制新增 Langfuse compose service。

## Impact

- **FastAPI / Agent（共用）**：`agents/shared` 增加观测初始化与 callback 注入；教材 / 对话 / Supervisor（及尽量判分）调用链挂上 handler。
- **前端**：无家长可见变更。
- **数据**：业务 Postgres 不变；trace 落在 Langfuse（云或自建 Host）。
- **部署**：仅环境变量；流式出题长请求不因上报阻塞响应（异步/后台 flush，失败吞掉并打日志）。
- **密钥**：`LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` / 可选 `LANGFUSE_HOST`；与 `bailian_api_key` 独立。
