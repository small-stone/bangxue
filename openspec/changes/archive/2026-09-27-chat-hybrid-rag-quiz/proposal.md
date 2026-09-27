# Proposal

## Why

方式 B 对话出题目前只按家长意图直调百炼，**不读教材库**，题目容易飘出课本。入库侧已有 `textbook_chunks` + pgvector embedding，但未接入对话路径。需要把对话出题改成 **BM25（稀疏）+ 向量（稠密）混合检索 → 再生成**，让题目紧贴已入库课文。

## What Changes

- 新增共用教材混合检索能力：元数据过滤后，BM25 与向量检索并行，经融合（如 RRF）取 Top-K 课文块。
- 方式 B 在 Jev 判定信息足够后、起草题目前 MUST 先检索；出题 prompt MUST 附带检索到的课文，并要求紧扣原文。
- 检索无命中或册次未入库时：MUST 追问 / 提示，MUST NOT 静默退回纯意图编题冒充教材题。
- 废止「一期对话可不绑教材 RAG」的现行约束（与本变更冲突）。
- Jev「足够出题」的条件扩展：至少能确定检索范围所需的科目（及年级或等价约束）与知识点 / 主题，以及题量。

## Capabilities

### New Capabilities

- `textbook-retrieval`: 对已入库 `textbook_chunks` 做元数据过滤 + BM25/向量混合检索，返回可引用的课文块（供方式 B 本期使用，接口可复用给方式 A 后续）。

### Modified Capabilities

- `chat-generation`: 对话出题改为检索 grounding 后再生成；移除「一期不强制教材 RAG」。
- `flow-judgment`: 方式 B 完整性判断纳入检索所需范围字段（年级 / 科目等），不足则追问。

## Impact

- **FastAPI / Agent B**：`agents/chat` 起草前调用检索；`generate_chat_questions` 注入课文上下文。
- **共用**：新建检索模块（建议 `agents/shared` 或 `ingest` 旁的检索 API），读 Postgres + pgvector；BM25 实现选型见 design。
- **数据**：复用现有 `textbook_chunks`；可能增加全文检索辅助列/索引（设计定）。
- **前端**：可仅改追问文案；本期不强制做教材选题 UI。
- **方式 A**：本期可不改图；检索模块预留复用。
- **Non-goals**：Elasticsearch / 独立搜索服务；方式 A 全量改向量 RAG；对话里强制图形化选单元；HITL / Checkpointer 改造；错题组卷。
- **超时**：检索 + embedding 查询 + 出题仍走现有同步对话回合；需控制候选集与 Top-K，避免单回合过长。
