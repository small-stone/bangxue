# Spec Delta

## Purpose

覆盖家长确认后的成绩落库、历史查询与科目筛选，以及登录后从成绩与「我的」进入的错题本聚合查看。

## ADDED Requirements

### Requirement: Score history list and summary
已登录家长打开成绩记录页时，系统 MUST 展示该账号下已确认成绩的练习次数、平均得分率、科目筛选芯片与「最近练习」列表。每条记录 MUST 包含日期、科目、出题方式标记（教材 / 对话）、范围或对话摘要、正确题数/总题数与得分率。未登录时页面仍可用，但 MUST 提示登录后可同步，且 MUST NOT 展示其他账号的数据。

#### Scenario: Logged-in parent sees own scores
- **WHEN** 已登录家长打开成绩记录且账号下已有确认成绩
- **THEN** 练习次数与平均得分反映其历史；列表展示最近练习条目

#### Scenario: Filter by subject
- **WHEN** 家长在成绩页选择某一科目芯片（如「数学」）
- **THEN** 列表与汇总统计仅包含该科目的记录；选「全部」时恢复全部科目

#### Scenario: Empty subject filter
- **WHEN** 某科目下没有成绩
- **THEN** 展示空态引导（如去首页出题），不伪造演示数据冒充真实成绩

### Requirement: Open attempt detail from score list
家长点击某条成绩记录时，系统 MUST 打开该次练习的成绩详情（至少含逐题对错或等价摘要），并 MUST 能进入该次错题查看。

#### Scenario: Tap score opens detail
- **WHEN** 家长点击「最近练习」中的一条记录
- **THEN** 进入该次成绩详情，可继续查看错题

### Requirement: Wrong-question book aggregation
已登录家长从「我的 · 错题本」进入时，系统 MUST 展示该账号已确认成绩中的错题聚合列表（按练习或按题均可）。游客点击错题本时，系统 MUST 引导登录，MUST NOT 假装已有云端错题本。本期 MUST NOT 要求错题重练或自动组卷。

#### Scenario: Logged-in opens wrong-question book
- **WHEN** 已登录家长打开错题本且历史中存在错题
- **THEN** 看到可浏览的错题列表，并可追溯到来源练习

#### Scenario: Guest opens wrong-question book
- **WHEN** 游客点击「错题本」
- **THEN** 系统提示需要登录后同步错题，不展示伪造的他人错题

#### Scenario: No wrong questions yet
- **WHEN** 已登录家长打开错题本但历史无可展示错题
- **THEN** 展示空态说明，不报错
