# 改动说明(v2)

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
会自然 fallback 到 `:root` 默认变量(即 kurzgesagt 风格)——无需额外兜底逻辑。

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
