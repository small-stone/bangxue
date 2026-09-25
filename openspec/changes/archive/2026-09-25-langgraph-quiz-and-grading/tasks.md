# Tasks

## 1. Textbook LangGraph

- [x] 1.1 在 `agents/textbook` 实现可编译 StateGraph（至少：准备课文 → 生成题目），错误写入 state 并由门面转为现有 `TextbookError`。验证：`build_graph()` 返回非 `None` 且可 `invoke`
- [x] 1.2 将 `generate_questions`（及 `POST /api/quizzes` 所用路径）改为只经该图执行，删除或停用旁路直调。验证：有密钥时出题成功；无 `bailian_api_key` 时仍返回配置错误且无编造题
- [x] 1.3 在 `apps/api/README.md` 注明方式 A 出题走 LangGraph、进程内调用、本期不挂 Checkpointer。验证：README 含上述三点

## 2. Grading LangGraph

- [x] 2.1 在 `agents/shared` 实现判分 StateGraph（准备输入 → Vision/演示回退 → draft），复用现有 `vision_grade`/`demo_grade`。验证：无密钥时 `demo=true` 的稳定结果；图 `invoke` 可单测
- [x] 2.2 `grade_questions` 与 `POST /api/grading/attempts` 改为只经判分图；确认接口仍为 REST、不进图。验证：判分 → 游客确认 401 → 登录确认 → `/api/scores` 可见；响应字段与改前兼容
- [x] 2.3 README 补充判分图位置与「确认不走 interrupt / 无 MemorySaver 默认」。验证：文档可检索到判分图与 Checkpointer 策略

## 3. Regression slice

- [x] 3.1 走通教材出题 → PDF → 上传判分 → 确认成绩。验证：前端主路径无断；方式 B 对话出题未改图仍可用
