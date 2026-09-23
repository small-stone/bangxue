# Tasks

## 1. 环境文件

- [x] 1.1 在仓库根目录 `.env` 追加 `QUIZ_MODEL=qwen3.7-plus`、`EMBEDDING_MODEL=qwen3.7-text-embedding`、`EMBEDDING_PROVIDER=bailian`、`EMBEDDING_DIMENSION=1024`，保留原有 `bailian_api_key` 的值。验证：只打印变量名和两个模型名时能对上，且 `git status` 不出现 `.env`
- [x] 1.2 FastAPI 与 `python -m ingest` 启动时加载仓库根目录 `.env`，进程里已有的同名变量优先。验证：不手动 export 时，两侧都能读到 `QUIZ_MODEL=qwen3.7-plus`，日志里没有密钥

## 2. 出题模型

- [x] 2.1 `agents/textbook` 用 `bailian_api_key` 和 `QUIZ_MODEL` 调用百炼兼容接口，并关闭思考模式。没有密钥时返回配置错误。验证：去掉密钥得到 4xx/503 且没有题目；用假模型时 10/15/20/30 的数量仍一致
- [x] 2.2 用真实 `qwen3.7-plus` 对已入库的一个一年级单元出 10 题。验证：返回 10 道题干，响应里没有思考过程字段被当成题目

## 3. 向量模型

- [x] 3.1 `ingest/embed.py` 在 `EMBEDDING_PROVIDER=bailian` 时调用 `qwen3.7-text-embedding`，维度 1024，每批最多 20 条。验证：对超过 20 条的短文本，返回条数相同且每条长度为 1024
- [x] 3.2 删除现有 `textbook_chunks` 后，用原入库命令重写人教版数学一年级上册。验证：向量列是 `vector(1024)`；同一单元检索只返回该单元；连续入库两次后块数等于第二次，不混入 512 维旧向量

## 4. 串起来

- [x] 4.1 重启 API 后，对重入库的一个真实单元请求 `POST /api/quizzes`，题量 10。验证：题目数量为 10，且与该单元相关；未配置密钥时结果里没有题目
