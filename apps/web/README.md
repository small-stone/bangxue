# apps/web

家长端移动 Web：Vite + React + TypeScript SPA（React Router + Tailwind）。

## 命令

```bash
cd apps/web
npm install
npm run dev      # http://localhost:5173
npm run build    # 产出 dist/
npm run preview
```

## `/api` 代理

开发时，前端请求 `/api/*` 由 Vite 代理到 `http://127.0.0.1:8000`（见 `vite.config.ts`）。

上线时由 Nginx 将 `/api` 反代到 FastAPI，静态资源托管本目录的 `dist/`。
