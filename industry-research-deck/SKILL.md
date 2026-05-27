---
name: industry-research-deck
description: |
  把"行业调研 / 主题讲解"自动做成一份**可在浏览器播放的 HTML 演讲**（默认 2 分钟、5-6 段、AI 生图主视觉+TTS+字幕+数据源标注），不渲染 MP4。
  触发场景：用户说"做个调研讲解 / 出一份 N 分钟演讲 / 帮我讲讲 X 为啥 Y / 做个 hyperframes 演讲 / 做个短视频草稿"。
  整合**联网搜索能力**(优先 Tavily 深度检索;agent 自带的 web_search / web_fetch 是合格的下位替代;也支持用户直接喂资料)、edge-tts 配音、agent-native 生图能力(不限工具名;当前 agent 能生成/编辑并保存位图就优先;否则 adapter;最后结构化 SVG scene 兜底)、HTML 母版组装。
  风格默认 editorial-cinematic（现代编辑部电影感，可视化讲解），可换。
---

# Industry Research Deck

把任意主题做成一份本地可播的 HTML 演讲。本 skill 是**总指挥**：LLM 负责调研判断、叙事、视觉分镜和生图提示词；脚本负责依赖检查、SVG 兜底、配音和 HTML 组装这些机械且容易出错的环节。

## 何时触发

用户说：
- "做个/出一份调研演讲""讲讲 X 为什么 Y"
- "做个 N 分钟讲解 / 短视频草稿"
- "做个 hyperframes 演讲 / HTML 演讲"
- "把这个主题做成短片"

## 工作流总览

