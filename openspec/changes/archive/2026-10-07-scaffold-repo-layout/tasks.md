# Tasks

## 1. 目录骨架

- [x] 1.1 创建 `apps/web/` 与 `apps/api/`（含 `app/`、`agents/textbook/`、`agents/chat/`、`agents/shared/`）及各自 README，说明「Agent 为库、非独立服务」；验证：树形存在且无 `apps/agent` 服务目录
- [x] 1.2 确认根目录仍保留 `REQUIREMENTS.md`、`docs/`、`openspec/`；验证：路径未移动

## 2. 前端脚手架（apps/web）

- [x] 2.1 用 Vite 初始化 React + TypeScript 工程于 `apps/web`（含 React Router）；验证：`npm install && npm run build` 在 `apps/web` 成功
- [x] 2.2 接入 Tailwind（移动优先）；验证：页面可引用 utility class 且 build 通过
- [x] 2.3 在 `apps/web/README.md` 写明开发命令与 `/api` 代理约定；验证：README 含 `dev` / `build` 说明

## 3. 后端与 Agent 占位（apps/api）

- [x] 3.1 添加 Python 依赖清单（一期选定 `requirements.txt` 或 `pyproject.toml` + uv 其一）与最小 FastAPI `app/main.py`（健康检查路由）；验证：本地可启动并 `GET /health` 返回 200
- [x] 3.2 在 `agents/textbook`、`agents/chat`、`agents/shared` 放置可导入的占位模块（空图/空函数即可）；验证：从 `app` 能 `import agents.textbook` / `agents.chat` / `agents.shared` 且无循环依赖
- [x] 3.3 在 `apps/api/README.md` 写明：Agent 进程内调用、禁止默认独立 Agent 服务；验证：README 含上述约束

## 4. 仓库约定收尾

- [x] 4.1 更新根 `.gitignore`（覆盖 `apps/web/node_modules`、Python venv、`.env` 等）；验证：敏感与依赖目录不会被 `git status` 误跟踪
- [x] 4.2 可选：根 README 链到 `apps/web` 与 `apps/api`；验证：新人能从根目录找到两端入口
- [x] 4.3 对照 `repo-layout` spec 自检：两应用根、Agent 在 API 树内、无独立 agent compose/Dockerfile；验证：目录与文档符合 scenarios
