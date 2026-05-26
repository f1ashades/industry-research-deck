#!/usr/bin/env python3
"""Generate storyboard-grade SVG fallback visuals for sections in script.json."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path


PALETTES = {
    "editorial-cinematic": ("#f7f7f2", "#10141f", "#f05a3f", "#1768ac", "#3fbf7f", "#ffffff"),
    "kurzgesagt": ("#17223b", "#263979", "#ff9c39", "#46d2ff", "#f05a3f", "#ffffff"),
    "bloomberg": ("#05070d", "#111827", "#00d96a", "#ff3a3a", "#2f80ed", "#ffffff"),
    "vox": ("#faf8f3", "#1a1a1a", "#e63946", "#ffd60a", "#1768ac", "#ffffff"),
    "bilibili-hardcore": ("#0d0014", "#16122a", "#00f0ff", "#ff2bd6", "#fff700", "#ffffff"),
    "stratechery": ("#faf8f3", "#1a1a1a", "#2c3e50", "#8b3a3a", "#1768ac", "#ffffff"),
    "apple-keynote": ("#ffffff", "#000000", "#0071e3", "#ff3b30", "#30d158", "#f5f5f7"),
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


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def kind_for(section: dict) -> str:
    text = " ".join(
        str(section.get(key) or "")
        for key in ("title", "narration", "visual_prompt")
    ).lower()
    checks = [
        ("pipeline", ("编译", "pipeline", "source", "资料", "ingest", "输入", "输出")),
        ("graph", ("wiki", "知识", "节点", "关系", "graph", "链接", "概念")),
        ("layers", ("三层", "结构", "schema", "规则", "raw", "source of truth")),
        ("loop", ("query", "lint", "维护", "更新", "自我", "循环")),
        ("risk", ("风险", "错误", "幻觉", "审查", "矛盾", "过期")),
        ("dashboard", ("数据", "规模", "市场", "增长", "玩家", "财报")),
    ]
    for kind, words in checks:
        if any(word in text for word in words):
            return kind
    return "scene"


def rounded_rect(x: float, y: float, w: float, h: float, fill: str, stroke: str = "none", opacity: float = 1.0) -> str:
    return (
        f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" '
        f'rx="28" fill="{fill}" stroke="{stroke}" stroke-width="5" opacity="{opacity}"/>'
    )


def arrow(x1: float, y1: float, x2: float, y2: float, color: str) -> str:
    return (
        f'<path d="M{x1:.0f},{y1:.0f} C{(x1+x2)/2:.0f},{y1:.0f} {(x1+x2)/2:.0f},{y2:.0f} {x2:.0f},{y2:.0f}" '
        f'fill="none" stroke="{color}" stroke-width="12" stroke-linecap="round" marker-end="url(#arrow)"/>'
    )


def node(cx: float, cy: float, r: float, fill: str, stroke: str) -> str:
    return f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r:.0f}" fill="{fill}" stroke="{stroke}" stroke-width="7"/>'


def tiny_label(x: float, y: float, text: str, color: str) -> str:
    return f'<text x="{x:.0f}" y="{y:.0f}" class="tiny" fill="{color}">{esc(text)}</text>'


def pipeline(width: int, height: int, colors: tuple[str, ...]) -> str:
    bg, ink, accent, blue, green, card = colors
    y = height * 0.44
    blocks = [
        (width * 0.16, y, "SOURCE"),
        (width * 0.43, y, "LLM"),
        (width * 0.70, y, "WIKI"),
    ]
    parts = []
    for x, yy, label in blocks:
        parts.append(rounded_rect(x - 135, yy - 105, 270, 210, card, ink, 0.96))
        parts.append(tiny_label(x - 70, yy + 12, label, ink))
    parts.append(arrow(width * 0.28, y, width * 0.36, y, accent))
    parts.append(arrow(width * 0.55, y, width * 0.63, y, accent))
    for i in range(4):
        parts.append(rounded_rect(width * 0.10 + i * 34, height * 0.25 + i * 18, 130, 18, blue, "none", 0.32))
    for i in range(7):
        parts.append(node(width * 0.70 + (i % 3) * 76 - 76, height * 0.34 + (i // 3) * 82, 24, green if i == 0 else blue, card))
    return "\n".join(parts)


def graph(width: int, height: int, colors: tuple[str, ...]) -> str:
    bg, ink, accent, blue, green, card = colors
    coords = [
        (0.30, 0.32), (0.45, 0.25), (0.61, 0.34), (0.36, 0.51),
        (0.55, 0.53), (0.70, 0.48), (0.48, 0.68)
    ]
    parts = []
    for a, b in [(0, 1), (1, 2), (0, 3), (3, 4), (4, 2), (4, 5), (3, 6), (6, 5)]:
        x1, y1 = coords[a]
        x2, y2 = coords[b]
        parts.append(f'<line x1="{x1*width:.0f}" y1="{y1*height:.0f}" x2="{x2*width:.0f}" y2="{y2*height:.0f}" stroke="{ink}" stroke-width="8" opacity="0.36"/>')
    for i, (x, y) in enumerate(coords):
        fill = accent if i in (1, 4) else blue if i % 2 else green
        parts.append(node(x * width, y * height, 42, fill, card))
    parts.append(rounded_rect(width * 0.25, height * 0.72, width * 0.50, 72, card, "none", 0.9))
    parts.append(tiny_label(width * 0.37, height * 0.77, "linked knowledge layer", ink))
    return "\n".join(parts)


def layers(width: int, height: int, colors: tuple[str, ...]) -> str:
    bg, ink, accent, blue, green, card = colors
    parts = []
    labels = [("RAW SOURCES", blue), ("WIKI", accent), ("SCHEMA", green)]
    for i, (label, color) in enumerate(labels):
        x = width * (0.26 + i * 0.20)
        y = height * (0.62 - i * 0.13)
        parts.append(rounded_rect(x, y, width * 0.34, 120, color, card, 0.9))
        parts.append(tiny_label(x + 58, y + 75, label, card))
    parts.append(arrow(width * 0.33, height * 0.41, width * 0.63, height * 0.30, accent))
    return "\n".join(parts)


def loop(width: int, height: int, colors: tuple[str, ...]) -> str:
    bg, ink, accent, blue, green, card = colors
    cx, cy = width * 0.50, height * 0.47
    parts = [
        f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{height*0.25:.0f}" fill="none" stroke="{ink}" stroke-width="30" opacity="0.14"/>',
        f'<path d="M{cx-height*0.25:.0f},{cy:.0f} A{height*0.25:.0f},{height*0.25:.0f} 0 1 1 {cx+height*0.20:.0f},{cy+height*0.15:.0f}" fill="none" stroke="{accent}" stroke-width="18" stroke-linecap="round" marker-end="url(#arrow)"/>',
    ]
    labels = [("INGEST", cx, cy - height * 0.27, blue), ("QUERY", cx + width * 0.20, cy + 20, green), ("LINT", cx - width * 0.20, cy + 20, accent)]
    for label, x, y, color in labels:
        parts.append(rounded_rect(x - 110, y - 48, 220, 96, color, card, 0.95))
        parts.append(tiny_label(x - 55, y + 10, label, card))
    return "\n".join(parts)


def risk(width: int, height: int, colors: tuple[str, ...]) -> str:
    bg, ink, accent, blue, green, card = colors
    parts = [
        rounded_rect(width * 0.23, height * 0.24, width * 0.54, height * 0.38, card, ink, 0.95),
        f'<path d="M{width*0.50:.0f},{height*0.31:.0f} L{width*0.64:.0f},{height*0.55:.0f} L{width*0.36:.0f},{height*0.55:.0f} Z" fill="{accent}" opacity="0.92"/>',
        f'<text x="{width*0.50:.0f}" y="{height*0.50:.0f}" text-anchor="middle" class="bang" fill="{card}">!</text>',
    ]
    for i, color in enumerate((green, blue, green)):
        parts.append(f'<path d="M{width*(0.30+i*0.20):.0f},{height*0.72:.0f} l60,45 l110,-92" fill="none" stroke="{color}" stroke-width="14" stroke-linecap="round"/>')
    return "\n".join(parts)


def dashboard(width: int, height: int, colors: tuple[str, ...]) -> str:
    bg, ink, accent, blue, green, card = colors
    parts = [rounded_rect(width * 0.18, height * 0.20, width * 0.64, height * 0.52, card, "none", 0.96)]
    for i, h in enumerate((150, 240, 105, 300, 210)):
        x = width * 0.28 + i * 115
        parts.append(rounded_rect(x, height * 0.64 - h, 70, h, [blue, green, accent, blue, green][i], "none", 0.92))
    parts.append(f'<polyline points="{width*0.26:.0f},{height*0.55:.0f} {width*0.38:.0f},{height*0.45:.0f} {width*0.50:.0f},{height*0.50:.0f} {width*0.64:.0f},{height*0.32:.0f} {width*0.74:.0f},{height*0.38:.0f}" fill="none" stroke="{ink}" stroke-width="11" stroke-linecap="round" stroke-linejoin="round"/>')
    return "\n".join(parts)


def scene(width: int, height: int, colors: tuple[str, ...]) -> str:
    bg, ink, accent, blue, green, card = colors
    return "\n".join([
        rounded_rect(width * 0.18, height * 0.22, width * 0.64, height * 0.46, card, "none", 0.94),
        f'<circle cx="{width*0.36:.0f}" cy="{height*0.43:.0f}" r="95" fill="{accent}" opacity="0.92"/>',
        rounded_rect(width * 0.48, height * 0.34, 290, 190, blue, card, 0.86),
        f'<path d="M{width*0.33:.0f},{height*0.62:.0f} C{width*0.44:.0f},{height*0.72:.0f} {width*0.60:.0f},{height*0.72:.0f} {width*0.70:.0f},{height*0.57:.0f}" fill="none" stroke="{green}" stroke-width="18" stroke-linecap="round"/>',
    ])


DRAWERS = {
    "pipeline": pipeline,
    "graph": graph,
    "layers": layers,
    "loop": loop,
    "risk": risk,
    "dashboard": dashboard,
    "scene": scene,
}


def svg_for(section: dict, index: int, total: int, style: str, width: int, height: int) -> str:
    colors = PALETTES.get(style, PALETTES["editorial-cinematic"])
    bg, ink, accent, blue, green, card = colors
    section_id = esc(section.get("id") or f"sec-{index + 1}")
    title = esc(section.get("title") or f"Section {index + 1}")
    kind = kind_for(section)
    art = DRAWERS[kind](width, height, colors)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{title}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{bg}"/>
      <stop offset="100%" stop-color="{card}"/>
    </linearGradient>
    <marker id="arrow" markerWidth="14" markerHeight="14" refX="10" refY="7" orient="auto">
      <path d="M0,0 L12,7 L0,14 Z" fill="{accent}"/>
    </marker>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="22" stdDeviation="24" flood-color="#000" flood-opacity="0.16"/>
    </filter>
  </defs>
  <rect width="{width}" height="{height}" fill="url(#bg)"/>
  <circle cx="{width * 0.10:.0f}" cy="{height * 0.18:.0f}" r="{height * 0.11:.0f}" fill="{blue}" opacity="0.14"/>
  <circle cx="{width * 0.88:.0f}" cy="{height * 0.76:.0f}" r="{height * 0.15:.0f}" fill="{accent}" opacity="0.15"/>
  <g filter="url(#shadow)">{art}</g>
  <text x="{width * 0.06:.0f}" y="{height * 0.10:.0f}" class="meta" fill="{accent}">{section_id.upper()} / {index + 1:02d}-{total:02d}</text>
  <style>
    .meta {{ font: 800 28px ui-monospace, SFMono-Regular, Menlo, monospace; letter-spacing: 2px; }}
    .tiny {{ font: 800 34px -apple-system, BlinkMacSystemFont, "PingFang SC", "Noto Sans CJK SC", sans-serif; letter-spacing: 1px; }}
    .bang {{ font: 900 132px -apple-system, BlinkMacSystemFont, sans-serif; }}
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

    style = str(script.get("style") or "editorial-cinematic")
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
