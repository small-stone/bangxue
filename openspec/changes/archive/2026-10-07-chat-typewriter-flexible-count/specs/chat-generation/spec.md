# Spec Delta

## Purpose

方式 B 对话出题的家长体验：助手回复打字机展示，题量按自然语言任意指定（1–100）。

## ADDED Requirements

### Requirement: Assistant reply typewriter
对话出题页的助手文字回复 MUST 以打字机方式逐步出现（增量追加到同一气泡），MUST NOT 仅在整段生成结束后一次性替换为完整回复而不展示中间过程。出题等待期间 MAY 显示进度文案；进度文案本身不要求打字机。

#### Scenario: Clarifying reply types out
- **WHEN** 系统判定信息不足并返回追问文案
- **THEN** 家长看到助手气泡中的文字逐步出现，而不是只看到进度后突然整段出现

#### Scenario: Draft-ready reply types out
- **WHEN** 系统已生成题目草稿并返回确认提示文案
- **THEN** 该确认提示文案以打字机方式出现；题目预览可在文案开始展示之后或完成时出现

### Requirement: Arbitrary count up to 100
方式 B 出题题量 MUST 接受家长给出的 1 至 100（含）的任意正整数，并按该数量生成题目。系统 MUST NOT 再将题量强制收成仅 10、15、20、30 四档。

#### Scenario: Parent asks for twelve
- **WHEN** 家长说「出 12 道…」且其他出题信息已足够
- **THEN** 草稿恰好包含 12 道题

#### Scenario: Parent asks for one hundred
- **WHEN** 家长要求 100 道且信息足够
- **THEN** 草稿恰好包含 100 道题

### Requirement: Count over 100 is rejected
当家长要求的题量大于 100 时，系统 MUST NOT 静默截断为 100 并出题；MUST 追问或明确提示上限为 100 道。

#### Scenario: Parent asks for one hundred and one
- **WHEN** 家长说「出 101 道…」
- **THEN** 不生成 101 道题草稿，而是提示题量最多 100 道（或请其改到上限内）

## MODIFIED Requirements

### Requirement: Multi-turn clarification before draft
方式 B MUST 支持多轮对话。当出题所需信息不足时，系统 MUST 向家长追问（例如题量、知识点或科目），且 MUST NOT 在信息不足时生成练习题列表。追问题量时 MUST NOT 暗示只能选择 10、15、20 或 30。

#### Scenario: Incomplete request gets a follow-up
- **WHEN** 家长只说「出点数学题」一类缺少题量或具体知识点的话
- **THEN** 助手追问所缺信息，页面不出现完整题目列表

#### Scenario: Parent can refine after a reply
- **WHEN** 家长在追问后补充题量或知识点
- **THEN** 同一会话继续，系统基于补充后的意图推进

#### Scenario: Follow-up mentions flexible count
- **WHEN** 系统因缺少题量而追问
- **THEN** 追问文案说明可指定 1–100 道，不限定四档
