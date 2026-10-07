# Tasks

## 1. Schema and store

- [x] 1.1 实现 `grade_attempts` 建表 / ensure_schema（`DATABASE_URL` + psycopg，字段对齐 design），在 API 启动时调用；验证连上 Postgres 后表存在
- [x] 1.2 用 Postgres 重写 `score_store` 的 `create_attempt` / `get_attempt` / `confirm_attempt` / `list_confirmed_scores` / `list_wrong_questions`，保留函数签名；`save_upload` 仍写本地盘并把路径写入 `photo_paths`；验证 create→get→confirm→list 与错题聚合
- [x] 1.3 无 `DATABASE_URL` 或连接失败时成绩写/读 API fail closed（明确错误，不回退 JSON）；用去掉环境变量的请求验证返回非 2xx 且无新 JSON 权威写入

## 2. Wire and migrate

- [x] 2.1 确认 `grading_routes` / `main.py` 仅依赖新 store，去掉对 `scores.json` 作为权威存储的依赖；跑通上传判分 → 确认 → `/api/scores` → `/api/wrong-questions`
- [x] 2.2 （可选）提供一次性从 `scores.json` 导入的逻辑或脚本；有旧文件时导入后 list 可见，无文件时跳过
- [x] 2.3 更新 `apps/api/README.md`：说明成绩/答卷引用依赖 Postgres、本地 uploads 路径语义；验证文档与 `DATABASE_URL` 要求一致

## 3. Regression

- [x] 3.1 手测：登录确认成绩后重启 API，成绩与错题本仍在；游客演示夹具仍可用且不入库
- [x] 3.2 手测：未确认 attempt 重启后仍可按 id 打开并确认；详情含 `photo_paths` 引用
