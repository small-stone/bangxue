# flow-judgment Specification

## Purpose

在出题流程中用 TypeSafe Jev 做封闭判断。本期覆盖方式 B：对话信息是否已足够生成题目；不覆盖方式 A 范围校验与答卷判分。

## Requirements

### Requirement: Chat intake completeness
方式 B 在调用生成式模型起草题目之前，MUST 调用 Jev（或当前等价封闭判断），根据当前对话判断出题所需信息是否足够（至少包含可执行的科目或知识点，以及 1–100 范围内的题量或等价范围意图）。足够条件亦 MUST 覆盖可检索的年级或等价学段约束（若会话中无可用默认）。信息不足时，系统 MUST 向家长追问，且 MUST NOT 直接生成练习题，也 MUST NOT 跳过检索直接编题。题量大于 100 时 MUST 视为不足或非法，MUST NOT 按足够处理。

#### Scenario: Missing count or topic
- **WHEN** 家长只说「出点数学题」一类缺少题量或具体知识点的话
- **THEN** 判断为不足，对话继续追问，不进入题目列表

#### Scenario: Missing grade for retrieval scope
- **WHEN** 家长只给科目与题量但未说明年级（且会话中无可用默认年级）
- **THEN** Jev 判断为不足或系统追问年级，不进入检索与出题

#### Scenario: Enough information to draft
- **WHEN** 判断科目或知识点、年级（或等价约束）、以及 1–100 内的题量等已足够
- **THEN** 系统才进入检索与出题，题目正文仍由生成式大模型撰写

#### Scenario: Count exceeds one hundred
- **WHEN** 家长要求超过 100 道题
- **THEN** 判断不通过出题门闩，向家长说明上限，不生成草稿

### Requirement: Jev does not author questions
流程判断 MUST NOT 由 Jev 输出题目正文、解析或 PDF。Jev 只返回预定义的判断结果与置信度。

#### Scenario: Generation remains with the chat agent
- **WHEN** 流程判断结果为可以出题
- **THEN** 题目由方式 B 的 DeepAgents 调用百炼生成式模型产出

### Requirement: Low confidence stays conservative
当 Jev 置信度低于约定阈值，或 Jev 调用失败时，方式 B MUST 采取更保守分支：继续追问或提示暂时无法自动判断，MUST NOT 在不确定时静默出题。

#### Scenario: Jev unavailable
- **WHEN** 未配置 Jev 密钥或 Jev 接口失败
- **THEN** 系统明确提示错误或改为追问，不假装已判定足够并生成题目

### Requirement: Parent confirmation is not skipped
Jev 的判断 MUST NOT 替代家长对题目列表的确认。低置信度只影响追问或提示，不自动定稿练习。

#### Scenario: Draft still needs confirm
- **WHEN** Jev 判定信息足够且已生成题目列表
- **THEN** 仍须家长确认后才进入共用结果与 PDF
