# Spec Delta

## Purpose

方式 B 对话出题在进入追问或草稿前，改为经 Supervisor 编排；家长可见的多轮追问、草稿确认与确认后共用结果 / PDF 行为保持一致。

## MODIFIED Requirements

### Requirement: Multi-turn clarification before draft
方式 B MUST 支持多轮对话。当出题所需信息不足时，系统 MUST 向家长追问（例如题量、知识点或科目），且 MUST NOT 在信息不足时生成练习题列表。追问题量时 MUST NOT 暗示只能选择 10、15、20 或 30。对话消息在判定是否出草稿之前 MUST 经 Supervisor 路由（见 `request-supervisor`）。

#### Scenario: Incomplete request gets a follow-up
- **WHEN** 家长只说「出点数学题」一类缺少题量或具体知识点的话
- **THEN** 助手追问所缺信息，页面不出现完整题目列表

#### Scenario: Parent can refine after a reply
- **WHEN** 家长在追问后补充题量或知识点
- **THEN** 同一会话继续，系统基于补充后的意图推进

#### Scenario: Follow-up mentions flexible count
- **WHEN** 系统因缺少题量而追问
- **THEN** 追问文案说明可指定 1–100 道，不限定四档

#### Scenario: Routed clarify does not invent a draft
- **WHEN** Supervisor 将本轮路由为追问
- **THEN** 响应中没有可确认的完整题目列表

## ADDED Requirements

### Requirement: Chat path may hand off to textbook generation
当 Supervisor 判定应走教材式出题时，对话会话 MUST 能得到与方式 A 同类的题目 JSON（可确认后进入共用结果与 PDF），并 MUST 在元数据中标明来源仍为「对话」或明确标注教材式生成（实现二选一，但 MUST NOT 伪装成家长未发起的按教材 UI 会话）。

#### Scenario: Unit-named request yields confirmable questions
- **WHEN** 家长在对话中给出足够的年级/册次/单元与题量，且 Supervisor 选择教材式出题
- **THEN** 对话中出现可确认的题目列表（或等价确认视图），确认后可进入共用结果与 PDF
