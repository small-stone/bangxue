# Proposal

## Why

一年级出题和教材向量现在还指向 OpenAI 或本地 bge，而本机 `.env` 里已经有百炼密钥 `bailian_api_key`。出题和入库应改用百炼上指定的两个模型，否则有密钥也出不了题，已入库的 512 维向量也无法和新模型对齐。

## What Changes

- 在现有 `.env` 中写入出题模型名 `qwen3.7-plus` 和向量模型名 `qwen3.7-text-embedding`。不改动、不提交已有的 `bailian_api_key`。
- 方式 A 出题改为用该密钥调用百炼兼容接口上的 `qwen3.7-plus`。没有密钥时仍返回配置错误，不编造题目。
- 教材 embedding 改为 `qwen3.7-text-embedding`（默认 1024 维）。**BREAKING**：现有 `textbook_chunks.embedding` 是本地 bge 的 512 维，必须删表后按同一入库命令重写已入库的一年级上册，不能混用旧向量。
- FastAPI 与入库命令启动时读取仓库根目录 `.env`。当前进程不会自动加载该文件。

## Capabilities

### New Capabilities

- `bailian-models`: 出题与向量都使用百炼；模型名来自 `.env`，密钥沿用已有的 `bailian_api_key`。

### Modified Capabilities

- `textbook-ingest`: 入库写入的向量改为百炼 `qwen3.7-text-embedding`。单元切分、一次一本、同书覆盖、代码位置和 PDF 不入库的要求不变。

## Impact

- 前端：不改页面。失败文案仍由接口返回，家长看到的是未配置百炼密钥，而不是未配置 OpenAI。
- FastAPI：`POST /api/quizzes` 在进程内调用百炼，不新开服务，本变更仍不用 SSE。单次出题是一次同步请求，超时沿用现有长请求约定。
- Agent A：`agents/textbook` 的生成调用换模型。Agent B（对话）不在本期。
- 数据：删掉并重建 `textbook_chunks` 的向量列后，重新入库人教版数学一年级上册。其他册次尚未入库，不受影响。
- 与进行中的 `add-grade1-quiz-screens` 冲突处：该变更设计里写的是 `OPENAI_API_KEY`。本变更改为百炼，出题接口字段不变。

## Non-goals

- 不改首页、选题流程、登录、对话出题、拍照判分、Jev。
- 不把 API Key 写入仓库或 OpenSpec 文档。
- 不引入任务队列或独立 Agent 服务。
