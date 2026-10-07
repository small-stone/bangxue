# Spec Delta

## ADDED Requirements

### Requirement: Confirmed scores persist in PostgreSQL
已登录家长确认后的成绩记录 MUST 持久化到 PostgreSQL。进程重启或 API 多实例共用同一数据库时，按家长邮箱查询成绩历史 MUST 仍能返回这些记录。系统 MUST NOT 将已确认成绩仅写入本地 `scores.json` 作为权威存储。

#### Scenario: Confirmed score survives restart
- **WHEN** 已登录家长确认一次成绩，随后 API 进程重启
- **THEN** 再次打开成绩记录仍能看到该次练习（得分、出题方式、摘要等）

#### Scenario: List scores reads from database
- **WHEN** 已登录家长请求成绩列表且库中有该邮箱的已确认记录
- **THEN** 返回的条目来自数据库查询结果，而非仅内存或本地 JSON 文件

### Requirement: Answer sheet refs linked to attempts
每次判分 attempt MUST 在数据库中保存关联的答卷引用（本地相对路径或对象存储键，至少一页）。引用 MUST 在创建 attempt 时写入，并在确认后仍可随 attempt 查询。本期 MUST NOT 要求将照片二进制以 BYTEA 存入数据库。

#### Scenario: Upload creates attempt with photo refs
- **WHEN** 家长上传一张或多张答卷并成功开始判分
- **THEN** 系统创建 attempt 记录，且该记录包含可追溯的答卷引用列表

#### Scenario: Confirmed attempt retains photo refs
- **WHEN** 家长确认成绩后按 attempt id 读取详情
- **THEN** 详情仍包含此前保存的答卷引用（路径或键）

## MODIFIED Requirements

### Requirement: Parent confirms before score is saved
最终成绩 MUST 在家长确认之后才作为已确认成绩出现在成绩历史中。未确认的判分结果 MUST NOT 出现在成绩历史的已确认列表中。游客 MUST 能完成上传与查看判分结果，但 MUST NOT 将成绩同步到登录账号的成绩库。判分草稿（未确认 attempt）与确认后的成绩 MUST 均以 PostgreSQL 为权威存储，以便重启后仍可按 id 打开并确认。

#### Scenario: Confirm writes score
- **WHEN** 已登录家长在判分结果确认本次成绩
- **THEN** 该次练习出现在成绩记录中，并带出题方式、范围摘要、题量与得分；记录持久化在 PostgreSQL

#### Scenario: Guest grades without account sync
- **WHEN** 游客完成判分并查看结果
- **THEN** 结果可查看；登录账号的成绩记录与错题本不增加该次已确认记录

#### Scenario: Unconfirmed attempt readable after restart
- **WHEN** 家长已完成判分但未确认，API 进程随后重启，再打开同一 attempt id
- **THEN** 仍可看到判分结果并可继续确认（若仍符合登录要求）
