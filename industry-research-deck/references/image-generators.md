# 生图能力与 adapter 约定

这个 skill 只要求“能为每段得到一张视觉图”，不把工作流绑定到某个供应商或具体工具名。**当前 agent 自判能生图时，生图是主路径**；没有时再考虑 adapter；仍没有或连续失败时，用结构化 SVG scene 兜底。

用户反馈过：新版 image-2 已经能做出高质量中文 PPT/生态图风格主视觉。之前 skill 生图效果差，主要不是模型能力问题，而是工作流问题：prompt 太抽象、没有固定文字清单、没有明确版式、没有参考图保持风格、没有生成后纠错迭代，还把 fallback SVG 当成默认主路径。

## 选择顺序

1. **Agent-native 生图能力**：如果当前运行环境提供任何可由 agent 调用的生图/修图能力，直接用它生成 `deck/assets/img/sec-{N}.png`。这可以是工具、skill、插件、MCP、IDE 内置能力或产品原生图片能力；不要限定为某个名字。
2. **Pi gpt-image-2 skill**：如果 `~/.pi/agent/skills/gpt-image-2/scripts/gen.sh` 存在，且 `codex` CLI 支持 `--enable image_generation`，可调用 `scripts/generators/gpt-image-2.sh` 生成 `deck/assets/img/sec-{N}.png`；这是当前 Pi 环境里常见的 agent-native 路径。
3. **OpenAI API adapter**：如果用户已经设置 `OPENAI_API_KEY`，可调用 `scripts/generators/openai-api.sh`。这是跨 agent 环境的通用付费路径。
4. **Gemini adapter**：如果用户已经设置 `GEMINI_API_KEY`，可调用 `scripts/generators/nano-banana.sh`。这是可选实验路径。
5. **Structured SVG fallback**：没有任何生图能力、或生图连续失败时，运行 `scripts/generate-slide-scenes.py --script deck/script/script.json --out-dir deck/assets/img` 生成 SVG scene，然后继续组装 HTML。

不要把未内置的后端写成当前能力。即梦、文心、其他国内模型可以以后按下面接口新增 adapter，但当前 skill 不承诺已经支持。

## Agent-native 生图判断

执行 skill 的 agent 必须自己判断当前会话是否“能生图”。不要只检查 `image_gen`、`$imagegen` 这样的特定名称；它们只是 Codex/ChatGPT 环境里的例子。满足下面条件即可视为可生图：

1. 当前会话有可由 agent 直接调用的工具 / skill / plugin / MCP / IDE 能力，能根据文本 prompt 或参考图生成、编辑位图。
2. 生成结果能落盘到当前工作区，最终路径必须是 `deck/assets/img/sec-{N}.png` 或同目录下可被 `assemble-deck.py` 识别的图片。
3. 不需要用户手工去网页下载、截图、复制附件；如果只能得到临时 URL 或聊天附件，agent 必须把它保存为项目文件后才算成功。
4. 当前能力允许至少一次检查和定向重生/编辑。无法检查、明显错字、主体没有占满画面时，不要硬用。

模型名称本身不等于生图能力。比如某个 IDE 里用了更新的 GPT 文本模型，但没有开放图片工具或图片 API，对本 skill 来说仍然是“无 agent-native 生图”，应继续看 adapter；反过来，非 OpenAI agent 只要暴露了可保存位图的图片工具，也应该走生图主路径。

执行时建议在最终报告里写清楚 `visual_backend`：`agent-native` / `openai-api` / `gemini` / `svg-fallback`。

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
3. 如果后端不支持 reference image，把固定风格后缀追加到每段 prompt：`保持与第 1 张相同的深色科技信息图风格、蓝色霓虹光效、3D 圆形平台、细线网络、中文标题排版、电影级对比度`。
4. 如果一轮生成后风格明显漂移，优先用 reference image 或复制完整风格描述重生。

## Prompt 结构

每段 prompt 保持稳定结构。参考 OpenAI Academy、Runway 和主流图像模型提示词指南：清楚写出用途、主体、动作、场景、风格；需要控制画面时补充构图、光线、颜色、视角；要生成信息图/PPT 图时，必须给出**准确文字清单和版式位置**，不要只写抽象口号。这个 skill 的 HTML 模板会把生成图作为整页背景，因此 prompt 必须按 full-bleed scene 写。

