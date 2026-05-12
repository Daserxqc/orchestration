from __future__ import annotations

import base64
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parent
PNG_PATH = ROOT / "figure2_rescue_loop.png"
SVG_PATH = ROOT / "figure2_rescue_loop.svg"

WIDTH = 1380
HEIGHT = 620

BG = (250, 251, 252, 255)
TEXT = (43, 55, 69, 255)
MUTED = (112, 125, 138, 255)
LINE = (112, 127, 146, 170)

BLUE = (120, 188, 229, 255)
BLUE_DARK = (73, 145, 198, 255)
GREEN = (115, 197, 162, 255)
GREEN_DARK = (78, 163, 127, 255)
ORANGE = (247, 171, 112, 255)
ORANGE_DARK = (222, 132, 63, 255)
GRAY = (239, 244, 248, 255)


def load_font(size: int, bold: bool = False):
    candidates = (
        ["C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/msyhbd.ttc"]
        if bold
        else ["C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/msyh.ttc"]
    )
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


FONT_SMALL = load_font(20)
FONT_BODY = load_font(28)
FONT_HEAD = load_font(30, bold=True)


def add_shadow_rect(base: Image.Image, bbox, radius, fill, outline=None, offset=(0, 8), alpha=45):
    shadow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    x0, y0, x1, y1 = bbox
    dx, dy = offset
    sdraw.rounded_rectangle((x0 + dx, y0 + dy, x1 + dx, y1 + dy), radius=radius, fill=(10, 25, 40, alpha))
    shadow = shadow.filter(ImageFilter.GaussianBlur(12))
    base.alpha_composite(shadow)
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    odraw.rounded_rectangle(bbox, radius=radius, fill=fill, outline=outline, width=2 if outline else 0)
    base.alpha_composite(overlay)


def text_center(draw, xy, text, font, fill=TEXT):
    bbox = draw.textbbox((0, 0), text, font=font)
    draw.text((xy[0] - (bbox[2] - bbox[0]) / 2, xy[1] - (bbox[3] - bbox[1]) / 2), text, font=font, fill=fill)


def multiline_center(draw, xy, lines, font, fill=TEXT, spacing=6):
    heights = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        heights.append(bbox[3] - bbox[1])
    total = sum(heights) + spacing * (len(lines) - 1)
    top = xy[1] - total / 2
    for line, h in zip(lines, heights):
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        draw.text((xy[0] - w / 2, top), line, font=font, fill=fill)
        top += h + spacing


def draw_arrow(draw, start, end, fill=LINE, width=4):
    draw.line([start, end], fill=fill, width=width)
    vx = end[0] - start[0]
    vy = end[1] - start[1]
    norm = max((vx**2 + vy**2) ** 0.5, 1.0)
    ux, uy = vx / norm, vy / norm
    px, py = -uy, ux
    size = 11
    p1 = (end[0] - ux * size - px * size * 0.7, end[1] - uy * size - py * size * 0.7)
    p2 = (end[0] - ux * size + px * size * 0.7, end[1] - uy * size + py * size * 0.7)
    draw.polygon([end, p1, p2], fill=fill)


