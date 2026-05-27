# PPT Scene System

这个文件描述 **SVG fallback** 路线：文字、卡片、箭头、流程、指标和表格由 HTML/SVG 程序化渲染。当前 skill 的主路径是 agent-native 生图；当没有可用生图能力、用户明确不要生图、或生图连续出现错字/版式错误时，再切到这里。

## 借鉴边界

- **可直接借鉴思路**：HTMLSlides 的组件库、make-slide 的主题参考、Presenton 的 schema + template 工作流、Slidev/Marp 的内容与样式分离、Remotion/Motion Canvas 的 scene/timeline 思维。生图路径也要借鉴这些项目的“先 schema、再版式”的思想。
- **不要直接内置重项目**：不要把 Presenton、Slidev、Remotion、Motion Canvas 当成本 skill 的硬依赖；它们会增加安装成本。只有用户明确要 PPTX/MP4/复杂动画时再接入。
- **不要复制整套社区代码**：可以采用 MIT/Apache 项目的设计思想和小型模式，但本 skill 的默认产物必须保持本地、轻量、可审查。

## Fallback 流水线

1. LLM 写 `script.json`，每段包含 narration 和 `visual` 结构化对象。
2. 如果 agent-native 生图能力和 adapter 都不可用，或生图连续失败，运行 `scripts/generate-slide-scenes.py` 生成 `deck/assets/img/sec-N.svg`。
3. 如果有生图能力，优先用 `image_prompt` 生成 `sec-N.png`，`visual` 只作为 prompt blueprint 和 fallback scaffold。
4. 运行 `scripts/assemble-deck.py` 组装 HTML。含 `visual` 的段落会自动标记 `data-visual-mode="slide-scene"`，标题由 SVG scene 承载，避免重复。
5. 预览后用浏览器检查：scene 覆盖全屏、字幕可读、没有文字裁切或卡片重叠。

## Visual Schema

每段建议写：

```json
{
  "id": "sec-2",
  "title": "聊天机器人回答问题，Agent 推进任务",
  "narration": "...",
  "visual": {
    "mode": "slide-scene",
    "layout": "comparison-cards",
    "kicker": "能力区别",
    "headline": "聊天机器人回答问题，Agent 推进任务",
    "subhead": "关键差异不是语言能力，而是能否把一个目标变成连续的外部行动。",
    "cards": [
      {"label": "CHATBOT", "title": "一次对话", "body": "用户问，模型答。输出通常停留在文本层面。"},
      {"label": "AGENT", "title": "持续执行", "body": "接收目标后，自己规划步骤、使用工具、验证结果、再交付产物。"}
    ],
    "flow": [
      {"title": "目标"}, {"title": "计划"}, {"title": "交付"}
    ]
  },
  "sources": []
}
```

## Layout 选择

| layout | 用途 | 内容上限 |
|---|---|---|
| `comparison-cards` | 两个概念/公司/路径对比 | 2 cards，每卡标题 1 行、正文 2-4 行 |
| `architecture-flow` | 三步流程、系统架构、任务链路 | 3 flow 节点 |
| `dashboard` | 指标、成本、规模、价格、趋势 | 3 metrics + 1 趋势图 |
| `matrix` | 4 个维度、风险、能力象限 | 4 cards |
| `statement` | 关键判断、转场、结论 | 1 大标题 + 1 callout |

内容超限时拆段，不要压缩字号硬塞。

## 视觉质量规则

- 画面必须像 PPT：大标题、明确层级、卡片、箭头、网格/纹理背景、稳定留白。
- 每张 scene 只表达一个判断；一个复杂问题拆成多张。
- 正文最多 2-4 行；解释性内容放 narration/subtitle。
- 不让 SVG/图片区域和底部字幕争夺注意力；底部 25%-30% 保持相对安静。
- 不用同一种 layout 连续超过 2 张，除非用户明确要统一模板。

## 何时接入外部项目

- 要真实可编辑 PPTX：优先考虑 Presenton 或 PptxGenJS 路线。
- 要 Markdown/演讲 deck：可考虑 Slidev/Marp，但默认 HTML deck 更轻。
- 要高质量 MP4/头像画中画/转场：接 Remotion；只做图形动画也可考虑 Motion Canvas。
- 要完整产品化编辑器：Presenton/HTMLSlides 更适合，不应把本 skill 变成它们的复制品。
