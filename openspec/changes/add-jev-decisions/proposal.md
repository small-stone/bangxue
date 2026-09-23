# Proposal

## Why

出题质量和答卷对错里有一批封闭判断（信息够不够、是否贴合教材、每题对错、要不要重拍）。这些判断若都交给生成式大模型，又慢又难拿到稳定的类型化结果。引入 TypeSafe **Jev**（System One）专门做这类判断，生成与看图仍留给现有大模型。

## What Changes

- 在需求与实现中增加 Jev，覆盖两类判断：
  - **判分判断**：视觉模型识别答卷之后，由 Jev 给出每题对错倾向与置信度，并判断是否因模糊/缺页需要重拍
  - **流程判断**：方式 B 判断对话信息是否足够出题（否则追问）；方式 A 判断生成题目是否落在所选教材范围内
- 主观题评语、题目正文、PDF、答卷识图仍由 OpenAI / Claude（文本 + Vision）完成
- 成绩仍须家长 HITL 确认后落库；Jev 的低置信度只提高「需人工看」的提示，不自动跳过确认
- 更新 `REQUIREMENTS.md` 技术栈与判分/出题流程描述（本 change 的实现任务，规划阶段不改该文件）
- Jev 经 TypeSafe 云端 API 调用，密钥只来自环境变量；不单独部署 Jev 服务

## Capabilities

### New Capabilities

- `grading-judgment`：答卷识别之后的对错、置信度与重拍判断
- `flow-judgment`：出题前信息是否足够、出题后是否贴合教材范围

### Modified Capabilities

- （无）主规格目录仍为空；`repo-layout` 尚未归档进 `openspec/specs/`

## Impact

- **前端**：判分结果展示置信度与「建议重拍」；对话页展示追问；教材出题确认前可看到「超出范围」提示
- **FastAPI**：在共用判分路径与两条出题路径中调用 Jev 客户端；短调用，进度仍跟在现有识图/出题流式反馈里
- **Agent**：方式 A / B 图中增加判断节点；判分放在 `agents/shared`，不把 Jev 拆成独立进程
- **数据**：练习/成绩可存 Jev 判断与置信度；不新增向量库。Jev 不替代 Postgres
- **外部依赖**：TypeSafe Jev API（`TYPESAFE_API_KEY` 或等价环境变量）
- **Non-goals**：Jev 不生成题目、不写评语、不看图、不替代家长确认；一期不做独立判分 worker
