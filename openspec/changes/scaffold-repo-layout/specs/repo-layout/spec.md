# Spec Delta

## Purpose

定义本仓库一期目录与部署边界：前端与 API 为两个可部署单元，Agent 作为 API 进程内库代码存放，避免误拆成第三个服务。

## ADDED Requirements

### Requirement: Two deployable application roots
仓库 SHALL 提供两个应用根目录：`apps/web`（家长端 SPA）与 `apps/api`（FastAPI 服务）。一期部署拓扑 MUST 仅以这两个应用为构建与发布单元（外加基础设施容器如 Postgres）。

#### Scenario: Contributor locates frontend and API
- **WHEN** 贡献者打开仓库根目录
- **THEN** 其能在 `apps/web` 找到前端工程，在 `apps/api` 找到后端工程，且不存在作为独立可部署服务的 `apps/agent`（或等价顶层 Agent 服务目录）

### Requirement: Agent code lives inside the API package tree
Agent 实现（方式 A LangGraph、方式 B DeepAgents、以及 PDF / 判分等共用能力）SHALL 存放在 `apps/api/agents/`（或其子目录）中，并由 FastAPI 进程内调用。一期 MUST NOT 将 Agent 暴露为独立 HTTP 服务或独立进程入口作为默认部署方式。

#### Scenario: API imports agents in-process
- **WHEN** FastAPI 处理出题或判分相关请求
- **THEN** 其通过进程内导入调用 `apps/api/agents` 中的图 / harness，而不是向另一个 Agent 服务发起网络调用

#### Scenario: Agent modules are separated by entry
- **WHEN** 贡献者查看 `apps/api/agents/`
- **THEN** 其能区分教材出题、对话出题与共用能力的模块边界（例如 `textbook/`、`chat/`、`shared/`）

### Requirement: Existing docs and OpenSpec roots remain stable
仓库 SHALL 继续在根目录保留 `REQUIREMENTS.md`、`docs/`、`openspec/`，本能力 MUST NOT 要求迁移这些路径作为一期脚手架的一部分。

#### Scenario: Docs stay at repo root
- **WHEN** 贡献者查找需求或 mockup
- **THEN** 其仍在仓库根的 `REQUIREMENTS.md` 与 `docs/mockups/` 找到它们

### Requirement: Phase-1 excludes third service and multi-repo split
一期脚手架 MUST NOT 引入独立 Agent 微服务仓、多 git 仓拆分，或强制的 JS monorepo 工具链（如 turbo）作为默认结构。

#### Scenario: No separate agent service scaffold
- **WHEN** 完成一期目录脚手架
- **THEN** 仓库中不包含独立 Agent 服务的 Dockerfile / compose service 作为默认交付物
