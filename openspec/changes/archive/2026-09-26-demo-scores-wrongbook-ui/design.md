# Design

## Context

见 `proposal.md`。现状：`Scores.tsx` / `WrongBook.tsx` 在游客态只显示「去登录」空卡；真实列表样式未对齐 `mockup-07-scores.png` / `mockup-07b-wrongbook.png`。后端成绩 / 错题 API 已存在，但演示路径不应依赖账号与落库。

## Goals / Non-Goals

**Goals:**

- 两屏视觉与交互对齐墨金纸感稿，访客可完整浏览。
- 演示数据常量与稿面条目一致（成绩 4 次 / 均分 90% / 近 7 日柱；错题待复习 6、本周新增 2、钟表与加减等样例）。
- 有真实数据时优先真实；否则演示回退并打标。

**Non-Goals:**

- 新增近 7 日聚合 API 或改成绩存储模型。
- 错题组卷 / Agent 出题。
- JWT、云端同步策略重做。

## Decisions

### 1. 前端演示数据优先，不改后端

| 方案 | 结论 |
|------|------|
| API 返回 `demo: true` 样例 | 拒绝：多一层契约，演示改稿还要动后端 |
| **前端常量 `demoScores` / `demoWrongItems`，空或游客时注入** | **采用** |
| 仅改 CSS、游客仍登录墙 | 拒绝：违背「访客可用」 |

数据选择：

```
if (loggedIn && apiItems.length > 0) → 真实数据, demo=false
else → 演示常量, demo=true（游客或空列表）
```

### 2. 演示标识

页头使用「演示」徽标（游客也可用；已登录空回退同样显示）。不使用「已登录」冒充。已登录且有真实数据时保留现有 `GuestBadge` 逻辑（非演示）。

### 3. UI 结构映射

**成绩：** 统计双卡 → `spark-card` 近 7 日柱（CSS 条，非图表库）→ chips → `score-card`（`menu-ico` + 进度条 + `wrong-count`）。

**错题本：** 统计双卡 → chips → `wrong-card`（答案对比 `ans-box bad/ok`）→ sticky「用错题出一卷」。

样式优先复用 / 扩展 `apps/web/src/index.css` 中已有纸感 token（`--amber`、`--paper`、`--wrong`），对照 `_html/screens.html` 新增类名。

### 4. CTA「用错题出一卷」

`button` 可见；`onClick` → `alert`/轻提示「演示功能，敬请期待」或 `navigate('/')`。不调 `/api/quizzes`。

### 5. 列表点击

演示条目：可点但详情无真实 attempt 时 → 轻提示或不跳转坏链。真实条目：保持 `navigate(/grade/result/:id)` / `navigate(/grade/wrong/:attemptId)`。

## Risks / Trade-offs

- **[Risk] 家长误以为演示成绩是自己的** → Mitigation：明显「演示」徽标；文案不说「已同步」。
- **[Risk] 真实空列表被演示掩盖，难发现未确认成绩** → Mitigation：已登录空回退时副文案保留「判分确认后会出现真实成绩」。
- **[Trade-off] 近 7 日柱为静态** → 可接受；真聚合留给后续 change。

## Migration Plan

纯前端变更；无数据迁移。回滚即还原两页与 CSS。

## Open Questions

无（演示常量以两张 mockup 为准即可）。
