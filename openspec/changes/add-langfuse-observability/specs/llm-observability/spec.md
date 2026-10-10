# Spec Delta

## Purpose

为进程内百炼 / Agent 调用提供可选的 LLM 可观测性：配置观测密钥时产生可查询的调用链路，未配置时不影响家长出题、对话与判分。

## ADDED Requirements

### Requirement: Observability is optional and fail-open
系统 MAY 将 LLM 与 Agent 编排调用上报到已配置的 Langfuse 项目。当公钥与密钥均未配置时，系统 MUST 正常完成出题、对话与判分，MUST NOT 因缺少观测配置而失败或编造题目。观测上报失败时，系统 MUST 继续服务家长请求，MUST NOT 向家长暴露内部观测错误作为出题失败原因。

#### Scenario: Missing Langfuse keys does not block quiz
- **WHEN** 进程未配置 Langfuse 公钥/密钥，且已配置 `bailian_api_key`，家长对已入库单元请求出题
- **THEN** 出题仍可成功返回（或按既有百炼错误失败），响应中不出现「未配置观测」类错误

#### Scenario: Observability backend outage does not invent quiz failure
- **WHEN** 已配置 Langfuse 但上报短暂失败，且百炼出题本身成功
- **THEN** 家长仍收到成功练习结果，观测失败仅留在服务端日志侧

### Requirement: Configured observability records generation traces
当 Langfuse 公钥与密钥已配置时，系统 MUST 为教材出题（含流式通道）与对话出题相关的百炼聊天调用产生可在 Langfuse 中查询的 trace（至少含模型调用起止与错误状态）。同一家长会话或练习相关调用 SHOULD 带上可关联的会话标识（如 `thread_id` 或练习元数据），便于排查。

#### Scenario: Textbook quiz appears in Langfuse after success
- **WHEN** 已配置 Langfuse，家长完成一次教材出题且模型调用成功
- **THEN** Langfuse 项目中出现对应 trace，且能识别为教材出题路径

#### Scenario: Chat draft path is traced when configured
- **WHEN** 已配置 Langfuse，家长在对话出题中触发一次需调用百炼的草稿生成且调用完成
- **THEN** Langfuse 项目中出现对应该次调用的 trace

### Requirement: Observability credentials stay out of git
仓库示例环境文件 MAY 列出 Langfuse 相关变量名与 Host 占位，但 MUST NOT 提交真实公钥或密钥。生产密钥 MUST 仅通过运行环境注入。

#### Scenario: Example env lists names without secrets
- **WHEN** 查看仓库中的 `.env.example`
- **THEN** 能看到 Langfuse 相关变量名（及可选 Host），且不包含可用的真实密钥值
