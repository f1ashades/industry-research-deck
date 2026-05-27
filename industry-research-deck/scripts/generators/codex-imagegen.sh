#!/usr/bin/env bash
# Agent-native 生图入口（兼容旧文件名的占位说明）。
#
# 如果当前 agent 有任何可调用的生图/修图能力（工具、skill、插件、MCP、IDE 内置能力均可），
# 应该由 agent 直接调用该能力，而不是通过 shell 脚本间接调用。例如在执行 skill 时：
#
#     使用当前 agent 的生图能力生成: "<风格后缀> 内容描述..."  → 保存到 deck/assets/img/sec-N.png
#
# 这个 shell 脚本只在被误调用时给提示。

cat <<'MSG' >&2
codex-imagegen.sh 是一个兼容旧名的占位脚本，不能从 shell 直接调用 agent-native 生图能力。

如果当前 agent 提供任何可调用的生图/修图能力，请直接使用它生成图片并保存到 deck/assets/img/。

如果当前环境没有 agent-native 生图能力，请改用：
  - scripts/generators/openai-api.sh    （要 OPENAI_API_KEY）
  - scripts/generators/nano-banana.sh   （要 GEMINI_API_KEY）

如果都没有，跑 SVG fallback：
  scripts/generate-slide-scenes.py --script deck/script/script.json --out-dir deck/assets/img
MSG
exit 2
