"""字体：排版用到的字体角色、按名字找字体文件、量字宽、算基线。

字体名会原样写进 PPTX，打开时由 PowerPoint / Keynote / WPS 用本机字体渲染；
这里只负责在生成时量出文字宽度（日期块右对齐、副标题撑满主标题宽度、标签紧跟姓名等）。
量宽优先用本机字体文件；没有时用 metrics.json 里默认字体的字宽表（所以 Windows / Linux 上排版也一致）；
都没有时按字符类别估算并提示一次，不影响生成。"""
import glob
import json
import os
import sys
import unicodedata
from functools import lru_cache
from pathlib import Path

from PIL import ImageFont

# 角色 → (西文字体, 中文字体)。typeface 直接写字重全名，避免 PowerPoint 伪粗体。
# 可以在 poster.yaml 的 fonts: 里按角色覆盖（例如换成思源宋体 / 思源黑体）。
DEFAULT_FONTS = dict(
    serif_black=("Songti SC Black", "Songti SC Black"),        # 主标题、嘉宾姓名
    serif=("Songti SC", "Songti SC"),                          # 场次名（配合 b=1 → Songti SC Bold）
    sans=("PingFang SC", "PingFang SC"),                       # 学院、注释
    sans_medium=("PingFang SC Medium", "PingFang SC Medium"),  # 院校、底栏小标签
    sans_semibold=("PingFang SC Semibold", "PingFang SC Semibold"),  # 分享主题、特邀标签
    display=("Didot", "PingFang SC"),                          # 年份、日期、场次编号
    latin_medium=("Avenir Next Medium", "PingFang SC"),        # 时间、地点
    latin_demibold=("Avenir Next Demi Bold", "PingFang SC"),   # 英文副标题、底栏内容
)
FONTS = dict(DEFAULT_FONTS)

# hhea 上 / 下伸（em）：不同字体的文本框之间按基线对齐时用
METRICS = {"Songti": (1.06, 0.34), "PingFang": (1.06, 0.34), "Avenir": (1.0, 0.366), "Didot": (0.941, 0.299)}

REPO_FONTS = Path(__file__).resolve().parent.parent / "fonts"
TABLE_FILE = Path(__file__).resolve().parent / "metrics.json"
HOME = Path.home()
SEARCH = [
    REPO_FONTS,
    HOME / "Library/Fonts", Path("/Library/Fonts"), Path("/System/Library/Fonts"),
    Path("/System/Library/Fonts/Supplemental"),
    *map(Path, glob.glob("/System/Library/AssetsV2/com_apple_MobileAsset_Font*/*/AssetData")),
    Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts",
    HOME / "AppData/Local/Microsoft/Windows/Fonts",
    Path("/usr/share/fonts"), Path("/usr/local/share/fonts"), HOME / ".fonts", HOME / ".local/share/fonts",
]
EXTS = (".ttf", ".ttc", ".otf", ".otc")
REGULAR = ("Regular", "Normal", "Book", "Roman", "W3")


def configure(overrides):
    """poster.yaml 里的 fonts: 覆盖默认角色（值可以是一个名字，或 [西文, 中文] 两个名字）"""
    FONTS.clear()
    FONTS.update(DEFAULT_FONTS)
    for role, v in (overrides or {}).items():
        if role not in DEFAULT_FONTS:
            raise ValueError(f"fonts: 里没有「{role}」这个角色，可选：{', '.join(DEFAULT_FONTS)}")
        FONTS[role] = (v, v) if isinstance(v, str) else tuple(v)
    _face.cache_clear()


def _key(s):
    return "".join(ch for ch in s.lower() if ch.isalnum())


def _files():
    for d in SEARCH:
        if d.is_dir():
            for root, _, names in os.walk(d):
                for n in names:
                    if n.lower().endswith(EXTS):
                        yield Path(root) / n


@lru_cache(maxsize=None)
def _all_files():
    return tuple(_files())


def _faces_in(path):
    i = 0
    while True:
        try:
            f = ImageFont.truetype(str(path), 1000, index=i)
        except (OSError, ValueError):
            return
        yield i, f
        i += 1
        if not str(path).lower().endswith((".ttc", ".otc")):
            return


