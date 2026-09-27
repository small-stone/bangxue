# Design

## Context

见 `proposal.md`。现状：`generate_chat_questions` 只吃 `intent`；`textbook_chunks.embedding` 仅入库写入；方式 A 用单元名 SQL 取文，亦非混合检索。规格 `chat-generation` 仍写「一期不强制 RAG」，将被本变更废止。

## Goals / Non-Goals

**Goals:**

- 共用混合检索：元数据过滤 → BM25 + 向量 → 融合 Top-K。
- 方式 B 起草前强制 grounding；无命中则追问。
- Jev 完整性含检索范围字段。

**Non-Goals:**

- 独立搜索集群；改写方式 A 选题图；前端教材选单元器；重训 embedding。

## Decisions

### 1. 检索落点：`agents/shared/retrieval.py`（或同级包）

| 方案 | 结论 |
|------|------|
| 写在 `agents/chat` 内 | 拒绝：方式 A 难复用 |
| **`agents/shared` 检索 API** | **采用** |
| 独立微服务 | 拒绝：违背进程内约定 |

签名示意：`hybrid_retrieve(query, *, stage, grade, subject, edition, term, top_k=8) -> list[Chunk]`。

### 2. 混合算法

```
家长消息 → Jev(足够?) 
  no → 追问
  yes → hybrid_retrieve(topic, meta)
         ├─ candidates = SQL WHERE meta…
         ├─ dense: embed(query) ↔ pgvector ORDER BY distance LIMIT k
         ├─ sparse: BM25(query, candidates) TOP k
         └─ RRF(dense, sparse) → Top-K texts
       → generate_chat_questions(intent, source_text=joined)
```

- **稠密**：复用入库 embedding 模型（`qwen3.7-text-embedding` / `bailian_api_key`）。
- **稀疏**：在元数据过滤后的候选集上做 BM25（推荐 `rank_bm25` + 简易中文分词如 jieba；候选过大时先 `LIMIT` 或加粗过滤）。不引入 ES。
- **融合**：Reciprocal Rank Fusion（k=60 常规默认），再截断 Top-K（如 6–8），拼接进 prompt（总长上限约 6–8k 字，超出截断低分块）。

### 3. 范围从哪来

优先 Jev / 会话 `meta`（grade、subject；edition/term 默认「人教版」+ 当前学期启发式或追问）。不强制新 UI；缺 grade 则追问。

### 4. 无命中策略

检索空 → 助手文案提示「该册可能未入库或换个知识点」，**禁止**无 context 的 `generate_chat_questions`。

### 5. 状态存放

- **Checkpointer**：仍只存对话轮次（方式 B 现有）。
- **业务**：确认后的 quiz meta 增加 `retrieval_summary`（年级科目册 + 命中单元名列表）；不存全文 embedding。
- **textbook_chunks**：只读；本期可不改表，除非 BM25 需要 `tsvector` 列（若用库内 FTS）。首选应用内 BM25 → **可不改表**。

### 6. 密钥与依赖

- `bailian_api_key`：出题 + query embedding。
- 新 Python 依赖：`rank_bm25`、分词库（设计实现时锁定版本进 `requirements.txt`）。

## Risks / Trade-offs

- **[Risk] 中文 FTS/BM25 分词差** → Mitigation：先元数据缩候选；评测命中后再调分词。
- **[Risk] 回合变慢（embed + 双路检索 + 出题）** → Mitigation：限制候选与 K；embed 超时明确错误。
- **[Risk] 家长跨科自由聊无法 grounding** → Mitigation：Jev 追问年级科目；空检索不编题。
- **[Trade-off] 应用内 BM25 vs Postgres FTS** → 选应用内以少迁库、利中文分词；候选集需有上限。

## Migration Plan

1. 落地 `hybrid_retrieve` + 单测（假 embedding / 小块集）。
2. 接线 `draft_quiz` / `generate_chat_questions`。
3. 更新 Jev prompt / 完整性字段。
4. 用已入库一年级数学验证对话「口算」类请求命中课文。
5. 同步 REQUIREMENTS §6「方式 B 与教材库关系」文案（实现或归档时）。

回滚：feature 开关或恢复直调生成（不推荐与规格并存）。

## Open Questions

无阻断项。默认 edition=人教版、缺 term 时追问或用「上册」启发式，实现时在 tasks 验收说明里写死一种。
