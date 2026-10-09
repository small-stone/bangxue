# Spec Delta

## MODIFIED Requirements

### Requirement: Result screen shows generated questions

练习结果页 MUST 对齐 `mockup-04-pdf.png` 的结构，并展示本次生成的题目原文，而不是稿面里的示例算式。标题 MUST 体现所选年级、科目和所选范围（不限于一年级数学）。家长从出题设置发起生成时，MUST 经流式出题通道完成后再进入结果页（或在完成事件后进入）；结果页展示的题目 MUST 与完成事件中的列表一致。

#### Scenario: Questions appear after generation

- **WHEN** 流式出题成功完成并进入结果页
- **THEN** 结果页列出这些题目，家长无需再打开其他工具即可阅读

#### Scenario: Answer sheet follows the toggle

- **WHEN** 家长在设置中打开「同时生成答案卷」且出题成功
- **THEN** 结果页提供答案内容；关闭时不展示答案

## ADDED Requirements

### Requirement: Config page shows streaming progress while generating
出题设置页在生成过程中 MUST 消费教材出题 SSE，并向家长展示与服务端进度相关的状态文案（例如读取课文、生成中、已出 N 题）。MUST NOT 仅依赖与服务器无关的固定假文案轮播作为唯一反馈。生成失败时 MUST 进入结果/错误态并展示错误说明，MUST NOT 无限转圈。

#### Scenario: Progress updates during a long generation

- **WHEN** 家长点击开始出题且服务端推送进度或单题事件
- **THEN** 加载界面上的状态文案随事件更新（例如题数进度），而不是整段等待结束后才第一次变化

#### Scenario: Error ends the busy state

- **WHEN** 流式通道返回错误事件或连接失败
- **THEN** 结束加载态并展示无法出题的说明
