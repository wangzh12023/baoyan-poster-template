"""主办方 logo：读 SVG / PNG，按需要改成单色（跟随配色的墨色或强调色），返回 PNG（必需）+ SVG（可选，矢量更清晰）。"""
import io
import re
import shutil
import subprocess
import sys

from PIL import Image

_HEX = re.compile(r"#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")
_WHITE = {"#fff", "#ffffff"}


def target_color(spec, theme):
    """keep → None；ink / body / accent → 当前配色里的对应颜色；#RRGGBB → 指定颜色"""
    s = spec.strip()
    if s.lower() == "keep":
        return None
    if s.lower() in ("ink", "body", "accent", "muted"):
        return theme[s.lower()]
    if re.fullmatch(r"#?[0-9a-fA-F]{6}", s):
        return s.lstrip("#").upper()
    raise ValueError(f"logo.color 写的是「{spec}」，可选 keep / ink / accent / #RRGGBB")


def _recolor_svg(svg, color):
    svg = _HEX.sub(lambda m: m.group(0) if m.group(0).lower() in _WHITE else f"#{color}", svg)
    return re.sub(r'(fill|stroke)="(black|currentColor)"', rf'\1="#{color}"', svg)


def _rasterize(svg, width=1200):
    """SVG → PNG：依次尝试 rsvg-convert、cairosvg；都没有时返回 None"""
    if shutil.which("rsvg-convert"):
        return subprocess.run(["rsvg-convert", "-w", str(width)], input=svg, capture_output=True, check=True).stdout
    try:
        import cairosvg
        return cairosvg.svg2png(bytestring=svg, output_width=width)
    except (ImportError, OSError):
        return None


def _recolor_png(png, color):
    im = Image.open(io.BytesIO(png)).convert("RGBA")
    solid = Image.new("RGBA", im.size, f"#{color}")
    solid.putalpha(im.getchannel("A"))
    buf = io.BytesIO()
    solid.save(buf, "PNG", optimize=True)
    return buf.getvalue()


def load(path, color):
    """返回 (png, svg 或 None, 宽高比)"""
    svg = None
    if path.suffix.lower() == ".svg":
        text = path.read_text(encoding="utf-8")
        svg = (_recolor_svg(text, color) if color else text).encode()
        png = _rasterize(svg)
        if png is None:                                     # 没有 SVG 渲染器：退回同名 PNG
            alt = path.with_suffix(".png")
            if not alt.exists():
                sys.exit(f"✗ 渲染 {path.name} 需要 rsvg-convert（brew install librsvg）或 cairosvg，"
                         f"也可以在旁边放一张同名的 {alt.name}")
            png = alt.read_bytes()
            if color:
                png = _recolor_png(png, color)
    else:
        png = path.read_bytes()
        if color:
            png = _recolor_png(png, color)
    w, h = Image.open(io.BytesIO(png)).size
    return png, svg, w / h
