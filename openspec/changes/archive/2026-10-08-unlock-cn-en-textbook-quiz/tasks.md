# Tasks

## 1. Frontend allowlist and Select UX

- [x] 1.1 在 `apps/web/src/draft.ts` 定义开放册白名单（数学人教版一至六；语文统编版一至六；英语人教版三至六）、`defaultEdition` / `editionsFor`，改写 `canContinue`，并验证：语文统编版二年级上册为 true、英语一年级为 false、苏教版为 false
- [x] 1.2 更新 `apps/web/src/pages/Select.tsx`：版本芯片随科目变化；切换科目时写入默认版本；「更多」不可继续；notice 文案列出三科开放范围；验证页面上手选语文/英语可点「下一步」，选「更多」或英语一二年级不可

## 2. Backend allowlist and subject-aware quiz

- [x] 2.1 扩展 `apps/api/agents/textbook/generate.py` 的 `is_allowed_book` / 拒绝文案，与前端白名单语义一致；验证 `list_units` 对语文统编版、英语三起人教版不再被门禁拒掉（未入库仍可 404）
- [x] 2.2 出题 prompt 使用请求 `subject`；数学保留 scene 说明，语文/英语不强制 scene；确认图节点对无 scene 题目仍可返回；用假 generator 或本地一次真实出题抽检英语/语文路径

## 3. Integration smoke

- [x] 3.1 本机走通：选题语文统编版 → 范围页拉到单元 → 设置 → 出题结果页标题含语文；再抽检英语三年级上册同一路径
- [x] 3.2 抽检数学人教版原路径未回归；初中 / 「更多」仍不可继续
