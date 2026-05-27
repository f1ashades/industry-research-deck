# 视觉工作流规则

这个 skill 的画面默认按“讲解视频 scene”处理，而不是把一张小插图贴进幻灯片。参考社区里更稳定的做法：Slidev / Marp / reveal.js 用 slide-as-code 把内容、布局和主题分离，Presenton / PreGenie 把生成、模板和导出拆成阶段，Remotion 用 React 组件分层合成视频，Manim / Motion Canvas 用代码精确描述动画/图形。落到本 skill，就是先产出结构化视觉分镜；如果当前 agent 能生图，就用 imagegen/image-2 生成高质量主视觉；否则才用 SVG scene fallback。

## 原则

1. **整页画布优先**：每段图像是 16:9 full-bleed scene，覆盖整个页面。不要生成小卡片、小 PPT、插在标题下面的小图。
2. **生图优先**：当前有 imagegen/image-2 时，优先生成 `sec-N.png`。`visual` schema 用来帮助写 prompt 和兜底，不是默认输出。
3. **scene spec 优先于口号**：`image_prompt` 必须描述文字清单、版式、主体、空间关系、镜头、光线、色彩、字幕安全区。只写“高质量、科技感、对比图”不合格。
4. **复杂关系先结构化再生图**：流程、因果、架构、生态关系，先用 schema 写清楚，再转成 image prompt；不要让模型自由发明密集小字。
5. **字幕安全区**：画面下方 28%-32% 保持视觉相对安静，字幕由 HTML 叠加，不让图像模型生成长文本。
6. **每段不同构图**：连续段落不要都用“中央节点图”。可轮换：左右对比、管线、系统工作台、仪表盘、风险闸门、人物/空间隐喻。
7. **可验证**：预览时检查图片是否覆盖 section、标题/字幕/来源是否互相遮挡、移动端是否可读。

## 分镜模板

```text
画布：1920x1080 full-bleed，主体占画面 65%-85%，下方 30% 字幕安全区干净。
信息角色：这张图负责呈现 <机制/关系/对比/风险>，字幕和长解释由 HTML 承担。
文字清单：主标题 <...>；标签 <...>；不要出现其他随机文字。
主体：<具体实体，不要只写“AI/科技/未来”>
动作：<实体之间如何流动、分叉、连接、对抗或被审核>
空间：<前景 / 中景 / 背景分别是什么>
构图：<wide shot / split-screen / overhead map / diagonal pipeline / editorial close-up>
风格：<固定风格后缀>
限制：no title card, no long text, no bullet list, no watermark, lower third clean
```

## 参考路径

- Slidev / Marp / reveal.js：slide-as-code，适合借鉴“内容、布局、主题、导出”分层，而不是一次性生成整页。
- Presenton / PreGenie：AI 生成演示的分阶段管线，适合借鉴“先大纲和结构，再视觉，再渲染检查”的流程。
- Remotion：React 组件化视频，适合把画面拆成可布局的层和 Sequence。
- Manim / Motion Canvas：用代码生成精确的解释动画，适合复杂流程和数学/工程图。
- AutoPresent/相关 GitHub 工作流：把 slide 文本、结构图和生成反馈分阶段处理，质量比一次性让模型吐完整幻灯片更稳。

## 调研链接

- Slidev: https://github.com/slidevjs/slidev
- Marp: https://github.com/marp-team/marp
- reveal.js: https://github.com/hakimel/reveal.js
- Presenton: https://github.com/presenton/presenton
- PreGenie: https://github.com/NUS-HPC-AI-Lab/PreGenie
- Remotion: https://github.com/remotion-dev/remotion
- Motion Canvas: https://github.com/motion-canvas/motion-canvas
