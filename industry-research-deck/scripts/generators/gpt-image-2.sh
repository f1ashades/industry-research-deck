#!/usr/bin/env bash
# Adapter: use the installed Pi gpt-image-2 skill (ChatGPT/Codex imagegen)
# with the industry-research-deck generator interface.
#
# Usage:
#   gpt-image-2.sh --prompt "..." --out deck/assets/img/sec-1.png [--ref deck/assets/img/sec-1.png] [--size 1920x1080]

set -euo pipefail

PROMPT=""
OUT=""
REFS=()
SIZE="1920x1080"
TIMEOUT_SEC="420"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --prompt) PROMPT="$2"; shift 2 ;;
    --prompt=*) PROMPT="${1#*=}"; shift ;;
    --out) OUT="$2"; shift 2 ;;
    --out=*) OUT="${1#*=}"; shift ;;
    --ref) REFS+=("$2"); shift 2 ;;
    --ref=*) REFS+=("${1#*=}"); shift ;;
    --size) SIZE="$2"; shift 2 ;;
    --size=*) SIZE="${1#*=}"; shift ;;
    --timeout-sec) TIMEOUT_SEC="$2"; shift 2 ;;
    --timeout-sec=*) TIMEOUT_SEC="${1#*=}"; shift ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

[[ -z "$PROMPT" ]] && { echo "Missing --prompt" >&2; exit 2; }
[[ -z "$OUT" ]] && { echo "Missing --out" >&2; exit 2; }

GEN="${GPT_IMAGE_2_GEN:-$HOME/.pi/agent/skills/gpt-image-2/scripts/gen.sh}"
[[ -x "$GEN" ]] || {
  echo "gpt-image-2 skill script not found: $GEN" >&2
  echo "Install the gpt-image-2 skill or set GPT_IMAGE_2_GEN=/path/to/gen.sh" >&2
  exit 3
}
command -v codex >/dev/null 2>&1 || {
  echo "codex CLI not found. Install with: npm install -g @openai/codex@latest && codex login" >&2
  exit 3
}
if ! codex exec --help 2>/dev/null | grep -q -- '--enable <FEATURE>'; then
  echo "codex CLI is too old for gpt-image-2 image_generation. Upgrade: npm install -g @openai/codex@latest" >&2
  exit 3
fi

mkdir -p "$(dirname "$OUT")"
args=("$GEN" --prompt "$PROMPT" --out "$OUT" --timeout-sec "$TIMEOUT_SEC")
for ref in "${REFS[@]}"; do
  [[ -f "$ref" ]] || { echo "Reference image not found: $ref" >&2; exit 4; }
  args+=(--ref "$ref")
done

bash "${args[@]}"

python3 - <<PY
import json, pathlib
out = pathlib.Path("$OUT")
meta = {
    "backend": "gpt-image-2-skill",
    "model": "gpt-image-2 via codex image_generation",
    "size_requested": "$SIZE",
    "output": str(out),
}
out.with_suffix(out.suffix + ".json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
PY
