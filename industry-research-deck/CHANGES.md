# 改动说明(v2)

## 10. 2026-06-02:默认生图风格改为 Excalidraw 手绘白板

### 原痛点

- 默认生图提示词偏现代编辑部电影感,容易生成海报、3D、照片感或复杂背景,不适合中文课程讲义和长文档中的结构说明图。

### 改后

- 默认 `style` 改为 `excalidraw-whiteboard`,生图 prompt 后缀改为 Excalidraw/whiteboard sketch/hand-drawn infographic 风格。
- `SKILL.md`、`references/image-generators.md`、`references/visual-styles.md` 中的默认风格和示例 `image_prompt` 已统一为白底、黑色手绘马克笔线条、柔和浅色填充、清晰中文大字、避免 3D/照片感/复杂背景。
- HTML 模板和 SVG fallback 主题新增 `excalidraw-whiteboard`,保证生图失败时兜底视觉也靠近手绘白板风格。

## 9. 2026-06-01:生图机械校验 + 清理孤儿脚本

### 原痛点

- §4a 落盘探针的成功标准("文件存在 / 可读 / 接近 16:9 / 主体不是空白")全靠 agent 目视判断,没有可重复的机械兜底,生图返回竖图、半幅、纯色空白时容易漏判。
- `generate-placeholders.py` 自第 6 条改动起已被 `generate-slide-scenes.py`(渲染真实 `visual` 内容)取代,但文件留在包里,工作流和 references 都不再引用,只画抽象装饰形状、不传达信息,是孤儿脚本。
- `assemble-deck.py` 的 `safe_style()` 同时被 `style` 和 `visual_mode` 复用,命名语义混淆;`visual_mode` 非法时还会错误回退到风格名 `editorial-cinematic`。

### 改后

- 新增 `scripts/check-visual.py`:栅格图用 Pillow 查尺寸/宽高比/纯色空白(按非背景像素占比)/字幕区亮度,SVG 查 well-formed/viewBox 比例/是否含可绘制元素。退出码 = FAIL 数量,可像 `check-deps.sh` 一样 gate 流程。Pillow 缺失时退化为只查比例/SVG,不阻塞。
- `SKILL.md` §4a:落盘探针和批量生成后各接一次 `check-visual.py`,机械校验通过才算成功;硬性视觉规则改为"先机械校验、再人工看错字"。§0 把 Pillow 列为可选依赖。
- 删除孤儿 `generate-placeholders.py`;slide-scenes 在 `visual` 缺失时已能优雅降级,删除不丢功能。
- `safe_style()` 改名 `safe_slug(value, fallback)`,style 与 visual_mode 共用同一白名单校验,`visual_mode` 非法时回退到 `slide-scene`。

针对 v2 分析中发现的 3 个问题做的修正,新增 1 个校验脚本。

## 8. 2026-05-28:跨 agent 生图自检与落盘探针

### 原痛点

- `check-deps.sh` 只能检测 CLI/API adapter,检测不到对话工具、MCP、插件或 IDE 原生生图能力。
- Agent 容易把“Shell 无法检测 agent-native 生图能力”误读成“没有生图能力”,直接走 SVG fallback。
- 缺少一个跨 agent 的统一判断:什么时候必须先尝试生图,什么时候才允许降级。

### 改后

- `SKILL.md` 加入硬规则:进入素材生成前必须做工具层自检,发现可调用生图能力就用第 1 段正式 prompt 做 `sec-1.png` 落盘探针。
- `references/image-generators.md` 新增 Agent-native 自检协议:枚举候选能力、判断能否落盘、第 1 张即探针、验证文件、记录 `visual_backend`。
- `check-deps.sh` 明确 Shell 提示不能作为 SVG fallback 理由;只有没有候选工具、无法落盘、用户禁用、adapter 未授权或连续失败才 fallback。

## 7. 2026-05-28:支持 Pi gpt-image-2 生图路径

### 原痛点

- Pi 环境已安装 `gpt-image-2` skill，但 `industry-research-deck` 只提示“Shell 无法可靠检测 agent-native 生图能力”，容易误判并直接走 SVG fallback。
- `gpt-image-2` 依赖新版 Codex CLI 的 `codex exec --enable image_generation`；旧版 Codex 报错时缺少明确升级提示。
- 缺少符合本 skill generator 统一接口的 gpt-image-2 adapter。

### 改后

- `check-deps.sh` 检测 `~/.pi/agent/skills/gpt-image-2/scripts/gen.sh` 和 Codex CLI `--enable <FEATURE>` 支持，明确报告 “gpt-image-2 skill 可用”。
- 新增 `scripts/generators/gpt-image-2.sh`，接口兼容 `--prompt / --out / --ref / --size`，内部调用 Pi 的 `gpt-image-2` skill 生成 PNG。
- `SKILL.md` 和 `references/image-generators.md` 明确：Pi 环境可优先走 gpt-image-2 skill，优先级高于 SVG fallback。
- 当 Codex CLI 过旧或未安装时，提示 `npm install -g @openai/codex@latest && codex login`。

## 6. 2026-05-27:语速、视觉和预览质量修正

### 原痛点

