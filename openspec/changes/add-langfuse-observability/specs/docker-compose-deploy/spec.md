# Spec Delta

## ADDED Requirements

### Requirement: Deploy docs document optional Langfuse env
部署文档与 `.env.example` MUST 说明可选的 Langfuse 环境变量（公钥、密钥、可选 Host），以及「未配置则跳过观测」的行为。一期 Compose 栈 MUST NOT 把自建 Langfuse 服务列为必选依赖；运营者 MAY 使用云托管或外部自建实例。

#### Scenario: Example env mentions Langfuse without requiring the service
- **WHEN** 阅读 `.env.example` 与部署 README 中的环境变量说明
- **THEN** 能看到 Langfuse 相关可选变量，且默认 `docker compose` 服务列表仍仅为 web / api / db（无强制 langfuse 服务）
