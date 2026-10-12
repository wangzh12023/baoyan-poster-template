"""维护用：用仓库自带的示例 poster.yaml 重新生成 posters/ 里的 54 款成品，以及 README 用到的全部图片。

    uv run --with python-pptx --with segno --with pyyaml --with pillow --with lxml --with zxing-cpp \
        python scripts/make_docs.py        # 或 make docs

需要 macOS（QuickLook 渲染预览）。输出：
  posters/*.pptx                 54 款示例成品
  docs/images/overview.jpg       配色总览
  docs/images/rows/<色系>.jpg     每个色系一行
  docs/images/hero.png           README 头图
  docs/images/social-preview.png GitHub 社交预览图（Settings → Social preview 上传）
  docs/palettes.md               54 款色值表"""
import math
import shutil
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from posterkit import config as C, fonts as F, layout, palettes as P, preview  # noqa: E402

DOCS = ROOT / "docs"
IMG = DOCS / "images"
HERO_PICKS = ["红1", "橙1", "黄2", "绿3", "绿1", "蓝3", "青1", "紫1", "粉1"]


def build_all(tmp):
    cfg = C.load(ROOT / "poster.yaml")
    F.configure(cfg["fonts"])
    files = []
    for p in P.PALETTES:
        path = tmp / f"{p['file']}.pptx"
        layout.build(cfg, p).save(path)
        files.append(path)
    done = preview.render(files, tmp / "preview")
    if len(done) != len(files):
        sys.exit(f"预览图只渲染出 {len(done)}/{len(files)} 张（需要 macOS QuickLook）")
    out = ROOT / "posters"
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir()
    for f in files:
        shutil.copy(f, out / f.name)
    return {p["key"]: done[f] for p, f in zip(P.PALETTES, files)}


def shadowed(im, radius=28, offset=(0, 18), alpha=70):
    """给海报加圆角投影，返回 RGBA"""
    pad = radius * 3
    w, h = im.size
    canvas = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle((pad + offset[0], pad + offset[1], pad + w + offset[0], pad + h + offset[1]),
                                 fill=(30, 30, 40, alpha))
    canvas = Image.alpha_composite(canvas, sh.filter(ImageFilter.GaussianBlur(radius)))
    canvas.paste(im.convert("RGBA"), (pad, pad))
    return canvas


def fan(prev, size, keys, poster_h, spread, lift, bg):
    """把几张海报排成扇形：中间最大最靠前，两侧依次旋转、缩小、下沉"""
    W, H = size
    canvas = Image.new("RGBA", size, bg)
    n = len(keys)
    mid = (n - 1) / 2
    order = sorted(range(n), key=lambda i: -abs(i - mid))          # 先画两侧，再画中间
    for i in order:
        t = (i - mid) / mid if mid else 0
        h = round(poster_h * (1 - 0.16 * abs(t)))
        im = Image.open(prev[keys[i]]).convert("RGB")
        im = im.resize((round(h * im.width / im.height), h), Image.LANCZOS)
        card = shadowed(im, radius=max(8, h // 40), offset=(0, h // 60), alpha=60)
        card = card.rotate(-t * spread, resample=Image.BICUBIC, expand=True)
        cx = W / 2 + t * W * 0.36
        cy = H / 2 + abs(t) ** 1.6 * lift + H * 0.04
        canvas.alpha_composite(card, (round(cx - card.width / 2), round(cy - card.height / 2)))
    return canvas


def hero(prev):
    im = fan(prev, (2400, 1100), HERO_PICKS, 1000, 16, 140, (246, 245, 242, 255))
    im.convert("RGB").save(IMG / "hero.png", optimize=True)


def social(prev):
    W, H = 1280, 640
    bg = (246, 245, 242, 255)
    im = Image.new("RGBA", (W, H), bg)
    posters = fan(prev, (760, 640), ["红1", "黄2", "绿1", "蓝3", "紫1"], 500, 14, 70, (0, 0, 0, 0))
    im.alpha_composite(posters, (W - 760 + 20, 10))
    d = ImageDraw.Draw(im)
    d.text((72, 180), "保研分享会", font=F.ui_font(84), fill="#16201B")
    d.text((72, 290), "海报模板", font=F.ui_font(84), fill="#16201B")
    d.text((76, 410), "54 套配色 · 改一个 YAML", font=F.ui_font(30, "regular"), fill="#555555")
    d.text((76, 456), "一条命令批量生成可编辑 PPTX", font=F.ui_font(30, "regular"), fill="#555555")
    for i, fam in enumerate(P.FAMILIES.values()):
        x = 80 + i * 40
        d.ellipse((x, 540, x + 26, 566), fill=f"#{fam[0]['accent']}")
    im.convert("RGB").save(IMG / "social-preview.png", optimize=True)


def palettes_md():
    lines = ["# 配色一览 · Palettes", "",
             "54 款配色的全部色值（sRGB 十六进制）。所有颜色都在 OKLCH 色彩空间里定义，"
             "源码见 [`posterkit/palettes.py`](../posterkit/palettes.py)。", "",
             "| 列 | 含义 |", "|---|---|",
             "| 墨色 ink | 主标题、姓名、底栏内容 |", "| 正文 body | 院校、英文副标题、场次时间 |",
             "| 注释 muted | 嘉宾时间、小标签、注释 |", "| 强调 accent | 分享主题、场次编号、星期、特邀标签 |",
             "| 点缀 pop | 年份横线、场次末尾圆点 |", "| 细线 hair | 嘉宾之间的分隔线 |",
             "| 背景 bg | 背景渐变的三个色标 |", ""]
    for fam, pals in P.FAMILIES.items():
        en, big, small = P.FAMILY_INFO[fam]
        lines += [f"## {big} · {small}", "", f"![{small}](images/rows/{en}.jpg)", "",
                  "| 编号 | 名称 | id | 墨色 | 正文 | 注释 | 强调 | 点缀 | 细线 | 背景渐变 |",
                  "|---|---|---|---|---|---|---|---|---|---|"]
        for p in pals:
            accent = "同墨色（黑字款）" if p["topic"] == p["ink"] else ""
            lines.append(f"| {p['key']} | {p['name']} | `{p['slug']}` | `#{p['ink']}` | `#{p['body']}` | "
                         f"`#{p['muted']}` | `#{p['accent']}`{' ' + accent if accent else ''} | `#{p['pop']}` | "
                         f"`#{p['hair']}` | `#{p['bg'][0]}` → `#{p['bg'][1]}` → `#{p['bg'][2]}` |")
        lines.append("")
    (DOCS / "palettes.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    (IMG / "rows").mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        prev = build_all(Path(tmp))
        items = [(p, prev[p["key"]]) for p in P.PALETTES]
        preview.overview(items, "2026 保研分享会海报 · 全色系配色总览", IMG / "overview.jpg", tile_w=260)
        for fam, pals in P.FAMILIES.items():
            row = preview.family_row([(p, prev[p["key"]]) for p in pals], fam, tile_w=300)
            row.save(IMG / "rows" / f"{P.FAMILY_INFO[fam][0]}.jpg", quality=88, optimize=True)
        hero(prev)
        social(prev)
    palettes_md()
    for f in sorted(IMG.rglob("*.*")):
        print(f"{f.relative_to(ROOT)}  {f.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