```
0. 依赖自检   →  1. 澄清需求    →  2. 信息检索   →  3. 拆段写脚本 + 视觉分镜
                                                                       ↓
6. 本地预览  ←  5. HTML 组装   ←  4a/4b. 并行生图主视觉 + 配音
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
| **风格** | `editorial-cinematic`（现代编辑部电影感） | 用户说了"换风格"或"自由描述"时按 [references/visual-styles.md](references/visual-styles.md) 走 |
| **语言** | 中文 | 用户用英文交流时改 en |
| **配音音色** | `zh-CN-XiaoxiaoNeural`（女）/ `zh-CN-YunxiNeural`（男） | 见 [references/tts-voices.md](references/tts-voices.md) |
| **视觉方式** | 当前 agent 自判具备生图能力就优先生成位图；不能生图或失败再 SVG scene | 用户明确指定“不要生图/只要 SVG”时改 |
| **是否输出 MP4** | 否 | 用户说"要视频"时改 yes |

**反问示例**：「主题我理解是「X」，2 分钟、中文女声、现代编辑部电影感、用 {后端} 生图，OK 我开始 ── 任何一项要改？」

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

- L1（始终遵守）：N 段，每段 `{标题, 配音文案, image_prompt, visual 兜底 scene, 数据源 url[]}`；首段必须是钩子；末段必须收束
- L2（按需读）：如果觉得节奏需要参考，**主动**读 [references/narrative-patterns.md](references/narrative-patterns.md)，选一个模板套用
- 视觉（默认读）：先读 [references/image-generators.md](references/image-generators.md) 写适合当前 agent 生图能力的主视觉 prompt；再写 `visual` 作为 SVG fallback scaffold。只有无生图能力或生图失败时才读 [references/ppt-scene-system.md](references/ppt-scene-system.md) 并执行 SVG scene。

输出到 `deck/script/script.json`：

```json
{
  "title": "...",
  "duration_sec": 120,
  "style": "editorial-cinematic",
  "voice": "zh-CN-XiaoxiaoNeural",
  "sections": [
    {
      "id": "sec-1",
      "duration_sec": 20,
      "title": "...",
      "narration": "...约 90-130 字（中文 edge-tts 自然语速 ≈ 4.6-5.4 字/秒）...",
      "image_prompt": "生成 16:9 高质量中文演讲主视觉。左侧大标题：...；右侧是...生态图/流程图/对比图；只出现这些短文字标签：...；深色科技感/现代编辑部电影感；主体占满画布；底部 28% 保持干净给字幕。",
      "visual": {
        "mode": "slide-scene",
        "layout": "comparison-cards",
        "kicker": "核心判断",
        "headline": "一句话标题，像 PPT 大标题",
        "subhead": "一句解释，不超过两行",
        "cards": [
          {"label": "LEFT", "title": "左侧观点", "body": "2-4 行解释"},
          {"label": "RIGHT", "title": "右侧观点", "body": "2-4 行解释"}
        ]
      },
      "sources": [{"label": "来源名", "url": "https://..."}]
    }
  ]
}
```

**字数提示**：中文 edge-tts 自然语速通常接近 **4.6-5.4 字/秒**。不要为了凑 2 分钟把语速降到很慢；要通过增删文案控制时长。20s 建议 90-110 字，24s 建议 110-130 字。英文按 **2.0-2.5 words/sec**。先用自然语速生成音频，再用 §4b 的时长回写脚本校准 `duration_sec`。

**视觉分镜提示**：当前 agent 如果具备任何 agent-native 位图生图能力（工具、skill、插件、MCP、IDE 内置能力均可，不限定名称），必须优先生成 raster 主视觉。`visual` 不是默认产物，而是为了生图失败、无生图能力、或精确文字持续出错时的兜底。连续段落要轮换构图（生态图 / 对比图 / 流程图 / 仪表盘 / 结论页），避免每张都是同一种中央图。

---

## 4. 素材生成（4a + 4b 可并行）

进入本节前必须已经通过 §0 的依赖自检。若 `edge-tts` 缺失，正式流程应停在 §0；只有用户明确授权“无声草稿”时，才跳过 §4b。

### 4a. 生图主视觉（默认）+ SVG scene 兜底

先走 [references/image-generators.md](references/image-generators.md)。由当前 agent 自己判断是否具备可用的 agent-native 生图能力；只要能根据 prompt/reference 生成或编辑位图，并把最终图片保存到 `deck/assets/img/sec-{N}.png`，就直接使用它。不要因为 SVG 更可控就跳过生图。只有当前环境确实不能生图、用户明确要求不用生图、或生图连续失败时，才执行 SVG fallback。

- 当前 agent 有内置/插件/MCP/IDE 生图能力时，按该环境的图片保存策略执行：先生成，检查输出，把最终选中的图片复制/移动到 `deck/assets/img/sec-{N}.png`。项目引用的图片不能只留在临时生成目录、聊天附件、远程 URL 或不可复现缓存里。
- 如果没有 agent-native 生图，但用户已配置 adapter 凭证，可调用 `scripts/generators/openai-api.sh` 或 `scripts/generators/nano-banana.sh`。
- 如果没有任何生图能力或生图失败，运行：

```bash
scripts/generate-slide-scenes.py --script deck/script/script.json --out-dir deck/assets/img
```

该脚本会读取每段 `visual`，输出 `deck/assets/img/sec-{N}.svg`。`assemble-deck.py` 会把含 `visual` 的段落标记为 `data-visual-mode="slide-scene"`，避免 HTML 标题和 SVG 标题重复。

**硬性视觉规则**：
- 每段生图必须是 full-bleed 16:9 主视觉，不是小图贴片。可以是 PPT/信息图风格，但必须有真实视觉质感、空间层级和统一光效。
- image prompt 必须给出：画布尺寸/用途、主标题原文、允许出现的短标签清单、版式布局、主体元素、色彩/材质/光效、字幕安全区。
- 允许 image-2 渲染短中文标题和短标签；不要让它渲染长段正文。正文和解释仍由字幕/旁白承担。
- 生图后必须人工/视觉检查：标题是否错字、标签是否错字、构图是否占满、底部字幕区是否干净。错字或构图问题要定向重生/编辑一次；仍失败再切 SVG fallback。

**风格一致性**：第 1 张作为 reference。第 2 段及之后，如果工具支持 reference image，传 `sec-1.png`；不支持时，在 prompt 中复用同一套风格、镜头、材质、色彩和构图语言。

输出：优先 `deck/assets/img/sec-{N}.png`；fallback 输出 `deck/assets/img/sec-{N}.svg`。组装脚本会自动优先使用已存在的图片文件。

### 4b. 配音 + 字幕

用 `scripts/synthesize-voice.sh` 为每段生成 mp3 + vtt 字幕：

```bash
scripts/synthesize-voice.sh --voice "$VOICE" --text "$NARRATION" --out-dir deck/assets --id sec-1
```

`edge-tts --write-subtitles` 输出 VTT 字幕，HTML 播放器会按 `data-subtitle` 加载并同步显示。

**语速规则**：默认 `--rate +0%`，短视频可用 `--rate +6%` 到 `+10%`。不要用 `-20%`、`-25%` 这类慢速去凑总时长，除非用户明确要慢速朗读。生成完所有 mp3 后，用实际音频时长回写脚本：

```bash
scripts/sync-audio-durations.py --script deck/script/script.json --audio-dir deck/assets/audio
```

再重新组装 HTML，保证切段时长和真实音频一致。

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
  <img src="assets/img/sec-1.png" alt="..."> <!-- full-bleed generated visual; fallback may be .svg -->
  <h2>...标题...</h2>
</section>
```

