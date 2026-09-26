# 备选视觉 · 墨金纸感

路径：`docs/mockups/alt-ink-amber/`  
**不覆盖**根目录下的珊瑚橙主方案。

对应同一套需求流程（双入口出题 → PDF → 拍照判分 → 成绩），换一套视觉语言便于对比选型。

## 与主方案差异

| | 主方案（根目录） | 本方案（alt-ink-amber） |
|--|--|--|
| 气质 | 轻快家长端、珊瑚活力 | 书房纸感、暖金可信 |
| 底色 | 暖白 `#FAFAF8` | 石纸色 `#F3F1EB` + 细横纹 |
| 主色 | 珊瑚橙 `#FF6B4A` | 琥珀金 `#C47A1A`（选中 / CTA / 主入口） |
| 结构色 | 暖炭黑 | 深墨 `#161616` 仅用于正文，**不作大块选中底** |
| 主入口 | 珊瑚实心卡 | 琥珀金实心卡（教材）+ 描边卡（对话） |
| 圆角 | 偏圆（~20px / 胶囊） | 更利落（~12–14px） |
| 品牌字 | 无衬 | 衬线「帮学」 |

## Token

| 角色 | 值 | 用途 |
|------|------|------|
| 60% 底 | `#F3F1EB` | 纸感背景 |
| 30% 墨 | `#161616` | 正文文字（不作选中底色） |
| 10% 金 | `#C47A1A` | CTA、选中 chip、主入口、进度、得分环 |
| 纸面 | `#FFFEFA` | 卡片底 |
| 错误 | `#C44B3C` | 错题态 |

## 文件

| 文件 | 页面 |
|------|------|
| `mockup-00-home.png` | 首页双入口 |
| `mockup-01-select.png` | 按教材选题 |
| `mockup-01b-chat.png` | 对话出题（确认在结果卡内，输入区贴底） |
| `mockup-02-range.png` | 出题范围 |
| `mockup-03-config.png` | 出题设置 |
| `mockup-04-pdf.png` | PDF 已生成 |
| `mockup-05-upload.png` | 拍照上传 |
| `mockup-06-result.png` | 判分结果 |
| `mockup-07-scores.png` | 成绩记录 |
| `mockup-07b-wrongbook.png` | 错题本 |
| `mockup-08-me.png` | 我的 |
| `mockup-09-login.png` | 登录 |

源文件：`_html/screens.html`，重导出：`node _html/capture.cjs`
