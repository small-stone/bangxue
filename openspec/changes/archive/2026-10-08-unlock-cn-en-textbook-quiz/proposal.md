# Proposal

## Why

语文（统编版）与英语（人教版）教材已完成 RAG 入库，但家长端选题页仍只放行「小学数学人教版」，后端 `is_allowed_book` 同样锁死数学。家长选语文/英语无法进入下一步，即便库里已有对应册。需要把前后端开放范围对齐到已入库科目与版本。

## What Changes

- 选题页：`canContinue` 与提示文案扩展为小学已入库组合——数学人教版（一至六上下）、语文统编版（一至六上下）、英语人教版（三至六上下）；选科目时自动切到该科默认版本；「更多」仍不可继续。
- 教材版本芯片：按科目展示可用版本（语文含统编版；数学/英语为人教版等），避免语文仍只能点人教版却永远无法继续。
- 后端方式 A：`list_units` / 出题元数据校验与前端同一白名单；出题 prompt 按科目表述（不再写死「小学数学」）；数学看图 `scene` 规则仅在数学科保留。
- 范围页/配置页沿用 draft 五元组，无新路由。

## Capabilities

### New Capabilities

- （无）

### Modified Capabilities

- `primary-math-quiz`: 将「仅小学数学人教版」扩展为已入库的小学数学/语文/英语白名单（含英语起始年级与语文统编版）。
- `textbook-quiz-ui`: 选题页可继续条件、提示文案与版本芯片随科目变化；与后端白名单一致。

## Impact

- 前端：`apps/web/src/draft.ts`、`apps/web/src/pages/Select.tsx`（必要时 Range/Config 文案）。
- FastAPI / Agent A：`apps/api/agents/textbook/generate.py`（及依赖其校验的 API 路由）；出题图若写死科目需一并按 meta 传递。
- 数据：只读已有 `textbook_chunks`；不改 schema、不重新入库。
- 非目标：初中；苏教版/北师大版/沪教版实际出题；对话路径 Supervisor 规则大改；VPS dump/restore（部署另做）。
- 长任务：出题仍同步走现有 `/api/quizzes` 超时策略，不新增流式要求。
