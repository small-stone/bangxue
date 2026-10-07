# Design

## Context

见 `proposal.md`。`apps/web` 仍是占位首页。`textbook_chunks` 里已有人教版数学一年级上册（学习准备、第一至第六单元）。出题图 `agents/textbook` 还是空函数。视觉以 `docs/mockups/alt-ink-amber/` 为准，色值见该目录 README（底 `#F3F1EB`、墨 `#161616`、金 `#C47A1A`、纸面 `#FFFEFA`）。

## Goals / Non-Goals

**Goals:**

- 五屏可点通，结果页展示真实生成的题目
- 检索限定在已入库的那一册，单元列表来自数据库而不是稿面上的「三年级第二单元」
- 生成失败时页面说明原因，不展示假题冒充成功

**Non-Goals:**

- 登录、会话、成绩入库
- 对话出题、拍照、判分、Jev
- 一年级下册及其他年级的入库或出题
- 公式级 PDF 排版；本变更的 PDF 只需可读地放下题干和可选答案

## Decisions

### 1. 页面路由

```
/                  首页
/textbook          选题（01）
/textbook/range    范围（02）
/textbook/config   设置（03）
/textbook/result   结果（04）
```

范围页的单元 chip 调用 `GET /api/textbooks/units?stage=小学&grade=一年级&subject=数学&edition=人教版&term=上册`，返回库中的 `unit_name`。半学期取单元列表的前一半，整学期取全部。

选题页上其他学段、年级、科目、版本按稿面画出，但不可进入下一步。

### 2. 出题

```
设置页「开始出题」
    → POST /api/quizzes
         校验五元组必须是一年级上册
         按单元取出 textbook_chunks
         将单元文本 + 题量/难度/题型比例交给生成式模型
    → 结果页渲染 JSON
    → GET /api/quizzes/{id}/paper.pdf  （及可选 answers.pdf）
```

模型与密钥来自环境变量（沿用 `OPENAI_API_KEY` 或等价项）。没有密钥时接口返回配置错误，前端显示「暂时无法出题」。Agent 代码放在 `agents/textbook`，由 FastAPI 进程内调用，不新开服务。

题目先存在本次进程内存，用返回的 id 下载 PDF。重启后旧 id 失效，并在下载时说明。不建练习业务表。

### 3. 等待

出题按钮在请求期间不可重复提交，并显示生成中。网关超时按现有长请求约定放宽。本变更不使用 SSE。

## Risks / Trade-offs

- **[Risk] 模型脱离单元原文** → 提示中附上检索到的单元文本，并在结果为空或拒答时不当作成功
- **[Risk] 稿面示例是三年级** → 界面文案改成一年级和真实单元名，布局仍跟稿
- **[Trade-off] PDF 用纯文本排版** → 一年级口算够用；公式多的册次以后再换引擎
- **[Trade-off] 题目只活在内存** → 本切片没有登录和成绩库，避免提前建表

## Migration Plan

- 不改 `textbook_chunks` 结构
- 前端从占位页换成上述路由，无数据迁移

## Open Questions

- 生成式模型的具体名称在实现时按已配置的密钥选定，不改变接口字段
