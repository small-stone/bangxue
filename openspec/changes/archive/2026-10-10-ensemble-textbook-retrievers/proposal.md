# Proposal

## Why

教材混合检索已在 `agents/shared/retrieval.py` 手写「元数据过滤 → BM25 + pgvector → RRF」，行为正确，但未接入 LangChain Retriever / `EnsembleRetriever` 抽象，后续难与标准 RAG 链、评测工具或其它 Retriever 组合对齐。现在要把**同等检索语义**完整 Ensemble 化，同时保持家长可观察行为不变。

## What Changes

- 将稠密（pgvector）与稀疏（中文分词 + BM25）路径分别实现为 LangChain `BaseRetriever`（或等价 Retriever）。
- 用 LangChain `EnsembleRetriever`（RRF）融合两路结果，取代手写 `_rrf_fuse` 作为融合实现。
- 保留进程内、元数据先过滤、空命中不编造课文等现有语义；`hybrid_retrieve` / `join_chunk_texts` 对外签名可保留为薄门面，内部改为调用 Ensemble。
- **不**迁移 `textbook_chunks` 到 LangChain 默认 `PGVector` collection 表结构；仍读写现有表。
- **不**改家长 API、SSE、出题 prompt 契约；**不**拆独立检索服务。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `textbook-retrieval`: 在保留元数据过滤、混合检索、空命中、进程内约束的前提下，要求稠密/稀疏路径以 LangChain Retriever 实现，并由 `EnsembleRetriever`（或同库等价 Ensemble + RRF）完成融合。

## Impact

- **Agent 共用层**：`apps/api/agents/shared/retrieval.py`（及必要的拆分模块）；`agents/chat` 起草路径继续经 `hybrid_retrieve`。
- **方式 A**：按单元名 SQL 取文路径本期可不改；不强制 Ensemble。
- **数据**：`textbook_chunks` 表结构不变；无迁移。
- **依赖**：已有 `langchain` / `rank-bm25` / `jieba`；若 Ensemble / community Retriever 需额外包（如 `langchain-community`），写入 `requirements.txt`。
- **前端 / 部署 / 流式超时**：无变更；检索仍为同步进程内调用，时延特性目标与现网对齐（候选上限与 Top-K 保持）。
- **Non-goals**：ES/独立搜索集群；改 embedding 模型或维度；Compose 新服务；方式 A 选题图改写；LangSmith 替换观测。
