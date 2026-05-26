#!/usr/bin/env python3
"""Sync script.json section durations from generated audio files."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--script", default="deck/script/script.json", help="Path to script.json")
    parser.add_argument("--audio-dir", default="deck/assets/audio", help="Directory containing sec-id mp3 files")
    parser.add_argument("--out", help="Output path; defaults to overwrite --script")
    parser.add_argument("--pad", type=float, default=0.8, help="Seconds added per section for transition slack")
    return parser.parse_args()


def audio_duration(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return float(result.stdout.strip())


def main() -> int:
    args = parse_args()
    script_path = Path(args.script)
    audio_dir = Path(args.audio_dir)
    out_path = Path(args.out) if args.out else script_path
    data = json.loads(script_path.read_text(encoding="utf-8"))
    sections = data.get("sections") or []
    if not isinstance(sections, list) or not sections:
        raise SystemExit("script.json must contain sections")

    total = 0
    missing: list[str] = []
    for index, section in enumerate(sections, start=1):
        if not isinstance(section, dict):
            continue
        section_id = str(section.get("id") or f"sec-{index}")
        audio_path = audio_dir / f"{section_id}.mp3"
        if not audio_path.exists():
            missing.append(str(audio_path))
            continue
        duration = max(1, round(audio_duration(audio_path) + args.pad))
        section["duration_sec"] = duration
        total += duration

    if missing:
        raise SystemExit("Missing audio files:\n" + "\n".join(missing))
    data["duration_sec"] = total
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out_path} with duration_sec={total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
