---
name: industry-research-deck
description: |
  把"行业调研 / 主题讲解"自动做成一份**可在浏览器播放的 HTML 演讲**（默认 2 分钟、5-6 段、配图+TTS+字幕+数据源标注），不渲染 MP4。
  触发场景：用户说"做个调研讲解 / 出一份 N 分钟演讲 / 帮我讲讲 X 为啥 Y / 做个 hyperframes 演讲 / 做个短视频草稿"。
  整合**联网搜索能力**(优先 Tavily 深度检索;agent 自带的 web_search / web_fetch 是合格的下位替代;也支持用户直接喂资料)、edge-tts 配音、可用生图能力(优先使用当前 agent 的内置生图;可选 OpenAI/Gemini adapter;否则占位图)、HTML 母版组装。
  风格默认 Kurzgesagt 扁平科普风，可换。
---

# Industry Research Deck

把任意主题做成一份本地可播的 HTML 演讲。本 skill 是**总指挥**：LLM 负责调研判断、叙事和视觉创意；脚本负责依赖检查、配音、占位图和 HTML 组装这些机械且容易出错的环节。

## 何时触发

用户说：
- "做个/出一份调研演讲""讲讲 X 为什么 Y"
- "做个 N 分钟讲解 / 短视频草稿"
- "做个 hyperframes 演讲 / HTML 演讲"
- "把这个主题做成短片"

## 工作流总览

```
0. 依赖自检   →  1. 澄清需求    →  2. 信息检索   →  3. 拆段写脚本
                                                           ↓
6. 本地预览  ←  5. HTML 组装   ←  4a/4b. 并行生图 + 配音
```

不渲染 MP4。最终产物是 `deck/deck.html` + `assets/` 目录，浏览器打开就能播。

下文的 `scripts/...` 和 `templates/...` 都相对本 skill 目录；输出目录 `deck/...` 相对用户当前工作区。

---

## 0. 依赖自检（**最先做**,缺哪个引导装哪个）

先运行 `scripts/check-deps.sh`。不要静默自动装依赖；硬依赖缺失时提示用户手动安装后再继续。

**严格规则**：如果 `scripts/check-deps.sh` 返回非 0，不要继续生成正式演讲，不要跳过 TTS，也不要只给文字回答。必须先把缺失项和安装命令告诉用户，等待用户安装或明确授权“先做无声草稿”。只有用户明确说可以接受无声草稿时，才允许跳过 §4b，并在最终报告里标明“无声草稿，未生成音频/字幕”。

| 工具 | 类型 | 检测命令 | 缺失时提示 |
|---|---|---|---|
| **联网搜索能力** | 硬依赖(三选一) | 见下方决策表 | 见下方决策表 |
| `edge-tts` | 硬依赖（正式配音版缺一不可） | `which edge-tts` | `uv tool install edge-tts`(或 `pip install --user edge-tts`) |
| `python3` | 硬依赖 | `python3 --version` | macOS 自带;Linux 用包管理装 |
| `ffprobe` | 可选 | `ffprobe -version` | 可用于精确检查 TTS 时长;缺失不阻塞 |

### 联网搜索能力决策

这个 skill 的"硬依赖"是**能联网做 5 次主题搜索**,不是 Tavily 本身。优先级:

1. **Tavily CLI**(首选):`which tvly && tvly auth status` 通过。质量最稳——支持 `--depth advanced` 深度搜索,直接吐 JSON,信源带发布时间。命令见第 2 节。
2. **Agent 内置 web_search / web_fetch**(下位替代):当前 agent 提供这类工具时直接用。让 LLM 自己规划 3–5 次搜索,覆盖原理 / 数据 / 玩家 / 风险维度,把结果手工整理到 `deck/research/notes.md`。Claude / Claude Code / ChatGPT 等环境默认走这条路。
3. **用户提供素材**:如果用户上传了 PDF / URL / 自己的笔记,完全跳过检索环节,直接进 §3 拆段。

