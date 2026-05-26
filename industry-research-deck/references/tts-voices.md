# edge-tts 音色推荐

edge-tts 用微软 Neural TTS，免费、无 key、300+ voices、50+ 语言。

## 中文（zh-CN）

| voice | 性别 | 风格 | 适合 |
|---|---|---|---|
| `zh-CN-XiaoxiaoNeural` | 女 | 清晰、亲和（默认） | 通用、科普、轻松内容 |
| `zh-CN-YunxiNeural` | 男 | 沉稳、磁性 | 财经、深度分析 |
| `zh-CN-XiaoyiNeural` | 女 | 年轻、活泼 | 年轻向、B 站风 |
| `zh-CN-YunjianNeural` | 男 | 新闻播报感 | 严肃新闻、调查 |
| `zh-CN-XiaohanNeural` | 女 | 温柔、慢节奏 | 故事型、情感向 |
| `zh-CN-YunyangNeural` | 男 | 专业、播音 | 教育、严肃科普 |

## 中文方言

| voice | 方言 |
|---|---|
| `zh-CN-liaoning-XiaobeiNeural` | 东北话（女） |
| `zh-CN-shaanxi-XiaoniNeural` | 陕西话（女） |
| `zh-HK-HiuMaanNeural` | 粤语（女） |
| `zh-HK-WanLungNeural` | 粤语（男） |
| `zh-TW-HsiaoChenNeural` | 台湾话（女） |
| `zh-TW-YunJheNeural` | 台湾话（男） |

## 英文（en-US）

| voice | 性别 | 风格 |
|---|---|---|
| `en-US-AriaNeural` | 女 | 清晰、新闻播音 |
| `en-US-GuyNeural` | 男 | 中性、温暖 |
| `en-US-JennyNeural` | 女 | 助手感、亲切 |
| `en-US-RogerNeural` | 男 | 沉稳、播音 |

## 风格匹配建议

| 视觉风格 | 推荐 voice |
|---|---|
| kurzgesagt（扁平科普） | XiaoxiaoNeural / GuyNeural |
| bloomberg（财经数据） | YunxiNeural / RogerNeural |
| vox（新闻） | YunjianNeural / AriaNeural |
| bilibili-hardcore（B 站硬核） | XiaoyiNeural |
| stratechery（学术分析） | YunyangNeural |
| apple-keynote（极简） | XiaohanNeural |

## 调用示例

```bash
# 基础
edge-tts --voice zh-CN-XiaoxiaoNeural --text "你好世界" --write-media out.mp3

# 含字幕
edge-tts --voice zh-CN-XiaoxiaoNeural --text "你好世界" \
  --write-media out.mp3 \
  --write-subtitles out.vtt

# 调速 / 调音调（rate / pitch）
edge-tts --voice zh-CN-XiaoxiaoNeural --text "..." \
  --rate="+10%" --pitch="-2Hz" \
  --write-media out.mp3

# 列出所有 voice
edge-tts --list-voices | grep zh-CN
```

## 字数 → 时长换算（粗略）

| voice | 字 / 秒（默认 rate） |
|---|---|
| XiaoxiaoNeural | ~3.8-4.5 字 |
| YunxiNeural | ~3.5-4.2 字（更慢） |
| XiaoyiNeural | ~4.2-5.0 字（更快） |
| 英文 voices | ~2.0-2.5 词 / 秒 |

产业解释类内容优先保守估算：20 秒配音 ≈ 70-90 中文字 / 40-50 英文词。复杂概念靠近下限，轻松口播可接近上限。