```text
用途：为一段浏览器演讲生成 1920x1080 full-bleed 中文 PPT/信息图主视觉。
画布：16:9，主体占满画面；下方 28%-32% 保持视觉安静，留给字幕。
文字：必须准确出现这些文字，且不要出现其他大段文字：
- 主标题：<短标题，建议 8-16 个汉字；可含 AI / API 等英文缩写>
- 标签：<2-8 个短标签，每个 2-8 个汉字>
版式：<左标题右生态图 / 中央枢纽放射 / 左右对比卡 / 三步流程 / 仪表盘>
主体：<具体平台、节点、图标、卡片、连接线、数据面板>
空间关系：<中心是什么，周围有哪些模块，如何连接>
风格：<深色科技生态图 / editorial cinematic / 3D glassmorphism / clean keynote>
光效与材质：<蓝色霓虹、玻璃、金属、发光连线、城市/云/数据中心背景>
限制：no watermark, no random text, no tiny unreadable paragraphs, no cropped title, lower third clean for subtitles
```

LLM 可以自由发挥画面隐喻，但不要省略文字清单、版式、主体、空间关系和光线。

## 中文 PPT / 信息图专用实践

你的 prompt 要像给设计师的 brief，而不是给模型的关键词堆。成熟做法：

1. **先列文字，再描述画面**：把主标题和标签逐条列出，要求“只出现这些文字”。短标签可以交给 image-2；长段解释留给字幕。
2. **指定版式**：例如“左侧巨大标题，右侧中心平台向 6 个生态节点放射连接线”。不要只写“做一张生态图”。
3. **指定层级**：主标题最大，标签次级，装饰文字最少。不要让图像模型自由添加段落。
4. **指定安全区**：底部 28%-32% 干净，给 HTML 字幕。
5. **用第 1 张当风格 reference**：后续段落复制它的色彩、材质、光效和镜头语言。
6. **检查后迭代**：如果错字、漏字、随机字、标题被裁切，定向编辑/重生一次；仍失败再切 SVG fallback。

适合 image-2 的画面类型：
- 标题型生态图：左侧大标题，右侧中心枢纽 + 5-8 个模块节点。
- 对比型信息图：左右两组大卡片，每组只放短标题和短标签。
- 流程型画面：3-5 个步骤节点，标签短且明确。
- 战略地图：中心能力平台，周围业务/生态/基础设施节点。

不适合纯生图、应该切 SVG fallback 的情况：
- 必须 100% 准确的大段中文正文。
- 表格、代码、细小脚注、复杂财务数字。
- 用户要求可编辑文字、可导出 PPTX、或需要严格对齐的 UI 组件。

## 禁止的低质量图

- 纯标题卡：一大段中文标题居中，几何背景，基本没有信息。
- PPT 套娃：图里又出现一张空幻灯片、长段文字、项目符号，但没有信息结构。
- 小图贴片：主体只占画面中间一小块，四周大面积空白，放进 HTML 后像一张缩小的图片。
- 抽象空洞：只有光球、渐变、云雾、装饰线条，看不出段落机制。
- 错误信息图：密集小字、随机乱码、复杂流程图、不可读标签。复杂信息应由 HTML 字幕/来源区承载，或切 SVG fallback。

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

如果没有真实生图后端，fallback SVG 会按 `visual` schema 输出 PPT scene；它不是最终美术，但必须能承载结构和文字。

## 默认风格：editorial-cinematic

用于行业研究和技术解释的默认风格，目标是“像一张现代媒体长文的主视觉”，不是儿童科普标题卡。

Prompt 后缀：

```text
modern editorial cinematic illustration, crisp vector-meets-collage look, realistic paper and glass textures, clean off-white and charcoal base, cobalt blue and coral accents, professional magazine explainer aesthetic, 35mm editorial framing, clear foreground-midground-background, dramatic but natural lighting, high detail, no long text, no title card
```

## 资料来源

- OpenAI Academy: https://openai.com/academy/image-generation/
- OpenAI image generation docs: https://platform.openai.com/docs/guides/image-generation
- Runway Gen-4 Image Prompting Guide: https://help.runwayml.com/hc/en-us/articles/35694045317139-Gen-4-Image-Prompting-Guide
- Runway Image References Guide: https://help.runwayml.com/hc/en-us/articles/40042718905875-Gen-4-Image-References-Guide
- Runway text-to-image guide: https://runwayml.com/resources/how-to-make-an-ai-image-with-text-prompt
- Runway image styles guide: https://runwayml.com/resources/ai-image-styles
