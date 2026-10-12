#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "python-pptx>=1.0",
#   "segno>=1.6",
#   "pyyaml>=6.0",
#   "pillow>=10.1",
#   "lxml>=4.9",
#   "zxing-cpp>=2.2; python_version >= '3.10'",
# ]
# ///
"""一键生成海报：改好 poster.yaml 后运行

    uv run build.py            # 推荐：自动装好依赖
    python build.py            # 或者先 pip install -r requirements.txt

python build.py --help 查看全部用法。"""
import sys

try:
    from posterkit.cli import main
except ModuleNotFoundError as e:
    sys.exit(f"✗ 缺少依赖 {e.name}。请运行  uv run build.py  或先  pip install -r requirements.txt")

if __name__ == "__main__":
    sys.exit(main())
