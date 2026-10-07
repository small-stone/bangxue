# Spec Delta

## Purpose

让一年级看图类练习题用结构化场景程序化生成插图，保证图中可数物体数量与题意和答案一致，并在结果页与可打印 PDF 中一同展示。

## ADDED Requirements

### Requirement: Illustrated questions carry a structured scene
当一道题依赖图示才能作答时，出题结果 MUST 包含结构化场景描述（至少：场景类型、容器或分组列表、每组物体个数、物体种类标签）。不依赖图示的题目 MUST NOT 被强制附带场景。场景计数 MUST 与题干所述数量及答案逻辑一致。系统 MUST NOT 使用文生图模型生成这些插图。

#### Scenario: Counting scene matches the answer logic
- **WHEN** 生成一道「从左数第 N 个容器有 M 个物体」类题目且需要图示
- **THEN** 返回的场景中各容器物体个数可核验，且与题干与答案所指位置/数量一致

#### Scenario: Text-only question stays without scene
- **WHEN** 生成一道纯计算或不依赖图示的题目
- **THEN** 该题可以没有插图字段，家长仍能完整作答

### Requirement: Renderer draws exact object counts
系统 MUST 根据场景结构在进程内渲染插图，使图中可数物体的个数与场景中声明的个数完全一致。渲染 MUST NOT 调用外部 text-to-image API。渲染失败时，该题 MUST NOT 带着错误数量的图返回；可降级为无图并保留题干，或整次出题失败并返回明确错误。

#### Scenario: Drawn counts equal schema counts
- **WHEN** 场景声明某容器有 6 个物体
- **THEN** 渲染结果中该容器可见的可数物体恰好为 6 个

#### Scenario: No text-to-image dependency
- **WHEN** 生成带插图的练习卷
- **THEN** 插图由程序渲染完成，不依赖文生图模型密钥或模型名

### Requirement: Result page and PDF show the same illustration
结果页 MUST 在有插图的题干附近展示该插图。同一次练习的练习 PDF（及已生成的答案 PDF）MUST 嵌入同一插图内容，使家长打印后看到的图与屏幕一致。

#### Scenario: Parent sees illustration on result screen
- **WHEN** 练习结果中至少一题带插图
- **THEN** 结果页在对应题号下显示该图，不只显示文字题干

#### Scenario: Downloaded paper matches on-screen illustration
- **WHEN** 家长下载该次练习的 PDF
- **THEN** PDF 中对应题的插图与结果页展示为同一次渲染产物（或等价矢量内容）