def build_png() -> None:
    image = Image.new("RGBA", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)

    glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    gdraw.ellipse((160, 140, 720, 560), fill=(165, 214, 241, 22))
    gdraw.ellipse((640, 60, 1240, 500), fill=(252, 210, 171, 18))
    glow = glow.filter(ImageFilter.GaussianBlur(55))
    image.alpha_composite(glow)

    add_shadow_rect(image, (90, 184, 330, 324), 34, (235, 246, 253, 255), (194, 222, 239, 255))
    multiline_center(draw, (210, 226), ["Draft Code"], FONT_HEAD)
    text_center(draw, (210, 260), "first sampled solution", FONT_SMALL, fill=MUTED)
    draw.rounded_rectangle((142, 274, 278, 304), radius=10, fill=(255, 255, 255, 255), outline=(195, 205, 214, 255), width=2)
    draw.line((158, 286, 248, 286), fill=BLUE_DARK, width=3)
    draw.line((158, 297, 228, 297), fill=(148, 171, 192, 255), width=3)

    add_shadow_rect(image, (408, 170, 668, 338), 34, (239, 244, 248, 255), (207, 217, 226, 255))
    multiline_center(draw, (538, 214), ["Execute", "Against Tests"], FONT_HEAD)
    text_center(draw, (538, 258), "observe runtime and assertion failures", FONT_SMALL, fill=MUTED)
    draw.line((490, 288, 584, 288), fill=(168, 190, 206, 255), width=3)
    draw.line((490, 304, 562, 304), fill=(168, 190, 206, 255), width=3)

    add_shadow_rect(image, (756, 148, 1048, 360), 36, (254, 239, 225, 255), (244, 190, 143, 255))
    multiline_center(draw, (902, 194), ["Compress Failure"], FONT_HEAD)
    text_center(draw, (902, 230), "retain only actionable error evidence", FONT_SMALL, fill=MUTED)
    draw.rounded_rectangle((810, 248, 898, 314), radius=16, fill=(255, 248, 243, 255), outline=(234, 174, 124, 255), width=2)
    draw.ellipse((828, 264, 852, 288), outline=ORANGE_DARK, width=4)
    draw.line((840, 288, 840, 296), fill=ORANGE_DARK, width=4)
    draw.line((868, 264, 884, 264), fill=ORANGE_DARK, width=4)
    draw.line((868, 278, 884, 278), fill=ORANGE_DARK, width=4)
    draw.line((868, 292, 878, 292), fill=ORANGE_DARK, width=4)
    draw.line((904, 282, 940, 282), fill=ORANGE_DARK, width=4)
    draw.polygon([(940, 282), (928, 275), (928, 289)], fill=ORANGE_DARK)
    draw.rounded_rectangle((954, 248, 1014, 314), radius=16, fill=(255, 255, 255, 255), outline=(229, 183, 144, 255), width=2)
    draw.line((968, 266, 998, 266), fill=(179, 159, 142, 255), width=3)
    draw.line((968, 280, 998, 280), fill=(179, 159, 142, 255), width=3)
    draw.line((968, 294, 988, 294), fill=ORANGE_DARK, width=4)

    add_shadow_rect(image, (770, 406, 1040, 536), 34, (232, 249, 240, 255), (182, 225, 202, 255))
    multiline_center(draw, (905, 446), ["Repair Attempt"], FONT_HEAD)
    text_center(draw, (905, 478), "generate a targeted local fix", FONT_SMALL, fill=MUTED)
    draw.rounded_rectangle((860, 490, 950, 522), radius=10, fill=(255, 255, 255, 255), outline=(186, 217, 198, 255), width=2)
    draw.line((875, 502, 930, 502), fill=GREEN_DARK, width=3)
    draw.line((875, 513, 915, 513), fill=(143, 180, 161, 255), width=3)

    add_shadow_rect(image, (1120, 238, 1278, 374), 34, (239, 251, 244, 255), (192, 226, 206, 255))
    multiline_center(draw, (1199, 284), ["Pass or", "Stop"], FONT_HEAD)
    text_center(draw, (1199, 322), "accept success or halt the loop", FONT_SMALL, fill=MUTED)
    draw.ellipse((1160, 330, 1180, 350), fill=GREEN_DARK)
    draw.text((1190, 326), "pass", font=FONT_SMALL, fill=TEXT)

    draw_arrow(draw, (330, 254), (408, 254))
    draw_arrow(draw, (668, 254), (756, 254))
    draw_arrow(draw, (902, 360), (902, 406))
    draw_arrow(draw, (1040, 470), (1120, 332))

    # Loop-back arrow.
    draw.line((1198, 374, 1198, 560, 214, 560, 214, 324), fill=LINE, width=4)
    draw.polygon([(214, 324), (207, 336), (221, 336)], fill=LINE)
    text_center(draw, (702, 580), "retry only with compressed local evidence", FONT_SMALL, fill=MUTED)

    image.save(PNG_PATH)


def build_svg() -> None:
    png_base64 = base64.b64encode(PNG_PATH.read_bytes()).decode("ascii")
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">
  <image href="data:image/png;base64,{png_base64}" width="{WIDTH}" height="{HEIGHT}"/>
</svg>
"""
    SVG_PATH.write_text(svg, encoding="utf-8")


def main() -> None:
    build_png()
    build_svg()
    print(f"Wrote {PNG_PATH}")
    print(f"Wrote {SVG_PATH}")


if __name__ == "__main__":
    main()
