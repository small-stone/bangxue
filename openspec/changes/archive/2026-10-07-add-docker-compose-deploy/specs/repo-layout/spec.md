# Spec Delta

## ADDED Requirements

### Requirement: Deploy artifacts target apps web and api only

仓库 MAY 在根目录或约定路径提供 Dockerfile 与 Compose 文件，但其构建上下文 MUST 对准 `apps/web` 与 `apps/api`（外加 Postgres 等基础设施镜像）。一期 MUST NOT 新增以 Agent 为唯一入口的可部署单元目录或默认 compose service。

#### Scenario: Compose references two app contexts

- **WHEN** 贡献者查看默认 docker-compose 服务定义
- **THEN** 业务应用服务仅对应家长端 Web 与 FastAPI API，Agent 代码仍由 API 镜像内导入，无独立 `agent` 服务
