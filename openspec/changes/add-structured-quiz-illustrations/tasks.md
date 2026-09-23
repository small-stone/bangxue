# Tasks

## 1. Scene schema and renderer

- [ ] 1.1 定义 `row_of_groups` 场景类型与校验（合法 count、未知 kind 拒绝），并加单元测试覆盖合法/非法 scene
- [ ] 1.2 实现 SVG 渲染器：按 `groups[].count` 画出可数物体，用断言或快照测试验证「声明 6 个则 SVG 中有 6 个 item 节点」
- [ ] 1.3 增加 SVG→PNG（或 PDF 可嵌入位图）辅助函数，用固定样例 scene 跑通一次转换并检查输出非空

## 2. Generation pipeline

- [ ] 2.1 扩展出题 prompt / JSON schema：看图题可带 `scene`；纯文字题可省略；确认仍用 `bailian_api_key` + `qwen3.7-plus`，不新增文生图环境变量
- [ ] 2.2 在 `generate_questions` 清洗阶段：校验 scene、渲染 SVG，写入 `illustration`；校验失败则该题无插图且不阻断整卷；用假 generator 注入 scene 验证返回字段
- [ ] 2.3 确认 `POST /api/quizzes` 响应与 quiz store 持久化含 `illustration`（有图题），无图题行为与改造前一致

## 3. Result UI and PDF

- [ ] 3.1 结果页对有 `illustration.svg` 的题渲染插图（可用 `dangerouslySetInnerHTML` 或 `<img src="data:image/svg+xml...">`），无插图题仍只显示文字
- [ ] 3.2 更新 `pdf_paper`：有插图时在题干下嵌入位图；下载练习 PDF 后肉眼确认与结果页同题同图
- [ ] 3.3 若开启答案卷，答案 PDF 同样嵌入插图；确认未开启答案卷时答案链接仍 404

## 4. Smoke check

- [ ] 4.1 用一年级含「数一数 / 合起来」单元实际出题一次：至少一题带图，结果页可见，练习 PDF 可打开且计数与题意一致
