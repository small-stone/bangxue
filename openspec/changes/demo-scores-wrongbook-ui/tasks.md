# Tasks

## 1. Demo data

- [x] 1.1 新增前端演示常量模块（成绩列表、近 7 日柱高、错题列表与答案对比），内容对齐 `mockup-07-scores` / `mockup-07b-wrongbook`。验证：模块可 import，样例条数与稿面关键字段一致
- [x] 1.2 实现「有真实数据用真实、否则演示」选择逻辑（游客或空列表 → `demo=true`）。验证：单元或页面上游客必出演示；已登录且 API 非空时不出演示标识

## 2. Scores UI

- [x] 2.1 按稿改 `Scores.tsx`：统计双卡、近 7 日 spark、科目 chip、新 `score-card` 布局；去掉游客登录墙。验证：未登录打开 `/scores` 可见完整演示 UI 与「演示」标识
- [x] 2.2 补充 / 对齐 CSS（spark、score-card、wrong-count 等）与现有墨金 token。验证：手机宽下视觉接近 mockup，无布局溢出挡底栏
- [x] 2.3 科目 chip 过滤演示/真实列表并刷新统计。验证：点「数学」只留数学条；「全部」恢复

## 3. Wrong book UI

- [x] 3.1 按稿改 `WrongBook.tsx`：待复习 / 本周新增、chip、错题卡答案对比、底部「用错题出一卷」；去掉游客登录墙。验证：未登录打开 `/me/wrong-book` 可见演示错题与 CTA
- [x] 3.2 CTA 点击仅演示反馈（提示或回首页），不调出题 API。验证：Network 无 quizzes 请求
- [x] 3.3 补充错题卡相关 CSS（ans-box、sticky-cta）。验证：对比区红/琥珀可读，CTA 在拇指区可见

## 4. Regression

- [x] 4.1 已登录且有真实成绩/错题时仍优先真实数据。验证：确认一条成绩后列表出现该条且无「演示」冒充同步
- [x] 4.2 从「我的」进错题本、底栏进成绩，访客与登录各走一遍。验证：主路径无白屏 / 控制台报错
