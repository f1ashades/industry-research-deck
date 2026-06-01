#!/usr/bin/env python3
"""校验生成的主视觉是否达标 —— SKILL.md §4a 落盘探针的机械兜底。

把原本靠 agent 目视判断的 "文件存在 / 可读 / 接近 16:9 / 主体不是空白"
做成可重复的脚本检查。支持两种调用：

    # 单图（最常用：sec-1 落盘探针后立刻验）
    scripts/check-visual.py --image deck/assets/img/sec-1.png

    # 整套（批量生成后回扫，按 script.json 的 section id 找图）
    scripts/check-visual.py --script deck/script/script.json --img-dir deck/assets/img

栅格图（png/jpg/webp）用 Pillow 查尺寸、宽高比、是否近乎纯色空白；
SVG 查是否 well-formed、viewBox 宽高比、是否含可绘制元素。

退出码：0 = 全部通过（允许 WARN）；非 0 = FAIL 的数量。
这样可以像 check-deps.sh 一样在工作流里 gate：FAIL 即提示重生或切 fallback。
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

RASTER_EXTS = (".png", ".webp", ".jpg", ".jpeg")
IMAGE_EXTS = RASTER_EXTS + (".svg",)

TARGET_RATIO = 16 / 9          # 1.778
RATIO_WARN_BAND = (1.6, 1.97)  # 之外只 WARN（gpt-image 常给 1.5 / 1.75）
RATIO_FAIL_BELOW = 1.3         # 竖图 / 近方图，破坏 full-bleed → FAIL
MIN_SHORT_SIDE = 720           # 短边低于此值 → WARN（full-bleed 会糊）
INK_FAIL_FRAC = 0.003          # 非背景像素占比低于此值 → 近乎空白 FAIL


class Result:
    def __init__(self, name: str) -> None:
        self.name = name
        self.fails: list[str] = []
        self.warns: list[str] = []
        self.infos: list[str] = []

    def fail(self, msg: str) -> None:
        self.fails.append(msg)

    def warn(self, msg: str) -> None:
        self.warns.append(msg)

    def info(self, msg: str) -> None:
        self.infos.append(msg)

    @property
    def ok(self) -> bool:
        return not self.fails


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--image", help="单张图片路径")
    p.add_argument("--script", default="deck/script/script.json", help="批量模式：script.json 路径")
    p.add_argument("--img-dir", default="deck/assets/img", help="批量模式：图片目录")
    return p.parse_args()


def ratio_checks(res: Result, w: int, h: int) -> None:
    if h == 0:
        res.fail("高度为 0，图片无效")
        return
    ratio = w / h
    res.info(f"尺寸 {w}x{h}，宽高比 {ratio:.3f}（目标 {TARGET_RATIO:.3f}）")
    if ratio < RATIO_FAIL_BELOW:
        res.fail(f"宽高比 {ratio:.2f} 偏离 16:9 太多（竖图/近方图），无法做 full-bleed 主视觉")
    elif not (RATIO_WARN_BAND[0] <= ratio <= RATIO_WARN_BAND[1]):
        res.warn(f"宽高比 {ratio:.2f} 不在 16:9 容差带内，full-bleed 会留黑边或被裁切")
    if min(w, h) < MIN_SHORT_SIDE:
        res.warn(f"短边 {min(w, h)}px 偏小，full-bleed 放大后可能发糊")


def check_raster(path: Path, res: Result) -> None:
    try:
        from PIL import Image, ImageStat
    except ImportError:
        res.warn("未安装 Pillow，跳过栅格内容检查（pip install --user pillow）")
        return
    try:
        img = Image.open(path)
        img.load()
    except Exception as exc:  # noqa: BLE001 - 任何打不开都算 FAIL
        res.fail(f"无法作为图片打开：{exc}")
        return

    w, h = img.size
    ratio_checks(res, w, h)

    rgb = img.convert("RGB")

    # 全局对比度（次要信号）
    stddev = ImageStat.Stat(rgb).stddev
    res.info(f"全局 stddev R/G/B = {stddev[0]:.1f}/{stddev[1]:.1f}/{stddev[2]:.1f}")

    # 空白检测：缩到 160x90，找出背景主色，统计"墨水"像素占比
    small = rgb.resize((160, 90))
    colors = small.getcolors(maxcolors=160 * 90) or []
    if colors:
        _, bg = max(colors, key=lambda c: c[0])

        def dist(col: tuple[int, int, int]) -> float:
            return ((col[0] - bg[0]) ** 2 + (col[1] - bg[1]) ** 2 + (col[2] - bg[2]) ** 2) ** 0.5

        ink = sum(cnt for cnt, col in colors if dist(col) > 40)
        ink_frac = ink / (160 * 90)
        res.info(f"主体（非背景）像素占比 {ink_frac * 100:.2f}%，背景主色 rgb{bg}")
        if ink_frac < INK_FAIL_FRAC:
            res.fail(f"画面近乎纯色/空白（主体占比 {ink_frac * 100:.2f}% < {INK_FAIL_FRAC * 100:.1f}%），疑似生图失败")

    # 字幕安全区：底部 28% 平均亮度（只报告，不判失败 —— 背景被字幕覆盖是允许的）
    band = rgb.crop((0, int(h * 0.72), w, h))
    lum = ImageStat.Stat(band).mean
    avg_lum = sum(lum) / len(lum)
    band_std = sum(ImageStat.Stat(band).stddev) / 3
    res.info(f"底部字幕区平均亮度 {avg_lum:.0f}/255，区内 stddev {band_std:.1f}"
             + ("（偏亮，浅色字幕需描边）" if avg_lum > 170 else ""))


def check_svg(path: Path, res: Result) -> None:
    try:
        raw = path.read_text(encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        res.fail(f"无法读取 SVG：{exc}")
        return
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        res.fail(f"SVG 不是 well-formed XML：{exc}")
        return

    # viewBox 优先，退回 width/height
    vb = root.get("viewBox")
    w = h = None
    if vb:
        try:
            _, _, vw, vh = (float(x) for x in vb.replace(",", " ").split())
            w, h = vw, vh
        except ValueError:
            res.warn("viewBox 解析失败")
    if w is None:
        try:
            w = float(str(root.get("width", "0")).rstrip("px"))
            h = float(str(root.get("height", "0")).rstrip("px"))
        except ValueError:
            w = h = None
    if w and h:
        ratio_checks(res, int(w), int(h))
    else:
        res.warn("SVG 缺少可解析的尺寸（viewBox/width/height）")

    drawable = any(tag in raw for tag in ("<text", "<rect", "<path", "<circle", "<line", "<polyline"))
    if not drawable:
        res.fail("SVG 不含任何可绘制元素（text/rect/path/...），是空画布")


def resolve_image(img_dir: Path, section_id: str) -> Path | None:
    for ext in IMAGE_EXTS:
        cand = img_dir / f"{section_id}{ext}"
        if cand.exists():
            return cand
    return None


def check_one(path: Path) -> Result:
    res = Result(path.name)
    if not path.exists():
        res.fail("文件不存在")
        return res
    if path.suffix.lower() == ".svg":
        res.info("类型：SVG fallback")
        check_svg(path, res)
    elif path.suffix.lower() in RASTER_EXTS:
        res.info("类型：栅格主视觉")
        check_raster(path, res)
    else:
        res.warn(f"未知扩展名 {path.suffix}，跳过")
    return res


def print_result(res: Result) -> None:
    if res.fails:
        mark = "FAIL"
    elif res.warns:
        mark = "WARN"
    else:
        mark = "PASS"
    print(f"[{mark}] {res.name}")
    for m in res.infos:
        print(f"    · {m}")
    for m in res.warns:
        print(f"    ! {m}")
    for m in res.fails:
        print(f"    ✗ {m}")


def main() -> int:
    args = parse_args()
    results: list[Result] = []

    if args.image:
        results.append(check_one(Path(args.image)))
    else:
        script_path = Path(args.script)
        if not script_path.exists():
            raise SystemExit(f"找不到 {script_path}（也可用 --image 单图模式）")
        script = json.loads(script_path.read_text(encoding="utf-8"))
        sections = script.get("sections") or []
        if not isinstance(sections, list) or not sections:
            raise SystemExit("script.json 缺少非空 sections 数组")
        img_dir = Path(args.img_dir)
        for i, sec in enumerate(sections):
            if not isinstance(sec, dict):
                continue
            sid = str(sec.get("id") or f"sec-{i + 1}")
            found = resolve_image(img_dir, sid)
            if found is None:
                res = Result(f"{sid}.*")
                res.fail(f"在 {img_dir} 找不到 {sid} 的任何图片（{'/'.join(IMAGE_EXTS)}）")
                results.append(res)
            else:
                results.append(check_one(found))

    print()
    for res in results:
        print_result(res)
    print()

    fails = sum(1 for r in results if r.fails)
    warns = sum(1 for r in results if r.warns and not r.fails)
    if fails:
        print(f"{fails} 张未通过 —— 定向重生这些图，或对该段切 SVG fallback。")
    else:
        print(f"全部通过（{warns} 张有可选警告）。" if warns else "全部通过。")
    return fails


if __name__ == "__main__":
    sys.exit(main())
