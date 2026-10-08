# Design

## Context

见 `proposal.md` — Why。现状：`draft.canContinue` 与 `agents/textbook/generate.is_allowed_book` 均只放行小学数学人教版；`Select.tsx` 的 `EDITIONS` 无统编版；`_bailian_generator` 系统提示写死「小学数学」并强看图 `scene`。语文/英语向量已入库（数学人教版、语文统编版、英语人教版三起）。

## Goals / Non-Goals

**Goals:**

- 前后端共用同一套「开放册」判定（科目 × 版本 × 年级 × 学期）。
- 选题 UX：换科目自动落到默认版本；版本芯片按科目过滤。
- 出题 prompt 跟科目走；数学保留看图能力，语文/英语不依赖 `scene`。

**Non-Goals:**

- 不改入库/切分；不迁 VPS 数据。
- 不开放苏教版等未入库版本的真实出题（UI 可灰显或选中后不可继续）。
- 不改对话 Supervisor / 混合检索规则（检索本就可按 meta 过滤）。

## Decisions

1. **白名单表驱动，前后端各维护一份同构常量**  
   - 前端：`ALLOWED_BOOKS` + `defaultEdition(subject)` + `editionsFor(subject)`。  
   - 后端：`is_allowed_book` 读同一语义的映射（不必共享文件；注释写明需与 `draft.ts` 对齐）。  
   - 备选：单一 JSON 由 API 下发——本期不必，白名单很小且静态。

2. **英语仅三至六年级**  
   - 与教材「三年级起点」及入库范围一致；一二年级选英语时 `canContinue=false`。

3. **语文默认/唯一开放版本 = 统编版**  
   - 切换到语文时若当前 edition 不在该科列表，写入 `统编版`。

4. **出题 prompt**  
   - `你是{grade}小学{subject}出题助手…`；题型说明：数学保留 scene；语文/英语用选择题/填空/简答等文本题，scene 可选忽略。  
   - graph 里对 illustration 的处理已对无效 scene 丢弃，语文/英语不强制生成 scene 即可。

5. **错误文案**  
   - `_require_*` 与前端 notice 使用同一开放范围描述，避免前后不一致。

## Risks / Trade-offs

- [前后端白名单漂移] → tasks 里两边改完后用同一组场景手测；注释交叉引用。  
- [某册未入库] → 可进入范围页但 list_units 404；保持现有「该册尚未入库」即可。  
- [能力名仍叫 primary-math-quiz] → 本 change 只改需求文本，不重命名能力路径，避免大范围归档扰动。

## Migration Plan

- 纯应用变更：发版前端 + API 即可；无需 DB migration。  
- 回滚：恢复 `is_allowed_book` / `canContinue` 旧逻辑。

## Open Questions

- （无）开放范围以本机已入库科目为准，已在 proposal 固定。
