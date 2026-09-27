# Spec Delta

## MODIFIED Requirements

### Requirement: Chat intake completeness
方式 B 在调用生成式模型起草题目之前，MUST 调用 Jev，根据当前对话判断出题所需信息是否足够。足够条件 MUST 至少包含：可检索的科目（以及年级或等价学段约束）、可检索的知识点或主题，以及题量或等价范围意图。信息不足时，系统 MUST 向家长追问，且 MUST NOT 直接生成练习题列表，也 MUST NOT 跳过检索直接编题。

#### Scenario: Missing count or topic
- **WHEN** 家长只说「出点数学题」一类缺少题量或具体知识点的话
- **THEN** Jev 判断为不足，对话继续追问，不进入题目列表

#### Scenario: Missing grade for retrieval scope
- **WHEN** 家长只给科目与题量但未说明年级（且会话中无可用默认年级）
- **THEN** Jev 判断为不足或系统追问年级，不进入检索与出题

#### Scenario: Enough information to draft
- **WHEN** Jev 判断科目、年级（或等价约束）、知识点与题量等已足够
- **THEN** 系统才进入检索与出题，题目正文仍由生成式大模型撰写
