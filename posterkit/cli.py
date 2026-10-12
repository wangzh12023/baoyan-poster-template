"""命令行：python build.py [配色 ...] [选项]"""
import argparse
import sys
import time
from pathlib import Path

from . import __version__
from . import config as C
from . import fonts as F
from . import layout
from . import palettes as P
from . import preview

ROOT = Path(__file__).resolve().parent.parent

EPILOG = """示例：
  python build.py                 生成全部 54 款到 output/
  python build.py 绿1 蓝3          只生成这两款
  python build.py 粉 草绿          生成整个色系
  python build.py --list          列出全部配色
  python build.py -c my.yaml -o dist --no-preview
"""


def list_palettes():
    for fam, pals in P.FAMILIES.items():
        en, big, small = P.FAMILY_INFO[fam]
        print(f"\n  {big}  {small}  ({en})")
        for p in pals:
            print(f"    {p['key']:<5} {p['name']:<8}  强调 #{p['accent']}  点缀 #{p['pop']}  墨 #{p['ink']}  "
                  f"底 #{p['bg'][1]}   id: {p['slug']}")
    print(f"\n  共 {len(P.PALETTES)} 款。按编号、名称、色系或 id 挑选，例如：python build.py 绿1 蓝 pink-3\n")


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):                # Windows 管道默认不是 UTF-8；进度与提示按时间顺序输出
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    ap = argparse.ArgumentParser(prog="build.py", description="保研分享会海报：读 poster.yaml，一键生成多款配色的可编辑 PPTX。",
                                 epilog=EPILOG, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("palettes", nargs="*", help="要生成的配色（编号 / 名称 / 色系 / id），不写则全部 54 款")
    ap.add_argument("-c", "--config", default=str(ROOT / "poster.yaml"), help="内容配置文件（默认 poster.yaml）")
    ap.add_argument("-o", "--out", default=str(ROOT / "output"), help="输出目录（默认 output/）")
    ap.add_argument("--no-preview", action="store_true", help="不渲染 PNG 预览图和配色总览")
    ap.add_argument("--list", action="store_true", help="列出全部配色后退出")
    ap.add_argument("-V", "--version", action="version", version=f"%(prog)s {__version__}")
    a = ap.parse_args(argv)

    if a.list:
        list_palettes()
        return 0
    try:
        cfg = C.load(a.config)
        F.configure(cfg["fonts"])
        pals = P.select(a.palettes)
    except (C.ConfigError, ValueError) as e:
        print(f"✗ {e}", file=sys.stderr)
        return 1

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    print(f"▶ {Path(a.config).name} → {out}/   共 {len(pals)} 款配色")
    files = []
    for i, p in enumerate(pals, 1):
        path = out / f"{p['file']}.pptx"
        layout.build(cfg, p).save(path)
        files.append(path)
        print(f"  [{i:>2}/{len(pals)}] {path.name}")

    if not a.no_preview:
        kind = preview.renderer()
        if kind is None:
            print("  · 没有可用的渲染器（macOS 自带 QuickLook，其他系统可装 LibreOffice），跳过预览图")
        else:
            print(f"  · 渲染预览图（{'QuickLook' if kind == 'quicklook' else 'LibreOffice'}）…")
            done = preview.render(files, out / "preview")
            if len(done) >= 2:
                items = [(p, done[f]) for p, f in zip(pals, files) if f in done]
                title = f"{cfg['year']} {cfg['title']} · 配色总览".strip()
                sheet = preview.overview(items, title, out / "overview.jpg", tile_w=360)
                print(f"  · 预览图 {len(done)} 张 → {out / 'preview'}/，配色总览 → {sheet}")
            elif done:
                print(f"  · 预览图 → {next(iter(done.values()))}")
    print(f"✓ 完成，用时 {time.time() - t0:.1f}s。用 PowerPoint / Keynote / WPS 打开 {out}/ 里的 .pptx 即可继续微调，需要 PDF 就在软件里「导出 → PDF」。")
    return 0
