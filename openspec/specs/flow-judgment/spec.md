# flow-judgment Specification

## Purpose

在出题流程中判断「信息是否足够进入检索与出题」。由对话路径的 request Supervisor 做封闭路由（`clarify` / `chat_draft` / `textbook_quiz`），不引入独立判断服务。

## Requirements

### Requirement: Chat intake completeness
方式 B 在调用生成式模型起草题目之前，MUST 经 Supervisor 路由判断出题所需信息是否足够（至少包含可执行的科目或知识点，以及 1–100 范围内的题量或等价范围意图）。足够条件亦 MUST 覆盖可检索的年级或等价学段约束（若会话中无可用默认）。信息不足时，系统 MUST 路由为追问，且 MUST NOT 直接生成练习题，也 MUST NOT 跳过检索直接编题。题量大于 100 时 MUST 视为不足或非法，MUST NOT 按足够处理。

#### Scenario: Missing count or topic
- **WHEN** 家长只说「出点数学题」一类缺少题量或具体知识点的话
- **THEN** 路由为追问，对话继续，不进入题目列表

#### Scenario: Missing grade for retrieval scope
- **WHEN** 家长只给科目与题量但未说明年级（且会话中无可用默认年级）
- **THEN** 系统追问年级，不进入检索与出题

#### Scenario: Enough information to draft
- **WHEN** Supervisor 判定科目或知识点、年级（或等价约束）、以及 1–100 内的题量等已足够并路由为出题草稿
- **THEN** 系统才进入检索与出题，题目正文仍由生成式大模型撰写

#### Scenario: Count exceeds one hundred
- **WHEN** 家长要求超过 100 道题
- **THEN** 判断不通过出题门闩，向家长说明上限，不生成草稿

### Requirement: Routing does not author questions
流程判断 / 路由层 MUST NOT 输出题目正文、解析或 PDF。路由只返回封闭集合中的路径与结构化字段（如追问文案、年级、题量）。

#### Scenario: Generation remains with the chat agent
- **WHEN** 流程判断结果为可以出题
- **THEN** 题目由方式 B 的 DeepAgents 或教材图调用百炼生成式模型产出

### Requirement: Uncertain routing stays conservative
当路由模型失败、结果不可解析或置信不足时，方式 B MUST 采取更保守分支：继续追问或提示暂时无法自动判断，MUST NOT 在不确定时静默出题。

#### Scenario: Router unavailable
- **WHEN** 路由调用失败或返回非法结果
- **THEN** 系统明确提示错误或改为追问，不假装已判定足够并生成题目

### Requirement: Parent confirmation is not skipped
流程判断 MUST NOT 替代家长对题目列表的确认。路由只影响追问或出题草稿，不自动定稿练习。

#### Scenario: Draft still needs confirm
- **WHEN** 信息足够且已生成题目列表
- **THEN** 仍须家长确认后才进入共用结果与 PDF
