#!/usr/bin/env python3
"""Generate simple SVG placeholder images for sections in script.json."""

from __future__ import annotations

import argparse
import html
import json
import textwrap
from pathlib import Path


PALETTES = {
    "kurzgesagt": ("#1a2540", "#2c3e80", "#ff9c39", "#46d2ff", "#ffffff"),
    "bloomberg": ("#05070d", "#0a0e1a", "#00d96a", "#ff3a3a", "#ffffff"),
    "vox": ("#faf8f3", "#ffffff", "#e63946", "#ffd60a", "#1a1a1a"),
    "bilibili-hardcore": ("#0d0014", "#1a0028", "#00f0ff", "#ff2bd6", "#ffffff"),
    "stratechery": ("#faf8f3", "#f0ece3", "#2c3e50", "#8b3a3a", "#1a1a1a"),
    "apple-keynote": ("#ffffff", "#f5f5f7", "#0071e3", "#ff3b30", "#000000"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--script", default="deck/script/script.json", help="Path to script.json")
    parser.add_argument("--out-dir", default="deck/assets/img", help="Output image directory")
    parser.add_argument("--size", default="1920x1080", help="SVG viewport size, e.g. 1920x1080")
    return parser.parse_args()


def parse_size(raw: str) -> tuple[int, int]:
    try:
        w, h = raw.lower().split("x", 1)
        width, height = int(w), int(h)
    except ValueError as exc:
        raise SystemExit("--size must look like 1920x1080") from exc
    if width <= 0 or height <= 0:
        raise SystemExit("--size values must be positive")
    return width, height


def wrap_title(title: str, width: int = 14) -> list[str]:
    if any("\u4e00" <= ch <= "\u9fff" for ch in title):
        return [title[i : i + width] for i in range(0, len(title), width)][:3]
    return textwrap.wrap(title, width=24, max_lines=3, placeholder="...")


def svg_for(section: dict, index: int, total: int, style: str, width: int, height: int) -> str:
    bg1, bg2, accent, accent2, fg = PALETTES.get(style, PALETTES["kurzgesagt"])
    section_id = html.escape(str(section.get("id") or f"sec-{index + 1}"))
    title = str(section.get("title") or f"Section {index + 1}")
    lines = wrap_title(title)
    escaped_lines = [html.escape(line) for line in lines]

    title_y = height * 0.46 - (len(escaped_lines) - 1) * 52
    line_nodes = "\n".join(
        f'<text x="{width / 2:.0f}" y="{title_y + i * 104:.0f}" '
        f'text-anchor="middle" class="title">{line}</text>'
        for i, line in enumerate(escaped_lines)
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{bg1}"/>
      <stop offset="100%" stop-color="{bg2}"/>
    </linearGradient>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="24" stdDeviation="28" flood-color="#000" flood-opacity="0.22"/>
    </filter>
  </defs>
  <rect width="{width}" height="{height}" fill="url(#bg)"/>
  <circle cx="{width * 0.18:.0f}" cy="{height * 0.22:.0f}" r="{height * 0.12:.0f}" fill="{accent2}" opacity="0.34"/>
  <circle cx="{width * 0.82:.0f}" cy="{height * 0.78:.0f}" r="{height * 0.16:.0f}" fill="{accent}" opacity="0.28"/>
  <rect x="{width * 0.17:.0f}" y="{height * 0.24:.0f}" width="{width * 0.66:.0f}" height="{height * 0.52:.0f}" rx="42" fill="rgba(255,255,255,0.10)" filter="url(#shadow)"/>
  <text x="{width * 0.08:.0f}" y="{height * 0.10:.0f}" class="meta">{section_id.upper()} / {index + 1:02d}-{total:02d}</text>
  {line_nodes}
  <text x="{width / 2:.0f}" y="{height * 0.72:.0f}" text-anchor="middle" class="hint">placeholder visual - replace with generated image when available</text>
  <style>
    .title {{ font: 700 76px -apple-system, BlinkMacSystemFont, "PingFang SC", "Noto Sans CJK SC", sans-serif; fill: {fg}; }}
    .meta {{ font: 700 28px ui-monospace, SFMono-Regular, Menlo, monospace; fill: {accent}; letter-spacing: 2px; }}
    .hint {{ font: 400 24px -apple-system, BlinkMacSystemFont, sans-serif; fill: {fg}; opacity: 0.62; }}
  </style>
</svg>
"""


def main() -> int:
    args = parse_args()
    width, height = parse_size(args.size)
    script = json.loads(Path(args.script).read_text(encoding="utf-8"))
    sections = script.get("sections") or []
    if not isinstance(sections, list) or not sections:
        raise SystemExit("script.json must contain a non-empty sections array")

    style = str(script.get("style") or "kurzgesagt")
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for i, section in enumerate(sections):
        if not isinstance(section, dict):
            continue
        section_id = str(section.get("id") or f"sec-{i + 1}")
        out = out_dir / f"{section_id}.svg"
        out.write_text(svg_for(section, i, len(sections), style, width, height), encoding="utf-8")
        print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
