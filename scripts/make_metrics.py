"""维护用：从 macOS 自带字体导出默认字体的字宽表 posterkit/metrics.json。
有了它，在没有这些字体的 Windows / Linux / GitHub Actions 上排版结果也和 macOS 完全一致。
只记录字符的前进宽度和字偶距（排版度量），不含任何字形。

    python scripts/make_metrics.py"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from posterkit import fonts as F  # noqa: E402

CHARS = "".join(chr(c) for c in range(0x20, 0x7F)) + "–—‘’“”…·•、，。：；！？（）《》〈〉【】「」『』～／＆％＋－＝"


def main():
    names = sorted({n for pair in F.DEFAULT_FONTS.values() for n in pair})
    out = {}
    for name in names:
        face = F._face(name)
        if face is None:
            sys.exit(f"本机没有字体 {name}（需要在 macOS 上运行）")
        adv = {ch: face.getlength(ch) for ch in CHARS}
        kern = {}
        for a in CHARS:
            for b in CHARS:
                k = face.getlength(a + b) - adv[a] - adv[b]
                if abs(k) > 0.01:
                    kern[a + b] = round(k, 2)
        out[name] = dict(wide=round(face.getlength("中"), 2), adv={c: round(v, 2) for c, v in adv.items()}, kern=kern)
    path = ROOT / "posterkit" / "metrics.json"
    path.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(path, f"{path.stat().st_size // 1024} KB", names)


if __name__ == "__main__":
    main()
