# apps/api

FastAPI 业务 API。LangGraph / DeepAgents 代码在 `agents/`，作为**进程内库**由本服务调用。

**约束（一期）**

- Agent MUST 在 FastAPI 同进程内 `import` 调用（`ainvoke` / `astream` / `resume`）
- 不要默认把 Agent 拆成独立 HTTP 服务或独立进程入口
- 不要新增 `apps/agent` 可部署单元

## 布局

- `app/` — FastAPI 入口、路由、依赖注入
- `agents/textbook/` — 方式 A（按教材 / LangGraph）。只负责出题图，不解析 PDF
- `ingest/` — 离线教材入库：解析、按单元拆分、写入 pgvector。不是 HTTP 服务

## 教材入库

```bash
cd apps/api
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=postgresql://bangxue:bangxue@127.0.0.1:5432/bangxue
# 模型名和百炼密钥在仓库根目录 .env：
# QUIZ_MODEL=qwen3.7-plus
# EMBEDDING_MODEL=qwen3.7-text-embedding
# EMBEDDING_PROVIDER=bailian
python -m ingest ingest \
  --pdf /path/to/book.pdf \
  --stage 小学 --grade 一年级 --subject 数学 --edition 人教版 --term 上册
# 批量入库 book/小学/数学 下全部人教版 PDF：
python -m ingest ingest-primary-math
python -m ingest query \
  --stage 小学 --grade 一年级 --subject 数学 --edition 人教版 --term 上册 \
  --unit 第一单元
```

同一五项元数据再次执行会先删除该书旧块再写入。识别不到单元标题时命令失败且不写库。
- `agents/chat/` — 方式 B（对话 / DeepAgents）
- `agents/shared/` — PDF、判分、**教材混合检索**（BM25 + pgvector）等共用能力

## 方式 B 混合检索

对话出题在 Jev 判定信息足够后，于 **FastAPI 进程内** 对 `textbook_chunks` 做：

1. 按学段 / 年级 / 科目 / 版本 / 学期过滤  
2. **向量检索**（百炼 embedding + pgvector）与 **BM25**（`rank-bm25` + jieba）并行  
3. RRF 融合 Top-K 课文，再交给百炼出题  

无命中时追问，不静默编题。依赖见 `requirements.txt` 中的 `rank-bm25`、`jieba`。

## 本地运行

```bash
cd apps/api
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export DATABASE_URL=postgresql://bangxue:bangxue@127.0.0.1:5432/bangxue
# 出题读取仓库根目录 .env 里的 bailian_api_key；没有密钥时接口返回配置错误，不会编造题目
# Use `python -m uvicorn` so conda/base PATH cannot shadow the venv binary
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
# GET http://127.0.0.1:8000/health → {"status":"ok"}
# GET /api/textbooks/units  列出已入库小学数学人教版某册的单元
# POST /api/quizzes         按单元出题
# POST /api/grading/attempts  上传答卷并判分（multipart photos + quiz_id / questions_json）
# POST /api/grading/attempts/{id}/confirm  确认写入成绩（需头 X-Parent-Email）
# GET  /api/scores | /api/wrong-questions  按 X-Parent-Email 查询
```

## 判分与成绩（Postgres）

- **权威存储**：判分 attempt（含逐题结果、确认态、家长邮箱、`photo_paths`）在 PostgreSQL 表 `grade_attempts`；**必须**配置 `DATABASE_URL`（可与教材 / Checkpointer 共用）
- **答卷文件**：二进制仍在 `apps/api/data/uploads/`（gitignore）；库中只存相对路径如 `uploads/<uuid>.jpg`，本期不把照片写入 BYTEA
- **启动**：`bootstrap_score_store()` 建表；若存在旧版 `apps/api/data/scores.json` 会一次性导入（已存在 id 跳过）
- **Fail closed**：无 `DATABASE_URL` 或库不可达时，成绩写/读接口返回 **503**，**不会**静默回退 JSON
- **身份头**：`X-Parent-Email` 与前端本地登录邮箱一致；**非安全边界**，生产需换 JWT
- **判分超时**：百炼视觉约 60s；失败或无 `bailian_api_key` 时默认走确定性**演示回退**（响应 `demo: true`）。设 `GRADING_DISABLE_DEMO=1` 可关闭回退
- **游客演示**：前端 `demoShowcase` 夹具不入库；仅真实判分确认写入 `grade_attempts`

## LangGraph 运行时（方式 A + 判分）

- **方式 A 出题**：`agents/textbook/graph.py` 固定 StateGraph（`load_units_text` → `generate_json_questions`），由 FastAPI **进程内** `invoke`；`POST /api/quizzes` 走该图。生成节点对模型/校验失败（5xx）最多重试 3 次；题量非法等 4xx 不重试
- **判分**：`agents/shared/grading_graph.py` StateGraph（准备输入 → Vision/演示回退 → draft）；`POST /api/grading/attempts` 走该图
- **本期不挂 Checkpointer**（无跨请求 interrupt）；家长确认成绩仍为 REST，**不**走 graph interrupt
- 若将来需要 `resume`，MUST 用 Postgres Checkpointer（见 `agents/shared/checkpointer.py`），**禁止** MemorySaver 作为生产默认
- 方式 B 对话仍为 DeepAgents + Postgres Checkpointer；出题前走 `agents/shared/retrieval.hybrid_retrieve`（BM25 + 向量）
