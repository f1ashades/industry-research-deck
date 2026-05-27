#!/usr/bin/env python3
"""Generate polished PPT-style SVG scenes from script.json visual specs."""

from __future__ import annotations

import argparse
import html
import json
import math
import re
from pathlib import Path
from typing import Any


W, H = 1920, 1080

THEMES = {
    "editorial-cinematic": {
        "bg": "#f6f9fc",
        "ink": "#172033",
        "muted": "#687385",
        "line": "#dbe4ef",
        "card": "#ffffff",
        "card2": "#f8fbff",
        "blue": "#4e7bc7",
        "blue_soft": "#dfe9ff",
        "coral": "#f05a3f",
        "coral_soft": "#ffe4de",
        "green": "#42b883",
        "green_soft": "#daf3e8",
        "shadow": "#93a4bd",
    },
    "bloomberg": {
        "bg": "#07111f",
        "ink": "#f6fbff",
        "muted": "#9dadbf",
        "line": "#203145",
        "card": "#0f1b2b",
        "card2": "#12243a",
        "blue": "#4aa3ff",
        "blue_soft": "#173657",
        "coral": "#ff5a5f",
        "coral_soft": "#4a1c24",
        "green": "#00d96a",
        "green_soft": "#123d2b",
        "shadow": "#000000",
    },
    "apple-keynote": {
        "bg": "#f7f7f9",
        "ink": "#111111",
        "muted": "#6d7178",
        "line": "#e5e7eb",
        "card": "#ffffff",
        "card2": "#fbfbfd",
        "blue": "#0071e3",
        "blue_soft": "#e5f1ff",
        "coral": "#ff453a",
        "coral_soft": "#ffe8e6",
        "green": "#30d158",
        "green_soft": "#e4f8e9",
        "shadow": "#9aa0aa",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--script", default="deck/script/script.json", help="Path to script.json")
    parser.add_argument("--out-dir", default="deck/assets/img", help="Output image directory")
    return parser.parse_args()


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def visual_for(section: dict[str, Any]) -> dict[str, Any]:
    raw = section.get("visual")
    if isinstance(raw, dict):
        return raw
    title = str(section.get("title") or "")
    prompt = str(section.get("visual_prompt") or "")
    text = f"{title} {prompt}".lower()
    if any(k in text for k in ("对比", "比较", "vs", "一边", "另一边", "怎么选")):
        layout = "comparison-cards"
    elif any(k in text for k in ("流程", "pipeline", "管线", "进入", "输出", "步骤", "目标")):
        layout = "architecture-flow"
    elif any(k in text for k in ("数据", "成本", "价格", "规模", "增长", "指标")):
        layout = "dashboard"
    elif any(k in text for k in ("风险", "问题", "限制", "挑战")):
        layout = "matrix"
    else:
        layout = "statement"
    return {
        "layout": layout,
        "kicker": "",
        "headline": "",
        "subhead": "",
        "cards": [],
        "flow": [],
    }


def weighted_len(text: str) -> float:
    total = 0.0
    for ch in text:
        if "\u4e00" <= ch <= "\u9fff":
            total += 1.0
        elif ch.isspace():
            total += 0.35
        elif ch.isupper():
            total += 0.72
        else:
            total += 0.58
    return total


def wrap_text(text: object, max_units: float, max_lines: int) -> list[str]:
    raw = re.sub(r"\s+", " ", str(text or "")).strip()
    if not raw:
        return []
    parts: list[str] = []
    line = ""
    for token in re.findall(r"[\u4e00-\u9fff]|[^\s\u4e00-\u9fff]+|\s+", raw):
        if token.isspace():
            candidate = line + " "
        else:
            candidate = line + token
        if line and weighted_len(candidate) > max_units:
            parts.append(line.strip())
            line = token.strip()
            if len(parts) >= max_lines:
                break
        else:
            line = candidate
    if line.strip() and len(parts) < max_lines:
        parts.append(line.strip())
    if len(parts) == max_lines and weighted_len(parts[-1]) > max_units:
        parts[-1] = parts[-1].rstrip("，。,. ") + "..."
    return parts[:max_lines]


def text_block(
    text: object,
    x: float,
    y: float,
    *,
    size: int,
    color: str,
    max_units: float,
    max_lines: int,
    weight: int = 600,
    line_height: float = 1.2,
    anchor: str = "start",
    family: str = "PingFang SC, Noto Sans CJK SC, Source Han Sans CN, Arial, sans-serif",
) -> str:
    lines = wrap_text(text, max_units, max_lines)
    if not lines:
        return ""
    tspans = []
    for i, line in enumerate(lines):
        dy = 0 if i == 0 else size * line_height
        tspans.append(f'<tspan x="{x:.0f}" dy="{dy:.0f}">{esc(line)}</tspan>')
    return (
        f'<text x="{x:.0f}" y="{y:.0f}" fill="{color}" font-size="{size}" '
        f'font-weight="{weight}" font-family="{esc(family)}" text-anchor="{anchor}">'
        + "".join(tspans)
        + "</text>"
    )


def rect(x: float, y: float, w: float, h: float, fill: str, stroke: str = "none", rx: int = 42, opacity: float = 1) -> str:
    return (
        f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" rx="{rx}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="2" opacity="{opacity}"/>'
    )


def arrow(x1: float, y1: float, x2: float, y2: float, color: str, opacity: float = 1) -> str:
    return (
        f'<path d="M{x1:.0f},{y1:.0f} L{x2:.0f},{y2:.0f}" fill="none" '
        f'stroke="{color}" stroke-width="5" stroke-linecap="round" opacity="{opacity}" marker-end="url(#arrow)"/>'
    )


def base_defs(c: dict[str, str]) -> str:
    grid = c["line"]
    return f"""
  <defs>
    <pattern id="grid" width="64" height="64" patternUnits="userSpaceOnUse">
      <path d="M64 0H0V64" fill="none" stroke="{grid}" stroke-width="1" opacity="0.54"/>
    </pattern>
    <filter id="shadow" x="-12%" y="-12%" width="124%" height="132%">
      <feDropShadow dx="0" dy="18" stdDeviation="22" flood-color="{c['shadow']}" flood-opacity="0.20"/>
    </filter>
    <marker id="arrow" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto">
      <path d="M0,0 L12,6 L0,12 Z" fill="{c['blue']}"/>
    </marker>
  </defs>
"""


def scene_header(v: dict[str, Any], c: dict[str, str]) -> str:
    kicker = str(v.get("kicker") or "ANALYSIS")
    headline = str(v.get("headline") or v.get("title") or "")
    subhead = str(v.get("subhead") or "")
    parts = []
    if kicker:
        parts.extend(
            [
                rect(90, 70, max(140, min(340, weighted_len(kicker) * 18 + 48)), 46, c["blue_soft"], "none", 23),
                text_block(kicker.upper(), 120, 102, size=24, color=c["blue"], max_units=22, max_lines=1, weight=800),
            ]
        )
    if headline:
        parts.append(text_block(headline, 90, 188, size=70, color=c["ink"], max_units=14, max_lines=2, weight=900, line_height=1.04))
    if subhead:
        parts.append(text_block(subhead, 1150, 150, size=31, color=c["muted"], max_units=22, max_lines=3, weight=500, line_height=1.25))
    return "\n".join(parts)


def normalize_cards(v: dict[str, Any], count: int) -> list[dict[str, str]]:
    raw = v.get("cards")
    cards = raw if isinstance(raw, list) else []
    out: list[dict[str, str]] = []
    for i in range(count):
        item = cards[i] if i < len(cards) and isinstance(cards[i], dict) else {}
        out.append(
            {
                "label": str(item.get("label") or item.get("tag") or f"PART {i + 1}"),
                "title": str(item.get("title") or item.get("name") or ["左侧观点", "右侧观点", "第三步", "第四步"][i % 4]),
                "body": str(item.get("body") or item.get("desc") or item.get("description") or ""),
            }
        )
    return out


def comparison_cards(v: dict[str, Any], c: dict[str, str]) -> str:
    cards = normalize_cards(v, 2)
    parts = [scene_header(v, c)]
    specs = [(90, 300, 830, 610, c["blue_soft"], c["blue"]), (1000, 300, 830, 610, c["coral_soft"], c["coral"])]
    for i, (x, y, w, h, soft, accent) in enumerate(specs):
        card = cards[i]
        parts.append(f'<g filter="url(#shadow)">')
        parts.append(rect(x, y, w, h, c["card"], c["line"], 46))
        parts.append(rect(x + 54, y + 54, max(132, weighted_len(card["label"]) * 15 + 46), 48, soft, "none", 24))
        parts.append(text_block(card["label"].upper(), x + 78, y + 88, size=23, color=accent, max_units=18, max_lines=1, weight=850))
        parts.append(text_block(card["title"], x + 54, y + 184, size=58, color=c["ink"], max_units=14, max_lines=2, weight=850, line_height=1.05))
        parts.append(text_block(card["body"], x + 54, y + 290, size=31, color=c["muted"], max_units=25, max_lines=4, weight=500, line_height=1.38))
        parts.append(f'<circle cx="{x + w - 120:.0f}" cy="{y + 90:.0f}" r="110" fill="none" stroke="{accent}" stroke-dasharray="12 12" opacity="0.18" stroke-width="5"/>')
        parts.append("</g>")
    flow = v.get("flow")
    if isinstance(flow, list) and flow:
        items = [item if isinstance(item, dict) else {"title": str(item)} for item in flow[:3]]
        x0, y0, chip_w, gap = 1060, 770, 190, 56
        for i, item in enumerate(items):
            x = x0 + i * (chip_w + gap)
            parts.append(rect(x, y0, chip_w, 76, c["card2"], c["line"], 24, 0.98))
            parts.append(text_block(item.get("title") or "", x + chip_w / 2, y0 + 49, size=27, color=c["ink"], max_units=6, max_lines=1, weight=800, anchor="middle"))
            if i < len(items) - 1:
                parts.append(arrow(x + chip_w + 14, y0 + 38, x + chip_w + gap - 16, y0 + 38, c["blue"], 0.9))
    parts.append(f'<path d="M922,600 L998,548 L998,652 Z" fill="{c["blue_soft"]}" opacity="0.88"/>')
    return "\n".join(parts)


def architecture_flow(v: dict[str, Any], c: dict[str, str]) -> str:
    raw = v.get("flow")
    flow = raw if isinstance(raw, list) and raw else v.get("cards")
    items = flow if isinstance(flow, list) else []
    if len(items) < 3:
        items = [
            {"title": "目标", "body": "明确要完成什么"},
            {"title": "计划", "body": "拆成可执行步骤"},
            {"title": "交付", "body": "验证并输出结果"},
        ]
    parts = [scene_header(v, c)]
    xs = [170, 680, 1190]
    colors = [(c["blue_soft"], c["blue"]), (c["green_soft"], c["green"]), (c["coral_soft"], c["coral"])]
    for i, item in enumerate(items[:3]):
        if not isinstance(item, dict):
            item = {"title": str(item), "body": ""}
        x, y, w, h = xs[i], 420, 390, 150
        soft, accent = colors[i]
        parts.append(f'<g filter="url(#shadow)">')
        parts.append(rect(x, y, w, h, c["card"], c["line"], 28))
        parts.append(text_block(item.get("title") or f"Step {i+1}", x + w / 2, y + 91, size=38, color=c["ink"], max_units=10, max_lines=1, weight=850, anchor="middle"))
        parts.append("</g>")
        parts.append(rect(x, 635, w, 84, soft, "none", 28))
        parts.append(text_block(item.get("body") or item.get("subtitle") or "", x + w / 2, 688, size=26, color=accent, max_units=15, max_lines=1, weight=750, anchor="middle"))
        if i < 2:
            parts.append(arrow(x + w + 50, y + 75, xs[i + 1] - 50, y + 75, c["blue"], 0.85))
    callout = v.get("callout")
    if callout:
        parts.append(text_block(callout, 960, 845, size=32, color=c["muted"], max_units=45, max_lines=2, weight=500, anchor="middle"))
    return "\n".join(parts)


def dashboard(v: dict[str, Any], c: dict[str, str]) -> str:
    parts = [scene_header(v, c)]
    metrics = v.get("metrics")
    if not isinstance(metrics, list) or not metrics:
        metrics = [
            {"value": "低价", "label": "文本推理"},
            {"value": "多模态", "label": "产品能力"},
            {"value": "长上下文", "label": "知识处理"},
        ]
    for i, item in enumerate(metrics[:3]):
        if not isinstance(item, dict):
            item = {"value": str(item), "label": ""}
        x = 120 + i * 575
        parts.append(f'<g filter="url(#shadow)">')
        parts.append(rect(x, 330, 500, 190, c["card"], c["line"], 34))
        parts.append(text_block(item.get("value") or "", x + 45, 415, size=55, color=[c["blue"], c["green"], c["coral"]][i], max_units=11, max_lines=1, weight=900))
        parts.append(text_block(item.get("label") or "", x + 45, 475, size=28, color=c["muted"], max_units=18, max_lines=1, weight=550))
        parts.append("</g>")
    chart_x, chart_y = 150, 615
    parts.append(rect(chart_x, chart_y, 1620, 250, c["card"], c["line"], 34, 0.92))
    vals = [0.36, 0.58, 0.42, 0.76, 0.52, 0.68]
    for i, val in enumerate(vals):
        bw = 140
        x = chart_x + 130 + i * 235
        h = 185 * val
        parts.append(rect(x, chart_y + 205 - h, bw, h, [c["blue"], c["green"], c["coral"]][i % 3], "none", 18, 0.82))
    parts.append(f'<polyline points="220,775 455,720 690,745 925,660 1160,705 1395,630 1630,675" fill="none" stroke="{c["ink"]}" stroke-width="9" stroke-linecap="round" stroke-linejoin="round" opacity="0.48"/>')
    return "\n".join(parts)


def matrix(v: dict[str, Any], c: dict[str, str]) -> str:
    cards = normalize_cards(v, 4)
    parts = [scene_header(v, c)]
    for i, card in enumerate(cards):
        row, col = divmod(i, 2)
        x = 160 + col * 820
        y = 330 + row * 250
        parts.append(f'<g filter="url(#shadow)">')
        parts.append(rect(x, y, 700, 190, c["card"], c["line"], 32))
        parts.append(rect(x + 36, y + 34, 120, 42, [c["blue_soft"], c["green_soft"], c["coral_soft"], c["blue_soft"]][i], "none", 21))
        parts.append(text_block(card["label"].upper(), x + 58, y + 63, size=20, color=[c["blue"], c["green"], c["coral"], c["blue"]][i], max_units=9, max_lines=1, weight=850))
        parts.append(text_block(card["title"], x + 36, y + 118, size=34, color=c["ink"], max_units=17, max_lines=1, weight=850))
        parts.append(text_block(card["body"], x + 36, y + 160, size=24, color=c["muted"], max_units=24, max_lines=2, weight=500, line_height=1.25))
        parts.append("</g>")
    return "\n".join(parts)


def statement(v: dict[str, Any], c: dict[str, str]) -> str:
    parts = [scene_header(v, c)]
    statement_text = v.get("statement") or v.get("callout") or v.get("subhead") or ""
    parts.append(f'<circle cx="1530" cy="640" r="270" fill="{c["blue_soft"]}" opacity="0.7"/>')
    parts.append(f'<circle cx="1370" cy="710" r="150" fill="{c["coral_soft"]}" opacity="0.75"/>')
    if statement_text:
        parts.append(text_block(statement_text, 160, 530, size=52, color=c["ink"], max_units=30, max_lines=3, weight=850, line_height=1.16))
    return "\n".join(parts)


LAYOUTS = {
    "comparison-cards": comparison_cards,
    "comparison": comparison_cards,
    "architecture-flow": architecture_flow,
    "flow": architecture_flow,
    "process": architecture_flow,
    "dashboard": dashboard,
    "metrics": dashboard,
    "matrix": matrix,
    "cards": matrix,
    "statement": statement,
    "title": statement,
}


def validate_visual(section_id: str, v: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    layout = str(v.get("layout") or "statement")
    if layout in {"comparison-cards", "comparison"} and len(v.get("cards") or []) > 2:
        warnings.append(f"{section_id}: comparison-cards uses first 2 cards; extra cards ignored")
    if layout in {"matrix", "cards"} and len(v.get("cards") or []) > 4:
        warnings.append(f"{section_id}: matrix uses first 4 cards; extra cards ignored")
    headline = str(v.get("headline") or "")
    if weighted_len(headline) > 42:
        warnings.append(f"{section_id}: headline is long; consider shortening for slide-like composition")
    return warnings


def svg_for(section: dict[str, Any], style: str) -> tuple[str, list[str]]:
    visual = visual_for(section)
    if isinstance(section.get("visual"), dict):
        visual.setdefault("headline", section.get("title") or "")
    visual.setdefault("kicker", "SECTION")
    c = THEMES.get(style, THEMES["editorial-cinematic"])
    layout = str(visual.get("layout") or "statement")
    drawer = LAYOUTS.get(layout, statement)
    body = drawer(visual, c)
    warnings = validate_visual(str(section.get("id") or "section"), visual)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(section.get('title') or '')}">
{base_defs(c)}
  <rect width="{W}" height="{H}" fill="{c['bg']}"/>
  <rect width="{W}" height="{H}" fill="url(#grid)" opacity="0.72"/>
  <path d="M0,0 H{W} V{H * 0.30:.0f} C{W * 0.70:.0f},{H * 0.23:.0f} {W * 0.45:.0f},{H * 0.38:.0f} 0,{H * 0.28:.0f} Z" fill="{c['card2']}" opacity="0.56"/>
  <path d="M0,{H * 0.76:.0f} C{W * 0.28:.0f},{H * 0.68:.0f} {W * 0.68:.0f},{H * 0.88:.0f} {W},{H * 0.72:.0f} V{H} H0 Z" fill="{c['blue_soft']}" opacity="0.28"/>
  {body}
</svg>
""", warnings


def main() -> int:
    args = parse_args()
    script = json.loads(Path(args.script).read_text(encoding="utf-8"))
    sections = script.get("sections") or []
    if not isinstance(sections, list) or not sections:
        raise SystemExit("script.json must contain a non-empty sections array")
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    style = str(script.get("style") or "editorial-cinematic")
    all_warnings: list[str] = []
    for i, section in enumerate(sections):
        if not isinstance(section, dict):
            continue
        section_id = str(section.get("id") or f"sec-{i + 1}")
        svg, warnings = svg_for(section, style)
        all_warnings.extend(warnings)
        out = out_dir / f"{section_id}.svg"
        out.write_text(svg, encoding="utf-8")
        print(f"Wrote {out}")
    for warning in all_warnings:
        print(f"WARNING: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
