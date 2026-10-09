# textbook-quiz-ui Specification

## Purpose

让家长不登录就能按墨金纸感稿走完「首页 → 选题 → 范围 → 设置 → 结果」，并在结果页看到根据一年级数学上册生成的题目。

## Requirements

### Requirement: Home matches the ink-amber mock

首页 MUST 按 `docs/mockups/alt-ink-amber/mockup-00-home.png` 呈现：纸感底、琥珀金主入口「按教材出题」、描边入口「对话出题」、底部「首页 / 成绩 / 我的」。本变更 MUST NOT 要求登录。

#### Scenario: Parent opens the app

- **WHEN** 家长打开站点根路径
- **THEN** 看到上述首页，且无需登录即可点击「按教材出题」

#### Scenario: Chat entry is visible but not a quiz flow

- **WHEN** 家长点击「对话出题」
- **THEN** 不进入出题结果，并看到该入口尚未开放的说明

### Requirement: Textbook setup screens follow mocks 01 to 03

「按教材出题」「选择出题范围」「出题设置」MUST 分别对齐 `mockup-01-select.png`、`mockup-02-range.png`、`mockup-03-config.png` 的信息结构：学段、年级、科目、版本、按单元或半学期或整学期、题量、难度、题型比例、是否生成答案卷。选题页 MUST 在切换科目时展示该科可用版本，并在选择语文时提供统编版；默认版本 MUST 与该科白名单一致（数学/英语 → 人教版，语文 → 统编版）。「更多」科目 MUST NOT 进入下一步。

#### Scenario: Allowlisted Chinese selection can continue

- **WHEN** 家长选择小学、语文、统编版、任意一至六年级与上下册
- **THEN** 「下一步」可用，并可进入范围页

#### Scenario: Allowlisted English selection can continue

- **WHEN** 家长选择小学、英语、人教版、三年级至六年级与上下册
- **THEN** 「下一步」可用，并可进入范围页

#### Scenario: Closed combination cannot continue

- **WHEN** 家长选择初中、或「更多」、或英语一二年级、或不在白名单的版本
- **THEN** 「下一步」不可用，并说明当前开放的小学科目与版本范围

#### Scenario: Only grade-one math can continue

- **WHEN** 家长选择不在开放白名单内的组合（如初中、或英语一年级）
- **THEN** 「下一步」不可用，并说明当前开放的小学数学/语文/英语范围

#### Scenario: Parent reaches settings with a unit

- **WHEN** 家长选择任一已开放组合，并选定至少一个已入库单元
- **THEN** 进入出题设置，且摘要中能看到所选单元

### Requirement: Result screen shows generated questions

练习结果页 MUST 对齐 `mockup-04-pdf.png` 的结构，并展示本次生成的题目原文，而不是稿面里的示例算式。标题 MUST 体现所选年级、科目和所选范围（不限于一年级数学）。家长从出题设置发起生成时，MUST 经流式出题通道完成后再进入结果页（或在完成事件后进入）；结果页展示的题目 MUST 与完成事件中的列表一致。

#### Scenario: Questions appear after generation

- **WHEN** 流式出题成功完成并进入结果页
- **THEN** 结果页列出这些题目，家长无需再打开其他工具即可阅读

#### Scenario: Answer sheet follows the toggle

- **WHEN** 家长在设置中打开「同时生成答案卷」且出题成功
- **THEN** 结果页提供答案内容；关闭时不展示答案

### Requirement: Config page shows streaming progress while generating
出题设置页在生成过程中 MUST 消费教材出题 SSE，并向家长展示与服务端进度相关的状态文案（例如读取课文、生成中、已出 N 题）。MUST NOT 仅依赖与服务器无关的固定假文案轮播作为唯一反馈。生成失败时 MUST 进入结果/错误态并展示错误说明，MUST NOT 无限转圈。

#### Scenario: Progress updates during a long generation

- **WHEN** 家长点击开始出题且服务端推送进度或单题事件
- **THEN** 加载界面上的状态文案随事件更新（例如题数进度），而不是整段等待结束后才第一次变化

#### Scenario: Error ends the busy state

- **WHEN** 流式通道返回错误事件或连接失败
- **THEN** 结束加载态并展示无法出题的说明

### Requirement: Select notice lists open subjects
当当前选择不可继续时，选题页 MUST 用中文说明目前开放：小学数学人教版（一至六上下）、语文统编版（一至六上下）、英语人教版（三至六上下）。MUST NOT 再写「只开放小学数学人教版」作为唯一说明。

#### Scenario: Notice after picking closed edition

- **WHEN** 家长在数学科目下选择苏教版
- **THEN** 看到包含数学/语文/英语开放范围的说明，且「下一步」不可用
