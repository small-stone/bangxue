# Spec Delta

## ADDED Requirements

### Requirement: Hybrid retrieve uses LangChain Ensemble composition
教材混合检索的稠密路径与稀疏路径 MUST 分别实现为 LangChain Retriever（`BaseRetriever` 或等价可 `invoke` 的 Retriever）。两路结果 MUST 经 LangChain `EnsembleRetriever`（RRF）融合为统一 Top-K。系统 MUST NOT 以手写融合循环作为生产路径的唯一实现。元数据过滤、空命中与进程内约束 MUST 仍满足本能力既有要求。

#### Scenario: Ensemble fusion is the production path
- **WHEN** 方式 B 起草前对已配置册次元数据发起混合检索
- **THEN** 生产路径经稠密 Retriever、稀疏 Retriever 与 `EnsembleRetriever` 融合得到 Top-K，且结果仍含单元名、正文与来源元数据

#### Scenario: Behavior parity for empty and scoped results
- **WHEN** 范围内无块，或融合后无可用命中；或查询限定为某一册次
- **THEN** 空命中返回空且不伪造课文；非空结果 MUST NOT 跨册窜年级或科目
