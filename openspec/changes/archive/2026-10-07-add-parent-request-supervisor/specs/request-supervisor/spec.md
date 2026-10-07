# Spec Delta

## Purpose

在家长对话请求进入后提供显式路由与编排：先决定追问、对话出题或教材式出题，再在 API 进程内调用对应能力，避免各入口复制完整栈。

## ADDED Requirements

### Requirement: Parent chat requests are routed before drafting
家长在对话出题中发送的每条出题相关消息，系统 MUST 先经 Supervisor 路由，再进入追问或出题草稿。路由结果 MUST 属于封闭集合（至少：`clarify`、`chat_draft`、`textbook_quiz`）。系统 MUST NOT 在未路由的情况下直接假定唯一路径并静默出题。

#### Scenario: Incomplete request is clarified
- **WHEN** 家长消息缺少出题所需信息（如题量或知识点）
- **THEN** 路由为追问，助手返回澄清文案，且不出现完整题目草稿列表

#### Scenario: Free-form intent uses chat drafting
- **WHEN** 家长意图足够且适合自然语言对话出题（非明确「按某已选单元教材卷」）
- **THEN** 系统进入对话出题草稿路径，并最终可得到可确认的题目列表

#### Scenario: Explicit textbook unit intent uses textbook generation
- **WHEN** 家长明确要求按已入库教材的某单元（或等价范围）出固定题量练习，且信息足够
- **THEN** 系统走教材式出题路径生成题目，而不是仅用无课文 grounding 的自由编题冒充教材卷

### Requirement: Supervisor stays in-process
Supervisor 与其调用的教材 / 对话能力 MUST 在 FastAPI 同进程内执行。系统 MUST NOT 为此部署独立 Supervisor 或 Agent HTTP 服务。Supervisor MUST NOT 获得宿主机 shell 或任意写仓库文件的能力。

#### Scenario: Routing does not spawn a separate agent service
- **WHEN** 家长发送一条对话出题消息触发编排
- **THEN** 处理发生在现有 API 进程内，家长无感知独立编排服务

### Requirement: Dual home entries remain available
本期 MUST 保留首页「按教材出题」与「对话出题」两个入口。按教材入口的选题 → 设置 → `POST /api/quizzes` 流程 MUST 仍可用，且 MUST NOT 被强制改为先经对话 Supervisor。

#### Scenario: Textbook button still opens textbook flow
- **WHEN** 家长在首页选择「按教材出题」并完成选题设置
- **THEN** 仍可按教材流程出题，无需先进入对话页
