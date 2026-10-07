# agent-session-persistence Specification

## Purpose

对话会话与练习卷权威状态落在 PostgreSQL，跨 API 进程与重启可恢复；Supervisor 与对话 harness 的 checkpoint 命名空间隔离，避免同 thread 状态串台。

## Requirements

### Requirement: Chat session state is authoritative in PostgreSQL

家长对话出题的会话权威状态（至少包含 `thread_id`、消息列表、当前题目草稿、摘要、会话 meta）MUST 持久化到 PostgreSQL（共用 `DATABASE_URL`）。进程内字典 MAY 作短缓存，但 MUST NOT 作为唯一权威源。API 进程重启后，对仍存在于库中的 `thread_id`，系统 MUST 能继续对话与确认出题。无可用数据库时，创建或更新会话 MUST fail-closed（返回明确错误，MUST NOT 假装成功写入）。

#### Scenario: Session survives API restart

- **WHEN** 家长已创建对话会话并完成至少一轮出题草稿，随后 API 进程重启
- **THEN** 使用同一 `thread_id` 继续发送消息或确认出题时，系统能恢复草稿与历史，且不因「会话不存在」而失败（库中仍有该会话时）

#### Scenario: Missing database refuses session write

- **WHEN** 进程无法连接或未配置可用的 PostgreSQL
- **THEN** 创建或更新对话会话失败并返回明确错误，且不把会话仅写入进程内存冒充成功

### Requirement: Quiz papers are authoritative in PostgreSQL within TTL

确认前暂存与确认后的练习卷（至少含 `id`、题目列表、`include_answers`、来源 meta）MUST 持久化到 PostgreSQL。进程内字典 MAY 作短缓存，但 MUST NOT 作为唯一权威源。在约定 TTL 内，任意 API worker 用同一 quiz `id` MUST 能读取该卷（如下载 PDF、再判分）。TTL 到期后读取 MAY 返回不存在。无可用数据库时，保存练习卷 MUST fail-closed。

#### Scenario: Quiz readable after restart within TTL

- **WHEN** 家长确认生成练习卷得到 `id`，随后 API 进程重启，且仍在 TTL 内
- **THEN** 用该 `id` 下载 PDF 或进入判分时仍能读到同一题目集合

#### Scenario: Missing database refuses quiz save

- **WHEN** 进程无法连接或未配置可用的 PostgreSQL
- **THEN** 保存练习卷失败并返回明确错误，且不把试卷仅写入进程内存冒充成功

### Requirement: Supervisor and chat harness use distinct checkpoint namespaces

同一 `thread_id` 上，Supervisor 编排图与对话 DeepAgents harness MUST 使用不同的 checkpoint 命名空间。系统 MUST NOT 让二者共用空字符串或同一命名空间作为 checkpoint 键的一部分，以免状态互相覆盖或误读。

#### Scenario: Shared thread id does not collide checkpoints

- **WHEN** 同一 `thread_id` 先后经过 Supervisor 路由与对话 harness 草稿
- **THEN** 各自 checkpoint 互不覆盖；后续恢复时不会把对方状态当成自己的状态
