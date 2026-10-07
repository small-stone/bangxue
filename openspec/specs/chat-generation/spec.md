# chat-generation Specification

## Purpose

让家长从首页进入「对话出题」，用自然语言多轮说明需求，由 DeepAgents harness 追问并基于教材混合检索 grounding 生成题目，确认后进入与方式 A 共用的练习结果与 PDF。

## Requirements

### Requirement: Chat entry is available
首页 MUST 提供可进入的「对话出题」入口。家长进入后 MUST 看到可发送消息的对话界面，MUST NOT 再显示「对话出题尚未开放」。

#### Scenario: Parent opens chat from home
- **WHEN** 家长在首页选择「对话出题」
- **THEN** 进入对话页且可以输入第一条需求

### Requirement: Multi-turn clarification before draft
方式 B MUST 支持多轮对话。当出题所需信息不足时，系统 MUST 向家长追问（例如题量、知识点或科目），且 MUST NOT 在信息不足时生成练习题列表。追问题量时 MUST NOT 暗示只能选择 10、15、20 或 30。对话消息在判定是否出草稿之前 MUST 经 Supervisor 路由（见 `request-supervisor`）。

#### Scenario: Incomplete request gets a follow-up
- **WHEN** 家长只说「出点数学题」一类缺少题量或具体知识点的话
- **THEN** 助手追问所缺信息，页面不出现完整题目列表

#### Scenario: Parent can refine after a reply
- **WHEN** 家长在追问后补充题量或知识点
- **THEN** 同一会话继续，系统基于补充后的意图推进

#### Scenario: Follow-up mentions flexible count
- **WHEN** 系统因缺少题量而追问
- **THEN** 追问文案说明可指定 1–100 道，不限定四档

#### Scenario: Routed clarify does not invent a draft
- **WHEN** Supervisor 将本轮路由为追问
- **THEN** 响应中没有可确认的完整题目列表

### Requirement: Chat path may hand off to textbook generation
当 Supervisor 判定应走教材式出题时，对话会话 MUST 能得到与方式 A 同类的题目 JSON（可确认后进入共用结果与 PDF），并 MUST 在元数据中标明来源仍为「对话」或明确标注教材式生成（实现二选一，但 MUST NOT 伪装成家长未发起的按教材 UI 会话）。

#### Scenario: Unit-named request yields confirmable questions
- **WHEN** 家长在对话中给出足够的年级/册次/单元与题量，且 Supervisor 选择教材式出题
- **THEN** 对话中出现可确认的题目列表（或等价确认视图），确认后可进入共用结果与 PDF

### Requirement: Assistant reply typewriter
对话出题页的助手文字回复 MUST 以打字机方式逐步出现（增量追加到同一气泡），MUST NOT 仅在整段生成结束后一次性替换为完整回复而不展示中间过程。出题等待期间 MAY 显示进度文案；进度文案本身不要求打字机。

#### Scenario: Clarifying reply types out
- **WHEN** 系统判定信息不足并返回追问文案
- **THEN** 家长看到助手气泡中的文字逐步出现，而不是只看到进度后突然整段出现

#### Scenario: Draft-ready reply types out
- **WHEN** 系统已生成题目草稿并返回确认提示文案
- **THEN** 该确认提示文案以打字机方式出现；题目预览可在文案开始展示之后或完成时出现

### Requirement: Arbitrary count up to 100
方式 B 出题题量 MUST 接受家长给出的 1 至 100（含）的任意正整数，并按该数量生成题目。系统 MUST NOT 再将题量强制收成仅 10、15、20、30 四档。

#### Scenario: Parent asks for twelve
- **WHEN** 家长说「出 12 道…」且其他出题信息已足够
- **THEN** 草稿恰好包含 12 道题

#### Scenario: Parent asks for one hundred
- **WHEN** 家长要求 100 道且信息足够
- **THEN** 草稿恰好包含 100 道题

### Requirement: Count over 100 is rejected
当家长要求的题量大于 100 时，系统 MUST NOT 静默截断为 100 并出题；MUST 追问或明确提示上限为 100 道。

#### Scenario: Parent asks for one hundred and one
- **WHEN** 家长说「出 101 道…」
- **THEN** 不生成 101 道题草稿，而是提示题量最多 100 道（或请其改到上限内）

### Requirement: Draft questions after enough intent
当信息足够时，系统 MUST 先对教材库做混合检索得到相关课文，再使用百炼出题模型（默认 `qwen3.7-plus`，密钥 `bailian_api_key`）基于检索上下文生成题目列表，并展示给家长确认。题目正文 MUST NOT 由 Jev 生成。缺密钥时 MUST 返回明确错误，MUST NOT 编造题目。生成提示 MUST 要求题目紧扣所附课文，不要使用课文外知识点。

#### Scenario: Enough detail yields a grounded draft list
- **WHEN** 家长说明科目或知识点、题量等已足够，且检索返回可用课文块
- **THEN** 对话中出现可确认的题目列表（或等价确认视图），且出题调用附带了检索课文

#### Scenario: Missing Bailian key
- **WHEN** 服务未配置 `bailian_api_key` 却需要出题
- **THEN** 接口返回配置错误说明，不返回伪造题目

#### Scenario: Retrieval miss blocks free-form invent
- **WHEN** 信息看似足够但混合检索无命中可用课文
- **THEN** 系统追问或提示（如确认年级册次 / 换表述），MUST NOT 静默用无检索上下文的纯意图编题冒充教材题

### Requirement: Confirm then shared result and PDF
家长确认题目后，系统 MUST 将本次练习标记为来源「对话」，保存对话主题摘要（或等价元数据），并进入与方式 A 共用的结果展示与练习 PDF 下载。确认前 MUST NOT 把该次练习当作已定稿卷对外提供最终 PDF。

#### Scenario: Confirm opens shared result
- **WHEN** 家长确认当前题目列表
- **THEN** 可查看结果页题目，并可下载与题干一致的练习 PDF

#### Scenario: Source is chat
- **WHEN** 家长完成一次对话出题并确认
- **THEN** 该练习元数据标明来源为对话，并带有对话主题摘要

### Requirement: Chat draft uses hybrid textbook retrieval
方式 B 在进入题目草稿前 MUST 调用教材混合检索（BM25 + 向量融合）。练习元数据 MUST 记录检索所用的年级 / 科目等范围摘要（若有），来源仍标记为「对话」。

#### Scenario: Grounded chat quiz keeps chat source
- **WHEN** 家长完成一次经检索 grounding 的对话出题并确认
- **THEN** 练习来源仍为对话，且元数据可追溯所用教材范围摘要

### Requirement: Agent stays in-process
方式 B 的 DeepAgents harness MUST 在 FastAPI 进程内调用。系统 MUST NOT 为此部署独立 Agent 服务。Harness MUST NOT 向家长会话暴露宿主机 shell 或任意写文件能力。

#### Scenario: Chat request is handled by API process
- **WHEN** 家长发送对话消息触发出题或追问
- **THEN** 处理发生在现有 API 进程内，家长无感知独立 Agent 服务
