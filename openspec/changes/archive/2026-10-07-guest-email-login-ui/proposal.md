# Proposal

## Why

家长端已有「我的 / 登录」页面雏形，但验证码仍是演示随机码、未登录态缺少统一「游客模式」标识，也与墨金纸感 mockup 不完全一致。需要先落地可演示的邮箱登录（固定验证码、不接 SMTP）与游客可用体验，为后续真实鉴权留口子。

## What Changes

- 按 `mockup-08-me.png` / `mockup-09-login.png` 打磨「我的」「登录」页视觉与交互（邮箱 + 验证码，游客继续）
- 未登录时全站可用出题等主流程，但在合适位置标识「游客模式」
- 登录验证码固定为 `0000`；点击「发送验证码」不调用邮件/SMTP，仅做本地演示提示
- 登录态仍用前端本地会话（localStorage）；登录成功后「我的」展示脱敏邮箱
- **Non-goals**：不接 SMTP / 邮件服务商；不上 FastAPI JWT / 用户表；不做 OAuth、注册独立页、多孩子账号、服务端会话同步

## Capabilities

### New Capabilities

- `parent-auth-ui`: 家长端游客模式标识、邮箱固定验证码登录 UI、「我的」已登录/未登录态（本地会话）

### Modified Capabilities

- （无）本期不改出题 / 入库 / 判分等已有 main specs 的行为要求

## Impact

- **前端**：`Login.tsx`、`Me.tsx`、`session.ts`、首页等非登录页的游客标识、`index.css` / chrome；对齐 `docs/mockups/alt-ink-amber`
- **FastAPI / Agent / 数据库**：无变更（不发邮件、不写用户表）
- **依赖**：不新增邮件 SDK；不引入 NextAuth
