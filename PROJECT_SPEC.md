# Shower Agent MVP

目标：上传图片 → 生成Shot1(模板锚点) → 确认 → 生成Shot2-7(6张交付图)

## 规则
- Shot1 只是锚点，不作为最终交付
- Shot2-7 必须基于同一人物与场景（锁定）
- 支持按花洒类型匹配 Skill（Boost / LargePanel / Filter / TravelFilter / Descale）
- 第一版不接真实生成，只做 mock 返回图片URL，跑通流程

## 输出
- 一个网页：上传区 + 按钮 + 结果区（7张卡片）