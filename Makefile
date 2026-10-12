# 常用命令（也可以直接 uv run build.py）
UV  := uv run
DEV := uv run --with python-pptx --with segno --with pyyaml --with pillow --with lxml --with zxing-cpp

.PHONY: build list clean docs metrics

build:            ## 生成全部 54 款到 output/
	$(UV) build.py

list:             ## 列出全部配色
	$(UV) build.py --list

clean:            ## 删除 output/
	rm -rf output

docs:             ## 维护者：重新生成 posters/ 和 README 图片（需要 macOS）
	$(DEV) python scripts/make_docs.py

metrics:          ## 维护者：重新导出默认字体的字宽表（需要 macOS）
	$(DEV) python scripts/make_metrics.py
