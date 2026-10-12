# assets/

放你自己的素材，然后在 `poster.yaml` 里引用：

| 文件 | 用途 | 建议 |
|---|---|---|
| `logo.svg` | 示例主办方 logo（虚构的「示例大学」） | 换成你们学院 / 社团的 logo；SVG 最清晰，PNG 请用透明底 |
| `logo.png` | 同上的位图版 | 没装 `rsvg-convert` / `cairosvg` 时用来兜底 |
| `qr.png`（自己放） | 现成的二维码图片 | 微信群码这类不能由链接生成的，在 `qr.image` 里引用 |

`logo.color` 设为 `accent` / `ink` 时，logo 会被改成单色以跟随配色；想保留 logo 原本的颜色就写 `keep`。
