# Design

## Context

见 `proposal.md` — Why。现状：`agents/shared/retrieval.py` 的 `hybrid_retrieve` 手写 `_load_candidates` / `_dense_rank` / `_bm25_rank` / `_rrf_fuse`；对话起草（`agents/chat/harness.py`）调用 `hybrid_retrieve` + `join_chunk_texts`。表 `textbook_chunks` 由 `ingest/store.py` 维护，含册次元数据列与 `embedding vector(N)`。仓库已依赖 `langchain`、`rank-bm25`、`jieba`；**无** LangChain `VectorStore` / `EnsembleRetriever` 用法。方式 A 按单元名 SQL 取文，不经混合检索。

## Goals / Non-Goals

**Goals:**

- 稠密、稀疏各一个 LangChain Retriever；`EnsembleRetriever` 做 RRF 融合。
- 对外保持 `hybrid_retrieve(...)` / `RetrievedChunk` / `join_chunk_texts` 行为与签名兼容（门面内切换实现）。
- 元数据过滤、候选上限、Top-K、中文分词 BM25、空命中语义与现网对齐。
- 补检索单测（假 embedding / 小块或 mock DB），证明走 Ensemble 路径且不跨册。

**Non-Goals:**

- 迁表到 LangChain `PGVector` 默认 collection schema。
- 改 `chat` HTTP / SSE、Supervisor、方式 A 单元取文。
- 独立检索微服务；换 embedding 模型或维度；引入 ES。

## Decisions

### 1. 保留现有表 + 自定义 Retriever，不用官方 PGVector store

| 方案 | 结论 |
|------|------|
| 迁到 `langchain_community.vectorstores.PGVector` | 拒绝：表结构与同书覆盖逻辑重写成本高 |
| **自定义 `BaseRetriever`，内部 SQL / BM25** | **采用** |
| 仅门面改名、内部仍手写 RRF | 拒绝：不满足「完整 Ensemble 化」 |

稠密 Retriever：在构造时固定 `stage/grade/subject/edition/term`，`_get_relevant_documents(query)` 内 `embed_texts` + `ORDER BY embedding <=> … LIMIT`。  
稀疏 Retriever：同一册次加载候选（现有 `_load_candidates` / LIMIT），jieba + `BM25Okapi` 排序。  
Document：`page_content=content`，`metadata` 含 `id`、`unit_name` 与册次字段，便于门面还原 `RetrievedChunk`。

### 2. 融合用 `EnsembleRetriever`，权重均等 + RRF

```
hybrid_retrieve(query, meta…)
  → 若 meta 不全：RetrievalError（与现网一致）
  → dense = PgvectorTextbookRetriever(meta, k=_DENSE_POOL)
  → sparse = Bm25TextbookRetriever(meta, k=_SPARSE_POOL)
  → ensemble = EnsembleRetriever(
        retrievers=[dense, sparse],
        weights=[0.5, 0.5],  # 或库默认；语义为 RRF
      )
  → docs = ensemble.invoke(query)  # 或 get_relevant_documents
  → 映射为 RetrievedChunk[:top_k]，拼 score 可选
```

备选：继续手写 `_rrf_fuse` 只包一层假 Ensemble —— 不选。  
备选：社区 `BM25Retriever.from_documents` 全库构建 —— 不选（缺元数据过滤与中文分词控制）；稀疏路径保持自研 Retriever。

依赖：确认当前 `langchain` 版本导出 `EnsembleRetriever` 的包路径；若落在 `langchain_community` / `langchain_classic`，则增加对应依赖并钉版本到 `requirements.txt`。

### 3. 门面与模块拆分

- 保留 `hybrid_retrieve` / `join_chunk_texts` / `RetrievalError` 导出（`agents/shared/__init__.py` 不变或仅增工厂）。
- 实现可拆为同包内 `retrievers.py`（两个 Retriever + `build_textbook_ensemble`），`retrieval.py` 作门面；或单文件分区，以可读为准。
- Checkpointer / `thread_id`：**不参与**检索；会话状态仍在业务表 + checkpoint ns。检索无状态写入。

### 4. 密钥与外部依赖

- Query embedding：现有 `bailian_api_key` + `EMBEDDING_*`（`ingest.embed.embed_texts`）。
- DB：`DATABASE_URL`（与 ingest 同连接策略）。
- 无新密钥；无对象存储变更。

### 5. 验证策略

- 单测：mock / 假候选证明 (a) Ensemble 被构造并 invoke；(b) 过滤后无跨册 metadata；(c) 空候选 → 空列表。
- 手工或集成：已入库一年级数学册次，对话「口算」类意图仍能 grounding（行为回归）。

## Risks / Trade-offs

- **[Risk] EnsembleRetriever 文档 id 去重与现网 RRF 排序不完全一致** → Mitigation：固定 weights；单测对比同输入 Top-K 集合（允许顺序在并列分上轻微差异）；必要时调 `c`/weights 对齐。
- **[Risk] langchain 包路径随大版本搬迁** → Mitigation：tasks 中先锁定 import 路径与依赖名再改生产代码。
- **[Risk] 双 Retriever 各查一次 DB，变慢** → Mitigation：保持候选 LIMIT / pool 常量；稀疏侧可复用一次候选加载（构造时缓存 candidates）。
- **[Trade-off] 自定义 Retriever vs 全面 VectorStore** → 选前者，满足 Ensemble 目标且不迁表。

## Migration Plan

1. 加依赖（若需要）→ 实现两个 Retriever + Ensemble 工厂 → `hybrid_retrieve` 切门面。
2. 跑检索单测与对话起草相关既有测试。
3. 部署无数据迁移；回滚即恢复手写 RRF 门面（git revert），表不变。

## Open Questions

（无 — Ensemble 包路径在实现首步用环境确认后写入代码，不改变本设计结论。）
