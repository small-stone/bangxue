# Spec Delta

## ADDED Requirements

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
