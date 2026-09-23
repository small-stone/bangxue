# Spec Delta

## ADDED Requirements

### Requirement: Ingest embeddings come from the Bailian model
入库写入的 embedding MUST 使用环境中配置的百炼向量模型 `qwen3.7-text-embedding`。当库中已有向量列的维度与该模型不一致时，入库 MUST 失败并说明需要先更换向量列，MUST NOT 把新向量追加进旧维度的表。更换并重新入库后，仍 MUST 遵守同一五元组先删后写、其他教材不受影响的规则。

#### Scenario: Grade-one book is stored with the new vectors
- **WHEN** 向量列已改为 1024 维，操作者再次用小学、一年级、数学、人教版、上册执行入库
- **THEN** 该书的块带有 `qwen3.7-text-embedding` 生成的向量，且块数等于这一次写入的块数

#### Scenario: Old 512-dimension column rejects the new model
- **WHEN** `textbook_chunks` 的向量列仍是 512 维，操作者直接用百炼向量模型入库
- **THEN** 命令失败并说明维度不符，表中不出现混用的新向量
