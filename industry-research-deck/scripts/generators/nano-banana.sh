#!/usr/bin/env bash
# Google Gemini 2.5 Flash Image (nano-banana) 生图。需要 $GEMINI_API_KEY。
#
# 用法:
#   nano-banana.sh --prompt "..." --out path.png [--size 1920x1080] [--ref ref.png]
#
# 免费额度: aistudio.google.com 每天 ~1500 张

set -euo pipefail

PROMPT=""
OUT=""
SIZE="1024x1024"
REF=""
MODEL="gemini-2.5-flash-image"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --prompt) PROMPT="$2"; shift 2 ;;
    --out)    OUT="$2"; shift 2 ;;
    --size)   SIZE="$2"; shift 2 ;;
    --ref)    REF="$2"; shift 2 ;;
    *) echo "未知参数: $1" >&2; exit 1 ;;
  esac
done

[[ -z "$PROMPT" || -z "$OUT" ]] && { echo "缺 --prompt 或 --out" >&2; exit 1; }
[[ -z "${GEMINI_API_KEY:-}" ]] && { echo "未设置 GEMINI_API_KEY" >&2; exit 1; }

mkdir -p "$(dirname "$OUT")"
META="${OUT%.*}.json"

# 构造 request body（带 ref 时 inline base64）
PARTS_JSON=$(PROMPT="$PROMPT" REF="$REF" python3 <<'PY'
import base64
import json
import os

parts = [{"text": os.environ["PROMPT"]}]
ref = os.environ.get("REF", "")
if ref and os.path.isfile(ref):
    with open(ref, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    parts.append({"inline_data": {"mime_type": "image/png", "data": b64}})
print(json.dumps({"contents": [{"parts": parts}]}))
PY
)

RESP=$(curl -sS "https://generativelanguage.googleapis.com/v1beta/models/${MODEL}:generateContent?key=${GEMINI_API_KEY}" \
  -H "Content-Type: application/json" \
  -d "$PARTS_JSON")

# 解析返回的图片 base64
B64=$(echo "$RESP" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    for part in d['candidates'][0]['content']['parts']:
        if 'inline_data' in part or 'inlineData' in part:
            data = part.get('inline_data') or part.get('inlineData')
            print(data['data']); break
except Exception as e:
    print('', file=sys.stderr)
" 2>/dev/null)

if [[ -n "$B64" ]]; then
  printf "%s" "$B64" | python3 -c 'import base64, pathlib, sys; pathlib.Path(sys.argv[1]).write_bytes(base64.b64decode(sys.stdin.read()))' "$OUT"
  BACKEND="nano-banana" MODEL="$MODEL" SIZE="$SIZE" OUT="$OUT" META="$META" python3 <<'PY'
import json, os
from pathlib import Path

meta = {
    "backend": os.environ["BACKEND"],
    "model": os.environ["MODEL"],
    "size": os.environ["SIZE"],
    "out": os.environ["OUT"],
}
Path(os.environ["META"]).write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY
  echo "✓ $OUT  model=$MODEL"
  exit 0
fi

echo "Gemini 返回异常:" >&2
echo "$RESP" | head -c 500 >&2
exit 1
