# Design

## Context

列表级演示已在 `apps/web/src/demoShowcase.ts` + `Scores` / `WrongBook` 落地（见已归档 `demo-scores-wrongbook-ui`）。缺口：演示卡点击被 toast 拦截；`DEMO_SCORES[].items` 为空；`GradeResult` / `WrongQuestions` 只调 `fetchAttempt`，`demo-*` id 会 404。动机见 proposal.md。

本期不涉及 Checkpointer、thread_id、业务成绩表写入路径；演示数据仍纯前端，无 LLM / 对象存储密钥依赖。

## Goals / Non-Goals

**Goals:**

- 演示夹具成为「成绩列表 / 错题本 / 成绩详情 / 错题详情」的单一数据源，数字自洽。
- 复用现有路由 `/grade/result/:attemptId`、`/grade/wrong/:attemptId`，对 `demo-*` 走本地解析。
- 演示态隐藏或禁用「确认保存」，避免误导。

**Non-Goals:**

- 后端 `/scores` 对游客返回种子数据
- Postgres 演示账号 / seed migration
- 真实近 7 日趋势计算（继续用固定 spark 高度）

## Decisions

### 1. 前端夹具作权威演示源（不改 API）

- **选择**：扩充 `demoShowcase.ts`：`getDemoAttempt(id)`、由成绩 `items` 派生错题本列表；详情页 `isDemoId` 时短路 API。
- **备选**：后端 guest 返回 demo JSON → 多一层部署与缓存一致性，选型成本高。
- **理由**：与既有「游客不打 API」模式一致，改动面最小。

### 2. 导航：去掉 toast 挡路，走真实路由

```
Scores / WrongBook (demo)
  → navigate(/grade/result/demo-score-1)
  → GradeResult 读 getDemoAttempt
  → navigate(/grade/wrong/demo-score-1)
  → WrongQuestions 过滤 !correct
```

错题本条目的 `attempt_id` MUST 等于某条 `DEMO_SCORES[].id`。

### 3. 夹具形状

- 至少 2 条有错题的成绩（对应现有数学 / 英语样例），`items` 含对题 + 错题；满分样例可 `items` 全对或省略错题。
- `pendingReview` / `weekNew`：由派生列表长度计算，或写死但与列表长度一致。
- `confirmed: true` + `demo: true`，以便详情文案偏「已确认演示」；确认按钮对 demo 隐藏。

### 4. Me 页

仅可选：游客副文案改为「可先体验演示成绩与错题本」；不新增入口。

## Risks / Trade-offs

- [夹具与 UI 字段漂移] → 集中在 `demoShowcase`，详情与列表共用同一 getter。
- [用户误以为已云端同步] → 详情保留「演示」徽标；禁止确认落库。
- [真实 id 碰撞 `demo-` 前缀] → 生产 attempt id 不用该前缀（现状已约定 `isDemoId`）。

## Migration Plan

纯前端发布；无数据迁移。回滚即还原夹具与导航拦截即可。
