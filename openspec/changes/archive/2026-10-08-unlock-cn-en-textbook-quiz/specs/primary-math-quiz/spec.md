# Spec Delta

## MODIFIED Requirements

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

## ADDED Requirements

### Requirement: Quiz prompt follows the selected subject
方式 A 出题 MUST 按请求元数据中的科目生成系统提示（数学 / 语文 / 英语）。仅当科目为数学时，MAY 要求看图题 `scene`；语文与英语 MUST NOT 依赖数学看图场景字段才能出题。

#### Scenario: English quiz does not require math scene
- **WHEN** 家长对已入库英语单元成功出题
- **THEN** 返回的题目可为选择题或填空等文本题，不因缺少 `scene` 而失败
