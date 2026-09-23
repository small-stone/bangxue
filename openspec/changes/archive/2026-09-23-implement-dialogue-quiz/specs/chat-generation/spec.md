# Spec Delta

## Purpose

让家长从首页进入「对话出题」，用自然语言多轮说明需求，由 DeepAgents harness 追问并生成题目，确认后进入与方式 A 共用的练习结果与 PDF。

## ADDED Requirements

### Requirement: Chat entry is available
首页 MUST 提供可进入的「对话出题」入口。家长进入后 MUST 看到可发送消息的对话界面，MUST NOT 再显示「对话出题尚未开放」。

#### Scenario: Parent opens chat from home
- **WHEN** 家长在首页选择「对话出题」
- **THEN** 进入对话页且可以输入第一条需求

### Requirement: Multi-turn clarification before draft
方式 B MUST 支持多轮对话。当出题所需信息不足时，系统 MUST 向家长追问（例如题量、知识点或科目），且 MUST NOT 在信息不足时生成练习题列表。

#### Scenario: Incomplete request gets a follow-up
- **WHEN** 家长只说「出点数学题」一类缺少题量或具体知识点的话
- **THEN** 助手追问所缺信息，页面不出现完整题目列表

#### Scenario: Parent can refine after a reply
- **WHEN** 家长在追问后补充题量或知识点
- **THEN** 同一会话继续，系统基于补充后的意图推进

### Requirement: Draft questions after enough intent
当信息足够时，系统 MUST 使用百炼出题模型（默认 `qwen3.7-plus`，密钥 `bailian_api_key`）生成题目列表，并展示给家长确认。题目正文 MUST NOT 由 Jev 生成。缺密钥时 MUST 返回明确错误，MUST NOT 编造题目。

#### Scenario: Enough detail yields a draft list
- **WHEN** 家长说明科目或知识点、题量等已足够出题的信息
- **THEN** 对话中出现可确认的题目列表（或等价确认视图）

#### Scenario: Missing Bailian key
- **WHEN** 服务未配置 `bailian_api_key` 却需要出题
- **THEN** 接口返回配置错误说明，不返回伪造题目

### Requirement: Confirm then shared result and PDF
家长确认题目后，系统 MUST 将本次练习标记为来源「对话」，保存对话主题摘要（或等价元数据），并进入与方式 A 共用的结果展示与练习 PDF 下载。确认前 MUST NOT 把该次练习当作已定稿卷对外提供最终 PDF。

#### Scenario: Confirm opens shared result
- **WHEN** 家长确认当前题目列表
- **THEN** 可查看结果页题目，并可下载与题干一致的练习 PDF

#### Scenario: Source is chat
- **WHEN** 家长完成一次对话出题并确认
- **THEN** 该练习元数据标明来源为对话，并带有对话主题摘要

### Requirement: No textbook RAG required in phase one
一期对话出题 MUST NOT 强制绑定教材单元或向量检索。若家长提到年级或科目，系统 MUST 将其作为生成约束写入练习元数据。

#### Scenario: Free-form request without unit selection
- **WHEN** 家长未选择任何教材单元，仅用对话描述「三年级口算 10 道」
- **THEN** 系统仍可出题，且不要求先走教材选题页

### Requirement: Agent stays in-process
方式 B 的 DeepAgents harness MUST 在 FastAPI 进程内调用。系统 MUST NOT 为此部署独立 Agent 服务。Harness MUST NOT 向家长会话暴露宿主机 shell 或任意写文件能力。

#### Scenario: Chat request is handled by API process
- **WHEN** 家长发送对话消息触发出题或追问
- **THEN** 处理发生在现有 API 进程内，家长无感知独立 Agent 服务