- 为了凑 2 分钟把 TTS 降到 `-25%` 会明显不自然。
- `synthesize-voice.sh --rate -25%` 会被 edge-tts/argparse 当成选项而不是参数。
- 占位图几乎只是标题卡，缺少机制图、关系图和场景信息。
- 默认深蓝扁平风和移动端字幕布局容易显得单调、拥挤。

### 改后

- 默认风格改为 `editorial-cinematic`，保留 `kurzgesagt` 但不再默认使用。
- `synthesize-voice.sh` 支持 `--rate=-10%` / `--rate -10%`，内部统一用 `--rate=<value>` 传给 edge-tts。
- 新增 `scripts/sync-audio-durations.py`，用真实 mp3 时长回写 `script.json`，不再靠极端慢速凑时长。
- `generate-placeholders.py` 改为 storyboard fallback：按 pipeline / graph / layers / loop / risk / dashboard 等类型画结构草图，不再输出纯标题卡。
- `templates/deck.html` 加 favicon、桌面/移动端防重叠布局，标题上置，字幕区固定安全。
- `references/image-generators.md` 加入视觉 prompt 结构、禁止项、推荐画面类型和参考来源。

基于原版的针对性优化,5 处改动。

## 1. assemble-deck.py:修复 title 含反斜杠时崩溃的 bug

### 原 bug

```python
html_out = re.sub(r"<title[^>]*>.*?</title>", f"<title>{title}</title>", ...)
```

`re.sub` 的 repl 参数会把 `\1`–`\9`、`\g<name>`、`\U`、`\w` 等当成正则元语法。
`html.escape()` 不动反斜杠,所以以下 title 全部触发 `re.error`:

- `AI 工具:\1 年涨 90%` → `invalid group reference 1`
- `路径 C:\Users\test` → `bad escape \U`
- `正则速查 \w \d \g<name>` → `bad escape \w`
- LaTeX、转义引号同理

### 修法

模板里加 `__DECK_TITLE__` 和 `__DECK_STYLE__` 占位符,脚本里全部改用 `str.replace()`。
`str.replace()` 没有任何元字符解释,反斜杠 / `$` / `&` / `\g<0>` 全部当字面量处理。

未替换状态下打开模板,`__DECK_STYLE__` 不匹配任何 `body[data-style="..."]` 选择器,
会自然 fallback 到 `:root` 默认变量(当前为 excalidraw-whiteboard 风格)——无需额外兜底逻辑。

## 2. SKILL.md + check-deps.sh:Tavily 软化为可选

### 原状

Tavily CLI 是硬依赖,缺失就中断流程。但本质上这个 skill 需要的是"联网搜索能力",
Tavily 只是其中一种实现。

### 改后

把 Tavily 从硬依赖降级为"首选搜索后端",声明 3 条等价路径:

1. **Tavily CLI**(首选,质量最稳)
2. **Agent 自带 web_search / web_fetch**(下位替代,Claude / ChatGPT / Codex 自带)
3. **用户提供素材**(PDF / URL / 笔记,跳过检索)

`check-deps.sh` 把 Tavily 改成 optional,只在 edge-tts / python3 缺失时返回非零退出码。

## 3. deck.html:TTS 失败时的 narration 兜底

### 原痛点

如果 edge-tts 失败,或 VTT 加载错误,字幕区彻底空白——观众只看到图和标题,
信息密度骤降。同时 `<section>` 里也没有 narration 文本,不可访问性也差。

### 改后

`assemble-deck.py` 给每个 `<section>` 注入 `data-narration="..."` 属性。
母版 JS 里:

- 进入段落时先把 `staticNarration` 显示出来(无声但有字)
- VTT 加载成功后,timeupdate 按时间切换 cue 内容
- cue 之间的空隙(原本是空白)用 narration 兜底,不再闪空字幕
- 完全没有 VTT 时,staticNarration 全程保持

副作用:屏幕阅读器现在可以拿到完整文本,可访问性提升。

## 4. deck.html:小修

- **goTo 切段防竞态**:`playAudio()` 加 `playToken` 自增 + 在每个 await 后比对。
  用户快速按 → 键时,旧 section 的 loadVTT/play 不会污染新 section。
- **autoplay 提示**:浏览器拒绝自动播放时,显示半透明覆盖层"点击或按空格开始"。
  原版只用 `{ once: true }` click handler 兜底,不可见。
- **fetch 加 res.ok 检查**:VTT 404 时不再把 HTML 错误页面当字幕解析。

## 5. SKILL.md:硬依赖失败时停止正式流程

### 原痛点

`edge-tts` 已经被列为硬依赖,`check-deps.sh` 也会在缺失时返回非 0。
但失败处理里同时写了"TTS 失败时 HTML 仍可播",容易让 agent 把缺依赖误解成可自动降级的无声版。

### 改后

在依赖自检部分加入严格规则:

- `scripts/check-deps.sh` 返回非 0 时,停止正式演讲流程
- 先提示缺失项和安装命令,等待用户安装
- 只有用户明确授权"先做无声草稿"时,才允许跳过 TTS
- 最终报告必须标明无声草稿未生成音频 / 字幕
