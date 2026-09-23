# Spec Delta

## Purpose

在两条出题路径上，用 Jev 做封闭流程判断：对话信息是否够生成题目，以及按教材生成的题目是否落在所选范围内。

## ADDED Requirements

### Requirement: Chat intake completeness
方式 B 在生成题目之前 MUST 调用 Jev，根据当前对话判断出题所需信息是否足够（至少包含可执行的科目或知识点、题量或范围意图）。信息不足时，系统 MUST 向家长追问，且 MUST NOT 直接生成练习题。

#### Scenario: Missing count or topic
- **WHEN** 家长只说「出点数学题」一类缺少题量或具体知识点的话
- **THEN** 对话继续追问所缺信息，不进入题目列表

#### Scenario: Enough information to draft
- **WHEN** Jev 判断科目或知识点、题量等已足够
- **THEN** 系统进入出题，题目正文仍由生成式大模型撰写

### Requirement: Textbook scope alignment
方式 A 在家长确认题目之前 MUST 调用 Jev，判断已生成题目是否落在所选学段、教材版本与单元或学期范围内。超出范围的题目 MUST 被标出，且在家长确认前不得静默当作范围内题目。

#### Scenario: Question drifts outside the selected unit
- **WHEN** 家长选择了某一单元，而生成结果含有该范围之外的题
- **THEN** 确认列表标明这些题超出范围，家长可以要求重出或剔除

#### Scenario: Questions stay inside the selected range
- **WHEN** Jev 判断题目均落在所选范围内
- **THEN** 家长进入正常确认，确认后才生成 PDF

### Requirement: Jev does not author questions
流程判断 MUST NOT 由 Jev 输出题目正文、解析或 PDF。Jev 只返回预定义的判断结果与置信度。

#### Scenario: Generation remains with the chat or textbook agent
- **WHEN** 流程判断结果为可以出题
- **THEN** 题目由方式 A 的 LangGraph 或方式 B 的 DeepAgents 调用生成式模型产出
