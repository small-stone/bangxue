# Design

## Context

参见 `proposal.md` 的 Why / What。现状：出题与 PDF 可用（`quiz_store` 进程内存、前端 `sessionStorage` quiz）；登录为 `session.ts` localStorage 邮箱演示会话，无 JWT；`Scores` / 首页待办 /「错题本」为占位或硬编码；无上传与判分路由。视觉对齐 `docs/mockups/alt-ink-amber/mockup-05|06|07-*.png`。Jev 判分判断仍属 `add-jev-decisions`，本期不接入。

## Goals / Non-Goals

**Goals:**

- 打通「上传 → 判分 → 确认 → 成绩/错题可查」垂直切片
- 登录邮箱作为成绩与错题隔离键；游客可判分预览但不写入账号库
- 判分放在 `agents/shared`，由 FastAPI 进程内调用

**Non-Goals:**

- Postgres / JWT / 独立 worker / Jev / 错题重练 / 跨设备真同步保证

## Decisions

### 1. 身份：请求头携带本地会话邮箱

- **选择**：前端已登录时在成绩读写与确认接口带 `X-Parent-Email`（与 `session.ts` 一致）；服务端按邮箱分桶。不上 JWT。
- **替代**：仅 localStorage 成绩 → 无法统一 API、与后续 Postgres 迁移更远；先上 JWT → 超出当前登录 change 范围。
- **说明**：演示级隔离，非安全边界；文档写明生产需换 JWT。

### 2. 成绩存储：JSON 文件落盘 + 进程内缓存

- **选择**：`apps/api` 本地目录（如 `data/scores.json` + `data/uploads/`）持久化答卷与已确认成绩，重启不丢；结构含 `email`、`attempt_id`、`source`、`subject`、`title`、`correct`/`total`、`items[]`（对错与题干）、`created_at`。
- **替代**：纯内存 → 一重启演示断；Postgres → 本期过重且环境未普遍就绪。
- **Checkpointer / thread_id**：本期判分为同步请求-响应，不开 LangGraph 判分图；`thread_id` 不出场。业务数据只进成绩文件，不进 Checkpointer。

### 3. 判分：百炼多模态 + 确定性演示回退

```
上传照片 → 存本地 uploads/
     ↓
POST /api/grading/attempts  (quiz_id + photos + optional email)
     ↓
Vision（bailian_api_key）识别作答 → 对照 quiz 标准答案出对错
     ↓
返回 draft result（未确认）
     ↓
家长确认 → POST .../confirm → 写入 scores（仅已登录邮箱）
```

- **选择**：有 `bailian_api_key` 时调多模态；无 key 或 Vision 失败时用基于 `quiz_id` 哈希的确定性假结果，保证无密钥也能演示 UI（与出题「无 key 直接报错」不同：判分链需要可走通页面）。回退结果须在响应中标记 `demo: true`，前端可提示「演示判分」。
- **替代**：无 key 一律失败 → mockup 闭环难演示；先接 Jev → 阻塞本切片。
- **超时**：服务端判分调用设明确超时（如 60s）；前端「判分中」禁用重复提交；超时返回错误，不写成绩。

### 4. 前端路由与页面

| 路由 | 对应 |
|------|------|
| `/grade/upload` | mockup-05；query/state 带 `quizId` 或 pending attempt |
| `/grade/result/:attemptId` | mockup-06 |
| `/grade/wrong/:attemptId` | 单次错题 |
| `/scores` | mockup-07，改为 API 数据 |
| `/me/wrong-book` | 错题本聚合 |

首页「去上传」→ `/grade/upload`（优先用当前 `loadQuiz()` / 服务端仍存活的 quiz；若 quiz 已失效则提示重新出题）。PDF 结果页可增加「去拍照判分」次要入口，避免断链。

### 5. 与出题数据的衔接

- 判分需要标准答案：优先 `get_quiz(quiz_id)`；若进程已丢 quiz，允许前端在上传时附带题目快照（题干+答案）以免演示中断。
- 出题方式 `source: textbook | chat` 与 title/subject 写入成绩，供筛选与标签。

## Risks / Trade-offs

- **[Risk] `X-Parent-Email` 可伪造** → Mitigation：文档标明演示身份；后续 JWT 替换同一分桶键
- **[Risk] Vision 不准 / 贵 / 慢** → Mitigation：超时与重试文案；演示回退保证 UI；Jev 交给后续 change 提置信度
- **[Risk] quiz 内存丢失导致无法对照答案** → Mitigation：上传请求附带题目快照；确认后成绩自包含错题信息
- **[Trade-off] JSON 文件非多实例安全** → 一期单 FastAPI 进程可接受；迁 Postgres 时按同一 schema 导入

## Migration Plan

- 无生产数据迁移。上线即新文件目录；回滚删除新路由与 `data/` 成绩文件即可，不影响出题 PDF。
- 日后 Postgres：将 `scores.json` 记录映射为 `score_attempts` / `score_items` 表，身份键从 email 换成 `user_id`。

## Open Questions

- 无（演示回退是否默认开启：默认开启并标记 `demo`；若产品后续要求「无 key 禁止判分」，可在实现时用环境变量关闭回退而不改规格主路径）。
