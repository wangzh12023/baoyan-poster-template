"""预览图与配色总览：PPTX → PNG（macOS 用 QuickLook，其他系统尽力用 LibreOffice），再拼成一张总对比图。
渲染器都不可用时跳过，不影响 PPTX 生成。LibreOffice 认不全 macOS 的中文字体，预览仅供参考。"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

from . import fonts as F
from .palettes import FAMILY_INFO

PREVIEW_H = 3000                       # 预览图高度（px），宽 = 2/3


def renderer():
    if sys.platform == "darwin" and shutil.which("qlmanage"):
        return "quicklook"
    for exe in ("soffice", "libreoffice"):
        if shutil.which(exe):
            return exe
    return None


def render(pptx_paths, out_dir):
    """批量渲染，返回 {pptx 路径: png 路径}"""
    out_dir.mkdir(parents=True, exist_ok=True)
    kind = renderer()
    done = {}
    if kind is None:
        return done
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        if kind == "quicklook":
            for i in range(0, len(pptx_paths), 20):
                subprocess.run(["qlmanage", "-t", "-s", str(PREVIEW_H), "-o", str(tmp),
                                *map(str, pptx_paths[i:i + 20])], capture_output=True)
            for p in pptx_paths:
                src = tmp / f"{p.name}.png"
                if src.exists():
                    done[p] = Path(shutil.move(src, out_dir / f"{p.stem}.png"))
        else:
            filt = ('png:impress_png_Export:{"PixelWidth":{"type":"long","value":"%d"},'
                    '"PixelHeight":{"type":"long","value":"%d"}}' % (PREVIEW_H * 2 // 3, PREVIEW_H))
            subprocess.run([kind, "--headless", "--convert-to", filt, "--outdir", str(tmp),
                            *map(str, pptx_paths)], capture_output=True)
            for p in pptx_paths:
                src = tmp / f"{p.stem}.png"
                if src.exists():
                    done[p] = Path(shutil.move(src, out_dir / f"{p.stem}.png"))
    return done


# ---------------- 配色总览 ----------------
TILE_W, GAP, LABEL_H, HEAD_W, PAD, TITLE_H = 600, 26, 64, 190, 44, 120
BG, INK, SUB = "#EDEDED", "#1F1F1F", "#7A7A7A"


def family_row(items, family, tile_w=TILE_W):
    """一个色系一行：左侧大字色系名，每张预览下方标编号与名称；items = [(配色, 预览图路径)]"""
    k = tile_w / TILE_W
    gap, label_h, head_w = round(GAP * k), round(LABEL_H * k), round(HEAD_W * k)
    tiles = [Image.open(png).convert("RGB") for _, png in items]
    tile_h = round(tile_w * tiles[0].height / tiles[0].width)
    im = Image.new("RGB", (head_w + len(items) * (tile_w + gap), tile_h + label_h + gap), BG)
    d = ImageDraw.Draw(im)
    _, big, small = FAMILY_INFO[family]
    cx = head_w / 2 - 14 * k
    d.text((cx, tile_h / 2 - 30 * k), big, font=F.ui_font(round(104 * k)), fill=f"#{items[0][0]['accent']}",
           anchor="mm")
    d.text((cx, tile_h / 2 + 62 * k), small, font=F.ui_font(round(24 * k)), fill=SUB, anchor="mm")
    f_key, f_name = F.ui_font(round(32 * k)), F.ui_font(round(30 * k))
    for i, ((p, _), tile) in enumerate(zip(items, tiles)):
        x = head_w + i * (tile_w + gap)
        im.paste(tile.resize((tile_w, tile_h), Image.LANCZOS), (x, 0))
        ly = tile_h + 33 * k
        d.ellipse((x + 2 * k, ly - 11 * k, x + 24 * k, ly + 11 * k), fill=f"#{p['topic']}")
        d.text((x + 36 * k, ly), p["key"], font=f_key, fill=INK, anchor="lm")
        d.text((x + 36 * k + d.textlength(p["key"], font=f_key) + 14 * k, ly), p["name"], font=f_name,
               fill="#444444", anchor="lm")
    return im


def overview(previews, title, out_path, tile_w=TILE_W):
    """previews = [(配色, 预览图路径)]，按色系分行拼成一张总览图"""
    rows, fams = [], []
    for p, png in previews:
        if p["family"] not in fams:
            fams.append(p["family"])
    for fam in fams:
        rows.append(family_row([(p, png) for p, png in previews if p["family"] == fam], fam, tile_w))
    k = tile_w / TILE_W
    pad, title_h, gap = round(PAD * k), round(TITLE_H * k), round(GAP * k)
    w = max(r.width for r in rows) + 2 * pad - gap
    sheet = Image.new("RGB", (w, title_h + sum(r.height for r in rows) + pad), BG)
    d = ImageDraw.Draw(sheet)
    d.text((pad, title_h / 2 + 8 * k), title, font=F.ui_font(round(52 * k)), fill=INK, anchor="lm")
    d.text((w - pad, title_h / 2 + 12 * k), f"共 {len(previews)} 款 · 版式与文字完全相同，只换配色",
           font=F.ui_font(round(28 * k), "regular"), fill=SUB, anchor="rm")
    y = title_h
    for r in rows:
        sheet.paste(r, (pad, y))
        y += r.height
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path, quality=90, subsampling=0, optimize=True)
    return out_path
