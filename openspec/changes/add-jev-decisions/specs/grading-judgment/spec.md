# Spec Delta

## Purpose

在答卷图片被视觉模型转成可核对的作答之后，用 Jev 给出每题对错倾向、置信度，以及是否应提示家长重拍。

## ADDED Requirements

### Requirement: Per-question judgment after vision extraction
系统 MUST 在视觉模型产出每题识别文本（及标准答案）之后，调用 Jev 判断该题为正确或错误，并返回置信度。系统 MUST NOT 用 Jev 直接读取答卷图片。

#### Scenario: Objective item judged from extracted text
- **WHEN** 视觉模型已给出某道客观题的识别作答，且该题存在标准答案
- **THEN** 系统展示该题的对错倾向与置信度，供家长在确认成绩前查看

#### Scenario: Vision has not produced an answer
- **WHEN** 某题没有可用的识别作答
- **THEN** 系统不对该题调用 Jev 做对错判断，并标记为未能识别

### Requirement: Retake when the sheet cannot be judged
系统 MUST 让 Jev 根据视觉模型给出的图像质量信号（模糊、缺页、关键区域不可读）判断是否要求重拍。当判断为需要重拍时，系统 MUST NOT 把该次上传记为已确认成绩。

#### Scenario: Blurry or incomplete photo
- **WHEN** 视觉模型报告图片模糊或疑似缺页，且 Jev 判断应重拍
- **THEN** 家长看到重拍提示，本次不写入最终成绩

#### Scenario: Photo is usable
- **WHEN** Jev 判断图像足以判分
- **THEN** 系统继续给出每题对错倾向，并进入家长确认

### Requirement: Comments and confirmation stay outside Jev
主观题的文字评语 MUST 仍由生成式大模型撰写。最终成绩 MUST 在家长确认之后才写入成绩记录。低置信度 MUST 在确认界面标出，且 MUST NOT 因此跳过家长确认。

#### Scenario: Low-confidence item still needs parent confirmation
- **WHEN** Jev 对某题给出低置信度
- **THEN** 该题在确认页被标为需留意，家长确认后系统才保存成绩

#### Scenario: Subjective item needs a written comment
- **WHEN** 题目为主观题且已完成对错或参考分判断
- **THEN** 评语来自生成式大模型，而不是 Jev 的生成文本
