# Spec Delta

## Purpose

约束方式 A 教材出题与共用答卷判分必须以 FastAPI 进程内的 LangGraph StateGraph 执行，统一 Agent 运行时边界，且不改变家长已依赖的接口契约。

## ADDED Requirements

### Requirement: Textbook quiz runs on an in-process LangGraph graph
方式 A 生成题目 MUST 通过可编译的 LangGraph StateGraph 执行（进程内 `invoke` / `ainvoke`），MUST NOT 仅依赖游离在图外的一次性脚本作为唯一出题路径。图 MUST 由 FastAPI 同进程加载；MUST NOT 将出题图部署为独立 HTTP Agent 服务。家长侧出题请求的成功与失败表现（题目 JSON、题量、缺密钥/未入库等错误）MUST 与现有 `primary-math-quiz` / `bailian-models` 要求兼容。

#### Scenario: Successful textbook quiz still returns questions
- **WHEN** 家长对已入库单元发起出题且百炼密钥可用
- **THEN** 接口返回与请求题量一致的题目列表，且服务端出题路径经过教材 StateGraph

#### Scenario: Textbook graph stays in-process
- **WHEN** FastAPI 处理教材出题请求
- **THEN** 出题在 API 进程内完成，不要求另行启动独立 Agent 进程或 Agent HTTP 端口

#### Scenario: Missing key still fails without inventing questions
- **WHEN** 未配置 `bailian_api_key` 时请求教材出题
- **THEN** 返回明确配置错误，响应中 MUST NOT 出现编造题目

### Requirement: Grading runs on an in-process LangGraph graph
答卷判分 MUST 通过可编译的 LangGraph StateGraph 执行（进程内调用），节点至少覆盖：准备题目与答卷输入、视觉判分或允许的演示回退、产出含逐题对错的 draft 结果。判分图 MUST 位于共用 Agent 能力中并由 FastAPI 调用。家长可见的判分结果字段（得分、逐题对错、`demo` 标记）与「确认后才写入成绩」行为 MUST 保持兼容。

#### Scenario: Grade attempt returns per-question results via graph
- **WHEN** 家长上传答卷并开始判分
- **THEN** 返回含每题对错的 draft 结果，且服务端判分路径经过判分 StateGraph

#### Scenario: Demo fallback still available when vision unavailable
- **WHEN** 未配置视觉密钥或视觉调用失败，且演示回退未关闭
- **THEN** 仍返回可展示的 draft 结果并标记为演示判分，MUST NOT 静默写入已确认成绩

#### Scenario: Unconfirmed grade is not final score
- **WHEN** 判分图产出 draft 但家长尚未确认
- **THEN** 该结果 MUST NOT 作为已登录账号的已确认成绩出现

### Requirement: Checkpointer policy for these graphs
本期无跨请求 interrupt 的出题图与判分图 MAY 在单次调用中不挂 Checkpointer。一旦图需要跨请求恢复状态（例如未来的确认 interrupt），系统 MUST 使用 Postgres Checkpointer，MUST NOT 以内存 Checkpointer 作为生产默认。

#### Scenario: One-shot invoke without durable interrupt
- **WHEN** 出题或判分为单次请求内完成且无 resume
- **THEN** 允许不写入 Checkpointer，请求结束后家长仍能拿到完整响应体

#### Scenario: Durable resume forbids memory checkpointer
- **WHEN** 图需要跨请求 `resume`
- **THEN** 必须使用 Postgres Checkpointer，不得默认使用 MemorySaver
