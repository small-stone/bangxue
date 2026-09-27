# Spec Delta

## MODIFIED Requirements

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

## REMOVED Requirements

### Requirement: No textbook RAG required in phase one
**Reason**: 方式 B 改为强制教材混合检索 grounding，与「一期可不绑 RAG」冲突。  
**Migration**: 以「Draft questions after enough intent」的检索后生成行为及 `textbook-retrieval` 为准；自由描述仍允许，但起草前须能解析检索范围并命中课文。

## ADDED Requirements

### Requirement: Chat draft uses hybrid textbook retrieval
方式 B 在进入题目草稿前 MUST 调用教材混合检索（BM25 + 向量融合）。练习元数据 MUST 记录检索所用的年级 / 科目等范围摘要（若有），来源仍标记为「对话」。

#### Scenario: Grounded chat quiz keeps chat source
- **WHEN** 家长完成一次经检索 grounding 的对话出题并确认
- **THEN** 练习来源仍为对话，且元数据可追溯所用教材范围摘要
