# 帮学（bangxue）

面向家长的 **智能出题与判分 Agent**：教材 / 对话双入口组卷 → 可打印 PDF → 拍照判分 → 成绩与错题。产品形态为移动 Web。

本仓库重点不在「再包一层 ChatGPT」，而在把 **多 Agent 编排、工具约束、RAG 与持久化运行时** 做成可上线的进程内架构。

---

## 面试可讲的 Agent 亮点

### 1. 双 Agent 出题 + 显式 Supervisor 路由

| 能力 | 实现 | 作用 |
|------|------|------|
| **方式 A · 教材出题** | LangGraph 固定 StateGraph（`agents/textbook`） | 单元范围 → 一次结构化生成；题量与 JSON schema 受控，禁止模型自行改题量或跑 shell |
| **方式 B · 对话出题** | DeepAgents harness（`agents/chat`） | 多轮意图、工具调用 `draft_quiz`；**显式剔除**宿主机 `execute` / 写文件等危险工具 |
| **Supervisor** | LangGraph 编排图（`agents/supervisor`） | 每条家长消息先路由：`clarify` / `chat_draft` / `textbook_quiz`，避免对话栈里静默乱出题 |

对话路径可以 **handoff 到教材图**（明确单元时），确认后仍标记来源为「对话」，双入口下游统一。

### 2. Agent 进程内嵌 FastAPI（非独立微服务）

- Agent 作为 `apps/api/agents/` 库代码，由 API **同进程** `invoke` / SSE 流式返回。
- 好处：共享 Postgres / Checkpointer / 密钥与会话；少一层网络与部署单元；适合一期单机 Compose。
- 约束写进 OpenSpec：`repo-layout` / `agent-runtime` — **默认不拆独立 Agent 服务**。

### 3. Grounded 生成：混合检索 RAG

对话出题在草稿前对 `textbook_chunks` 做 **BM25 + pgvector 向量** 并行检索，RRF 融合后再给百炼出题；无命中则追问，**禁止无课文 grounding 时静默编题**。

离线 `ingest/`：PDF 切单元 → embedding → pgvector；与在线出题图解耦。

### 4. 可信运行时：Checkpoint 隔离 + 会话落库

- 生产 Checkpointer 用 **Postgres**（禁止 MemorySaver 默认）。
- 同一 `thread_id` 上 Supervisor / DeepAgents 使用不同 **`checkpoint_ns`**（`supervisor` vs `chat-agent`），避免状态串台。
- 对话草稿与练习卷权威状态在 PostgreSQL（`chat_sessions` / `quiz_papers`），多 worker / 重启可恢复；缺库 **fail-closed**。

### 5. 判分与共用工具链

- 判分：LangGraph 子图（视觉识别 → 对错草稿 → 家长确认落库），与出题共用题库 / PDF 下游。
- 结构化插图（SVG/PNG）嵌入练习与 PDF，提升小学题可读性。
- 模型侧统一走阿里云百炼（出题 / embedding / 视觉），密钥仅环境变量。

### 6. Spec 驱动交付（OpenSpec）

需求与行为写在 `openspec/specs/`；变更走 propose → apply → archive。面试时可讲：**如何用规格约束 Agent 边界**（不操作宿主机、不跳过确认、路由封闭集合等），而不是只堆 prompt。

---

## 技术栈（一期）

- **前端**：Vite + React + TypeScript（移动优先）
- **后端**：FastAPI + SSE；Agent 进程内
- **编排**：LangGraph（教材图 / Supervisor / 判分图）+ DeepAgents（对话 harness）
- **数据**：PostgreSQL + pgvector；Checkpointer / 成绩 / 会话 / 教材块同库或同连接策略
- **部署**：Docker Compose（`web` + `api` + `db`），见 [`deploy/README.md`](deploy/README.md)

## 仓库入口

| 路径 | 说明 |
|------|------|
| [apps/web](apps/web) | 家长端 SPA |
| [apps/api](apps/api) | FastAPI；`agents/` = textbook / chat / supervisor / shared |
| [REQUIREMENTS.md](REQUIREMENTS.md) | 产品需求 |
| [openspec](openspec) | 行为规格与变更归档 |
| [docs/mockups](docs/mockups) | 界面参考 |

## 本地快速开始

```bash
# API（需 DATABASE_URL、bailian_api_key，见 apps/api/README.md）
cd apps/api && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000

# Web
cd apps/web && npm i && npm run dev
```

Compose 与 **本机教材库导出导入** 流程见 [deploy/README.md](deploy/README.md)。
