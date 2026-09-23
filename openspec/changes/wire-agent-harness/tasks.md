# Tasks

## 1. 依赖与共用模型

- [ ] 1.1 在 `apps/api/requirements.txt` 加入 LangChain、LangGraph、DeepAgents，并装进现有 API 环境。验证：三个包都能 import，且没有新增独立 Agent 进程或任务队列
- [ ] 1.2 在 `agents/shared` 增加百炼对话模型工厂，读取已有的 `bailian_api_key`、`QUIZ_MODEL`（默认 `qwen3.7-plus`）和 `BAILIAN_BASE_URL`，关闭思考。缺密钥时给出配置错误，不打印密钥。验证：有密钥时模型名是 `qwen3.7-plus`；去掉密钥时工厂失败且输出里没有密钥

## 2. 方式 A 固定图

- [ ] 2.1 让 `build_graph()` 返回 `START → generate → END` 的图，`compile()` 不传 checkpointer。`generate` 节点用共用模型做一次 JSON 出题，不注册工具。验证：图的节点只有出题这一步，且源码与编译参数里都没有 Checkpointer
- [ ] 2.2 `generate_questions` 改为调用这张图，题量、空题干和缺密钥的校验保持在图外。验证：假模型或桩模型在 10/15/20/30 以外被拒绝；缺 `bailian_api_key` 时没有题目
- [ ] 2.3 用真实 `qwen3.7-plus` 对已入库的一个一年级单元请求 `POST /api/quizzes`，题量 10。验证：返回 10 道题干，响应里没有思考过程被当成题目，也没有命令执行结果

## 3. 方式 B harness

- [ ] 3.1 `agents/chat.build_agent()` 用 `create_deep_agent` 和共用模型，只挂一个复用 `generate_questions` 的出题工具，不传入宿主机 shell 后端。若默认工具里有宿主机执行，用中间件去掉。验证：工具列表里没有 `execute`，也没有指向仓库或系统路径的写文件工具
- [ ] 3.2 在进程内用一条出题消息调用 harness，不新增 HTTP 路由。验证：调用期间没有宿主机命令，工作区没有新文件；若返回题目，则为题目 JSON。首页对话入口仍提示尚未开放，且不触发这次调用
