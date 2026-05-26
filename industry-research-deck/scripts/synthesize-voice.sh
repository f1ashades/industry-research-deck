#!/usr/bin/env bash
# 用 edge-tts 给一段 narration 生 mp3 + vtt 字幕。
#
# 用法:
#   synthesize-voice.sh --voice <voice> --text <text> --out-dir <dir> --id <sec-id> [--rate +0%] [--pitch +0Hz]
#
# 输出:
#   <out-dir>/audio/<id>.mp3
#   <out-dir>/subtitle/<id>.vtt

set -euo pipefail

VOICE="zh-CN-XiaoxiaoNeural"
TEXT=""
OUT_DIR="."
ID="sec-1"
RATE="+0%"
PITCH="+0Hz"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --voice)    VOICE="$2"; shift 2 ;;
    --voice=*)  VOICE="${1#*=}"; shift ;;
    --text)     TEXT="$2"; shift 2 ;;
    --text=*)   TEXT="${1#*=}"; shift ;;
    --out-dir)  OUT_DIR="$2"; shift 2 ;;
    --out-dir=*) OUT_DIR="${1#*=}"; shift ;;
    --id)       ID="$2"; shift 2 ;;
    --id=*)     ID="${1#*=}"; shift ;;
    --rate)     RATE="$2"; shift 2 ;;
    --rate=*)   RATE="${1#*=}"; shift ;;
    --pitch)    PITCH="$2"; shift 2 ;;
    --pitch=*)  PITCH="${1#*=}"; shift ;;
    *) echo "未知参数: $1" >&2; exit 1 ;;
  esac
done

[[ -z "$TEXT" ]] && { echo "缺 --text" >&2; exit 1; }

mkdir -p "$OUT_DIR/audio" "$OUT_DIR/subtitle"

MP3="$OUT_DIR/audio/$ID.mp3"
VTT="$OUT_DIR/subtitle/$ID.vtt"

# 重试 3 次（edge-tts 偶尔网络抖动）
tries=0
until [[ "$tries" -ge 3 ]]; do
  if edge-tts \
      --voice "$VOICE" \
      --text "$TEXT" \
      "--rate=$RATE" \
      "--pitch=$PITCH" \
      --write-media "$MP3" \
      --write-subtitles "$VTT"; then
    # 报告时长 + 字数
    if command -v ffprobe >/dev/null 2>&1; then
      DUR=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$MP3" 2>/dev/null || echo "?")
    else
      DUR="?"
    fi
    CHARS=$(printf "%s" "$TEXT" | wc -m | tr -d ' ')
    echo "✓ $ID  voice=$VOICE  chars=$CHARS  duration=${DUR}s"
    echo "   mp3: $MP3"
    echo "   vtt: $VTT"
    exit 0
  fi
  tries=$((tries + 1))
  echo "edge-tts 第 $tries 次失败，重试..." >&2
  sleep 2
done

echo "edge-tts 3 次重试都失败。检查网络 / 代理，或换个 voice。" >&2
exit 1
