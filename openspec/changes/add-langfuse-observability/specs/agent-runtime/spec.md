# Spec Delta

## ADDED Requirements

### Requirement: Optional observability must not widen agent host powers
可选 LLM 观测（Langfuse）MUST 仅作为进程内旁路上报。系统 MUST NOT 因接入观测而向对话 harness、Supervisor 或教材出题图授予宿主机 shell、任意写仓库文件、或独立 Agent HTTP 服务。缺 `bailian_api_key` 时出题/对话仍 MUST fail-closed（配置错误、无编造题目），与是否配置 Langfuse 无关。

#### Scenario: Tracing enabled still forbids host shell
- **WHEN** 已配置 Langfuse，API 处理一条对话出题消息
- **THEN** 调用期间仍无宿主机命令执行与任意写仓库文件；观测上报不改变该约束

#### Scenario: Missing Bailian key still fails without inventing questions
- **WHEN** 未配置 `bailian_api_key`（无论是否配置 Langfuse），家长请求出题
- **THEN** 接口返回配置错误（或流式错误事件），响应中没有题目
