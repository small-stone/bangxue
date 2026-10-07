# Spec Delta

## REMOVED Requirements

### Requirement: Chat entry stays closed

**Reason**: 产品已开放对话出题入口（见 `chat-generation` / `request-supervisor`）；本条与现状冲突，继续保留会造成规格与实现双标准。

**Migration**: 删除「对话入口关闭」要求；对话可用性以 `chat-generation` 与 `request-supervisor` 为准。本规格仅保留教材固定图出题与「harness 不得操作宿主机」。

#### Scenario: Choosing chat does not generate a paper

- **WHEN** 家长在首页点击对话出题
- **THEN** （已废止）不再要求留在首页并提示未开放

## ADDED Requirements

### Requirement: Chat entry is available in-process

家长 MAY 通过首页「对话出题」进入对话流程。进入后系统 MUST 可创建会话并调用进程内对话 harness（经 Supervisor 编排），MUST NOT 再以「入口未开放」拦截该入口。对话 harness 仍 MUST 遵守本规格中「不得操作宿主机」的要求。

#### Scenario: Choosing chat opens chat flow

- **WHEN** 家长在首页点击对话出题
- **THEN** 进入对话出题流程并可创建会话，而不是被提示对话出题尚未开放
