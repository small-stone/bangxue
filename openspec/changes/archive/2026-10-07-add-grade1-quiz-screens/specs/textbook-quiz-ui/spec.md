# Spec Delta

## Purpose

让家长不登录就能按墨金纸感稿走完「首页 → 选题 → 范围 → 设置 → 结果」，并在结果页看到根据一年级数学上册生成的题目。

## ADDED Requirements

### Requirement: Home matches the ink-amber mock
首页 MUST 按 `docs/mockups/alt-ink-amber/mockup-00-home.png` 呈现：纸感底、琥珀金主入口「按教材出题」、描边入口「对话出题」、底部「首页 / 成绩 / 我的」。本变更 MUST NOT 要求登录。

#### Scenario: Parent opens the app
- **WHEN** 家长打开站点根路径
- **THEN** 看到上述首页，且无需登录即可点击「按教材出题」

#### Scenario: Chat entry is visible but not a quiz flow
- **WHEN** 家长点击「对话出题」
- **THEN** 不进入出题结果，并看到该入口尚未开放的说明

### Requirement: Textbook setup screens follow mocks 01 to 03
「按教材出题」「选择出题范围」「出题设置」MUST 分别对齐 `mockup-01-select.png`、`mockup-02-range.png`、`mockup-03-config.png` 的信息结构：学段、年级、科目、版本、按单元或半学期或整学期、题量、难度、题型比例、是否生成答案卷。

#### Scenario: Only grade-one math can continue
- **WHEN** 家长不在小学、一年级、数学、人教版这一组合上
- **THEN** 「下一步」不可用，并说明目前只能出一年级数学

#### Scenario: Parent reaches settings with a unit
- **WHEN** 家长选择一年级数学人教版，并选定至少一个已入库单元
- **THEN** 进入出题设置，且摘要中能看到所选单元

### Requirement: Result screen shows generated questions
练习结果页 MUST 对齐 `mockup-04-pdf.png` 的结构，并展示本次生成的题目原文，而不是稿面里的示例算式。标题 MUST 体现一年级数学和所选范围。

#### Scenario: Questions appear after generation
- **WHEN** 出题接口成功返回
- **THEN** 结果页列出这些题目，家长无需再打开其他工具即可阅读

#### Scenario: Answer sheet follows the toggle
- **WHEN** 家长在设置中打开「同时生成答案卷」且出题成功
- **THEN** 结果页提供答案内容；关闭时不展示答案
