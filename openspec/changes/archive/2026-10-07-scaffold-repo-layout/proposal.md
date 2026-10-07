# Proposal

## Why

仓库尚处 greenfield，需要在写业务代码前固定「前端 / 后端 / Agent」的目录边界。需求约定 Agent **进程内嵌入 FastAPI、不单独部署**，若按三个独立服务拆文件夹，会与一期部署模型冲突，并增加无谓成本。

## What Changes

- 采用 **单仓 monorepo**：顶层按 **两个可部署单元** 组织，而不是三个服务
- 新增约定目录：
  - `apps/web/`：Vite + React + TypeScript SPA（家长端）
  - `apps/api/`：FastAPI 入口、业务 API、鉴权、流式、上传
  - `apps/api/agents/`：LangGraph / DeepAgents **库代码**（方式 A / B / 共用 Tool），由 API 进程内调用
- 保留既有 `docs/`、`openspec/`、`REQUIREMENTS.md` 位置不变
- 一期 **不** 新增独立 `apps/agent` 服务、不拆多仓、不引入 pnpm/turbo monorepo 工具链（除非后续明确需要）
- 可选后续：将 `agents/` 提升为 `packages/agents` 仅当需要被多个 Python 进程复用时再做

## Capabilities

### New Capabilities

- `repo-layout`：仓库目录与部署边界约定（何处放前端 / API / Agent 源码，以及非目标）

### Modified Capabilities

- （无）当前 `openspec/specs/` 为空

## Impact

- **前端**：代码落在 `apps/web`；构建产物由 Nginx 托管
- **FastAPI**：代码落在 `apps/api`；Docker 镜像以此为上下文
- **Agent（A/B/共用）**：源码在 `apps/api/agents`，导入调用，**无独立进程 / 无独立端口**
- **数据与存储**：本 change 不改 schema；仅预留 `apps/api` 内模块位置（db、storage 等）
- **流式 / 长任务**：本 change 不实现流式；结构上由 `apps/api` 暴露 SSE，Agent 同进程执行
- **Non-goals（一期不做）**：独立 Agent 微服务、LangGraph Platform、任务队列 worker 仓、Next.js、多仓拆分
