# Design

## Context

见 `proposal.md`。`.env` 只有 `bailian_api_key`，且被 git 忽略。FastAPI 和 `python -m ingest` 都不会加载这个文件。出题代码读 `OPENAI_API_KEY`，默认模型 `gpt-4o-mini`。入库 embedding 默认 `EMBEDDING_PROVIDER=local`、`BAAI/bge-small-zh-v1.5`、512 维。`textbook_chunks.embedding` 已是 `vector(512)`；维度不符时 `ensure_schema` 会拒绝写入。一年级出题按单元名读课文，还不按向量相似度检索。本变更不引入 Checkpointer，也不改练习 id 的进程内存。

## Goals / Non-Goals

**Goals:**

- 进程能读到仓库根目录 `.env` 里的密钥和两个模型名
- 出题与入库都走百炼北京兼容接口，仍在现有进程内
- 一年级上册用 1024 维新向量重写进库

**Non-Goals:**

- 把检索从「按单元名取课文」改成向量相似度
- 改对话 Agent、判分或前端页面
- 把密钥写进 git

## Decisions

### 1. 环境变量

在现有 `.env` 末尾追加，不改 `bailian_api_key` 的值：

```
QUIZ_MODEL=qwen3.7-plus
EMBEDDING_MODEL=qwen3.7-text-embedding
EMBEDDING_PROVIDER=bailian
EMBEDDING_DIMENSION=1024
```

变量名用大写。密钥保持文件里已有的小写 `bailian_api_key`，代码按这个名字读取。启动时从仓库根目录加载 `.env`，已在进程环境里的同名变量优先，避免覆盖操作者临时导出的值。

### 2. 调用方式

继续用已安装的 OpenAI SDK，只改 `base_url` 与密钥。默认：

`https://dashscope.aliyuncs.com/compatible-mode/v1`

若密钥所属地域拒绝该地址，用可选变量 `BAILIAN_BASE_URL` 覆盖，不改模型名。

```
.env
  ├─ QUIZ_MODEL + bailian_api_key
  │     → agents/textbook  chat.completions
  │        model=qwen3.7-plus
  │        extra_body.enable_thinking=false
  └─ EMBEDDING_MODEL + bailian_api_key
        → ingest/embed  embeddings.create
           model=qwen3.7-text-embedding
           dimensions=1024
           每批最多 20 条
```

`qwen3.7-plus` 默认会先思考。出题要的是题目 JSON，因此关闭思考，避免把思考过程当成题干。向量默认维度是 1024，请求里显式带上 `dimensions=1024`，与 `EMBEDDING_DIMENSION` 一致。该模型单批最多 20 条，30 个课文块必须分批。

### 3. 向量列

不在原列上改宽度。实现时先 `DROP TABLE textbook_chunks`，再按现有入库命令重写一年级上册。`ensure_schema` 仍在维度不一致时失败，避免静默混用 512 维旧向量。

`textbook_chunks` 只存课文块和向量。本变更不新增业务表，也不使用 `thread_id`。

## Risks / Trade-offs

- **[Risk] 思考模式让 `content` 为空或不是 JSON** → 出题请求关闭思考；解析失败仍按现有 502 处理，不当作成功
- **[Risk] 一批超过 20 条被接口拒绝** → 入库按 20 条分批计算向量
- **[Risk] 密钥地域不是默认北京域名** → `BAILIAN_BASE_URL` 可换，模型名不变
- **[Risk] 删表后重跑失败，一年级暂时查不到课文** → 删表与重入库放在同一次验证里；失败时保留命令输出，不把空库当成完成
- **[Trade-off] 出题仍按单元名取原文** → 新向量先入库，相似度检索留到后续变更

## Migration Plan

1. 写入模型名后重启 API，确认进程读到 `QUIZ_MODEL` 且不会把密钥打进日志
2. `DROP TABLE textbook_chunks`
3. 用原入库命令重写人教版数学一年级上册
4. 抽查一个单元的向量维度为 1024，并用该单元出一道数量匹配的题

回退：把 `EMBEDDING_PROVIDER` 改回 `local`、维度改回 512，再次删表并用本地模型入库。出题模型可单独改回，不影响向量列。

## Open Questions

无。模型名、维度和默认域名已按百炼文档定下；地域域名只用可选变量处理。
