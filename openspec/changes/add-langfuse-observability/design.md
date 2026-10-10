# Design

## Context

见 `proposal.md` — Why。现状：百炼调用经 `agents/shared/bailian.build_chat_model`（LangChain `ChatOpenAI`）以及部分 `OpenAI` SDK 直调（对话补洞、判分 vision、ingest embedding）。无统一 trace。Agent 仍全部在 FastAPI 进程内。

## Goals / Non-Goals

**Goals:**

- 配置 `LANGFUSE_PUBLIC_KEY` + `LANGFUSE_SECRET_KEY`（可选 `LANGFUSE_HOST`）后，教材出题与对话/Supervisor 主路径的聊天调用可在 Langfuse UI 查询。
- 未配置或上报失败：家长路径不受影响（fail-open）。
- 密钥只进环境变量 / `.env.example` 占位。

**Non-Goals:**

- Compose 内部署 Langfuse。
- 改 SSE / 题目 JSON / 白名单语义。
- 强制 ingest embedding 全量上屏（可作为后续增强）。
- 独立观测微服务。

## Decisions

1. **SDK 选型**  
   - 使用官方 `langfuse` Python SDK + LangChain `CallbackHandler`（或当前 SDK 推荐的等价集成），挂在 `build_chat_model` 的默认 callbacks，使 textbook `.stream` / `.invoke`、Supervisor `invoke`、chat harness 经 LangChain 的调用自动带上。  
   - 对 `OpenAI` SDK 直调（判分 vision 等）：本期 **尽力** 用 `langfuse` 装饰/显式 span；若成本高则 design 允许判分为「SHOULD」，tasks 标为可选，优先保证 ChatOpenAI 路径。

2. **启用条件**  
   - 仅当 public + secret 均非空时初始化客户端；否则 `get_langfuse_handler()` 返回 `None`，调用方不传 callbacks。  
   - `LANGFUSE_HOST` 默认云端；自建则填 Base URL。

3. **关联元数据**  
   - tags / metadata：`path=textbook|chat|supervisor|grading`、`thread_id`（若有）、`grade/subject`（若有）。  
   - 不新增业务表存 trace id。

4. **流式出题**  
   - textbook `.stream` 仍由同一 model + callbacks 驱动；flush 在请求结束时调用 SDK flush（短超时），失败只打日志。

5. **隐私**  
   - Trace 会含 prompt 中的课文片段（与现网发给百炼的内容同类）。文档注明：开启观测即同意将模型输入输出发往配置的 Langfuse Host。一期不做字段级 redact。

6. **备选放弃**  
   - 仅 OpenTelemetry 通用导出：与「接 Langfuse」目标不符，不采用。  
   - 每条路由手写 HTTP 打点：维护成本高，仅作 SDK 缺口补洞。

## Risks / Trade-offs

- [课文进第三方] → 文档说明；可用自建 Host；默认关闭。  
- [上报拖慢请求] → 异步/结束时 flush；失败吞掉。  
- [SDK 与 LangChain 版本摩擦] → 锁兼容版本；单测用假 handler 验证「有/无密钥」分支。  
- [直调 OpenAI 路径漏报] → 主路径保证 ChatOpenAI；vision 可选。

## Migration Plan

1. 加依赖与 shared 初始化；`.env.example` + deploy README。  
2. 本地/VPS 填密钥验证 textbook + chat 各一条 trace。  
3. 回滚：去掉密钥即关闭；或撤依赖与 callback 注入。

## Open Questions

- （无）一期默认云 Host + 可选自建 URL；Compose 不绑 Langfuse 服务。