三条都不可用时再中断流程,告诉用户:**装 Tavily(`uv tool install tavily-cli && tvly login --api-key tvly-...`,key 在 https://app.tavily.com),或换到带联网工具的 agent,或提供已有资料。**

> HyperFrames CLI 不是硬依赖。本 skill 默认**只输出 HTML**,不调用 hyperframes 渲染。
> 如果用户明确要求"也输出 MP4",再提示装:`npm i -g @heygen/hyperframes` 并在最后跑一次 `hyperframes render deck.html -o deck.mp4`。

---

## 1. 澄清需求（最多问 1 轮，能默认就默认）

需要从用户输入中确定：

| 字段 | 默认值 | 何时必须问 |
|---|---|---|
| **主题** | （从 prompt 提取） | 提取不到时问 |
| **时长** | 120s | 用户说"短/长"时澄清 |
| **段数** | `round(时长 / 24)` 段 | 不问 |
| **风格** | `kurzgesagt`（扁平科普） | 用户说了"换风格"或"自由描述"时按 [references/visual-styles.md](references/visual-styles.md) 走 |
| **语言** | 中文 | 用户用英文交流时改 en |
| **配音音色** | `zh-CN-XiaoxiaoNeural`（女）/ `zh-CN-YunxiNeural`（男） | 见 [references/tts-voices.md](references/tts-voices.md) |
| **生图方式** | 优先用当前 agent 的内置生图能力；没有则用 adapter 或占位图 | 用户明确指定、或有多个付费/外部后端可用时问 |
| **是否输出 MP4** | 否 | 用户说"要视频"时改 yes |

**反问示例**：「主题我理解是「X」，2 分钟、中文女声、扁平科普风、用 {后端} 生图，OK 我开始 ── 任何一项要改？」

---

## 2. 信息检索

根据 §0 决策结果选一条路。**目标固定**:产出 `deck/research/01-*.json` ... `04-*.json` + `deck/research/notes.md`,每条数据点带 url + 发布时间 + 引用片段。

```bash
mkdir -p deck/research deck/assets/{img,audio,subtitle} deck/script
```

### 路径 A:Tavily CLI(首选)

```bash
# 多角度检索:3-5 个 query,覆盖不同维度
tvly search "<主题> 是什么 原理 2026" --depth advanced --max-results 6 --json > deck/research/01-basic.json
tvly search "<主题> 数据 涨幅 规模 2026" --depth advanced --max-results 6 --json > deck/research/02-data.json
tvly search "<主题> 玩家 公司 财报 业绩" --max-results 6 --json > deck/research/03-players.json
tvly search "<主题> 风险 争议 未来" --max-results 5 --json > deck/research/04-risk.json
# 英文补充(可选,提升信源多样性)
tvly search "<topic in English> 2026 trend" --max-results 5 --json > deck/research/05-en.json
```

### 路径 B:Agent 自带 web_search / web_fetch

LLM 自己规划 3–5 次搜索,覆盖同样 4 个维度(基础原理 / 数据规模 / 玩家格局 / 风险争议),按需 web_fetch 展开关键页面。把每次搜索整理成 `deck/research/0N-<维度>.md`(markdown 格式即可,不必强求 JSON),字段:`title / url / published / snippet`。

**质量提示**:agent web_search 的结果通常没有 Tavily 那么干净的结构化输出,要主动 web_fetch 关键页面拿原文,避免只用 snippet 做事实判断。

### 路径 C:用户提供素材

跳过本节,直接到 §3。在 `notes.md` 里标明"信源来自用户上传材料 X、Y、Z",便于在 `script.json` 的 `sources` 字段如实标注。

---

**无论哪条路径**:最后提炼关键数据点到 `deck/research/notes.md`,每条带 url(或用户素材标识)+ 发布时间 + 引用片段。这份 notes 是 §3 拆段的唯一输入。

---

## 3. 拆段写脚本

**默认走 L1 结构约束 + 可选展开 L2 叙事框架**：

- L1（始终遵守）：N 段，每段 `{标题, 配音文案, 视觉提示词, 数据源 url[]}`；首段必须是钩子；末段必须收束
- L2（按需读）：如果觉得节奏需要参考，**主动**读 [references/narrative-patterns.md](references/narrative-patterns.md)，选一个模板套用

输出到 `deck/script/script.json`：

```json
{
  "title": "...",
  "duration_sec": 120,
  "style": "kurzgesagt",
  "voice": "zh-CN-XiaoxiaoNeural",
  "sections": [
    {
      "id": "sec-1",
      "duration_sec": 20,
      "title": "...",
      "narration": "...约 70-90 字（中文讲解 ≈ 3.5-4.5 字/秒）...",
      "visual_prompt": "扁平科普风插画，<具体内容>，<画面构图>，<配色>",
      "sources": [{"label": "来源名", "url": "https://..."}]
    }
  ]
}
```

**字数提示**：中文产业讲解按 **3.5-4.5 字/秒** 写稿；20s 建议 70-90 字，复杂概念靠近 70-80 字。英文按 **2.0-2.5 words/sec**。生成脚本时宁可略短，避免 TTS 超时。

---

## 4. 素材生成（4a + 4b 可并行）

进入本节前必须已经通过 §0 的依赖自检。若 `edge-tts` 缺失，正式流程应停在 §0；只有用户明确授权“无声草稿”时，才跳过 §4b。

### 4a. 配图（生图能力可插拔）

详见 [references/image-generators.md](references/image-generators.md)。生图是“能力”而不是必须绑定某个供应商：

- 当前 agent 有内置 image generation tool 时，直接使用内置生图能力，把结果保存为 `deck/assets/img/sec-{N}.png`。
- 如果没有内置生图，但用户已配置 adapter 凭证，可调用 `scripts/generators/openai-api.sh` 或 `scripts/generators/nano-banana.sh`。
- 如果没有任何生图能力，运行 `scripts/generate-placeholders.py --script deck/script/script.json --out-dir deck/assets/img` 生成占位图，保证 HTML 演讲流程先跑通。
- 不要声称即梦、文心等后端已经内置；需要时按 adapter 接口新增脚本。

**风格一致性**：第一张作为 reference，后续段在 prompt 末尾追加「保持与第一张相同的视觉风格、配色、笔触」。

输出：`deck/assets/img/sec-{N}.png`；占位图 fallback 会输出 `deck/assets/img/sec-{N}.svg`，组装脚本会自动优先使用已存在的图片文件。

### 4b. 配音 + 字幕

用 `scripts/synthesize-voice.sh` 为每段生成 mp3 + vtt 字幕：

```bash
scripts/synthesize-voice.sh --voice "$VOICE" --text "$NARRATION" --out-dir deck/assets --id sec-1
```

`edge-tts --write-subtitles` 输出 VTT 字幕，HTML 播放器会按 `data-subtitle` 加载并同步显示。

---

## 5. HTML 组装

用脚本把 `script.json` 注入 [templates/deck.html](templates/deck.html)。不要手写 HTML 注入逻辑，避免标题、URL、JSON attribute 转义出错：

```bash
scripts/assemble-deck.py --script deck/script/script.json --out deck/deck.html
```

脚本会生成每段 `<section>`：

```html
<section data-id="sec-1" data-duration="20"
         data-audio="assets/audio/sec-1.mp3"
         data-subtitle="assets/subtitle/sec-1.vtt"
         data-sources='[{"label":"来源名","url":"https://..."}]'>
  <img src="assets/img/sec-1.png" alt="...">
  <h2>...标题...</h2>
</section>
```

母版自带「自动播放配音 → 同步切段 → 显示字幕」的 JS。
**风格切换**：把 `templates/deck.html` 顶部的 `<body data-style="kurzgesagt">` 改成 `bloomberg / bilibili / vox / stratechery` 即可（CSS 变量映射）。

---

## 6. 本地预览

```bash
cd deck/
python3 -m http.server 8765 &
open http://localhost:8765/deck.html   # macOS
# Linux: xdg-open ... ; Windows: start ...
```

按空格暂停 / 播放，← → 切段，ESC 关闭。

---

## 输出清单

```
deck/
├── deck.html                # 主入口
├── script/script.json       # 脚本
├── research/                # 搜索原始结果(Tavily JSON / web_search md) + notes.md
└── assets/
    ├── img/sec-{N}.png 或 img/sec-{N}.svg
    ├── audio/sec-{N}.mp3
    └── subtitle/sec-{N}.vtt
```

完成后跟用户报告：本地地址 + 总段数 + 用了哪些数据源 + 用了哪种生图方式。

---

## 失败处理

- 联网搜索命中率低 → 换关键词重试,跨路径切换(Tavily ↔ agent web_search),或建议用户提供已有资料(PDF / URL)
- 生图 adapter 报错 → 切换到下一个可用 adapter;仍失败就生成占位图并告知用户
- edge-tts 未安装 → 属于硬依赖缺失，停止正式流程，提示安装命令；不要自动降级，除非用户明确授权“无声草稿”
- edge-tts 网络失败 → 重试 3 次,仍失败则建议换 voice 或检查代理;若用户明确接受降级，HTML 仍可播,母版会用每段的 `data-narration` 文本作为静态字幕兜底(无声但有文字)
- 字数超时 → 自动改短配音文案,保留信息密度

## 不做的事

- 不渲染 MP4（除非用户明确要求）
- 不上传 / 发送到任何外部平台
- 不调用付费 API 前不询问用户授权
