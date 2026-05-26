# 生图能力与 adapter 约定

这个 skill 只要求“能为每段得到一张视觉图”，不把工作流绑定到某个供应商。优先用当前 agent 的内置生图能力；没有时再考虑 adapter；仍没有时用 SVG 占位图先跑通演讲。

## 选择顺序

1. **Agent 内置生图能力**：如果当前运行环境提供 image generation tool，直接用它生成 `deck/assets/img/sec-{N}.png`。这是 Codex/ChatGPT 类环境的首选路径，不要求用户配置 API key。
2. **OpenAI API adapter**：如果用户已经设置 `OPENAI_API_KEY`，可调用 `scripts/generators/openai-api.sh`。这是跨 agent 环境的通用付费路径。
3. **Gemini adapter**：如果用户已经设置 `GEMINI_API_KEY`，可调用 `scripts/generators/nano-banana.sh`。这是可选实验路径。
4. **Placeholder fallback**：没有任何生图能力时，运行 `scripts/generate-placeholders.py --script deck/script/script.json --out-dir deck/assets/img` 生成 SVG 占位图，然后继续组装 HTML。

不要把未内置的后端写成当前能力。即梦、文心、其他国内模型可以以后按下面接口新增 adapter，但当前 skill 不承诺已经支持。

## Adapter 接口

每个生成器放在 `scripts/generators/<backend>.sh`，统一接口：

```bash
<backend>.sh \
  --prompt "<中文/英文 prompt>" \
  --out "deck/assets/img/sec-1.png" \
  [--ref "deck/assets/img/sec-1.png"] \
  [--size 1920x1080]
```

约定：
- 输出目标图片到 `--out`。
- 成功时尽量写同名 `.json` 元信息，至少包含 `backend`、`model`、`size`。
- 支持 reference image 的后端才使用 `--ref`；不支持时忽略或在 prompt 里强化“保持同一系列视觉风格”。
- 不要在脚本里静默安装 SDK 或改用户环境。

## 风格一致性

1. 第 1 段先生成定调图，保存为 `sec-1.png`。
2. 第 2 段及之后，如果后端支持 reference image，传 `--ref deck/assets/img/sec-1.png`。
3. 如果后端不支持 reference image，把固定风格后缀追加到每段 prompt：`保持与系列其他图片一致的色彩、笔触、构图风格`。
4. 如果一轮生成后风格明显漂移，优先重写 prompt 再重生，不要引入额外检测脚本，除非用户明确需要自动化质检。

## Prompt 结构

每段 prompt 保持稳定结构。参考 OpenAI Academy 和 Runway 的公开提示词指南：清楚写出用途、主体、动作、场景、风格；需要控制画面时补充构图、光线、颜色、视角；不要只写抽象口号。这个 skill 的 HTML 模板会把生成图作为整页背景，因此 prompt 必须按 full-bleed scene 写。

```text
目的：为一段浏览器演讲生成 1920x1080 full-bleed 视觉 scene；主要信息由 HTML 标题/字幕承担。
画布：主体占画面 65%-85%，不是中央小插图；下方 28%-32% 保持视觉安静，留给字幕。
主体：<具体人物/物体/系统，不要只写“概念”>
动作：<主体正在做什么，或关系如何变化>
场景：<地点/背景/空间层级>
构图：<wide shot / close-up / rule of thirds / centered subject / layered foreground-midground-background>
镜头与光线：<35mm editorial / overhead / dramatic side light / soft window light / rim light>
色彩与材质：<固定调色板、纸张/玻璃/胶片颗粒/3D clay 等>
限制：no long text, no title card, no bullet list, no watermark, no logo, keep lower third clean for subtitles
```

LLM 可以自由发挥画面隐喻，但不要省略主体、动作、构图和光线。

## 禁止的低质量图

- 纯标题卡：一大段中文标题居中，几何背景，基本没有信息。
- PPT 套娃：图里又出现一张幻灯片、长段文字、项目符号。
- 小图贴片：主体只占画面中间一小块，四周大面积空白，放进 HTML 后像一张缩小的图片。
- 抽象空洞：只有光球、渐变、云雾、装饰线条，看不出段落机制。
- 错误信息图：密集小字、复杂流程图、不可读标签。复杂信息应由 HTML 字幕/来源区承载。

## 推荐画面类型

- **机制图**：少量实体 + 箭头 + 空间层级，例如“资料 → LLM → Wiki”，但实体要铺满画布。
- **隐喻场景**：把抽象过程变成真实动作，例如“研究员把文件投进编译机，输出会发光的知识地图”。
- **关系网络**：节点和连线，但只保留 5-9 个核心节点。
- **对比画面**：左旧方法、右新方法，视觉差异清楚。
- **风险画面**：错误信息被审查护栏拦住，适合讲限制和争议。

## 生成前的视觉 brief

为每段先写一句 brief，再写 prompt：

```text
本段视觉任务：用 <对比/管线/工作台/仪表盘/风险闸门/人物场景> 表达 <核心判断>。
画面不能做：标题卡 / 小插图 / PPT 套娃 / 长文字说明图。
画面必须做：full-bleed，占满 16:9，主体明确，底部字幕区干净。
```

如果没有真实生图后端，fallback SVG 会按 `visual_prompt` 的关键词选择 split-screen、pipeline、graph、dashboard 等 full-screen storyboard；它不是最终美术，但不能再输出“中间小卡片”。

## 默认风格：editorial-cinematic

用于行业研究和技术解释的默认风格，目标是“像一张现代媒体长文的主视觉”，不是儿童科普标题卡。

Prompt 后缀：

```text
modern editorial cinematic illustration, crisp vector-meets-collage look, realistic paper and glass textures, clean off-white and charcoal base, cobalt blue and coral accents, professional magazine explainer aesthetic, 35mm editorial framing, clear foreground-midground-background, dramatic but natural lighting, high detail, no long text, no title card
```

## 资料来源

- OpenAI Academy: https://openai.com/academy/image-generation/
- Runway Gen-4 Image Prompting Guide: https://help.runwayml.com/hc/en-us/articles/35694045317139-Gen-4-Image-Prompting-Guide
- Runway text-to-image guide: https://runwayml.com/resources/how-to-make-an-ai-image-with-text-prompt
- Runway image styles guide: https://runwayml.com/resources/ai-image-styles
