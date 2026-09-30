# score-records Specification

## Purpose

覆盖家长确认后的成绩落库、历史查询与科目筛选，以及从成绩与「我的」进入的错题本聚合查看；支持访客浏览标注为演示的样例内容，并可下钻演示成绩与错题详情。

## Requirements

### Requirement: Score history list and summary

家长打开成绩记录页时，系统 MUST 展示练习次数、平均得分率、科目筛选芯片与「最近练习」列表，版式对齐墨金纸感成绩稿（含近 7 日得分趋势区）。已登录且存在真实确认成绩时，系统 MUST 优先展示该账号数据。游客、或已登录但无可用成绩时，系统 MUST 展示与稿面一致的**演示样例**成绩内容，且 MUST 以「演示」类标识标明非云端同步结果；MUST NOT 把演示数据呈现为已登录云端同步。

#### Scenario: Guest sees demo score showcase

- **WHEN** 游客打开成绩记录页
- **THEN** 页面展示演示样例（统计、近 7 日趋势、至少两条练习卡），并有演示标识；不要求先登录才能浏览

#### Scenario: Logged-in parent sees own scores

- **WHEN** 已登录家长打开成绩记录且账号下已有确认成绩
- **THEN** 练习次数与平均得分反映其历史；列表展示最近练习条目（可无演示标识）

#### Scenario: Logged-in falls back to demo when empty

- **WHEN** 已登录家长打开成绩记录但无可展示的真实成绩
- **THEN** 回退展示演示样例并标明演示态，不留空白登录墙

#### Scenario: Filter by subject

- **WHEN** 家长在成绩页选择某一科目芯片（如「数学」）
- **THEN** 列表与汇总统计仅包含该科目的记录（真实或演示数据同源过滤）；选「全部」时恢复全部科目

#### Scenario: Empty subject filter on real data

- **WHEN** 正在展示真实成绩且某科目下没有记录
- **THEN** 展示空态引导（如去首页出题），不静默用其他科目演示数据冒充该科目真实成绩

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

### Requirement: Score list visual structure

成绩记录列表条目 MUST 包含：科目图标井、日期、科目名、出题方式标记（教材 / 对话）、范围或摘要、得分率、进度条与错题数徽标（有错题时）。近 7 日得分区在演示态 MUST 展示固定样例柱状趋势。

#### Scenario: Score card matches showcase fields

- **WHEN** 家长查看成绩列表中的一条演示或真实记录
- **THEN** 卡片上可见得分率、进度条，以及错题数徽标（若该次有错题）

### Requirement: Wrong-question card answer contrast

错题本每条展示卡 MUST 包含题干，并在有数据时并列展示「你的答案」与「正确答案」对比区（演示样例 MUST 具备该对比）。

#### Scenario: Wrong card shows answer contrast

- **WHEN** 家长查看错题本中的一条演示错题
- **THEN** 可见题干，以及错误作答与正确答案的对比展示

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
