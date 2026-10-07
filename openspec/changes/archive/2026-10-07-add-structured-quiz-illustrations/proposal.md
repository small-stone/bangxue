# Proposal

## Why

一年级数学大量依赖「看图数一数 / 合起来」题（如鱼缸、草莓盘），当前出题只返回文字题干，结果页与 PDF 无法还原课文图示逻辑，练习价值不足。纯文生图模型数不准物体，不适合一期；需要用结构化场景 + 程序出图，保证图中数量与答案一致。

## What Changes

- 方式 A 出题在需要图示时，由现有 `qwen3.7-plus` 额外产出**场景结构 JSON**（容器数量、各容器物体个数、布局提示），而不是调用文生图模型。
- 新增**程序化插图渲染**（SVG 或等价矢量/位图）：按场景 JSON 画出可数物体，物体个数与 schema 中的计数 **MUST** 一致。
- 题目 JSON 增加可选插图字段（如 `illustration`：场景 + 渲染产物引用或内联 SVG）；纯文字题保持现状。
- 结果页展示插图；练习 PDF / 答案 PDF 嵌入同一插图，与屏幕一致。
- **不引入**通义万相 / Flux / DALL·E 等 text-to-image；**不新增**出图专用模型名到 `.env`。

## Capabilities

### New Capabilities

- `structured-quiz-illustrations`：一年级看图题用结构化场景 + 程序渲染插图，并在结果页与 PDF 中展示；数量与答案一致。

### Modified Capabilities

- （无）`bailian-models` 仍用 `qwen3.7-plus` 做文本/结构生成，不新增文生图模型要求。

## Impact

- **前端**：结果页在有插图的题下渲染 SVG/图片；草稿结构兼容无插图旧题。
- **FastAPI**：出题响应与 quiz store 携带插图；`pdf_paper` 嵌入插图，下载仍为同步。
- **Agent A**：出题 prompt / 结构化输出扩展 scene schema；渲染在进程内、确定性、不调外部出图 API。
- **数据与存储**：插图随 quiz 会话保存（内存/现有 store）；本期可不落对象存储。长任务：仍一次 `POST /api/quizzes`；带图题量增大时可能更慢，保持等待态，不做 SSE。
- **Non-goals**：文生图、vision 验图闭环、对话出题配图、判分读图、可编辑图、其他年级、独立 Agent 服务、任务队列。
