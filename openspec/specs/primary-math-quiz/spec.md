# primary-math-quiz Specification

## Purpose

让家长对已入库的小学数学人教版各册按单元出题，选题与接口的年级、学期范围一致，不再锁死一年级上册。

## Requirements

### Requirement: Quiz accepts any ingested primary math PEP volume
出题与列单元接口 MUST 接受以下已入库小学组合（且 `textbook_chunks` 中已有该五元组的块）：数学 + 人教版 + 一年级至六年级 + 上册或下册；语文 + 统编版 + 一年级至六年级 + 上册或下册；英语 + 人教版 + 三年级至六年级 + 上册或下册。题目 MUST 依据家长所选单元的课文生成。出题提示 MUST 使用请求中的科目，MUST NOT 在语文/英语请求中写死「小学数学」。初中、不在白名单的科目/版本/年级，或该册尚未入库时，接口 MUST 拒绝并说明原因，MUST NOT 编造题目。

#### Scenario: A non-grade-one ingested unit returns questions
- **WHEN** 库中已有二年级上册某单元，家长按该册与单元请求出题
- **THEN** 返回题量与请求一致的题目，内容对应该单元课文

#### Scenario: Missing volume or unit is rejected
- **WHEN** 请求的年级学期组合在库中没有块，或单元名不存在
- **THEN** 接口返回明确错误，响应中没有编造的题目

#### Scenario: Chinese textbook combination is accepted
- **WHEN** 库中已有小学语文统编版某册单元，家长按该五元组与单元请求出题
- **THEN** 返回题目，且出题上下文按语文科目表述

#### Scenario: English grade-one stays closed
- **WHEN** 请求小学英语人教版一年级或二年级
- **THEN** 接口拒绝该请求

#### Scenario: Non-primary-math combinations stay closed
- **WHEN** 请求初中、或其他非白名单版本（如苏教版）
- **THEN** 接口拒绝该请求

#### Scenario: Non-allowlisted combinations stay closed
- **WHEN** 请求初中、或苏教版等非白名单版本
- **THEN** 接口拒绝该请求

### Requirement: Select screen opens primary math grades and terms
选题页 MUST 允许选择小学一年级至六年级以及上册或下册。当组合属于已开放白名单（数学人教版一至六；语文统编版一至六；英语人教版三至六）时 MUST 可进入下一步。其他学段、科目、版本或英语一二年级 MUST 不可继续，并说明当前开放的科目与版本范围。范围页 MUST 展示接口返回的该册单元列表。

#### Scenario: Parent picks grade three lower volume
- **WHEN** 家长选择小学、三年级、数学、人教版、下册，且该册已入库
- **THEN** 可以进入范围页，并看到该册单元

#### Scenario: Parent picks Chinese unified edition
- **WHEN** 家长选择小学、二年级、语文、统编版、上册
- **THEN** 「下一步」可用，可进入范围页

#### Scenario: Parent picks English below grade three
- **WHEN** 家长选择小学英语人教版一年级或二年级
- **THEN** 「下一步」不可用，并看到英语自三年级起开放的说明

#### Scenario: Parent picks a subject that is not open
- **WHEN** 家长选择「更多」或初中
- **THEN** 「下一步」不可用，并看到当前开放的小学科目与版本说明

#### Scenario: Parent picks junior high
- **WHEN** 家长选择初中
- **THEN** 「下一步」不可用，并看到仅开放小学已入库科目的说明

### Requirement: Result reflects the chosen grade and units
结果页标题 MUST 体现所选年级、科目与单元范围，并列出本次生成的题目。下载练习 PDF 时内容 MUST 与页面题干一致。

#### Scenario: Questions appear for the selected range
- **WHEN** 出题成功返回
- **THEN** 结果页列出这些题目，标题含年级与所选单元信息

### Requirement: Quiz prompt follows the selected subject
方式 A 出题 MUST 按请求元数据中的科目生成系统提示（数学 / 语文 / 英语）。仅当科目为数学时，MAY 要求看图题 `scene`；语文与英语 MUST NOT 依赖数学看图场景字段才能出题。

#### Scenario: English quiz does not require math scene
- **WHEN** 家长对已入库英语单元成功出题
- **THEN** 返回的题目可为选择题或填空等文本题，不因缺少 `scene` 而失败

### Requirement: Textbook quiz generation streams over SSE
家长发起按教材出题时，系统 MUST 提供 SSE（`text/event-stream`）出题通道。流中 MUST 至少包含：阶段进度事件、最终成功事件（含练习 `id`、标题与完整题目列表）或错误事件。在生成过程中 MAY 推送已校验通过的单题事件。题量、白名单与「不得编造题目」约束 MUST 与同步出题一致。未配置 `bailian_api_key` 时 MUST 以错误事件（或等价失败）结束，MUST NOT 推送题目。

#### Scenario: Parent receives progress then a complete quiz
- **WHEN** 家长对已入库单元请求流式出题且模型成功返回合法题目
- **THEN** 客户端先收到至少一条进度类事件，最后收到含 `id` 与完整题目列表的完成事件，题量与请求一致

#### Scenario: Stream fails closed without inventing questions
- **WHEN** 未配置密钥或模型/校验最终失败
- **THEN** 流以错误事件结束，且全程未把编造题目当作成功完成

#### Scenario: Partial questions never exceed the requested count
- **WHEN** 流式过程中推送了单题事件
- **THEN** 累计题目数不超过请求题量，完成事件中的列表长度等于请求题量
