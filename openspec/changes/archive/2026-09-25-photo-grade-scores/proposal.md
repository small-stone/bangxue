# Proposal

## Why

出题与 PDF 已可演示，但共用下游「拍照上传 → 判分 → 错题 → 成绩记录」仍是占位：首页「去上传」与成绩详情未开放，成绩页为硬编码演示数据，「我的 · 错题本」不可用。邮箱登录 UI 已落地，需要把成绩与错题挂到登录身份上，补齐 mockup-05/06/07 对应的 P0 闭环。

## What Changes

- 新增拍照上传答卷页（对齐 `mockup-05-upload.png`）：多页照片、相册选择、「开始判分」
- 新增判分结果页（对齐 `mockup-06-result.png`）：得分环、逐题对错、「查看错题」「成绩记录」入口
- 新增单次练习的错题详情页；「我的 · 错题本」展示已登录账号下的错题聚合列表（不做重练）
- 成绩记录页（对齐 `mockup-07-scores.png`）改为读真实落库数据：练习次数、平均得分、科目筛选、最近练习；点击进入该次成绩/错题
- FastAPI 增加答卷上传与判分、确认写入成绩、按家长身份查询成绩/错题的 API；判分走百炼多模态（缺 key 时有可演示的确定性回退）
- 家长确认后才写入成绩；登录态用现有本地会话邮箱作为身份键（本期不上 JWT）
- **Non-goals**：错题重练 / 学习报告（P1）；Jev 判分判断（仍属 `add-jev-decisions`）；Postgres/JWT/OAuth；独立判分 worker；多孩子档案；游客跨设备同步

## Capabilities

### New Capabilities

- `photo-grading`: 答卷拍照上传、智能判分、判分结果与单次错题查看（含家长确认）
- `score-records`: 成绩落库、历史查询、科目筛选，以及登录后的错题本聚合列表

### Modified Capabilities

- （无）本期不改 `chat-generation` / `primary-math-quiz` / `flow-judgment` 等已有 main specs 的出题行为

## Impact

- **前端**：新增 Upload / GradeResult / WrongQuestions 等路由与页面；改 `Home` 待办入口、`Scores`、`Me` 错题本；对齐 `docs/mockups/alt-ink-amber`
- **FastAPI**：上传（本地磁盘）、判分（`agents/shared`）、成绩/错题读写；长任务用同步请求 + 前端进度态（一期不引入 SSE worker）
- **Agent**：共用判分子模块（非独立服务）；不改方式 A/B 出题图
- **数据与存储**：进程内或本地文件成绩库，按登录邮箱隔离；答卷图存本地磁盘。不上 Postgres
- **外部依赖**：`bailian_api_key` + 百炼多模态；密钥不进仓库
- **超时**：判分请求超时与前端「判分中」态；失败可重试或提示重拍，不静默写成绩