@lru_cache(maxsize=None)
def _index():
    """全量扫描一次：{规范化的 "家族 字重": (路径, 序号)}；常规字重另外登记一份只有家族名的键"""
    idx = {}
    for p in _all_files():
        for i, f in _faces_in(p):
            family, style = f.getname()
            idx.setdefault(_key(f"{family} {style}"), (p, i))
            if style in REGULAR:
                idx.setdefault(_key(family), (p, i))
    return idx


@lru_cache(maxsize=None)
def _face(typeface):
    """按 typeface 名（如 "Avenir Next Demi Bold"）找字体，返回 1000 号 PIL 字体；找不到返回 None。
    先只看文件名里带家族名首词的文件，找不到再查全量索引。"""
    want = _key(typeface)
    first = _key(typeface.split()[0])
    for p in (p for p in _all_files() if first in _key(p.name)):
        for _, f in _faces_in(p):
            family, style = f.getname()
            if _key(f"{family} {style}") == want or (_key(family) == want and style in REGULAR):
                return f
    hit = _index().get(want)
    return ImageFont.truetype(str(hit[0]), 1000, index=hit[1]) if hit else None


_warned = set()


@lru_cache(maxsize=None)
def _table():
    return json.loads(TABLE_FILE.read_text(encoding="utf-8")) if TABLE_FILE.exists() else {}


def _warn(typeface):
    if typeface not in _warned:
        _warned.add(typeface)
        print(f"  ⚠ 本机没找到字体「{typeface}」，按估算字宽排版（打开 PPTX 时会用替代字体显示）", file=sys.stderr)


def is_ea(ch):
    return unicodedata.east_asian_width(ch) in ("W", "F")


def _approx(ch):
    if is_ea(ch):
        return 1.0
    if ch == " ":
        return 0.28
    if ch.isdigit():
        return 0.58
    if ch.isupper():
        return 0.68
    if ch.isalpha():
        return 0.54
    return 0.36


def width(text, font, sz, spc=0.0):
    """文字宽度（pt）；中文字符用 font[1] 量，其余用 font[0] 量；spc 为每个字后的字距（pt）"""
    total = 0.0
    parts = [(text, font[0])] if font[0] == font[1] else [
        ("".join(ch for ch in text if is_ea(ch) == is_cjk), font[1] if is_cjk else font[0]) for is_cjk in (False, True)]
    for part, name in parts:
        if not part:
            continue
        face = _face(name)
        if face is not None:
            total += face.getlength(part)
        elif name in _table():
            t = _table()[name]
            total += sum(t["adv"].get(ch, t["wide"] if is_ea(ch) else _approx(ch) * 1000) for ch in part)
            total += sum(t["kern"].get(part[i:i + 2], 0) for i in range(len(part) - 1))
        else:
            _warn(name)
            total += sum(_approx(ch) for ch in part) * 1000
    return total * sz / 1000 + spc * len(text)


def metric(font):
    for k, v in METRICS.items():
        if font[0].startswith(k):
            return v
    face = _face(font[0]) or _face(font[1])
    if face is not None:
        asc, dsc = face.getmetrics()
        return asc / 1000, dsc / 1000
    return 1.0, 0.3


def base_off(*font_sz):
    """anchor=ctr 时，基线相对文本框中线的下移量（pt）；多个字号混排取最大上 / 下伸"""
    asc = max(metric(f)[0] * s for f, s in font_sz)
    dsc = max(metric(f)[1] * s for f, s in font_sz)
    return (asc - dsc) / 2


def ui_font(size, weight="semibold"):
    """拼对比图用的界面字体（PIL）：优先苹方，其次思源 / Noto / 微软雅黑"""
    names = {"semibold": ["PingFang SC Semibold", "Source Han Sans SC Bold", "Noto Sans CJK SC Bold",
                          "Microsoft YaHei Bold"],
             "regular": ["PingFang SC", "Source Han Sans SC", "Noto Sans CJK SC", "Microsoft YaHei"]}[weight]
    for n in names:
        f = _face(n)
        if f is not None:
            return f.font_variant(size=size)
    return ImageFont.load_default(size)
