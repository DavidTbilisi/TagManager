"""Regenerate tag.ico + tag.png in this directory.

Draws a stylised `>_` (terminal prompt) mark — the chevron in lime-green and
the underscore in cyan-blue — to match the chosen logo concept. Rounded caps
are applied by stamping circles at each line endpoint.

Run with the project's Python to refresh the icon. Bundles 16/24/32/48/64/
128/256 sizes into the .ico for crisp rendering at any DPI.
"""
from pathlib import Path
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent


GREEN = (60, 207, 138, 255)   # #3CCF8A (slightly punchy green for the >)
CYAN = (76, 194, 216, 255)    # #4CC2D8 (cool cyan for the _)


def _stroke(d: ImageDraw.ImageDraw, p1, p2, color, width: int) -> None:
    """Draw a rounded-cap line by stamping a thick line + two end circles."""
    d.line([p1, p2], fill=color, width=width)
    r = width // 2
    for (cx, cy) in (p1, p2):
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)


def draw_mark(size: int, scale: int = 4) -> Image.Image:
    """Render the >_ mark at `size`, supersampled by `scale` then downscaled."""
    s = size * scale
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    stroke_w = max(1, int(s * 0.105))
    cap_pad = stroke_w // 2 + int(s * 0.03)

    # Chevron `>` — two arms meeting at the right tip, slightly above centre
    # so the underscore can sit visually balanced below.
    tip_x = int(s * 0.55)
    tip_y = int(s * 0.50)
    arm_left_x = cap_pad
    arm_top_y = int(s * 0.22)
    arm_bot_y = int(s * 0.78)
    _stroke(d, (arm_left_x, arm_top_y), (tip_x, tip_y), GREEN, stroke_w)
    _stroke(d, (arm_left_x, arm_bot_y), (tip_x, tip_y), GREEN, stroke_w)

    # Underscore `_` — horizontal bar to the right of the chevron, baseline-aligned
    u_y = int(s * 0.80)
    u_x1 = int(s * 0.60)
    u_x2 = s - cap_pad
    _stroke(d, (u_x1, u_y), (u_x2, u_y), CYAN, stroke_w)

    return img.resize((size, size), Image.LANCZOS)


def main() -> None:
    sizes = [16, 24, 32, 48, 64, 128, 256]
    layers = [draw_mark(s) for s in sizes]

    ico_path = HERE / "tag.ico"
    layers[0].save(
        ico_path, format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=layers[1:],
    )

    png_path = HERE / "tag.png"
    draw_mark(64).save(png_path, format="PNG")

    preview_path = HERE / "tag-256.png"
    draw_mark(256).save(preview_path, format="PNG")

    print(f"wrote: {ico_path}, {png_path}, {preview_path}")


if __name__ == "__main__":
    main()
