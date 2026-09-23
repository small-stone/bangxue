# Proposal

## Why

方式 A 要按单元检索课本，但仓库里还没有可重复执行的教材入库流程。本地已有多册人教版数学 PDF，需要先把「解析 → 按单元拆分 → 写入 pgvector」写成一份需求加一套代码，以后换一本书只改输入、不改流程。

## What Changes

- 在 `REQUIREMENTS.md` 写明教材入库是独立流程：一次处理一本，输入为 PDF 路径和元数据（学段、年级、科目、版本、学期），输出为按单元切分并带向量的知识块
- 代码放在 `apps/api/ingest/`，与 `agents/textbook/`（出题图）分开；不新增可部署服务
- 同一本（元数据相同）再次执行时替换该书已有块，不追加重复内容
- 第一本验收用本地的人教版数学一年级上册；其余已放在 `book/` 下的册次沿用同一命令
- PDF 只留在本机 `book/`，不提交进 git
- 本 change 不实现按教材出题、对话出题或 Jev

## Capabilities

### New Capabilities

- `textbook-ingest`：把一本教材 PDF 拆成可按单元检索的向量块，并允许用同一流程处理下一本

### Modified Capabilities

- （无）主规格尚未归档

## Impact

- **需求文档**：第 6 节补充可重复入库命令、目录位置和「先过滤元数据再检索」
- **FastAPI 工程**：新增 `apps/api/ingest/`；运行时仍是离线命令，不占用 API 进程
- **Agent**：`agents/textbook/` 只消费检索结果，不包含拆分实现
- **数据**：Postgres（已启用 pgvector）存教材块；连接使用本机 `bangxue` 库
- **Non-goals**：不出题、不生成练习 PDF、不处理方式 B、不把 `book/` 里的教材 PDF 提交到仓库
