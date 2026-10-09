# Spec Delta

## MODIFIED Requirements

### Requirement: Long-running api routes survive proxy timeouts

对话 SSE、**教材出题 SSE**、出题与判分等长请求 MUST 在反向代理上配置足够的读/发送超时，MUST NOT 因默认短超时在正常出题窗口内被代理切断（建议级数值见设计文档，规格要求「可完成一次常规出题/对话回合而不被代理默认超时打断」）。

#### Scenario: Chat SSE is not cut by default short proxy timeout

- **WHEN** 家长在对话出题中发送一条需模型处理的消息（常规耗时）
- **THEN** 在代理与 API 均健康时，流式或最终响应可完成，而不是因代理默认数十秒超时中断

#### Scenario: Textbook quiz SSE is not cut by default short proxy timeout

- **WHEN** 家长发起一次常规题量的教材流式出题
- **THEN** 在代理与 API 均健康时，进度与完成/错误事件可送达，而不是因代理默认数十秒超时中断
