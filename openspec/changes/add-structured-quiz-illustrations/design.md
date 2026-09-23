# Design

## Context

方式 A 已能按单元从 `textbook_chunks` 取课文，经 `qwen3.7-plus`（`bailian_api_key`）返回 `{qtype, stem, answer?}`，结果页与 `fpdf` PDF 只排文字。见 proposal.md — Why。一年级「数一数 / 合起来」需要图，但文生图不可靠。用户已选定：**LLM 出场景 JSON + 程序渲染**。

无 Checkpointer / thread_id 变更：仍为一次 `POST /api/quizzes`，quiz 存现有内存 store。外部依赖仍只有百炼对话模型；不新增出图密钥。

## Goals / Non-Goals

**Goals:**

- 扩展出题结构化输出，为看图题附带可校验的 scene schema。
- 进程内确定性渲染（优先 SVG），计数与 schema 一致。
- 结果页与 PDF 共用同一插图数据。

**Non-Goals:**

- 文生图、vision 验图、对话出题配图、对象存储持久化插图。
- 把方式 A 改成 `create_agent` 工具循环（与 `wire-agent-harness` 分工不变）。

## Decisions

### 1. 两段式：结构生成 → 本地渲染

```
课文 chunks → qwen3.7-plus(JSON: questions[+scene])
           → validate scene counts vs stem/answer rules
           → render_svg(scene) → question.illustration.svg
           → save_quiz → Result / PDF
```

- **为何**：计数正确性由代码保证；模型只负责选题意与布局意图。
- **备选**：纯文生图（否决，数不准）；混合装饰背景（二期）。

### 2. Scene schema（一期最小集）

```json
{
  "kind": "row_of_groups",
  "item": "fish",
  "groups": [{"count": 3}, {"count": 6}, {"count": 7}]
}
```

或 `plates` / `item: strawberry` 等同构。未知 `kind` / `item` → 跳过渲染或失败策略见 Risks。

- **为何**：覆盖鱼缸横排、草莓盘组合两类样题，避免过早做通用场景图。
- **备选**：自由 DSL / LLM 直接出 SVG（否决：难校验计数）。

### 3. 渲染与嵌入形态

- 渲染：Python 拼 SVG 字符串（无 Cairo 依赖更易 Docker）；PDF 用 fpdf 嵌入 PNG 时可将 SVG 栅格化，或改用能吃 SVG/HTML 的 PDF 路径——一期优先 **SVG 存 quiz + 前端直接展示；PDF 侧栅格化为 PNG 嵌入**，避免大改 PDF 栈。
- 题目字段：`illustration: { scene, svg }`（或 `image_png_base64` 若 PDF 需要）。不把密钥写入响应。

### 4. Prompt 与校验

- System prompt：看图题必须带 `scene`；`groups[].count` 之和/序数须与答案一致；禁止用「参考课文 Pxx」代替图。
- 校验：schema 合法 + 每个 count ∈ [1, 10]（一年级上限可配置）+ 与选择题选项/填空答案可对上的简单规则；失败则丢弃该题插图或整卷重试（实现选一种并在 tasks 写清：一期 **无 scene 的看图题降级为纯文字，不阻断整卷**）。

### 5. 密钥与模型

- 继续 `bailian_api_key` + `QUIZ_MODEL`/`qwen3.7-plus`。
- `.env` **不**增加文生图模型名。

## Risks / Trade-offs

- [模型 scene 与答案不一致] → 校验器丢插图或重试；日志记录 mismatch。
- [SVG→PDF 栅格糊] → 固定高 DPI；打印预览人工抽检样题。
- [场景种类爆炸] → 一期只支持 `row_of_groups`；未知 kind 无图。
- [出题变慢] → 仍同步请求；前端保持等待态；不做 SSE。
- [与 wire-agent-harness 并行] → 插图挂在 generate 输出后处理，不依赖 LangGraph 是否已切换；若 harness 先合并，渲染节点可接在模型节点之后。

## Migration Plan

- 纯加字段：旧 quiz 无 `illustration` 仍可展示。
- 回滚：关掉 scene prompt 与渲染调用即可，API 形状向后兼容。

## Open Questions

- PDF 最终用 PNG 嵌入还是换 HTML→PDF：实现时以「能打印、字图不错位」为准，不改规格。
