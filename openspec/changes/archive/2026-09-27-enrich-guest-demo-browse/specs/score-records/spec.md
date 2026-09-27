# Spec Delta

## ADDED Requirements

### Requirement: Demo fixtures include per-question items
演示态成绩样例 MUST 包含与得分一致的逐题结果（至少一题错题带题干与学生作答 / 正确答案）；错题本演示条目 MUST 能追溯到对应演示成绩的 `attempt` id，且待复习等统计 MUST 与可展示错题条数一致（或明确为展示用上限，但 MUST NOT 与空列表矛盾）。

#### Scenario: Demo score has wrong items for browse
- **WHEN** 游客在演示态打开某条有错题的成绩详情
- **THEN** 可见逐题对错摘要，并能进入该次错题列表看到至少一题的题干与答案对比

#### Scenario: Wrong-book demo links to same attempt
- **WHEN** 游客在演示错题本中查看一条样例
- **THEN** 该条的练习来源与对应演示成绩记录一致（同一 attempt 标识）

### Requirement: Demo detail must not confirm to cloud
演示态成绩详情 MUST 标明演示；家长点击确认 / 保存类操作时，系统 MUST NOT 将演示成绩写入真实账号成绩库；可提示登录后才能保存真实成绩。

#### Scenario: Guest cannot save demo attempt
- **WHEN** 游客在演示成绩详情页尝试确认保存
- **THEN** 系统拒绝写入真实成绩（提示登录或演示不可保存），演示数据仍保持本地样例

## MODIFIED Requirements

### Requirement: Open attempt detail from score list
家长点击某条成绩记录时，系统 MUST 打开该次练习的成绩详情（至少含逐题对错或等价摘要），并 MUST 能进入该次错题查看。演示态（含游客与空数据回退）下的演示记录 MUST 同样可进入详情与错题浏览，MUST NOT 仅以 toast 阻挡浏览。

#### Scenario: Tap score opens detail
- **WHEN** 家长点击「最近练习」中的一条真实记录
- **THEN** 进入该次成绩详情，可继续查看错题

#### Scenario: Guest taps demo score opens detail
- **WHEN** 游客（或演示态）点击一条演示成绩卡
- **THEN** 进入该次演示成绩详情（含逐题摘要），可继续查看该次演示错题；页面有演示标识

### Requirement: Wrong-question book aggregation
家长从「我的 · 错题本」进入时，系统 MUST 展示错题列表（待复习 / 本周新增统计、科目筛选、题干与对错答案对比区），版式对齐墨金纸感错题本稿。已登录且存在真实错题时 MUST 优先展示账号错题。游客或无可展示真实错题时，系统 MUST 展示稿面样例错题并标明演示态。演示态下点击错题卡 MUST 能进入该次练习的错题详情（或等价逐题浏览），MUST NOT 仅 toast 阻挡。底部「用错题出一卷」MUST 可见；本期 MUST NOT 要求真正完成错题组卷。

#### Scenario: Guest opens wrong-question book showcase
- **WHEN** 游客打开错题本
- **THEN** 看到演示错题列表与统计，并有演示标识；可浏览，不强制跳转登录才能看到内容

#### Scenario: Guest taps demo wrong item
- **WHEN** 游客点击一条演示错题卡
- **THEN** 进入对应演示练习的错题详情浏览，并有演示标识

#### Scenario: Logged-in opens wrong-question book
- **WHEN** 已登录家长打开错题本且历史中存在错题
- **THEN** 看到可浏览的错题列表，并可追溯到来源练习

#### Scenario: Logged-in falls back to demo when empty
- **WHEN** 已登录家长打开错题本但历史无可展示错题
- **THEN** 回退演示样例并标明演示态

#### Scenario: Demo generate-from-wrong CTA
- **WHEN** 家长点击「用错题出一卷」
- **THEN** 系统给出演示态反馈（轻提示或回首页），MUST NOT 调用出题 Agent 组卷
