# Tasks

## 1. Supervisor graph skeleton

- [x] 1.1 在 `apps/api/agents/supervisor/`（或 `agents/shared/supervisor.py`）新增可 `compile()` 的 LangGraph 编排图：节点至少含 `route` / `clarify` / `chat_draft` / `textbook_quiz`，状态含家长原文、`thread_id`、路由枚举与输出 `ChatTurnResult` 等价字段；`compile` 使用 Postgres Checkpointer（与现有 chat 同源），禁止内存 Checkpointer。验证：图可 import，节点名齐全，编译参数不含 InMemory/MemorySaver 作为生产路径
- [x] 1.2 实现 `route`：输出封闭枚举 `clarify | chat_draft | textbook_quiz`（可用百炼 JSON，`enable_thinking=false`）；缺密钥或解析失败时落到 `clarify`，不得直接出题。验证：单元测试覆盖「信息不足→clarify」「自由出题意图→chat_draft」「明确单元+题量→textbook_quiz」及失败回退

## 2. Wire sub-paths

- [x] 2.1 `clarify` 节点返回中文追问（题量说明仍为 1–100），不写 draft。验证：假路由为 clarify 时响应无 `questions` 列表
- [x] 2.2 `chat_draft` 复用现有混合检索 + DeepAgents / 等价草稿逻辑（可抽取为函数供 Supervisor 调用），工具列表仍无 `execute` / 写仓库。验证：假路由为 chat_draft 且信息足够时得到可确认题目；工具名检查无宿主机执行
- [x] 2.3 `textbook_quiz` 解析年级/册次/单元后调用 `run_textbook_quiz`（或包装）；单元不存在则 clarify；成功草稿的 source 标 `chat`，meta 含 `via=textbook_quiz`。验证：注入已入库单元名可出题；伪造单元名得到追问或 4xx 风格错误文案且无编造题

## 3. Chat API integration

- [x] 3.1 将 `handle_parent_message`（及 SSE 路由）改为调用 Supervisor，保持对外状态字段兼容（`clarifying` / `draft_ready` 等）。验证：现有对话前端不改契约即可追问与出草稿
- [x] 3.2 确认首页「按教材出题」→ `POST /api/quizzes` 仍直连方式 A，不强制经 Supervisor。验证：教材路径出题一次成功且不经过 supervisor route 日志/调用（或等价断言）

## 4. End-to-end checks

- [x] 4.1 手测对话：「出点数学题」→ 追问；补全后出草稿可确认进结果/PDF
- [x] 4.2 手测对话：明确一年级某已入库单元 + 题量 → 走教材式路径，草稿可确认；成绩/元数据可见对话来源且带 `via=textbook_quiz`（或文档约定的等价字段）
- [x] 4.3 更新 `apps/api/README.md`：说明 Supervisor 挂在对话路径、双入口保留、Checkpointer 要求。验证：文档含上述三点
