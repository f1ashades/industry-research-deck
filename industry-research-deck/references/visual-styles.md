# 风格预设

每个风格定义：HTML `data-style` 值 + CSS 变量 + 生图 prompt 后缀。

## 1. editorial-cinematic（默认）

**HTML**：`<body data-style="editorial-cinematic">`

**视觉特征**：
- 现代媒体长文/纪录片解释器主视觉
- off-white / charcoal 基底，cobalt blue、coral、green 作重点，不再单调深蓝
- 真实纸张、玻璃、贴纸、轻微胶片颗粒与清晰矢量标注混合
- 35mm editorial framing，前景/中景/背景层次清楚
- 图像里不放长标题，主要文字交给 HTML 标题和字幕

**生图 prompt 后缀**：
> "modern editorial cinematic illustration, crisp vector-meets-collage look, realistic paper and glass textures, clean off-white and charcoal base, cobalt blue and coral accents, professional magazine explainer aesthetic, 35mm editorial framing, clear foreground-midground-background, dramatic but natural lighting, high detail, no long text, no title card"

**适合**：默认行业研究、技术解释、人物/公司/趋势讲解。

---

## 2. kurzgesagt（扁平科普）

**HTML**：`<body data-style="kurzgesagt">`

**视觉特征**：
- 圆角扁平插画
- 大胆色块（蓝/橙/品红/青）
- 简化拟人角色 / 抽象图形
- 深蓝渐变背景（`#1a2540 → #2c3e80`）
- 字体：圆体无衬线（中文：思源黑体；英文：Inter Rounded）

**生图 prompt 后缀**：
> "flat illustration style, rounded shapes, bold flat colors (deep blue, orange, magenta, cyan), playful but clean, in the style of Kurzgesagt – In a Nutshell, no realistic textures, no photo-realism"

**适合**：科普、原理解释、面向大众的解读。

---

## 3. bloomberg（财经数据风）

**HTML**：`<body data-style="bloomberg">`

**视觉**：
- 黑/深蓝底（`#000000` / `#0a0e1a`）
- 涨绿（`#00d96a`）跌红（`#ff3a3a`）
- 衬线大数字（中文：思源宋体；英文：Roboto Slab）
- 数据网格背景

**生图 prompt 后缀**：
> "financial dashboard aesthetic, dark navy background, monochrome with red/green accent for charts, serif numbers, terminal/grid feel, Bloomberg style"

**适合**：财经、涨跌、业绩、市场分析。

---

## 4. vox（解释性新闻风）

**HTML**：`<body data-style="vox">`

**视觉**：
- 白/米白底
- 黑色无衬线大字
- 红色（`#e63946`）高亮 + 黄色（`#ffd60a`）注解
- 黑白照片 + 线条图表

**生图 prompt 后缀**：
> "explanatory journalism illustration, clean white background, bold black sans-serif text overlay, red and yellow highlight accents, simple linework, Vox/NYT Daily style"

**适合**：时事解读、调查、深度新闻。

---

## 5. bilibili-hardcore（B 站硬核风）

**HTML**：`<body data-style="bilibili-hardcore">`

**视觉**：
- 深紫黑底（`#0d0014`）
- 霓虹色高亮（`#00f0ff` 青、`#ff2bd6` 品红、`#fff700` 黄）
- 强动效（GSAP 入场、数字滚动）
- 弹幕风装饰
- 字体：思源黑体 Heavy

**生图 prompt 后缀**：
> "cyberpunk infographic style, deep purple-black background, neon cyan/magenta/yellow accents, glowing edges, sci-fi tech aesthetic, Bilibili hardcore science channel style"

**适合**：年轻向、技术向、中文网感强的内容。

---

## 6. stratechery（学术分析风）

**HTML**：`<body data-style="stratechery">`

**视觉**：
- 米白底（`#faf8f3`）
- 灰蓝主色（`#2c3e50`）+ 暗红强调（`#8b3a3a`）
- 衬线字（中文：思源宋体；英文：Georgia）
- 几何图表（线、圆、矩形）
- 留白多

**生图 prompt 后缀**：
> "academic analysis diagram style, cream background, slate-blue and dark-red accents, geometric shapes (lines, circles, rectangles), serif typography, plenty of whitespace, MIT Tech Review / Stratechery feel"

**适合**：战略分析、产业格局、严肃长读。

---

## 7. apple-keynote（极简风）

**HTML**：`<body data-style="apple-keynote">`

**视觉**：
- 纯白 / 纯黑切换
- 中央巨字 + 单图
- SF Pro 字体（中文：苹方）
- 大留白，单焦点

**生图 prompt 后缀**：
> "minimalist Apple Keynote slide style, pure white or pure black background, single central focal point, massive whitespace, hero shot composition"

**适合**：产品发布感、单一概念冲击、低数据密度内容。

---

## 自由描述

用户给"自定义风格描述"时，按下面方式处理：
1. 用户描述 → 提炼成 CSS 变量（背景色 / 主色 / 强调色 / 字体 / 圆角度）+ 生图 prompt 后缀
2. 写入 `deck/custom-style.css` 覆盖默认
3. 沿用 `templates/deck.html` 结构，只换 CSS

---

## 跨风格的通用规则

- 字幕始终居底，半透明黑底白字（保证可读）
- 数据源标注始终右下角小字
- 字号梯度：标题 ≥ 48px，正文 ≥ 24px（演讲距离决定）
- 每段持续 ≥ 12s（再短观众读不完字幕）
- 图像不要承担长文本；标题、字幕、数据源由 HTML 承担
- 移动端必须验证标题、图片、字幕、来源不重叠
