# Spec Delta

## ADDED Requirements

### Requirement: Textbook quiz generation streams over SSE
家长发起按教材出题时，系统 MUST 提供 SSE（`text/event-stream`）出题通道。流中 MUST 至少包含：阶段进度事件、最终成功事件（含练习 `id`、标题与完整题目列表）或错误事件。在生成过程中 MAY 推送已校验通过的单题事件。题量、白名单与「不得编造题目」约束 MUST 与同步出题一致。未配置 `bailian_api_key` 时 MUST 以错误事件（或等价失败）结束，MUST NOT 推送题目。

#### Scenario: Parent receives progress then a complete quiz
- **WHEN** 家长对已入库单元请求流式出题且模型成功返回合法题目
- **THEN** 客户端先收到至少一条进度类事件，最后收到含 `id` 与完整题目列表的完成事件，题量与请求一致

#### Scenario: Stream fails closed without inventing questions
- **WHEN** 未配置密钥或模型/校验最终失败
- **THEN** 流以错误事件结束，且全程未把编造题目当作成功完成

#### Scenario: Partial questions never exceed the requested count
- **WHEN** 流式过程中推送了单题事件
- **THEN** 累计题目数不超过请求题量，完成事件中的列表长度等于请求题量
