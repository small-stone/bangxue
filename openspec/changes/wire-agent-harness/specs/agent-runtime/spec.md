# Spec Delta

## Purpose

规定按教材出题仍是一次固定的结构化生成，以及对话 harness 只能在 API 进程内使用且不能操作宿主机。

## ADDED Requirements

### Requirement: Textbook quiz is one fixed generation step
家长对已入库单元请求出题时，系统 MUST 用已配置的百炼出题模型做一次结构化生成，并在 FastAPI 进程内完成。返回的题目数量 MUST 与请求一致，题目 MUST 是 JSON，MUST NOT 把模型的思考过程当作题目。这次请求里系统 MUST NOT 让模型自行选择工具、执行命令或改写题量。未配置 `bailian_api_key` 时，接口 MUST 返回配置错误，响应中 MUST NOT 有题目。

#### Scenario: A configured request returns the requested count
- **WHEN** `.env` 中有 `bailian_api_key` 和出题模型名 `qwen3.7-plus`，且家长对已入库的一年级数学单元请求指定题量
- **THEN** 接口返回的题目由该模型一次生成，题量与请求一致，响应里没有命令执行结果

#### Scenario: Missing key does not invent questions
- **WHEN** 进程读不到 `bailian_api_key`，家长请求出题
- **THEN** 接口返回配置错误，响应中没有题目

### Requirement: Chat entry stays closed
对话出题对家长 MUST 仍不可用。点击对话入口 MUST NOT 发起出题，也 MUST NOT 调用对话 harness。

#### Scenario: Choosing chat does not generate a paper
- **WHEN** 家长在首页点击对话出题
- **THEN** 页面仍留在首页并说明对话出题尚未开放，且没有新的练习卷

### Requirement: Chat harness cannot operate the host
对话 harness MUST 只在 FastAPI 进程内构造和调用，MUST NOT 作为独立服务对外提供。它被调用时 MUST NOT 在宿主机执行 shell，也 MUST NOT 读写仓库或系统文件。它若产出题目，题目形态 MUST 与按教材出题的题目 JSON 一致，并使用同一个百炼出题模型。

#### Scenario: Invoking the harness does not touch the host
- **WHEN** API 进程调用对话 harness 处理一条出题消息
- **THEN** 调用期间没有宿主机命令执行，也没有写入仓库或系统文件；若返回题目，则为题目 JSON
