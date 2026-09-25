# Design

## Context

前端已有 `/login`、`/me`、`session.ts`（localStorage）与墨金纸感样式；验证码当前为演示自动填入 `123456`。出题 / 成绩等页面未统一展示游客标识。本期只改前端 UI 与本地会话规则，不接邮件与 JWT。参见 proposal.md。

## Goals / Non-Goals

**Goals:**

- 登录固定验证码 `0000`，发送验证码零 SMTP
- 「我的 / 登录」对齐 mockup-08 / mockup-09
- 未登录全站可逛，带「游客模式」标识

**Non-Goals:**

- SMTP / 阿里云邮件推送 / Resend 等
- FastAPI 用户表、JWT、服务端校验码
- 注册独立页、找回密码、OAuth

## Decisions

1. **本地会话继续用 `session.ts` + localStorage**  
   - 字段：`email` + `name`；无 token。  
   - 备选：Cookie / 后端 session → 拒绝（本期无 API）。

2. **验证码硬编码 `0000`**  
   - 「发送验证码」只校验邮箱格式 + 本地提示（不自动填真实邮件码；可提示「演示码 0000」）。  
   - 备选：继续自动填 `123456` → 按产品要求改为 `0000` 且需用户手动输入更贴近真流程。

3. **游客标识放在共享 chrome**  
   - 在 `PageNav` / 首页品牌行或统一 `GuestBadge`：未登录时显示「游客模式」chip。  
   - 登录页本身不强制显示游客 badge（已有「游客继续」）。  
   - 备选：仅首页显示 → 拒绝，出题路径也要可见。

4. **不拦截路由**  
   - 无 `RequireAuth`；「我的」未登录可进，点登录才去 `/login`。

```
未登录 ──► 任意主流程页（带游客标识）
         └► /me（未登录 UI）──► /login
登录：邮箱 + 0000 ──► localStorage session ──► /me 已登录
退出 ──► clearSession ──► 游客模式
```

## Risks / Trade-offs

- [Risk] 固定验证码可被滥用 → Mitigation：仅演示；文案标明演示；上线前换真发信 + 服务端校验  
- [Risk] localStorage 可被清掉 / 伪造 → Mitigation：本期可接受；后续 JWT 取代  
- [Risk] 游客与登录成绩数据混用 → Mitigation：成绩仍为演示数据；真同步留后

## Migration Plan

- 纯前端发布；旧 session 若仍含 `phone` 字段，读取时忽略并视为未登录（或迁移到 `email` 时一并清理）  
- 回滚：还原 Login/Me/badge 即可

## Open Questions

- 游客标识精确落点（顶栏 chip vs 首页副文案）：实现时优先顶栏/共用 badge，与 mockup 纸感一致即可
