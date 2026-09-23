# bailian-models Specification

## Purpose

让一年级按教材出题和教材向量都走百炼：模型名写在环境文件里，密钥沿用已有的百炼密钥，没有密钥时不出假题。

## Requirements

### Requirement: Env file names both Bailian models
仓库根目录的 `.env` MUST 在保留已有 `bailian_api_key` 的同时，写入出题模型名 `qwen3.7-plus` 与向量模型名 `qwen3.7-text-embedding`。该文件 MUST NOT 被 git 跟踪。文档与规格 MUST NOT 抄写密钥本身。

#### Scenario: Model names are present beside the existing key
- **WHEN** 查看本机 `.env` 的变量名
- **THEN** 能看到 `bailian_api_key`，以及分别指向 `qwen3.7-plus` 和 `qwen3.7-text-embedding` 的两个模型名变量，且 `git status` 不列出该文件

### Requirement: Grade-one quiz uses qwen3.7-plus
方式 A 出题 MUST 使用 `.env` 中的 `bailian_api_key` 调用百炼上的 `qwen3.7-plus`，并在 FastAPI 进程内完成。返回给家长的 MUST 是题目 JSON，MUST NOT 把模型的思考过程当作题目。未配置 `bailian_api_key` 时，接口 MUST 返回配置错误，MUST NOT 编造题目。

#### Scenario: Configured key produces questions from the unit
- **WHEN** `.env` 中有 `bailian_api_key` 和出题模型名 `qwen3.7-plus`，且家长对已入库的一年级数学单元请求出题
- **THEN** 接口返回的题目由 `qwen3.7-plus` 生成，题量与请求一致

#### Scenario: Missing key does not invent questions
- **WHEN** 进程读不到 `bailian_api_key`
- **THEN** 出题接口返回配置错误，响应中没有题目

### Requirement: Embeddings use qwen3.7-text-embedding
新写入的教材向量 MUST 由百炼模型 `qwen3.7-text-embedding` 生成，默认维度为 1024。系统 MUST NOT 把该模型的向量写入仍为其他维度的旧列。

#### Scenario: A new embedding matches the configured model width
- **WHEN** 用配置好的百炼向量模型为一段课文计算 embedding
- **THEN** 得到的向量维度为 1024，且调用的模型名是 `qwen3.7-text-embedding`
