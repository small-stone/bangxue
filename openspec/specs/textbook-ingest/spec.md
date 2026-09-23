# textbook-ingest Specification

## Purpose

提供一套可重复执行的教材入库流程：给定一本 PDF 和它的学段、年级、科目、版本、学期，按单元拆开并写入向量库，供方式 A 以后按范围检索。

## Requirements

### Requirement: One command ingests one textbook
系统 MUST 提供单一入库入口，每次处理一本教材。调用方 MUST 提供 PDF 路径以及学段、年级、科目、版本、学期。入口 MUST NOT 把某一册的路径或单元名写死。

#### Scenario: First book is grade-one math volume one
- **WHEN** 操作者以人教版数学一年级上册的 PDF，以及学段小学、年级一年级、科目数学、版本人教版、学期上册执行入库
- **THEN** 向量库中出现该书的文本块，且每块都带有上述元数据和单元标识

#### Scenario: Another volume uses the same entry
- **WHEN** 操作者换成另一册 PDF 和对应元数据，再次执行同一入口
- **THEN** 不需要修改入库代码，新册的块与第一册以元数据区分

### Requirement: Split follows textbook units
入库 MUST 按教材单元（或目录中的同等一级结构）切开，而不是只按固定字数切块。每个块 MUST 记录所属单元和页码范围。无法识别单元结构时，命令 MUST 失败并说明原因，MUST NOT 把整本无单元标记地写入。

#### Scenario: Unit query returns that unit
- **WHEN** 一年级上册已入库，并按该册元数据加上某一单元名检索
- **THEN** 返回的文本属于该单元，而不是其他单元或其他年级

### Requirement: Re-ingest replaces the same book
对元数据完全相同的教材再次入库时，系统 MUST 先移除该书已有的块再写入新块。其他教材的块 MUST 保持不变。

#### Scenario: Re-running the first book does not duplicate chunks
- **WHEN** 同一本人教版数学一年级上册被入库两次
- **THEN** 该册的块数量与第二次写入的块数一致，不出现两套重复内容

### Requirement: Ingest code lives apart from the quiz agent
拆分与入库实现 MUST 位于 `apps/api/ingest/`。它 MUST NOT 放在 `agents/textbook/` 中，也 MUST NOT 作为独立 HTTP 服务部署。方式 A 出题图以后只读取已入库的块。

#### Scenario: Contributor finds the pipeline
- **WHEN** 贡献者查看 `apps/api`
- **THEN** 能在 `ingest/` 找到入库实现，且 `agents/textbook/` 中没有 PDF 拆分逻辑

### Requirement: Textbook files stay out of git
教材 PDF MUST 只作为本地输入。仓库 MUST 忽略 `book/` 下的 PDF，使入库命令可以读取它们，但 git 不跟踪这些文件。

#### Scenario: PDF is readable locally and ignored by git
- **WHEN** 一年级上册 PDF 位于 `book/小学/数学/人教版/`
- **THEN** 入库命令能读取该文件，且 `git status` 不将其列为待提交内容

### Requirement: Ingest embeddings come from the Bailian model
入库写入的 embedding MUST 使用环境中配置的百炼向量模型 `qwen3.7-text-embedding`。当库中已有向量列的维度与该模型不一致时，入库 MUST 失败并说明需要先更换向量列，MUST NOT 把新向量追加进旧维度的表。更换并重新入库后，仍 MUST 遵守同一五元组先删后写、其他教材不受影响的规则。

#### Scenario: Grade-one book is stored with the new vectors
- **WHEN** 向量列已改为 1024 维，操作者再次用小学、一年级、数学、人教版、上册执行入库
- **THEN** 该书的块带有 `qwen3.7-text-embedding` 生成的向量，且块数等于这一次写入的块数

#### Scenario: Old 512-dimension column rejects the new model
- **WHEN** `textbook_chunks` 的向量列仍是 512 维，操作者直接用百炼向量模型入库
- **THEN** 命令失败并说明维度不符，表中不出现混用的新向量

### Requirement: Unit split covers both PEP heading styles
入库切分 MUST 识别两类人教版单元起点：带「第 N 单元」或孤行汉字序号（一至十）后接课题的 2022 修订版样式；以及目录式阿拉伯数字序号后接课题的旧版样式。无法识别任一单元起点时，该本 MUST 失败且 MUST NOT 写入无单元块。

#### Scenario: A 2022-style volume splits by Chinese unit indexes
- **WHEN** 对一本以孤行「一」「二」标记单元的小学数学 PDF 执行入库
- **THEN** 写入的块带有对应单元名，且块数大于零

#### Scenario: An older volume splits by numbered chapter titles
- **WHEN** 对一本以「1 四则运算」这类数字序号课题标记单元的小学数学 PDF 执行入库
- **THEN** 写入的块带有对应单元名，且块数大于零

#### Scenario: A book without unit markers is rejected
- **WHEN** PDF 中无法识别单元起点
- **THEN** 入库命令失败并说明原因，库中不出现该书的新块

### Requirement: Batch ingest for primary math under book/
系统 MUST 提供批量入口，扫描本地 `book/小学/数学/`（含人教版子目录）中的 PDF，从路径与文件名解析年级与学期，并对每一本调用现有「一次一本」入库。同一五元组再次执行时仍 MUST 先删后写。批量结果 MUST 汇总每本成功或失败，一本失败 MUST NOT 回滚其他已成功的书。

#### Scenario: Operator runs the primary-math batch
- **WHEN** `book/小学/数学/人教版` 下存在一年级到六年级上下册 PDF，且百炼向量配置可用
- **THEN** 批量命令对每一本能解析元数据的书尝试入库，结束时报告成功册数与失败册数及原因

#### Scenario: Re-running the batch replaces the same book only
- **WHEN** 操作者对已入库的同一年级、学期再次跑批量入库
- **THEN** 该书块被新写入替换，其他年级或学期的块保持不变
