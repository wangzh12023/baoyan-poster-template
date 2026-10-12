"""54 款配色：赤 · 橙 · 黄 · 绿（薄荷 / 草木）· 青 · 蓝 · 紫 · 粉，每个色系 6 款。

每款配色决定：背景渐变的三个色标、装饰渐变圆的色相 / 浓淡、圆点和横线的点缀色、
以及文字的墨色 / 正文色 / 注释色 / 强调色 / 细分隔线色。同一款里所有颜色同一色系。
装饰渐变取自原薄荷绿海报的色标，在 OKLCH 下换色相、保留各色标之间的明度关系。"""
from .oklch import hex_to_oklch, oklch_to_hex as lch

PEAK_L, PEAK_C = 0.870, 0.156           # 原海报渐变圆最浓色标 40F5C7 的明度 / 色度
MINT_HUE = round(hex_to_oklch("40F5C7")[2])
BLUE_HUE = 264


def tint(color, hue, drop, chroma=1.0, soft=1.0, mul=None):
    """把原薄荷绿色标换到目标色相：soft<1 把明度往白色方向压缩（更粉嫩），chroma 缩放色度，
    drop 按色度降明度；mul 为满底色版本的底色：与之正片叠底，渐变圆的白边才能融进有色背景"""
    L, C, _ = hex_to_oklch(color)
    out = lch(1 - soft * (1 - L) - drop * C, C * chroma, hue)
    if mul:
        out = "".join(f"{round(int(out[i:i + 2], 16) * int(mul[i:i + 2], 16) / 255):02X}" for i in (0, 2, 4))
    return out


def bg3(hue, c=0.03, ls=(0.968, 0.993, 0.958)):
    """背景渐变三个色标：两端带色、中间近白（色度超出色域时自动收到该色相能给的上限）"""
    return [lch(ls[0], c, hue), lch(ls[1], c * 0.25, hue), lch(ls[2], c * 1.2, hue)]


def full(hue, c=0.035, ls=(0.930, 0.962, 0.912), mul_l=0.955):
    """满底色：背景整体带色，渐变圆与 mul 正片叠底"""
    return dict(bg=[lch(ls[0], c, hue), lch(ls[1], c * 0.5, hue), lch(ls[2], c * 1.2, hue)],
                mul=lch(mul_l, c * 0.6, hue), hair=lch(0.80, 0.07, hue))


def pal(key, name, hue, accent, pop, text_hue, bg, chroma=1.0, soft=1.0, drop=0.0, peak=None,
        hair=None, topic=None, text_chroma=1.0, ink=None, body=None, muted=None, mul=None):
    """hue/chroma/soft/drop 控制渐变圆（或用 peak=(L, C) 直接给最浓处的明度与色度）；bg 为背景渐变的三个色标；
    topic 可单独指定主题文字颜色（"ink" = 黑字）；mul 用于满底色版本（渐变圆与底色正片叠底）"""
    if peak:
        drop, chroma = (PEAK_L - peak[0]) / PEAK_C, peak[1] / PEAK_C
    th, tc = text_hue, text_chroma
    ink = ink or lch(0.21, 0.022 * tc, th)
    return dict(
        key=key, name=name, hue=hue, chroma=chroma, soft=soft, drop=drop, mul=mul, bg=bg, pop=pop,
        ink=ink, body=body or lch(0.39, 0.030 * tc, th), muted=muted or lch(0.58, 0.036 * tc, th),
        accent=accent, hair=hair or lch(0.86, 0.050, hue), topic=ink if topic == "ink" else (topic or accent))


COOL_BG = (0.982, 0.997, 0.975)         # 绿 / 青在高明度下色度充足，背景取得更亮才清爽

# 色系名 → (英文 id, 对比图大字, 对比图小字)
FAMILY_INFO = {
    "红": ("red", "赤", "红色系"), "橙": ("orange", "橙", "橙色系"), "黄": ("yellow", "黄", "黄色系"),
    "绿": ("mint", "绿", "薄荷 · 偏冷"), "草绿": ("grass", "绿", "草木 · 偏暖"), "青": ("cyan", "青", "青色系"),
    "蓝": ("blue", "蓝", "蓝色系"), "紫": ("purple", "紫", "紫色系"), "粉": ("pink", "粉", "粉色系"),
}

