#!/usr/bin/env bash
# Agent 内置生图入口（占位说明）。
#
# 如果当前 agent 有内置 image generation tool，应该由 agent 直接调用该工具，
# 而不是通过 shell 脚本间接调用。例如在执行 skill 时：
#
#     使用内置生图工具生成: "<风格后缀> 内容描述..."  → 保存到 deck/assets/img/sec-N.png
#
# 这个 shell 脚本只在被误调用时给提示。

cat <<'MSG' >&2
codex-imagegen.sh 是一个占位脚本，不能从 shell 直接调用内置生图工具。

如果当前 agent 提供 image generation tool，请直接用该工具生成图片并保存到 deck/assets/img/。

如果当前环境没有内置生图工具，请改用：
  - scripts/generators/openai-api.sh    （要 OPENAI_API_KEY）
  - scripts/generators/nano-banana.sh   （要 GEMINI_API_KEY）

如果都没有，先跑：
  scripts/generate-placeholders.py --script deck/script/script.json --out-dir deck/assets/img
MSG
exit 2
