# Spec Delta

## Purpose

用 Docker Compose 在单机上构建并运行家长端静态 Web、内嵌 Agent 的 FastAPI，以及带向量扩展的 PostgreSQL，便于海外小 VPS 低成本部署演示环境。

## ADDED Requirements

### Requirement: Compose stack exposes web, api, and postgres

仓库 MUST 提供可构建的 Docker Compose 编排，至少包含三个服务：静态家长端 Web、FastAPI API（进程内 Agent）、PostgreSQL（启用 pgvector）。系统 MUST NOT 将 Agent 作为独立 compose 服务或独立镜像默认交付。

#### Scenario: Stack starts with three core services

- **WHEN** 运维在已配置环境变量的机器上执行 compose 启动
- **THEN** Web、API、Postgres 三个服务均可变为健康/可访问状态，且不存在名为独立 Agent 的第四业务服务

### Requirement: Same-origin API via reverse proxy

生产 Web 入口 MUST 将浏览器对 `/api` 的请求反代到 API 服务，使家长端继续使用相对路径 `/api/...`（与现网前端一致），MUST NOT 强制家长改跨域绝对 API 域名才能完成出题/对话/判分。

#### Scenario: Parent loads site and calls api paths

- **WHEN** 家长打开 compose 对外暴露的 Web 入口并触发出题或对话请求
- **THEN** 请求以同源 `/api/...` 到达 API，功能路径可用（至少健康检查与既有 `/api` 路由可达）

### Requirement: Durable database and upload volumes

Postgres 数据 MUST 落在持久化卷上，进程重启后业务库不丢。答卷等本地上传文件 MUST 挂载到 API 可写持久目录（或等价 volume），MUST NOT 仅写在无卷容器可写层作为生产默认。

#### Scenario: Restart keeps database

- **WHEN** compose 栈重启后家长再次查询成绩或会话相关依赖库的数据
- **THEN** 此前写入 PostgreSQL 的数据仍可读取（卷未删除前提下）

### Requirement: Secrets via environment, not images

构建产物与镜像 MUST NOT 烘焙 `bailian_api_key`、`DATABASE_URL` 密码等密钥。运行时 MUST 通过环境变量或未入库的 env 文件注入；缺少关键密钥时，既有 fail-closed 行为（如出题/成绩）MUST 保持。

#### Scenario: Image build without secrets

- **WHEN** 在无密钥的干净环境中构建 Web 与 API 镜像
- **THEN** 构建成功，且镜像层中不包含用于生产的 LLM/数据库密钥明文

### Requirement: Long-running api routes survive proxy timeouts

对话 SSE、出题与判分等长请求 MUST 在反向代理上配置足够的读/发送超时，MUST NOT 因默认短超时在正常出题窗口内被代理切断（建议级数值见设计文档，规格要求「可完成一次常规出题/对话回合而不被代理默认超时打断」）。

#### Scenario: Chat SSE is not cut by default short proxy timeout

- **WHEN** 家长在对话出题中发送一条需模型处理的消息（常规耗时）
- **THEN** 在代理与 API 均健康时，流式或最终响应可完成，而不是因代理默认数十秒超时中断