FAMILIES = {
    # ---- 赤：浅红必然偏粉，靠暖色相（朱红）与更深的红字把它和粉色系拉开 ----
    "红": [
        pal("红1", "朱红", 31, accent=lch(0.61, 0.21, 31), pop=lch(0.71, 0.18, 31), text_hue=30,
            peak=(0.775, 0.14), bg=bg3(31)),
        pal("红2", "正红", 25, accent=lch(0.55, 0.22, 27), pop=lch(0.66, 0.21, 26), text_hue=25,
            peak=(0.755, 0.155), bg=bg3(24)),
        pal("红3", "胭脂红", 13, accent=lch(0.56, 0.22, 14), pop=lch(0.68, 0.19, 12), text_hue=14,
            peak=(0.775, 0.14), bg=bg3(12)),
        pal("红4", "酒红", 16, accent=lch(0.43, 0.15, 17), pop=lch(0.62, 0.15, 16), text_hue=16,
            peak=(0.79, 0.095), bg=bg3(18, 0.02), hair=lch(0.85, 0.035, 16)),
        pal("红5", "朱红黑字", 29, accent=lch(0.63, 0.22, 29), pop=lch(0.68, 0.20, 29), text_hue=28,
            peak=(0.775, 0.14), bg=bg3(29), topic="ink"),
        pal("红6", "满底浅红", 27, accent=lch(0.53, 0.21, 27), pop=lch(0.66, 0.20, 27), text_hue=26,
            peak=(0.775, 0.14), **full(27)),
    ],
    # ---- 橙 ----
    "橙": [
        pal("橙1", "橘子橙", 56, accent=lch(0.67, 0.18, 48), pop=lch(0.77, 0.16, 58), text_hue=55,
            peak=(0.80, 0.145), bg=bg3(60)),
        pal("橙2", "柿子橙", 43, accent=lch(0.64, 0.20, 40), pop=lch(0.73, 0.17, 44), text_hue=42,
            peak=(0.785, 0.145), bg=bg3(45)),
        pal("橙3", "杏子橙", 67, accent=lch(0.68, 0.16, 58), pop=lch(0.81, 0.14, 68), text_hue=62,
            peak=(0.84, 0.125), bg=bg3(72)),
        pal("橙4", "奶橘", 58, accent=lch(0.65, 0.13, 54), pop=lch(0.80, 0.10, 60), text_hue=58,
            peak=(0.855, 0.085), bg=bg3(64, 0.022), hair=lch(0.87, 0.035, 60), text_chroma=0.8),
        pal("橙5", "橘橙黑字", 55, accent=lch(0.70, 0.18, 52), pop=lch(0.76, 0.17, 56), text_hue=55,
            peak=(0.80, 0.145), bg=bg3(60), topic="ink", text_chroma=0.7),
        pal("橙6", "满底浅橙", 58, accent=lch(0.60, 0.18, 44), pop=lch(0.72, 0.17, 52), text_hue=52,
            peak=(0.80, 0.145), **full(62, 0.045)),
    ],
    # ---- 黄：各色相在自己最亮最饱和的明度上取色（柠檬黄偏高、芒果黄偏低），避免发灰发土 ----
    "黄": [
        pal("黄1", "柠檬黄黑字", 104, accent=lch(0.66, 0.14, 80), pop=lch(0.88, 0.18, 102), text_hue=90,
            chroma=1.15, soft=0.55, bg=["FDFCE4", "FFFFFA", "FBFADA"], hair=lch(0.87, 0.04, 100),
            topic="ink", text_chroma=0.6),
        pal("黄2", "向日葵", 90, accent=lch(0.66, 0.18, 52), pop=lch(0.84, 0.17, 85), text_hue=70,
            chroma=1.2, soft=1.0, bg=["FFF9E1", "FFFEF8", "FFF5D6"], hair=lch(0.87, 0.045, 85), text_chroma=0.7),
        pal("黄3", "奶油黄", 92, accent=lch(0.56, 0.12, 62), pop=lch(0.84, 0.12, 88), text_hue=70,
            chroma=0.75, soft=0.75, bg=["FFF9E6", "FFFEFA", "FEF5DC"], hair=lch(0.87, 0.04, 85), text_chroma=0.7),
        pal("黄4", "芒果黄", 78, accent=lch(0.63, 0.20, 38), pop=lch(0.80, 0.16, 72), text_hue=55,
            chroma=1.2, soft=1.1, bg=["FFF6E3", "FFFDF8", "FFF1D8"], hair=lch(0.87, 0.05, 70), text_chroma=0.8),
        pal("黄5", "明黄藏青", 98, accent=lch(0.38, 0.13, 265), pop=lch(0.86, 0.18, 98), text_hue=265,
            chroma=1.2, soft=0.8, bg=["FFFBE0", "FFFFFA", "FDF8D2"], hair=lch(0.87, 0.045, 95),
            ink=lch(0.22, 0.04, 265)),
        pal("黄6", "满底鹅黄", 98, accent=lch(0.24, 0.02, 90), pop=lch(0.24, 0.02, 90), text_hue=90,
            chroma=1.2, soft=0.8, bg=["FFF3B5", "FFF9DC", "FFEFA3"], mul="FFF7D2", hair=lch(0.80, 0.09, 95),
            text_chroma=0.6),
    ],
    # ---- 绿 · 薄荷系（偏冷）：绿1 即原海报配色 ----
    "绿": [
        pal("绿1", "薄荷绿", MINT_HUE, accent="0B8A68", pop="00EAB0", text_hue=170,
            bg=["EFFFF9", "FFFFFF", "EDFFF8"]),
        pal("绿2", "松石绿", 166, accent="1F6B52", pop=lch(0.74, 0.14, 166), text_hue=166,
            peak=(0.86, 0.125), bg=bg3(166, 0.018, COOL_BG)),
        pal("绿3", "翡翠绿", 157, accent=lch(0.56, 0.15, 157), pop=lch(0.77, 0.18, 157), text_hue=158,
            peak=(0.84, 0.17), bg=bg3(157, 0.022, COOL_BG)),
        pal("绿4", "薄荷黑字", 172, accent=lch(0.66, 0.13, 172), pop=lch(0.83, 0.16, 172), text_hue=175,
            bg=["EFFFF9", "FFFFFF", "EDFFF8"], topic="ink"),
        pal("绿5", "鼠尾草", 160, accent=lch(0.50, 0.065, 160), pop=lch(0.74, 0.075, 160), text_hue=160,
            peak=(0.865, 0.07), bg=bg3(160, 0.012, COOL_BG), hair=lch(0.86, 0.03, 160)),
        pal("绿6", "满底薄荷", 170, accent=lch(0.48, 0.10, 170), pop=lch(0.74, 0.14, 170), text_hue=170,
            peak=(0.85, 0.15), **full(170, 0.04, (0.945, 0.972, 0.93), 0.965)),
    ],
    # ---- 绿 · 草木系（偏暖、带黄） ----
    "草绿": [
        pal("绿7", "春草绿", 146, accent=lch(0.57, 0.17, 147), pop=lch(0.80, 0.21, 146), text_hue=147,
            peak=(0.875, 0.175), bg=bg3(146, 0.022, COOL_BG)),
        pal("绿8", "青柠绿", 127, accent=lch(0.58, 0.16, 134), pop=lch(0.86, 0.20, 127), text_hue=132,
            peak=(0.905, 0.17), bg=bg3(124, 0.028, COOL_BG)),
        pal("绿9", "抹茶绿", 134, accent=lch(0.53, 0.10, 138), pop=lch(0.78, 0.12, 134), text_hue=136,
            peak=(0.875, 0.095), bg=bg3(128, 0.016, COOL_BG), hair=lch(0.87, 0.035, 132)),
        pal("绿10", "森林墨绿", 152, accent=lch(0.40, 0.09, 155), pop=lch(0.62, 0.15, 152), text_hue=155,
            peak=(0.855, 0.14), bg=bg3(150, 0.018, COOL_BG)),
        pal("绿11", "草绿黑字", 144, accent=lch(0.66, 0.19, 145), pop=lch(0.80, 0.21, 144), text_hue=146,
            peak=(0.875, 0.175), bg=bg3(144, 0.022, COOL_BG), topic="ink"),
        pal("绿12", "满底嫩绿", 138, accent=lch(0.50, 0.14, 142), pop=lch(0.74, 0.19, 140), text_hue=140,
            peak=(0.875, 0.165), **full(136, 0.045, (0.948, 0.974, 0.934), 0.967)),
    ],
    # ---- 青 ----
    "青": [
        pal("青1", "湖水青", 196, accent=lch(0.57, 0.10, 202), pop=lch(0.80, 0.13, 196), text_hue=200,
            peak=(0.875, 0.13), bg=bg3(196, 0.02, COOL_BG)),
        pal("青2", "孔雀青", 208, accent=lch(0.49, 0.10, 213), pop=lch(0.70, 0.12, 210), text_hue=212,
            peak=(0.84, 0.12), bg=bg3(208, 0.02, COOL_BG)),
        pal("青3", "天青", 226, accent=lch(0.58, 0.14, 233), pop=lch(0.76, 0.13, 228), text_hue=232,
            peak=(0.845, 0.11), bg=bg3(226, 0.02, COOL_BG)),
        pal("青4", "青瓷", 186, accent=lch(0.51, 0.06, 192), pop=lch(0.76, 0.07, 188), text_hue=190,
            peak=(0.875, 0.065), bg=bg3(186, 0.012, COOL_BG), hair=lch(0.86, 0.03, 188)),
        pal("青5", "青黑字", 200, accent=lch(0.66, 0.12, 205), pop=lch(0.78, 0.13, 200), text_hue=205,
            peak=(0.87, 0.13), bg=bg3(200, 0.02, COOL_BG), topic="ink"),
        pal("青6", "满底浅青", 202, accent=lch(0.48, 0.10, 210), pop=lch(0.72, 0.12, 205), text_hue=208,
            peak=(0.855, 0.12), **full(200, 0.035, (0.945, 0.972, 0.93), 0.965)),
    ],
    # ---- 蓝 ----
    "蓝": [
        pal("蓝1", "钴蓝", BLUE_HUE, accent="2345B0", pop=lch(0.66, 0.15, BLUE_HUE), text_hue=BLUE_HUE,
            drop=0.12, bg=[tint(c, BLUE_HUE, 0.35) for c in ("EFFFF9", "FFFFFF", "EDFFF8")],
            ink="121726", body="3A4152", muted="7A8193", hair=lch(0.84, 0.035, BLUE_HUE)),
        pal("蓝2", "天蓝", 246, accent=lch(0.58, 0.16, 251), pop=lch(0.72, 0.14, 248), text_hue=250,
            peak=(0.815, 0.11), bg=bg3(244)),
        pal("蓝3", "克莱因蓝", 267, accent=lch(0.43, 0.27, 266), pop=lch(0.60, 0.21, 266), text_hue=266,
            peak=(0.75, 0.135), bg=bg3(266)),
        pal("蓝4", "雾霾蓝", 250, accent=lch(0.50, 0.07, 252), pop=lch(0.72, 0.075, 250), text_hue=252,
            peak=(0.835, 0.06), bg=bg3(250, 0.012), hair=lch(0.86, 0.03, 250)),
        pal("蓝5", "蓝黑字", 258, accent=lch(0.60, 0.19, 260), pop=lch(0.66, 0.17, 258), text_hue=260,
            peak=(0.795, 0.11), bg=bg3(256), topic="ink"),
        pal("蓝6", "满底浅蓝", 256, accent=lch(0.47, 0.19, 261), pop=lch(0.64, 0.17, 258), text_hue=260,
            peak=(0.79, 0.115), **full(254)),
    ],
    # ---- 紫 ----
    "紫": [
        pal("紫1", "薰衣草", 296, accent=lch(0.56, 0.19, 296), pop=lch(0.70, 0.15, 296), text_hue=296,
            peak=(0.795, 0.11), bg=bg3(296)),
        pal("紫2", "香芋紫", 316, accent=lch(0.58, 0.19, 319), pop=lch(0.73, 0.16, 317), text_hue=318,
            peak=(0.81, 0.12), bg=bg3(316)),
        pal("紫3", "葡萄紫", 291, accent=lch(0.44, 0.21, 292), pop=lch(0.62, 0.19, 292), text_hue=292,
            peak=(0.76, 0.13), bg=bg3(290)),
        pal("紫4", "藕荷", 322, accent=lch(0.50, 0.08, 324), pop=lch(0.73, 0.08, 322), text_hue=324,
            peak=(0.83, 0.06), bg=bg3(322, 0.012), hair=lch(0.86, 0.03, 322)),
        pal("紫5", "紫黑字", 300, accent=lch(0.62, 0.19, 300), pop=lch(0.68, 0.17, 300), text_hue=300,
            peak=(0.795, 0.115), bg=bg3(300), topic="ink"),
        pal("紫6", "满底浅紫", 300, accent=lch(0.48, 0.20, 298), pop=lch(0.66, 0.17, 300), text_hue=300,
            peak=(0.795, 0.115), **full(300)),
    ],
    # ---- 粉：暖一点、浅一点；背景本身带粉，不靠加白变浅 ----
    "粉": [
        pal("粉1", "樱花粉", 9, accent=lch(0.65, 0.17, 6), pop=lch(0.79, 0.12, 8), text_hue=10,
            drop=0.22, bg=["FFF1F4", "FFFCFD", "FFEEF2"]),
        pal("粉2", "蜜桃粉", 28, accent=lch(0.67, 0.16, 28), pop=lch(0.81, 0.11, 35), text_hue=40,
            drop=0.22, bg=["FFF2EC", "FFFCFA", "FFEEE7"]),
        pal("粉3", "草莓牛奶", 6, accent=lch(0.61, 0.19, 8), pop=lch(0.74, 0.15, 6), text_hue=25,
            chroma=1.2, drop=0.35, bg=["FFF7EC", "FFFEFB", "FFF3E4"]),
        pal("粉4", "裸粉", 15, accent=lch(0.56, 0.10, 12), pop=lch(0.75, 0.08, 15), text_hue=30,
            chroma=0.62, drop=0.45, bg=["FBF0ED", "FFFBF9", "F8EBE7"], hair=lch(0.85, 0.03, 20)),
        pal("粉5", "浅粉黑字", 5, accent=lch(0.70, 0.16, 5), pop=lch(0.78, 0.13, 5), text_hue=10,
            drop=0.20, bg=["FFF0F4", "FFFBFC", "FFECF1"], topic="ink"),
        pal("粉6", "满底浅粉", 8, accent=lch(0.60, 0.18, 6), pop=lch(0.74, 0.14, 6), text_hue=10,
            drop=0.10, bg=["FFE2E9", "FFF1F4", "FFDBE4"], mul="FFEDF1", hair=lch(0.80, 0.07, 8)),
    ],
}

for _fam, _pals in FAMILIES.items():
    for _i, _p in enumerate(_pals, 1):
        _p.update(family=_fam, slug=f"{FAMILY_INFO[_fam][0]}-{_i}", file=f"{_p['key']}_{_p['name']}")

PALETTES = [p for fam in FAMILIES.values() for p in fam]


def select(tokens):
    """按编号（绿3）、名称（翡翠绿）、色系（蓝 / 草绿 / blue）或英文 id（mint-3）挑配色；不给则全部"""
    if not tokens:
        return list(PALETTES)
    picked, unknown = [], []
    for tok in tokens:
        hit = [p for p in PALETTES if tok in (p["key"], p["name"], p["slug"], p["file"], p["family"],
                                              FAMILY_INFO[p["family"]][0])]
        if not hit:
            unknown.append(tok)
        picked += [p for p in hit if p not in picked]
    if unknown:
        raise ValueError(f"没有这些配色：{'、'.join(unknown)}（用 --list 查看全部 54 款）")
    return sorted(picked, key=PALETTES.index)
