# Spec Delta

## Purpose

为家长端提供游客可用的主流程体验，以及邮箱 + 固定验证码的本地登录 UI，并在「我的」页区分已登录与未登录态；本能力不覆盖真实邮件发送或服务端鉴权。

## ADDED Requirements

### Requirement: Guest mode is available without login
未登录家长 MUST 能使用除登录页强制鉴权之外的主流程页面（首页、出题、成绩等）。系统 MUST 在未登录时展示可识别的「游客模式」标识，且 MUST NOT 因未登录而阻断进入这些页面。

#### Scenario: Guest opens home and textbook flow
- **WHEN** 家长未登录并打开首页或按教材出题流程
- **THEN** 页面可用，且能看到「游客模式」标识

#### Scenario: Guest opens scores and me
- **WHEN** 家长未登录并打开成绩记录或「我的」
- **THEN** 页面可用；「我的」展示未登录入口（如点击登录 / 登录注册），成绩页不因未登录而空白拦截

### Requirement: Email login uses fixed demo verification code
登录页 MUST 使用邮箱输入。验证码 MUST 接受固定值 `0000` 完成登录。系统 MUST NOT 调用 SMTP 或任何外部邮件服务发送验证码。

#### Scenario: Login with email and code 0000
- **WHEN** 家长输入有效邮箱，并提交验证码 `0000`
- **THEN** 系统写入本地登录会话并进入「我的」已登录态

#### Scenario: Wrong code is rejected
- **WHEN** 家长输入有效邮箱，但验证码不是 `0000`
- **THEN** 系统拒绝登录并给出错误提示，且不写入登录会话

#### Scenario: Send code does not send email
- **WHEN** 家长点击「发送验证码」且邮箱格式有效
- **THEN** 系统仅给出演示提示（可不自动填码），MUST NOT 发起网络发信

### Requirement: Me page reflects login state per mockup
「我的」页 MUST 在未登录时引导登录，在已登录时展示脱敏邮箱并可退出。视觉与信息结构 MUST 对齐 `docs/mockups/alt-ink-amber/mockup-08-me.png` 的意图（头像区、菜单、登录/退出主按钮）。

#### Scenario: Logged-out me page
- **WHEN** 未登录家长打开「我的」
- **THEN** 看到未登录头像文案与「登录 / 注册」入口，并可进入登录页

#### Scenario: Logged-in me page
- **WHEN** 已登录家长打开「我的」
- **THEN** 看到脱敏邮箱，并可退出登录回到游客态

### Requirement: Login page matches email mockup
登录页 MUST 对齐 `docs/mockups/alt-ink-amber/mockup-09-login.png` 的意图：品牌、邮箱、验证码、登录、游客继续。游客继续 MUST 回到可用主流程且保持未登录。

#### Scenario: Guest continue from login
- **WHEN** 家长在登录页选择「游客继续使用」
- **THEN** 进入主流程（如首页）且仍为游客模式
