#!/usr/bin/env bash
# 依赖自检。打印缺失项 + 安装提示。
# 退出码 0 = 硬依赖 OK；非 0 = 有硬依赖缺失（数字为缺失数量）。
# 由 SKILL.md 调用；输出给用户看，不静默自动装。

set -u

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'
[[ -t 1 ]] || { GREEN=''; YELLOW=''; RED=''; CYAN=''; BOLD=''; RESET=''; }

missing=0
warnings=0

check_required() {
  local name="$1" cmd="$2" install="$3"
  if eval "$cmd" >/dev/null 2>&1; then
    printf "  ${GREEN}✓${RESET} %s\n" "$name"
  else
    printf "  ${RED}✗${RESET} %s\n" "$name"
    printf "    ${CYAN}安装:${RESET} %s\n" "$install"
    missing=$((missing + 1))
  fi
}

check_optional() {
  local name="$1" cmd="$2" install="$3"
  if eval "$cmd" >/dev/null 2>&1; then
    printf "  ${GREEN}✓${RESET} %s\n" "$name"
  else
    printf "  ${YELLOW}!${RESET} %s（可选）\n" "$name"
    printf "    ${CYAN}可装:${RESET} %s\n" "$install"
    warnings=$((warnings + 1))
  fi
}

echo
printf "${BOLD}=== industry-research-deck 依赖自检 ===${RESET}\n\n"

printf "${BOLD}核心工具${RESET}\n"
check_required "edge-tts" "command -v edge-tts" "uv tool install edge-tts  (或 pip install --user edge-tts)"
check_required "python3" "command -v python3" "macOS 自带；Linux 用包管理器"
check_optional "ffprobe（用于精确检查音频时长）" "command -v ffprobe" "brew install ffmpeg  /  apt install ffmpeg"

echo
printf "${BOLD}联网搜索能力（三选一）${RESET}\n"
# Tavily 是首选,不是硬依赖。Agent 内置 web_search 是合格的下位替代。
if command -v tvly >/dev/null 2>&1 && tvly auth status >/dev/null 2>&1; then
  printf "  ${GREEN}✓${RESET} Tavily CLI 已认证(首选搜索后端)\n"
elif command -v tvly >/dev/null 2>&1; then
  printf "  ${YELLOW}!${RESET} Tavily CLI 已安装但未登录\n"
  printf "    ${CYAN}登录:${RESET} tvly login --api-key tvly-...  (key 在 https://app.tavily.com)\n"
else
  printf "  ${YELLOW}!${RESET} Tavily CLI 未安装(可选)\n"
  printf "    ${CYAN}装它:${RESET} uv tool install tavily-cli && tvly login --api-key tvly-...\n"
fi
printf "  ${CYAN}fallback:${RESET} 若当前 agent 提供 web_search / web_fetch,可直接用,不强依赖 Tavily。\n"
printf "  ${CYAN}fallback:${RESET} 若用户提供 PDF / URL 等已有资料,可跳过检索。\n"

echo
printf "${BOLD}生图能力${RESET}\n"
g_ok=0

printf "  ${YELLOW}!${RESET} Shell 无法可靠检测当前 agent 是否有 agent-native 生图能力\n"
printf "    ${CYAN}规则:${RESET} 若当前 agent 自判能生成/编辑位图并保存到工作区，直接用；否则看下面 adapter 或 SVG fallback。\n"

[[ -n "${OPENAI_API_KEY:-}" ]] && {
  printf "  ${GREEN}✓${RESET} OPENAI_API_KEY 已设置（可用 gpt-image-2 API）\n"; g_ok=$((g_ok + 1));
}
[[ -n "${GEMINI_API_KEY:-}" ]] && {
  printf "  ${GREEN}✓${RESET} GEMINI_API_KEY 已设置（可用 nano-banana）\n"; g_ok=$((g_ok + 1));
}

if [[ "$g_ok" -eq 0 ]]; then
  printf "  ${YELLOW}!${RESET} 未检测到 API adapter 凭证\n"
  printf "    ${CYAN}fallback:${RESET} 若当前 agent 也没有可用生图能力，运行 scripts/generate-slide-scenes.py 生成 SVG scene。\n"
fi

echo
if [[ "$missing" -eq 0 ]]; then
  printf "${GREEN}${BOLD}全部就绪${RESET} ── 可以开始做演讲了\n\n"
  [[ "$warnings" -gt 0 ]] && printf "${YELLOW}另有 %d 个可选项缺失，不阻塞。${RESET}\n\n" "$warnings"
  exit 0
else
  printf "${YELLOW}${BOLD}有 %d 项硬依赖缺失${RESET}，按上面提示手动安装后再继续。\n\n" "$missing"
  exit "$missing"
fi
