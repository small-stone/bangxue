# Spec Delta

## Purpose

对已入库教材块做元数据过滤后的 BM25 与向量混合检索，返回可引用的课文片段，供对话出题（及后续方式 A） grounding。

## ADDED Requirements

### Requirement: Metadata-scoped hybrid retrieve
系统 MUST 在检索前按学段 / 年级 / 科目 / 版本 / 学期等已知元数据过滤 `textbook_chunks`（缺字段时用已解析的子集过滤，MUST NOT 无过滤扫全库）。在该候选集上 MUST 同时执行稀疏检索（BM25 或等价词项排序）与稠密检索（pgvector 相似度），再融合为统一 Top-K 结果（K 可配置，默认足以覆盖出题上下文）。

#### Scenario: Query returns fused chunks
- **WHEN** 调用方提供有效元数据范围与自然语言查询（如知识点主题）
- **THEN** 返回按融合分排序的课文块列表，每块含单元名、正文与来源元数据

#### Scenario: Scope prevents cross-book bleed
- **WHEN** 查询限定为小学一年级数学人教版上册
- **THEN** 结果 MUST NOT 包含其他年级或科目的块

### Requirement: Empty or unusable retrieval is explicit
当范围内无入库块，或混合检索后无可用命中时，检索层 MUST 返回空结果（或等价「无命中」状态），MUST NOT 伪造课文。

#### Scenario: Book not ingested
- **WHEN** 家长意图指向尚未入库的册次
- **THEN** 检索返回空，调用方据此追问或提示，而不是编造课文

### Requirement: Retrieval stays in-process
教材混合检索 MUST 在 FastAPI 进程内访问 Postgres / pgvector 完成。系统 MUST NOT 为此部署独立检索微服务（本期）。

#### Scenario: Chat draft calls local retrieve
- **WHEN** 方式 B 起草前发起检索
- **THEN** 检索在现有 API 进程内完成
