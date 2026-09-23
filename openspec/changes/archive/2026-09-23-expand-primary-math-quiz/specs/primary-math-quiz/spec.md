# Spec Delta

## Purpose

让家长对已入库的小学数学人教版各册按单元出题，选题与接口的年级、学期范围一致，不再锁死一年级上册。

## ADDED Requirements

### Requirement: Quiz accepts any ingested primary math PEP volume
出题与列单元接口 MUST 接受「小学 + 数学 + 人教版」下任意年级与上册或下册，前提是 `textbook_chunks` 中已有该五元组的块。题目 MUST 依据家长所选单元的课文生成。初中、非数学、非人教版，或该册尚未入库时，接口 MUST 拒绝并说明原因，MUST NOT 编造题目。

#### Scenario: A non-grade-one ingested unit returns questions
- **WHEN** 库中已有二年级上册某单元，家长按该册与单元请求出题
- **THEN** 返回题量与请求一致的题目，内容对应该单元课文

#### Scenario: Missing volume or unit is rejected
- **WHEN** 请求的年级学期组合在库中没有块，或单元名不存在
- **THEN** 接口返回明确错误，响应中没有编造的题目

#### Scenario: Non-primary-math combinations stay closed
- **WHEN** 请求初中、语文或其他非人教版组合
- **THEN** 接口拒绝该请求

### Requirement: Select screen opens primary math grades and terms
选题页 MUST 允许选择小学一年级至六年级，以及上册或下册；科目为数学、版本为人教版时可进入下一步。其他学段、科目或版本 MUST 不可继续，并说明目前只开放已入库的小学数学人教版。范围页 MUST 展示接口返回的该册单元列表。

#### Scenario: Parent picks grade three lower volume
- **WHEN** 家长选择小学、三年级、数学、人教版、下册，且该册已入库
- **THEN** 可以进入范围页，并看到该册单元

#### Scenario: Parent picks a subject that is not open
- **WHEN** 家长选择语文或初中
- **THEN** 「下一步」不可用，并看到只开放小学数学人教版的说明

### Requirement: Result reflects the chosen grade and units
结果页标题 MUST 体现所选年级、科目与单元范围，并列出本次生成的题目。下载练习 PDF 时内容 MUST 与页面题干一致。

#### Scenario: Questions appear for the selected range
- **WHEN** 出题成功返回
- **THEN** 结果页列出这些题目，标题含年级与所选单元信息
