# Design

## Context

方式 B 已有 SSE：`progress` →（整段处理后）一条 `token`（整句）→ `done`。前端忽略 `token`，只在 `done` 时整段插入气泡，故无打字机。出题 `generate_chat_questions` 把非 `{10,15,20,30}` 的 count **就近吸附**到四档，故「12 道」变 10。完整性追问文案仍写「10、15、20 或 30」。

## Goals / Non-Goals

**Goals:**

- 助手回复可见打字机效果。
- 方式 B 题量 = 家长数字，范围 1–100；>100 不静默截断。

**Non-Goals:**

- 方式 A Config 芯片与 `generate_questions` 四档限制本期不动。
- 不做 LLM token 级真实流式出题（出题仍可一次补全）；打字机作用于**已生成的助手文案**。
- 题目预览列表不做逐题动画。

## Decisions

### 1. 打字机：后端切块推 `token` + 前端追加

```
POST messages
  → SSE progress「正在理解…」
  → handle_parent_message（同步算完）
  → 若 draft_ready：progress「正在出题…」（可选，若出题已在上一步完成可省略）
  → 将 assistant_text 按固定块（如 1–2 字或短词）yield token
  → done（含 status、完整 assistant_text、questions）
```

前端：

- 收到首个 `token`：清掉进度，追加空助手气泡，开始追加文字。
- 后续 `token`：追加到该气泡。
- `done`：用完整文案兜底对齐；若 `draft_ready` 再展示题目预览。

备选：仅前端对 `done.assistant_text` 做本地打字机——也能看，但长等待后仍是「算完才开始动」。采用后端切块，与现有 SSE 契约一致，便于以后真流式替换切块来源。

备选：出题模型真正 astream——成本高、JSON 题目流难拼；本期不做。

### 2. 题量 1–100，超过则追问

| 输入 | 行为 |
|------|------|
| 1–100 | 按该数出题 |
| >100 | `clarifying`，提示最多 100 道 |
| 未解析到题量 | 照旧追问题量（文案改为 1–100） |

实现要点：

- 删除 `generate_chat_questions` 中对 `{10,15,20,30}` 的就近吸附。
- `jev._extract_count` / 追问文案去掉四档暗示；可识别「12 道」「出12道」等。
- `handle_parent_message`：若 count>100，直接 clarifying，不调用出题。

方式 A 的 `count not in {10,15,20,30}` **保持不变**。

### 3. 状态存储

无新表。Checkpointer / `thread_id` / quiz_store 分工不变。`done` 里 `questions.length` 必须等于请求题量（1–100）。

### 4. 密钥与依赖

不新增外部依赖。仍用 `bailian_api_key`、`TYPESAFE_API_KEY`（本地判断）。100 道时出题更慢，依赖现有长超时与进度事件。

## Risks / Trade-offs

- **100 道一次 JSON 易失败或超时** → 校验失败返回明确错误；可后续再拆批（本期不拆）。
- **切块打字机在慢网上仍先等出题** → 进度文案保留；体验仍好于整段蹦出。
- **与会话累计意图叠加**（寒暄仍出题）→ 本期不改意图重置；另案处理。

## Migration Plan

只改 API/Web；无数据迁移。回滚：恢复四档吸附并忽略 `token` 追加即可。

## Open Questions

- 无。超过 100：追问不截断（已定）。
