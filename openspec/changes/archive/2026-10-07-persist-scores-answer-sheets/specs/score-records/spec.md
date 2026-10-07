# Spec Delta

## ADDED Requirements

### Requirement: Score history backed by PostgreSQL
成绩历史与错题本聚合（已登录真实数据路径）MUST 以 PostgreSQL 中的已确认 attempt 为权威数据源。同一 `DATABASE_URL` 下更换 API 实例 MUST NOT 导致已确认成绩丢失。

#### Scenario: Wrong-book aggregation from database
- **WHEN** 已登录家长打开错题本且库中有含错题的已确认成绩
- **THEN** 错题列表由数据库中的 attempt / 逐题结果聚合得出

#### Scenario: Missing database fails closed for real scores
- **WHEN** 未配置或无法连接成绩所用数据库，且家长为已登录请求真实成绩接口
- **THEN** 系统返回明确错误，MUST NOT 静默改写到本地 JSON 冒充成功落库
