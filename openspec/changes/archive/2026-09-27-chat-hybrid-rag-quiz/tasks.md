# Tasks

## 1. Hybrid retrieval module

- [x] 1.1 新增 `agents/shared`（或约定路径）混合检索：元数据过滤候选、pgvector Top-K、BM25 Top-K、RRF 融合。验证：对假数据 / 小库调用返回块含 unit_name 与 content，且不跨册
- [x] 1.2 将 `rank_bm25` 与中文分词依赖写入 `apps/api/requirements.txt` 并安装。验证：进程内可 import，无新增独立检索服务
- [x] 1.3 查询侧 embedding 复用百炼向量模型与 `bailian_api_key`。验证：缺密钥时检索或上层返回明确配置错误

## 2. Wire Mode B

- [x] 2.1 `generate_chat_questions` / `draft_quiz` 在出题前调用 `hybrid_retrieve`，将 Top-K 课文写入 system/user prompt。验证：有命中时请求体或日志可见课文片段，题目提示要求紧扣课文
- [x] 2.2 检索空结果时追问 / 错误，不调用无上下文的纯意图出题。验证：未入库册次对话不返回题目列表
- [x] 2.3 确认练习的 meta 记录检索范围摘要（年级科目等）与来源仍为对话。验证：确认后 quiz meta 可看到摘要字段

## 3. Jev / completeness

- [x] 3.1 更新方式 B 完整性判断：年级（或等价）+ 科目 + 主题 + 题量。验证：缺年级时追问，不进入出题
- [x] 3.2 回归：信息足够且库中有对应册时，对话出题仍可确认进结果页。验证：主路径无白屏；题目非空

## 4. Docs

- [x] 4.1 更新 `apps/api/README`（或等价）说明方式 B 混合检索与依赖。验证：文档写明 BM25 + 向量、进程内检索
