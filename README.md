# bangxue（帮学）

家长端智能出题与判分：按教材 / 对话双入口 → PDF → 拍照判分。

## 应用入口

| 目录                 | 说明                                   |
| -------------------- | -------------------------------------- |
| [apps/web](apps/web) | 前端 Vite + React SPA                  |
| [apps/api](apps/api) | FastAPI；Agent 在 `agents/` 进程内调用 |

产品需求见 [REQUIREMENTS.md](REQUIREMENTS.md)。界面参考见 [docs/mockups](docs/mockups)。规格与变更见 [openspec](openspec)。

## 一期结构

- 两个可部署单元：`apps/web`、`apps/api`
