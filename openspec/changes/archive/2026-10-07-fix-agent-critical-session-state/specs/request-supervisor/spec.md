# Spec Delta

## ADDED Requirements

### Requirement: Supervisor checkpoint namespace is isolated from chat harness

Supervisor 图在持久化或读取 checkpoint 时 MUST 使用显式、非空、且与对话 harness 不同的命名空间。即使与对话 harness 共用同一 `thread_id`，Supervisor MUST NOT 使用空命名空间与 harness 冲突。

#### Scenario: Routing checkpoint does not overwrite chat draft checkpoint

- **WHEN** 同一 `thread_id` 上 Supervisor 完成一次路由，随后对话 harness 写入草稿相关 checkpoint
- **THEN** 再次进入 Supervisor 时，其恢复到的状态仍是 Supervisor 自己的，而不是 harness 的草稿状态