母版自带「自动播放配音 → 同步切段 → 显示字幕」的 JS。
**风格切换**：`script.json` 的 `style` 可设为 `editorial-cinematic / kurzgesagt / bloomberg / bilibili-hardcore / vox / stratechery / apple-keynote`。

---

## 6. 本地预览

```bash
cd deck/
python3 -m http.server 8765 &
open http://localhost:8765/deck.html   # macOS
# Linux: xdg-open ... ; Windows: start ...
```

按空格暂停 / 播放，← → 切段，ESC 关闭。

预览后必须做一次浏览器/HTTP 验证：确认 `deck.html` 返回 200、图片全部加载且覆盖整个 section、音频和字幕数量等于段数、桌面和移动端没有标题/字幕/来源互相遮挡。图片作为背景允许被字幕覆盖；真正要查的是字幕是否可读、是否被裁切，图内中文标题/标签是否有错字。若后台服务在 shell 退出后被带掉，在 macOS 可用 `screen -dmS deck-preview bash -lc 'cd deck && python3 -m http.server 8765'`。

---

## 输出清单

```
deck/
├── deck.html                # 主入口
├── script/script.json       # 脚本
├── research/                # 搜索原始结果(Tavily JSON / web_search md) + notes.md
└── assets/
    ├── img/sec-{N}.png（优先生图）或 img/sec-{N}.svg（fallback）
    ├── audio/sec-{N}.mp3
    └── subtitle/sec-{N}.vtt
```

完成后跟用户报告：本地地址 + 总段数 + 用了哪些数据源 + 用了哪种生图方式。

---

## 失败处理

- 联网搜索命中率低 → 换关键词重试,跨路径切换(Tavily ↔ agent web_search),或建议用户提供已有资料(PDF / URL)
- 生图不可用/报错 → 切换到 adapter；仍失败就运行 `generate-slide-scenes.py` 输出 SVG scene，并在最终报告标明“使用 SVG fallback”
- 生图错字/构图不占满 → 定向重写 prompt 或用 image edit 修一次；仍失败再切 SVG scene
- scene fallback 内容拥挤 → 拆成更多段或换 layout；不要缩小字号硬塞
- edge-tts 未安装 → 属于硬依赖缺失，停止正式流程，提示安装命令；不要自动降级，除非用户明确授权“无声草稿”
- edge-tts 参数失败 → 检查负数参数是否写成 `--rate=-10%` 或直接用 `scripts/synthesize-voice.sh --rate=-10%`
- edge-tts 网络失败 → 重试 3 次,仍失败则建议换 voice 或检查代理;若用户明确接受降级，HTML 仍可播,母版会用每段的 `data-narration` 文本作为静态字幕兜底(无声但有文字)
- 字数超时/过短 → 不靠极端变速修正；增删文案后重生音频，再跑 `sync-audio-durations.py`

## 不做的事

- 不渲染 MP4（除非用户明确要求）
- 不上传 / 发送到任何外部平台
- 不调用付费 API 前不询问用户授权
