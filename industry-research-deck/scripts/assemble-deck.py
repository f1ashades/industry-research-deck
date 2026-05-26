#!/usr/bin/env python3
"""Assemble deck.html from script.json and the bundled HTML template.

注入是纯 str.replace,不走 re.sub —— title/narration 里允许任意反斜杠、$、&、<、> 等字符。
"""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path
from urllib.parse import urlparse


SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATE = SKILL_DIR / "templates" / "deck.html"
IMAGE_EXTS = (".png", ".webp", ".jpg", ".jpeg", ".svg")

# 模板中的占位符 token。所有注入都用 str.replace,不走 re.sub。
TITLE_TOKEN = "__DECK_TITLE__"
STYLE_TOKEN = "__DECK_STYLE__"
SECTIONS_TOKEN = "<!-- DECK_SECTIONS -->"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--script", default="deck/script/script.json", help="Path to script.json")
    parser.add_argument("--template", default=str(DEFAULT_TEMPLATE), help="Path to deck.html template")
    parser.add_argument("--out", default="deck/deck.html", help="Output HTML path")
    parser.add_argument("--asset-prefix", default="assets", help="Asset path prefix used from deck.html")
    return parser.parse_args()


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def attr(value: object) -> str:
    return html.escape(str(value), quote=True)


def text(value: object) -> str:
    return html.escape(str(value), quote=False)


def safe_style(value: object) -> str:
    style = str(value or "editorial-cinematic")
    if re.fullmatch(r"[a-z0-9-]+", style):
        return style
    return "editorial-cinematic"


def source_label(url: str) -> str:
    host = urlparse(url).netloc
    return host.removeprefix("www.") or "source"


def normalize_sources(raw: object) -> list[dict[str, str]]:
    if not raw:
        return []
    sources = raw if isinstance(raw, list) else [raw]
    out: list[dict[str, str]] = []
    for item in sources:
        if isinstance(item, str):
            url = item
            label = source_label(url)
        elif isinstance(item, dict):
            url = str(item.get("url") or item.get("href") or "")
            label = str(item.get("label") or item.get("title") or source_label(url))
        else:
            continue
        if url:
            out.append({"label": label, "url": url})
    return out


def image_path(deck_dir: Path, asset_prefix: str, section: dict) -> str:
    explicit = section.get("image") or section.get("image_path")
    if explicit:
        return str(explicit)

    section_id = str(section.get("id") or "")
    for ext in IMAGE_EXTS:
        candidate = deck_dir / asset_prefix / "img" / f"{section_id}{ext}"
        if candidate.exists():
            return f"{asset_prefix}/img/{section_id}{ext}"
    return f"{asset_prefix}/img/{section_id}.png"


def build_section(deck_dir: Path, asset_prefix: str, section: dict, index: int) -> str:
    section_id = str(section.get("id") or f"sec-{index + 1}")
    duration = section.get("duration_sec") or section.get("duration") or 20
    title = str(section.get("title") or f"Section {index + 1}")
    narration = str(section.get("narration") or "")
    sources_json = json.dumps(normalize_sources(section.get("sources")), ensure_ascii=False)
    img = image_path(deck_dir, asset_prefix, {**section, "id": section_id})
    audio = section.get("audio") or f"{asset_prefix}/audio/{section_id}.mp3"
    subtitle = section.get("subtitle") or f"{asset_prefix}/subtitle/{section_id}.vtt"

    return "\n".join(
        [
            f'    <section data-id="{attr(section_id)}" data-duration="{attr(duration)}"',
            f'             data-audio="{attr(audio)}"',
            f'             data-subtitle="{attr(subtitle)}"',
            f'             data-narration="{attr(narration)}"',
            f"             data-sources='{attr(sources_json)}'>",
            f'      <img src="{attr(img)}" alt="{attr(title)}">',
            f"      <h2>{text(title)}</h2>",
            "    </section>",
        ]
    )


def inject(template: str, *, title: str, style: str, sections_html: str) -> str:
    """三次纯 str.replace —— 不动 regex,反斜杠 / $ / & 全部安全。"""
    for token in (TITLE_TOKEN, STYLE_TOKEN, SECTIONS_TOKEN):
        if token not in template:
            raise SystemExit(f"template missing required token: {token}")
    return (
        template
        .replace(TITLE_TOKEN, text(title))
        .replace(STYLE_TOKEN, style)         # safe_style 已限定 [a-z0-9-]
        .replace(SECTIONS_TOKEN, sections_html)
    )


def main() -> int:
    args = parse_args()
    script_path = Path(args.script)
    template_path = Path(args.template)
    out_path = Path(args.out)
    deck_dir = out_path.parent

    script = load_json(script_path)
    template = template_path.read_text(encoding="utf-8")

    sections = script.get("sections") or []
    if not isinstance(sections, list) or not sections:
        raise SystemExit("script.json must contain a non-empty sections array")

    section_blocks = [
        build_section(deck_dir, args.asset_prefix, sec, i)
        for i, sec in enumerate(sections)
        if isinstance(sec, dict)
    ]
    if not section_blocks:
        raise SystemExit("script.json sections must contain objects")
    sections_html = "\n\n".join(section_blocks)

    title = str(script.get("title") or "Industry Research Deck")
    style = safe_style(script.get("style"))

    html_out = inject(template, title=title, style=style, sections_html=sections_html)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html_out, encoding="utf-8")
    print(f"Wrote {out_path} with {len(sections)} sections")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
