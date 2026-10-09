# Spec Delta

## MODIFIED Requirements

### Requirement: Textbook quiz is one fixed generation step

家长对已入库单元请求出题时，系统 MUST 用已配置的百炼出题模型做结构化生成，并在 FastAPI 进程内完成。传输 MAY 使用 SSE 流式推送进度与题目增量，但语义上仍是一次出题请求：最终题目数量 MUST 与请求一致，题目 MUST 是 JSON，MUST NOT 把模型的思考过程当作题目。这次请求里系统 MUST NOT 让模型自行选择工具、执行命令或改写题量。未配置 `bailian_api_key` 时，接口 MUST 返回配置错误（含流式错误事件），响应中 MUST NOT 有题目。

#### Scenario: A configured request returns the requested count

- **WHEN** `.env` 中有 `bailian_api_key` 和出题模型名 `qwen3.7-plus`，且家长对已入库的一年级数学单元请求指定题量
- **THEN** 接口（含流式完成事件）返回的题目由该模型生成，题量与请求一致，响应里没有命令执行结果

#### Scenario: Missing key does not invent questions

- **WHEN** 进程读不到 `bailian_api_key`，家长请求出题
- **THEN** 接口返回配置错误（或流式错误事件），响应中没有题目
