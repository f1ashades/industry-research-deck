# 视觉工作流规则

这个 skill 的画面默认按“讲解视频 scene”处理，而不是把一张小插图贴进幻灯片。参考社区里更稳定的做法：HTMLSlides / make-slide 用组件化 HTML 做 PPT，Presenton 用模板系统生成可导出演示，Remotion 用 React 组件分层合成视频，Manim / Motion Canvas 用代码精确描述动画/图形，Slidev/Marp 把内容和布局分离。落到本 skill，就是先产出结构化视觉分镜，再生成全屏 PPT scene。

## 原则

1. **整页画布优先**：每段图像是 16:9 full-bleed scene，覆盖整个页面。不要生成小卡片、小 PPT、插在标题下面的小图。
2. **PPT scene 优先**：默认按 [ppt-scene-system.md](ppt-scene-system.md) 写 `visual` schema，由 `generate-slide-scenes.py` 渲染标题、卡片、流程、指标和结构。
3. **scene spec 优先于口号**：如果还要写 `visual_prompt`，必须描述主体、动作、空间关系、镜头、光线、色彩、字幕安全区。只写“高质量、科技感、对比图”不合格。
4. **复杂关系用可控图形**：流程、因果、架构、数学/工程机制，优先用 SVG/HTML/Manim/Remotion 这类可控图形思路；不要依赖图像模型渲染密集小字。
5. **字幕安全区**：画面下方 28%-32% 保持视觉相对安静，字幕由 HTML 叠加，不让图像模型生成长文本。
6. **每段不同构图**：连续段落不要都用“中央节点图”。可轮换：左右对比、管线、系统工作台、仪表盘、风险闸门、人物/空间隐喻。
7. **可验证**：预览时检查图片是否覆盖 section、标题/字幕/来源是否互相遮挡、移动端是否可读。

## 分镜模板

```text
画布：1920x1080 full-bleed，主体占画面 65%-85%，下方 30% 字幕安全区干净。
信息角色：这张图负责呈现 <机制/关系/对比/风险>，标题和字幕由 HTML 承担。
主体：<具体实体，不要只写“AI/科技/未来”>
动作：<实体之间如何流动、分叉、连接、对抗或被审核>
空间：<前景 / 中景 / 背景分别是什么>
构图：<wide shot / split-screen / overhead map / diagonal pipeline / editorial close-up>
风格：<固定风格后缀>
限制：no title card, no long text, no bullet list, no watermark, lower third clean
```

## 参考路径

- HTMLSlides / make-slide：组件化 HTML PPT，适合借鉴版式、密度限制和单文件演示结构。
- Presenton：模板 + 导出系统，适合需要 PPTX/PDF 或产品化编辑时参考。
- Remotion：React 组件化视频，适合把画面拆成可布局的层和 Sequence。
- Manim / Motion Canvas：用代码生成精确的解释动画，适合复杂流程和数学/工程图。
- Slidev/Marp：Markdown 内容与布局分离，适合可维护的演示结构。
- AutoPresent/相关 GitHub 工作流：把 slide 文本、结构图和生成反馈分阶段处理，质量比一次性让模型吐完整幻灯片更稳。
