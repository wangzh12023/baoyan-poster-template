"""二维码：按链接现做（圆点 / 方块两种风格，透明底、墨色码点），或直接用现成的二维码图片。
现做的码会解码校验一遍，确保扫得出原链接。"""
import io
import sys

import segno
from PIL import Image, ImageDraw

BORDER = 2                   # 四周留 2 个模块的透明边
M, SS = 32, 4                # 圆点版：每模块像素 / 超采样倍数
DOT_R, RING, CORE = 0.42, 1.0, 1.5


def _decode(png):
    try:
        import zxingcpp
    except ImportError:          # 没装解码库就跳过校验
        return None
    im = Image.open(io.BytesIO(png)).convert("RGBA")
    flat = Image.alpha_composite(Image.new("RGBA", im.size, "white"), im).convert("RGB")
    return [r.text for r in zxingcpp.read_barcodes(flat)]


def _square(q, color):
    png, svg = io.BytesIO(), io.BytesIO()
    q.save(png, kind="png", scale=40, border=BORDER, dark=f"#{color}", light=None)
    q.save(svg, kind="svg", scale=10, border=BORDER, dark=f"#{color}", light=None, xmldecl=False)
    return png.getvalue(), svg.getvalue()


def _dots(q, color):
    """码点画成圆点，三个定位角画成圆环 + 圆心"""
    rows = [list(r) for r in q.matrix]
    n = len(rows)
    finders = ((0, 0), (0, n - 7), (n - 7, 0))

    def in_finder(r, c):
        return any(fr <= r < fr + 7 and fc <= c < fc + 7 for fr, fc in finders)

    size, u = (n + 2 * BORDER) * M, M * SS
    mask = Image.new("L", (size * SS, size * SS), 0)
    d = ImageDraw.Draw(mask)
    circles = []

    def disc(cx, cy, r, v=255):
        d.ellipse(((cx - r) * u, (cy - r) * u, (cx + r) * u, (cy + r) * u), fill=v)

    for r in range(n):
        for c in range(n):
            if rows[r][c] and not in_finder(r, c):
                cx, cy = BORDER + c + .5, BORDER + r + .5
                disc(cx, cy, DOT_R)
                circles.append(f'<circle cx="{cx}" cy="{cy}" r="{DOT_R}"/>')
    for fr, fc in finders:
        cx, cy = BORDER + fc + 3.5, BORDER + fr + 3.5
        disc(cx, cy, 3.5)
        disc(cx, cy, 3.5 - RING, 0)
        disc(cx, cy, CORE)
        circles.append(f'<circle cx="{cx}" cy="{cy}" r="{3.5 - RING / 2}" fill="none" stroke="#{color}" '
                       f'stroke-width="{RING}"/><circle cx="{cx}" cy="{cy}" r="{CORE}"/>')
    out = Image.new("RGBA", (size, size), f"#{color}")
    out.putalpha(mask.resize((size, size), Image.LANCZOS))
    buf = io.BytesIO()
    out.save(buf, "PNG", optimize=True)
    w = n + 2 * BORDER
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {w}" width="{w * 10}" height="{w * 10}">'
           f'<g fill="#{color}">{"".join(circles)}</g></svg>')
    return buf.getvalue(), svg.encode()


def make(cfg, color):
    """返回 (png, svg 或 None)"""
    if cfg["image"]:
        im = Image.open(cfg["image"]).convert("RGBA")
        buf = io.BytesIO()
        im.save(buf, "PNG")
        return buf.getvalue(), None
    q = segno.make(cfg["url"], error="q")
    png, svg = (_dots if cfg["style"] == "dots" else _square)(q, color)
    got = _decode(png)
    if got is not None and got != [cfg["url"]]:
        if cfg["style"] == "dots":
            print("  ⚠ 圆点二维码校验没通过，改用方块风格", file=sys.stderr)
            return make(dict(cfg, style="square"), color)
        raise RuntimeError(f"二维码解码校验失败：{got}")
    return png, svg
