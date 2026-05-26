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

每段 prompt 保持稳定结构：

```text
<视觉风格后缀>
主题：<deck title>
段落：<section title>
画面：<具体主体、动作、空间关系>
构图：16:9，主体清晰，字幕安全区不要放关键文字
限制：不要 photorealism，不要水印，不要 UI 截图，不要小字
```

LLM 可以自由发挥画面隐喻，但不要省略主体、构图和限制条件。
