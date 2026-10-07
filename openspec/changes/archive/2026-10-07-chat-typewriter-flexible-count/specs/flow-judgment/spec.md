# Spec Delta

## Purpose

方式 B 流程判断中的题量规则与追问文案，对齐 1–100 任意题量。

## MODIFIED Requirements

### Requirement: Chat intake completeness
方式 B 在调用生成式模型起草题目之前，MUST 调用 Jev（或当前等价封闭判断），根据当前对话判断出题所需信息是否足够（至少包含可执行的科目或知识点，以及 1–100 范围内的题量或等价范围意图）。信息不足时，系统 MUST 向家长追问，且 MUST NOT 直接生成练习题。题量大于 100 时 MUST 视为不足或非法，MUST NOT 按足够处理。

#### Scenario: Missing count or topic
- **WHEN** 家长只说「出点数学题」一类缺少题量或具体知识点的话
- **THEN** 判断为不足，对话继续追问，不进入题目列表

#### Scenario: Enough information to draft
- **WHEN** 判断科目或知识点、以及 1–100 内的题量等已足够
- **THEN** 系统才进入出题，题目正文仍由生成式大模型撰写

#### Scenario: Count exceeds one hundred
- **WHEN** 家长要求超过 100 道题
- **THEN** 判断不通过出题门闩，向家长说明上限，不生成草稿
