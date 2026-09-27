# Tasks

## 1. Demo fixtures

- [x] 1.1 扩充 `demoShowcase.ts`：为至少两条有错题的 `DEMO_SCORES` 填入与得分一致的 `items`（含错题题干 / 学生作答 / 正确答案），并导出 `getDemoAttempt(id)`；验证用脚本或手动断言 `getDemoAttempt('demo-score-1')` 非空且 `correct/total` 与 items 一致
- [x] 1.2 由成绩夹具派生 `DEMO_WRONG_ITEMS`（或同步手写并断言同源 `attempt_id`），使 `pendingReview` / `weekNew` 与列表不矛盾；验证错题本条目的 `attempt_id` 均能 `getDemoAttempt` 命中

## 2. Navigation and detail pages

- [x] 2.1 修改 `Scores.tsx`：演示卡点击 `navigate(/grade/result/:id)`，去掉仅 toast 拦截；游客无登录打开成绩页仍见样例列表并可点进详情
- [x] 2.2 修改 `WrongBook.tsx`：演示卡点击 `navigate(/grade/wrong/:attemptId)`（或先详情再错题，二选一并保持一致）；验证游客可从错题本进入错题详情
- [x] 2.3 修改 `GradeResult.tsx` / `WrongQuestions.tsx`：`isDemoId` 时用 `getDemoAttempt` 短路 API；演示态隐藏或禁用确认保存，并显示演示标识；验证 `demo-score-1` 详情可渲染且确认不会调用真实 confirm API

## 3. Polish and smoke

- [x] 3.1 （可选）`Me.tsx` 游客副文案提示可先体验演示成绩 / 错题本；验证文案可见且入口仍可进两页
- [x] 3.2 游客路径手测：成绩列表 → 详情 → 错题 → 返回；错题本 → 错题详情；全程有「演示」标识且无保存成功提示
