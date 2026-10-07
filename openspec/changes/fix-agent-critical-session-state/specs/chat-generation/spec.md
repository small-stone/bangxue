# Spec Delta

## ADDED Requirements

### Requirement: Chat session and confirmed quiz depend on durable store

对话出题路径中，会话与确认后的练习卷生命周期 MUST 依赖 PostgreSQL 权威存储（见 `agent-session-persistence`）。系统 MUST NOT 将「仅进程内存」作为生产路径上的权威会话或权威试卷存储。家长侧 API 契约（`thread_id`、确认后的 quiz `id`、SSE/JSON 形态）MUST 保持兼容，除非因 fail-closed 返回明确错误。

#### Scenario: Confirm uses durable quiz id

- **WHEN** 家长在对话中确认当前草稿生成练习卷
- **THEN** 返回的 quiz `id` 可在任意健康 API worker 上、在 TTL 内用于下载与判分，且不依赖创建该卷的那个进程是否仍存活

#### Scenario: Continue chat uses durable session

- **WHEN** 家长对已有 `thread_id` 发送下一条消息
- **THEN** 系统从权威存储恢复该会话后再处理，而不是仅依赖创建会话时的进程内存
