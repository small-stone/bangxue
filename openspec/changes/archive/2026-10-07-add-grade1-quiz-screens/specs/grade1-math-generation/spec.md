# Spec Delta

## Purpose

只根据已入库的小学一年级数学人教版上册生成练习题，并把题目交回前端展示。

## ADDED Requirements

### Requirement: Generate only from the ingested grade-one volume
出题接口 MUST 只接受小学、一年级、数学、人教版、上册。题目 MUST 依据所选单元在 `textbook_chunks` 中的文本生成。其他年级、科目、版本或下册 MUST 被拒绝。

#### Scenario: Selected unit returns questions grounded in that unit
- **WHEN** 家长请求一年级上册的某一已入库单元，并给出题量和难度
- **THEN** 响应包含该数量附近的题目，且内容对应该单元，而不是其他单元

#### Scenario: Book or unit is missing
- **WHEN** 请求的单元在库中没有文本块
- **THEN** 接口返回明确错误，不返回编造的该单元题目

### Requirement: Settings shape the question list
接口 MUST 接受题量、难度，以及是否包含答案。题型至少覆盖选择题、填空题、计算题中的设置项。返回的每道题 MUST 含题干；在要求答案时 MUST 含对应答案。

#### Scenario: Answer key is omitted unless requested
- **WHEN** 请求未要求答案卷
- **THEN** 响应中的题目没有答案字段

#### Scenario: Requested count is reflected
- **WHEN** 家长选择题量为 10、15、20 或 30 之一
- **THEN** 返回题目数量与该选择一致

### Requirement: A printable file matches the on-screen list
系统 MUST 能根据同一次出题结果生成练习 PDF，使下载内容与结果页题目一致。要求答案卷时 MUST 另给答案 PDF 或在同一下载中区分练习与答案。

#### Scenario: Parent downloads the paper
- **WHEN** 结果页已有题目且家长下载练习 PDF
- **THEN** 文件中的题目与页面上看到的题干一致
