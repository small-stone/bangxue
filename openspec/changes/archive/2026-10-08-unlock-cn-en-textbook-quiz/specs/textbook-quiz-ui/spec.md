# Spec Delta

## MODIFIED Requirements

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

## ADDED Requirements

### Requirement: Select notice lists open subjects
当当前选择不可继续时，选题页 MUST 用中文说明目前开放：小学数学人教版（一至六上下）、语文统编版（一至六上下）、英语人教版（三至六上下）。MUST NOT 再写「只开放小学数学人教版」作为唯一说明。

#### Scenario: Notice after picking closed edition

- **WHEN** 家长在数学科目下选择苏教版
- **THEN** 看到包含数学/语文/英语开放范围的说明，且「下一步」不可用
