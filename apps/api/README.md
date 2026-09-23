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
python -m ingest query \
  --stage 小学 --grade 一年级 --subject 数学 --edition 人教版 --term 上册 \
  --unit 第一单元
```

同一五项元数据再次执行会先删除该书旧块再写入。识别不到单元标题时命令失败且不写库。
- `agents/chat/` — 方式 B（对话 / DeepAgents）
- `agents/shared/` — PDF、判分等共用能力

## 本地运行

```bash
cd apps/api
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export DATABASE_URL=postgresql://bangxue:bangxue@127.0.0.1:5432/bangxue
# 出题读取仓库根目录 .env 里的 bailian_api_key；没有密钥时接口返回配置错误，不会编造题目
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
# GET http://127.0.0.1:8000/health → {"status":"ok"}
# GET /api/textbooks/units  列出一年级数学人教版上册单元
# POST /api/quizzes         按单元出题
```
