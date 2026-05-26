#!/usr/bin/env bash
# OpenAI API (gpt-image-2) 生图。需要 $OPENAI_API_KEY。
#
# 用法:
#   openai-api.sh --prompt "..." --out path.png [--size 1920x1080] [--ref ref.png]

set -euo pipefail

PROMPT=""
OUT=""
SIZE="1024x1024"
REF=""
MODEL="${OPENAI_IMAGE_MODEL:-gpt-image-2}"

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
[[ -z "${OPENAI_API_KEY:-}" ]] && { echo "未设置 OPENAI_API_KEY" >&2; exit 1; }

mkdir -p "$(dirname "$OUT")"
META="${OUT%.*}.json"

write_meta() {
  BACKEND="openai-api" MODEL="$MODEL" SIZE="$SIZE" OUT="$OUT" META="$META" python3 <<'PY'
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
}

if [[ -n "$REF" && -f "$REF" ]]; then
  # 带 reference image 走 edit endpoint
  RESP=$(curl -sS https://api.openai.com/v1/images/edits \
    -H "Authorization: Bearer $OPENAI_API_KEY" \
    -F model="$MODEL" \
    -F "image[]=@$REF" \
    -F prompt="$PROMPT" \
    -F size="$SIZE" \
    -F n=1)
else
  REQUEST_JSON=$(PROMPT="$PROMPT" MODEL="$MODEL" SIZE="$SIZE" python3 <<'PY'
import json, os

print(json.dumps({
    "model": os.environ["MODEL"],
    "prompt": os.environ["PROMPT"],
    "size": os.environ["SIZE"],
    "n": 1,
    "output_format": "png",
}, ensure_ascii=False))
PY
)
  RESP=$(curl -sS https://api.openai.com/v1/images/generations \
    -H "Authorization: Bearer $OPENAI_API_KEY" \
    -H "Content-Type: application/json" \
    -d "$REQUEST_JSON")
fi

# 解析 b64 或 url（gpt-image-2 默认返回 b64_json）
B64=$(echo "$RESP" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('data',[{}])[0].get('b64_json',''))" 2>/dev/null || echo "")
if [[ -n "$B64" && "$B64" != "null" ]]; then
  printf "%s" "$B64" | python3 -c 'import base64, pathlib, sys; pathlib.Path(sys.argv[1]).write_bytes(base64.b64decode(sys.stdin.read()))' "$OUT"
  write_meta
  echo "✓ $OUT  model=$MODEL  size=$SIZE"
  exit 0
fi

URL=$(echo "$RESP" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('data',[{}])[0].get('url',''))" 2>/dev/null || echo "")
if [[ -n "$URL" && "$URL" != "null" ]]; then
  curl -sSL "$URL" -o "$OUT"
  write_meta
  echo "✓ $OUT  model=$MODEL  size=$SIZE  (from url)"
  exit 0
fi

echo "OpenAI 返回异常:" >&2
echo "$RESP" | head -c 500 >&2
exit 1
