# Design

## Context

见 `proposal.md`。当前仓库仅有需求、mockup 与 OpenSpec；尚无 `apps/`。约束来自 REQUIREMENTS / `openspec/config.yaml`：Agent 嵌入 FastAPI，部署为静态前端 + FastAPI，不是三服务。

本 change 只定目录与边界；不实现业务 API、不接 LLM、不建 Checkpointer 表。

## Goals / Non-Goals

**Goals:**

- 固定「两个可部署应用 + Agent 库目录」的树形结构
- 在 `agents/` 内预留 A / B / shared 边界，方便后续对照学习两套 Agent
- 脚手架可空壳可跑最小 hello（可选），但不阻塞后续业务 change

**Non-Goals:**

- 实现出题 / 对话 / 判分 / PDF
- Docker Compose 完整上线栈（可在后续 change；本设计只约定镜像上下文应对准 `apps/*`）
- 将 Agent 拆成独立服务或 LangGraph Platform
- pnpm workspace / turborepo / Python uv workspace 的复杂多包发布

## Decisions

### 1. 顶层用 `apps/web` + `apps/api`，不用三顶层服务

- **选择**：两个应用根，对应一期两个进程（Nginx 静态 + uvicorn）
- **备选 A**：`frontend/` + `backend/` — 亦可，但 `apps/*` 更明确「可部署应用」
- **备选 B**：`web/` + `api/` + `agent/` — **拒绝**：暗示第三服务，与部署约束冲突
- **备选 C**：多仓（web / api / agents 各一 repo）— **拒绝**：一期过重

### 2. Agent 放在 `apps/api/agents/`，不放 `packages/agents`

- **选择**：同一 Python 工程内子包，FastAPI `import agents...`
- **理由**：一期只有一个 Python 运行时；少一层包管理
- **何时再拆 `packages/agents`**：出现第二个需要复用同一 Agent 代码的进程（如 worker）时

建议子结构：

```
apps/api/
  app/                 # FastAPI：routes, deps, main
    main.py
    api/
  agents/
    textbook/          # 方式 A：LangGraph
    chat/              # 方式 B：DeepAgents
    shared/            # PDF、判分 Tool / 子图
  pyproject.toml       # 或 requirements.txt
  README.md
apps/web/
  package.json
  src/
  README.md
```

### 3. 依赖与导入边界

```
浏览器 → Nginx(apps/web build) → /api → FastAPI(apps/api)
                                      └─ agents.*(同进程)
```

- Checkpointer / 业务 DB / 对象存储客户端：由 `app/` 配置并注入；`agents/` 不自己读散落的全局密钥文件
- 密钥：环境变量（`.env` 不入库）

### 4. 与 docs / openspec 的关系

- 产品意图：`REQUIREMENTS.md`
- 界面参考：`docs/mockups/`
- 规格与变更：`openspec/`
- 代码：`apps/`

三者并存；脚手架不搬迁。

## Risks / Trade-offs

- **[Risk] 新人仍想再建 `apps/agent` 服务** → Mitigation：README 与本 spec 明确「Agent = 库」；compose 不提供 agent service
- **[Risk] `agents/` 与 `app/` 循环依赖** → Mitigation：约定 `agents` 不导入 `app.api` 路由层；共享类型放 `agents/shared` 或 `app/domain`
- **[Trade-off] Agent 与 API 同仓同镜像** → 部署简单，但扩缩绑定；二期若拆 worker，再抽 `packages/agents`

## Migration Plan

- Greenfield：直接创建空目录与最小 README / 占位模块即可
- 无运行中系统，无需数据迁移或回滚

## Open Questions

- Python 包管理一期用 `uv` + `pyproject.toml` 还是纯 `requirements.txt`（不影响目录边界，实现时选定）
- `apps/web` 是否一期就接 Tailwind 脚手架（建议是，但不改变 layout spec）
