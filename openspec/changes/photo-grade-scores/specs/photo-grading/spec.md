# Spec Delta

## Purpose

覆盖家长拍照上传答卷、触发智能判分、查看判分结果与单次练习错题，并在家长确认后才允许写入成绩。

## ADDED Requirements

### Requirement: Answer sheet photo upload
家长 MUST 能从待办或练习上下文进入拍照上传页，拍摄或从相册选择一页或多页答卷照片。页面 MUST 展示练习上下文标签（如年级科目、单元或对话摘要）与清晰度提示。未选择任何照片时，系统 MUST NOT 允许开始判分。

#### Scenario: Open upload from home todo
- **WHEN** 家长在首页待办点击「去上传」且存在可判分的练习上下文
- **THEN** 进入拍照上传页，展示该练习的上下文标签与上传区域

#### Scenario: Add multiple pages
- **WHEN** 家长已添加第 1 页照片并点击添加第 2 页
- **THEN** 系统接受第二张照片，且页列表显示已添加页与可继续添加的入口

#### Scenario: Cannot grade without photos
- **WHEN** 家长未添加任何答卷照片并尝试「开始判分」
- **THEN** 系统阻止提交并提示需要先拍摄或选择照片

### Requirement: Start grading with progress feedback
家长点击「开始判分」后，系统 MUST 对已上传答卷进行判分，并展示可观察的「判分中」状态。判分 MUST 输出每题对错、正确题数、总题数与得分率。判分失败或超时 MUST 给出可理解错误提示，且 MUST NOT 自动写入成绩记录。

#### Scenario: Successful grade
- **WHEN** 家长已上传清晰答卷并点击「开始判分」，判分成功
- **THEN** 进入判分结果页，展示总分（如 18/20）、得分率与逐题对错列表

#### Scenario: Grading failure stays unconfirmed
- **WHEN** 判分服务失败或超时
- **THEN** 家长看到错误或重试提示，本次不出现已确认成绩，也不写入成绩记录

### Requirement: Grading result and wrong-question entry
判分结果页 MUST 对齐墨金纸感结果稿：得分环、鼓励文案、出题方式标记、逐题对错。页面 MUST 提供「查看错题」与「成绩记录」入口。存在错题时，「查看错题」MUST 打开该次练习的错题详情；无错题时 MUST 明确说明没有错题。

#### Scenario: View wrong questions for a graded attempt
- **WHEN** 判分结果中至少有一题错误，家长点击「查看错题」
- **THEN** 系统展示该次练习的错题列表（题干与对错信息至少可见）

#### Scenario: Perfect score has no wrong list
- **WHEN** 全部题目正确，家长点击「查看错题」
- **THEN** 系统说明本次没有错题，不展示空的错题伪装列表

### Requirement: Parent confirms before score is saved
最终成绩 MUST 在家长确认之后才写入成绩记录。未确认的判分结果 MUST NOT 出现在成绩历史的已确认列表中。游客 MUST 能完成上传与查看判分结果，但 MUST NOT 将成绩同步到登录账号的成绩库。

#### Scenario: Confirm writes score
- **WHEN** 已登录家长在判分结果确认本次成绩
- **THEN** 该次练习出现在成绩记录中，并带出题方式、范围摘要、题量与得分

#### Scenario: Guest grades without account sync
- **WHEN** 游客完成判分并查看结果
- **THEN** 结果可本地查看；登录账号的成绩记录与错题本不增加该次记录
