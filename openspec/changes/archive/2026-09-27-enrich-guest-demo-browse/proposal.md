# Proposal

## Why

成绩记录与错题本列表已能对游客展示演示样例，但点击卡片只会 toast「演示样例」且样例缺少逐题 `items`，游客无法走完「列表 → 成绩详情 → 错题」浏览路径，选型演示仍像半截功能。

## What Changes

- 扩充前端演示夹具：成绩样例带齐逐题对错（含错题题干与作答对比），错题本样例与成绩夹具同源、统计数字自洽。
- 游客（及空数据回退演示态）点击成绩卡 / 错题卡时，**可进入现有详情页**浏览，不再被 toast 挡回；全程保留「演示」标识。
- 详情页对 `demo-*` id 优先读本地夹具，不依赖后端 attempt API；演示态下禁止「确认保存」冒充真实落库。
- 「我的」入口文案可轻量提示游客可先体验演示成绩 / 错题（不强制改导航结构）。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `score-records`: 将「游客可浏览演示列表」扩展为「游客可完整浏览演示成绩详情与错题详情」；演示夹具 MUST 含逐题数据且与错题本一致；演示态 MUST NOT 触发真实确认落库。

## Impact

- **前端**：`demoShowcase.ts`、`Scores.tsx`、`WrongBook.tsx`、`GradeResult.tsx`、`WrongQuestions.tsx`（可选 `Me.tsx` 文案）；路由复用现有 `/grade/result/:id`、`/grade/wrong/:id`。
- **FastAPI / Agent / 存储**：本期可不改；演示数据继续以前端夹具为主。
- **Non-goals**：后端种子库、游客 JWT、真实近 7 日聚合 API、错题组卷 Agent、多孩子档案、把演示数据写成已登录云端同步。
