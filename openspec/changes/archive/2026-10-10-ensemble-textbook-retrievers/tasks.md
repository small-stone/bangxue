# Tasks

## 1. 依赖与导入路径

- [x] 1.1 在当前 `apps/api` 环境确认 `EnsembleRetriever` 与 `BaseRetriever` 的可导入路径；若需 `langchain-community`（或其它包）则写入 `requirements.txt` 并安装。验证：`python -c` 能成功 import 选定路径且不报错
- [x] 1.2 在 `agents/shared` 增加 Retriever 模块骨架（如 `retrievers.py`）与工厂函数占位，并在包导出中预留钩子（若需要）。验证：模块可 import，现有 `from agents.shared import hybrid_retrieve` 仍可用

## 2. Retriever 实现与 Ensemble 门面

- [x] 2.1 实现稠密 `BaseRetriever`：固定册次元数据，内部 pgvector 相似度查询，输出带 `id` / `unit_name` / 册次 metadata 的 `Document`。验证：对假/固定 SQL 结果或集成小库，返回条数 ≤ pool 且 metadata 无跨册
- [x] 2.2 实现稀疏 `BaseRetriever`：元数据过滤候选 + jieba + `BM25Okapi`，输出同类 `Document`。验证：空候选返回 `[]`；有候选时 Top 结果来自该册次
- [x] 2.3 用 `EnsembleRetriever`（均等权重 / RRF）组装两路 Retriever；`hybrid_retrieve` 改为经 Ensemble `invoke` 后映射为 `RetrievedChunk`，删除生产路径对手写 `_rrf_fuse` 的唯一依赖。验证：缺元数据仍抛 `RetrievalError`；空库/空命中返回 `[]`；`join_chunk_texts` 行为不变
- [x] 2.4 新增检索单测（mock embedding / 假候选或 mock DB）：断言生产路径构造并调用 Ensemble；跨册 metadata 不出现；空命中为空列表。验证：`pytest` 相关用例通过

## 3. 接线与文档

- [x] 3.1 确认 `agents/chat/harness.py` 仍只经 `hybrid_retrieve` 起草，无需改 HTTP 契约。验证：相关既有 chat/harness 测试通过（或最小冒烟 import + 调用签名检查）
- [x] 3.2 在 `apps/api/README.md` 或根 `README.md` 混合检索亮点处注明「LangChain Retriever + EnsembleRetriever（RRF），表仍为 `textbook_chunks`」。验证：文档描述与实现一致，且未声称迁到 PGVector collection 表
