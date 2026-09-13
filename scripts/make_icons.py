"""Generate the PWA PNG icons in frontend/public/icons/ (run once; output is committed)."""

from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / "frontend" / "public" / "icons"
FOREST = (6, 78, 59, 255)
MINT = (110, 231, 183, 255)


def leaf_icon(size: int, padding: float) -> Image.Image:
    scale = 4  # supersample for smooth edges
    s = size * scale
    img = Image.new("RGBA", (s, s), FOREST)
    draw = ImageDraw.Draw(img)
    inset = s * padding
    box = s - 2 * inset

    def p(x: float, y: float) -> tuple[float, float]:
        return inset + x / 64 * box, inset + y / 64 * box

    # Leaf body (same shape as favicon.svg, approximated with a polygon)
    outline = [p(46, 16), p(36, 17), p(27, 22), p(21, 30), p(18, 40), p(18.6, 44.5), p(19.6, 48),
               p(23, 49), p(30, 50), p(38, 47), p(43, 40), p(46, 30)]
    draw.polygon(outline, fill=MINT)
    # Vein
    draw.line([p(22, 49), p(30, 38), p(40, 27)], fill=FOREST, width=max(2, int(box * 0.035)))
    return img.resize((size, size), Image.LANCZOS)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    leaf_icon(192, 0.08).save(OUT / "icon-192.png")
    leaf_icon(512, 0.08).save(OUT / "icon-512.png")
    leaf_icon(512, 0.2).save(OUT / "icon-512-maskable.png")  # safe zone for Android masks
    leaf_icon(180, 0.1).convert("RGB").save(OUT / "apple-touch-icon.png")
    print(f"Icons written to {OUT}")


if __name__ == "__main__":
    main()
