from __future__ import annotations

import base64
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parent
FIGURES_DIR = ROOT / "figures"
PNG_PATH = FIGURES_DIR / "figure1_overview.png"
SVG_PATH = FIGURES_DIR / "figure1_overview.svg"

WIDTH = 1980
HEIGHT = 680

BG = (250, 251, 252, 255)
TEXT = (43, 55, 69, 255)
MUTED = (112, 125, 138, 255)
LINE = (112, 127, 146, 150)

BLUE = (120, 188, 229, 255)
BLUE_DARK = (73, 145, 198, 255)
GREEN = (115, 197, 162, 255)
GREEN_DARK = (78, 163, 127, 255)
ORANGE = (247, 171, 112, 255)
ORANGE_DARK = (222, 132, 63, 255)
PURPLE = (165, 142, 216, 255)
PURPLE_DARK = (122, 103, 184, 255)
GRAY_PANEL = (236, 241, 246, 255)


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = []
    if bold:
        candidates.extend(
            [
                "C:/Windows/Fonts/arialbd.ttf",
                "C:/Windows/Fonts/segoeuib.ttf",
                "C:/Windows/Fonts/msyhbd.ttc",
            ]
        )
    else:
        candidates.extend(
            [
                "C:/Windows/Fonts/arial.ttf",
                "C:/Windows/Fonts/segoeui.ttf",
                "C:/Windows/Fonts/msyh.ttc",
            ]
        )
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


FONT_SMALL = load_font(20)
FONT_BODY = load_font(28)
FONT_TITLE = load_font(34, bold=True)
FONT_HEAD = load_font(30, bold=True)


def text_center(draw: ImageDraw.ImageDraw, xy: tuple[float, float], text: str, font, fill=TEXT) -> None:
    bbox = draw.textbbox((0, 0), text, font=font)
    x = xy[0] - (bbox[2] - bbox[0]) / 2
    y = xy[1] - (bbox[3] - bbox[1]) / 2
    draw.text((x, y), text, font=font, fill=fill)


def multiline_center(
    draw: ImageDraw.ImageDraw,
    xy: tuple[float, float],
    lines: list[str],
    font,
    fill=TEXT,
    spacing: int = 6,
) -> None:
    heights = []
    widths = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        widths.append(bbox[2] - bbox[0])
        heights.append(bbox[3] - bbox[1])
    total_h = sum(heights) + spacing * (len(lines) - 1)
    top = xy[1] - total_h / 2
    for idx, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        draw.text((xy[0] - w / 2, top), line, font=font, fill=fill)
        top += h + spacing


def add_shadow_rect(
    base: Image.Image,
    bbox: tuple[int, int, int, int],
    radius: int,
    fill: tuple[int, int, int, int],
    outline: tuple[int, int, int, int] | None = None,
    shadow_offset: tuple[int, int] = (0, 8),
    shadow_alpha: int = 45,
) -> None:
    shadow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    x0, y0, x1, y1 = bbox
    dx, dy = shadow_offset
    sdraw.rounded_rectangle((x0 + dx, y0 + dy, x1 + dx, y1 + dy), radius=radius, fill=(10, 25, 40, shadow_alpha))
    shadow = shadow.filter(ImageFilter.GaussianBlur(12))
    base.alpha_composite(shadow)

    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    odraw.rounded_rectangle(bbox, radius=radius, fill=fill, outline=outline, width=2 if outline else 0)
    base.alpha_composite(overlay)


def bezier_points(points: list[tuple[float, float]], segments: int = 120) -> list[tuple[float, float]]:
    if len(points) == 3:
        p0, p1, p2 = points
        out = []
        for i in range(segments + 1):
            t = i / segments
            x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t**2 * p2[0]
            y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t**2 * p2[1]
            out.append((x, y))
        return out
    if len(points) == 4:
        p0, p1, p2, p3 = points
        out = []
        for i in range(segments + 1):
            t = i / segments
            x = (
                (1 - t) ** 3 * p0[0]
                + 3 * (1 - t) ** 2 * t * p1[0]
                + 3 * (1 - t) * t**2 * p2[0]
                + t**3 * p3[0]
            )
            y = (
                (1 - t) ** 3 * p0[1]
                + 3 * (1 - t) ** 2 * t * p1[1]
                + 3 * (1 - t) * t**2 * p2[1]
                + t**3 * p3[1]
            )
            out.append((x, y))
        return out
    raise ValueError("Bezier helper supports quadratic or cubic curves only.")


def draw_ribbon(draw: ImageDraw.ImageDraw, points: list[tuple[float, float]], width: int, color: tuple[int, int, int, int]) -> None:
    curve = bezier_points(points, segments=200)
    draw.line(curve, fill=color, width=width, joint="curve")


def densify_polyline(points: list[tuple[float, float]], steps_per_segment: int = 28) -> list[tuple[float, float]]:
    if len(points) < 2:
        return list(points)
    out: list[tuple[float, float]] = []
    for i in range(len(points) - 1):
        x0, y0 = points[i]
        x1, y1 = points[i + 1]
        for k in range(steps_per_segment):
            t = k / steps_per_segment
            out.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
    out.append(points[-1])
    return out


def draw_polyline_ribbon(
    draw: ImageDraw.ImageDraw,
    points: list[tuple[float, float]],
    width: int,
    color: tuple[int, int, int, int],
    steps_per_segment: int = 28,
) -> None:
    curve = densify_polyline(points, steps_per_segment=steps_per_segment)
    draw.line(curve, fill=color, width=width, joint="curve")


def draw_round_band(
    draw: ImageDraw.ImageDraw,
    x0: float,
    x1: float,
    y: float,
    height: int,
    color: tuple[int, int, int, int],
) -> None:
    left = min(x0, x1)
    right = max(x0, x1)
    half = height / 2
    draw.rounded_rectangle((left, y - half, right, y + half), radius=height / 2, fill=color)


def draw_arrow(draw: ImageDraw.ImageDraw, start: tuple[float, float], end: tuple[float, float], fill=LINE, width: int = 3) -> None:
    draw.line([start, end], fill=fill, width=width)
    vx = end[0] - start[0]
    vy = end[1] - start[1]
    norm = max((vx**2 + vy**2) ** 0.5, 1.0)
    ux, uy = vx / norm, vy / norm
    px, py = -uy, ux
    size = 10
    p1 = (end[0] - ux * size - px * size * 0.7, end[1] - uy * size - py * size * 0.7)
    p2 = (end[0] - ux * size + px * size * 0.7, end[1] - uy * size + py * size * 0.7)
    draw.polygon([end, p1, p2], fill=fill)


def card_icon(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, accent: tuple[int, int, int, int]) -> None:
    draw.rounded_rectangle((x, y, x + w, y + h), radius=14, fill=(255, 255, 255, 255), outline=(195, 205, 214, 255), width=2)
    draw.line((x + 18, y + 20, x + w - 20, y + 20), fill=accent, width=4)
    for i in range(3):
        yy = y + 38 + i * 18
        draw.line((x + 18, yy, x + w - 24, yy), fill=(182, 191, 203, 255), width=3)


def build_png() -> None:
    image = Image.new("RGBA", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)

    soft = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(soft)
    sdraw.ellipse((250, 130, 1080, 620), fill=(153, 208, 235, 20))
    sdraw.ellipse((700, 70, 1860, 540), fill=(161, 218, 187, 18))
    soft = soft.filter(ImageFilter.GaussianBlur(55))
    image.alpha_composite(soft)

    y_mid = 314
    branch_gap = 52
    branch_h = 170
    rescue_y0 = 118
    rescue_bbox = (900, rescue_y0, 1188, rescue_y0 + branch_h)
    cascade_y0 = rescue_bbox[3] + branch_gap
    cascade_bbox = (900, cascade_y0, 1188, cascade_y0 + branch_h)

    unified_bbox = (1298, 176, 1502, 396)
    unified_cx = (unified_bbox[0] + unified_bbox[2]) / 2
    unified_cy = (unified_bbox[1] + unified_bbox[3]) / 2
    unified_r = min(unified_bbox[2] - unified_bbox[0], unified_bbox[3] - unified_bbox[1]) / 2 - 6

    rescue_cx = (rescue_bbox[0] + rescue_bbox[2]) / 2
    rescue_cy = (rescue_bbox[1] + rescue_bbox[3]) / 2
    cascade_cx = (cascade_bbox[0] + cascade_bbox[2]) / 2
    cascade_cy = (cascade_bbox[1] + cascade_bbox[3]) / 2

    rx0, ry0, rx1, ry1 = rescue_bbox
    cx0, cy0, cx1, cy1 = cascade_bbox

    # Right-edge ports: mid-body, away from header and mini-diagram band.
    rescue_exit = (rx1, ry0 + 108)
    cascade_exit = (cx1, cy0 + 108)
    rescue_enter = (rx0, rescue_cy)
    cascade_enter = (cx0, cascade_cy)
    router_exit = (705, y_mid)

    result_specs = [
        ("Pass rate", BLUE_DARK, 1570, 220),
        ("API calls", GREEN_DARK, 1570, 286),
        ("Tokens", ORANGE_DARK, 1570, 352),
    ]
    trunk_out_x = min(result_specs[0][2] - 16, WIDTH - 48)
    trunk_y = unified_cy + 36

    # Merge angles: rescue approaches the upper-left arc; cascade wraps below then up the right flank.
    orange_merge_deg = 220.0
    purple_merge_deg = 278.0
    orange_merge_end = (
        unified_cx + unified_r * math.cos(math.radians(orange_merge_deg)),
        unified_cy + unified_r * math.sin(math.radians(orange_merge_deg)),
    )
    purple_merge_end = (
        unified_cx + unified_r * math.cos(math.radians(purple_merge_deg)),
        unified_cy + unified_r * math.sin(math.radians(purple_merge_deg)),
    )

    # All thick connectors under opaque nodes so labels stay readable.
    # Draw connectors at 2x then downscale for smoother wide strokes (PIL polyline AA is weak at 1x).
    conn_scale = 2
    cw, ch = WIDTH * conn_scale, HEIGHT * conn_scale

    def cs(v: float) -> float:
        return v * conn_scale

    under_big = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    udraw = ImageDraw.Draw(under_big)
    draw_round_band(udraw, cs(445), cs(705), cs(y_mid), int(cs(44)), (84, 181, 177, 255))
    draw_ribbon(
        udraw,
        [(cs(a), cs(b)) for a, b in (router_exit, (802, rescue_cy - 18), rescue_enter)],
        int(cs(26)),
        (241, 150, 82, 255),
    )
    draw_ribbon(
        udraw,
        [(cs(a), cs(b)) for a, b in (router_exit, (802, cascade_cy + 18), cascade_enter)],
        int(cs(26)),
        (141, 118, 208, 255),
    )
    draw_polyline_ribbon(
        udraw,
        [
            (cs(a), cs(b))
            for a, b in (
                rescue_exit,
                (1245, rescue_exit[1] - 16),
                (1320, rescue_exit[1] - 8),
                orange_merge_end,
            )
        ],
        int(cs(22)),
        (241, 150, 82, 255),
        steps_per_segment=16,
    )
    draw_polyline_ribbon(
        udraw,
        [
            (cs(a), cs(b))
            for a, b in (
                cascade_exit,
                (1260, cascade_exit[1]),
                (1380, unified_cy + unified_r + 34),
                (1480, unified_cy + unified_r + 34),
                (1540, unified_cy + 34),
                (1460, unified_cy - 91),
                purple_merge_end,
            )
        ],
        int(cs(22)),
        (141, 118, 208, 255),
        steps_per_segment=14,
    )
    draw_round_band(udraw, cs(unified_cx + unified_r - 4), cs(trunk_out_x), cs(trunk_y), int(cs(26)), (84, 181, 177, 255))
    resample = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS
    under_small = under_big.resize((WIDTH, HEIGHT), resample)
    image.alpha_composite(under_small)

    task_x = 70
    task_y = 230
    for idx in range(5):
        ox = idx * 10
        oy = idx * 8
        add_shadow_rect(
            image,
            (task_x + ox, task_y + oy, task_x + ox + 106, task_y + oy + 82),
            radius=16,
            fill=(255, 255, 255, 245),
            outline=(210, 217, 226, 255),
            shadow_offset=(0, 4),
            shadow_alpha=18,
        )
        overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
        odraw = ImageDraw.Draw(overlay)
        card_icon(odraw, task_x + ox, task_y + oy, 106, 82, BLUE_DARK)
        image.alpha_composite(overlay)

    add_shadow_rect(image, (245, 220, 445, 408), radius=96, fill=(235, 246, 253, 255), outline=(194, 222, 239, 255))
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    odraw.ellipse((264, 239, 426, 389), fill=(211, 236, 250, 255), outline=(114, 181, 219, 255), width=4)
    image.alpha_composite(overlay)

    add_shadow_rect(image, (520, 226, 705, 402), radius=34, fill=(229, 249, 240, 255), outline=(176, 224, 196, 255))
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    odraw.ellipse((571, 244, 652, 384), fill=(255, 255, 255, 192), outline=(100, 188, 138, 255), width=4)
    odraw.polygon([(610, 262), (652, 314), (610, 366)], fill=(97, 183, 132, 190))
    image.alpha_composite(overlay)

    add_shadow_rect(image, rescue_bbox, radius=38, fill=(254, 239, 225, 255), outline=(244, 190, 143, 255))
    add_shadow_rect(image, cascade_bbox, radius=38, fill=(241, 236, 252, 255), outline=(196, 181, 234, 255))

    add_shadow_rect(image, unified_bbox, radius=96, fill=(235, 246, 253, 255), outline=(194, 222, 239, 255))
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    odraw.ellipse(
        (unified_cx - unified_r, unified_cy - unified_r, unified_cx + unified_r, unified_cy + unified_r),
        fill=(211, 236, 250, 255),
        outline=(114, 181, 219, 255),
        width=4,
    )
    image.alpha_composite(overlay)

    for _idx, (_label, _color, x0, y0) in enumerate(result_specs):
        add_shadow_rect(
            image,
            (x0, y0, x0 + 138, y0 + 66),
            radius=16,
            fill=(255, 255, 255, 245),
            outline=(219, 225, 232, 255),
            shadow_offset=(0, 4),
            shadow_alpha=16,
        )

    # Mini-diagrams sit above underlay connectors.
    mini_left = rx0 + 22
    mini_top = rescue_cy - 34
    draw.rounded_rectangle((mini_left, mini_top, mini_left + 92, mini_top + 56), radius=16, fill=(255, 248, 243, 255), outline=(234, 174, 124, 255), width=2)
    draw.ellipse((mini_left + 16, mini_top + 16, mini_left + 40, mini_top + 40), outline=ORANGE_DARK, width=4)
    draw.line((mini_left + 28, mini_top + 40, mini_left + 28, mini_top + 48), fill=ORANGE_DARK, width=4)
    draw.line((mini_left + 52, mini_top + 14, mini_left + 72, mini_top + 14), fill=ORANGE_DARK, width=4)
    draw.line((mini_left + 52, mini_top + 28, mini_left + 72, mini_top + 28), fill=ORANGE_DARK, width=4)
    draw.line((mini_left + 52, mini_top + 42, mini_left + 66, mini_top + 42), fill=ORANGE_DARK, width=4)

    mini_right = rx0 + 210
    draw.line((mini_left + 102, mini_top + 28, mini_right, mini_top + 28), fill=ORANGE_DARK, width=4)
    draw.polygon([(mini_right + 10, mini_top + 28), (mini_right, mini_top + 20), (mini_right, mini_top + 36)], fill=ORANGE_DARK)
    draw.rounded_rectangle((mini_right + 18, mini_top + 6, mini_right + 92, mini_top + 52), radius=16, fill=(255, 255, 255, 255), outline=(229, 183, 144, 255), width=2)
    draw.line((mini_right + 32, mini_top + 22, mini_right + 78, mini_top + 22), fill=(179, 159, 142, 255), width=3)
    draw.line((mini_right + 32, mini_top + 34, mini_right + 78, mini_top + 34), fill=(179, 159, 142, 255), width=3)
    draw.line((mini_right + 32, mini_top + 46, mini_right + 64, mini_top + 46), fill=(222, 132, 63, 255), width=4)

    cloud_left = cx0 + 34
    cloud_top = cascade_cy - 34
    for col, row in [(cloud_left, cloud_top + 34), (cloud_left + 32, cloud_top + 14), (cloud_left + 54, cloud_top + 38), (cloud_left + 86, cloud_top + 18), (cloud_left + 118, cloud_top + 34), (cloud_left + 140, cloud_top + 14)]:
        draw.ellipse((col, row, col + 16, row + 16), fill=(205, 190, 243, 255), outline=PURPLE_DARK, width=2)
    funnel_x = cx0 + 210
    draw.polygon([(funnel_x, cascade_cy), (funnel_x + 30, cascade_cy - 18), (funnel_x + 30, cascade_cy + 18)], fill=(136, 118, 205, 225))
    for idx in range(2):
        x0 = funnel_x + 48 + idx * 18
        y0 = cascade_cy - 40 + idx * 16
        draw.rounded_rectangle((x0, y0, x0 + 54, y0 + 72), radius=12, fill=(255, 255, 255, 255), outline=(197, 185, 227, 255), width=2)
        for i in range(3):
            yy = y0 + 16 + i * 14
            draw.line((x0 + 10, yy, x0 + 38, yy), fill=(170, 158, 204, 255), width=3)

    text_center(draw, (150, 365), "Task Stream", FONT_HEAD)
    text_center(draw, (150, 398), "prompts, tests, signatures", FONT_SMALL, fill=MUTED)
    multiline_center(draw, (345, 306), ["Base Solve"], FONT_BODY)
    text_center(draw, (345, 340), "low-cost first attempt", FONT_SMALL, fill=MUTED)
    multiline_center(draw, (610, 314), ["Adaptive", "Routing"], FONT_BODY, fill=TEXT, spacing=4)

    multiline_center(draw, (rescue_cx, rescue_bbox[1] + 52), ["Rescue"], FONT_HEAD)
    text_center(draw, (rescue_cx, rescue_bbox[1] + 84), "failure  ->  repair cue", FONT_SMALL, fill=MUTED)
    text_center(draw, (rescue_cx, ry1 - 22), "focused local repair", FONT_SMALL, fill=ORANGE_DARK)

    multiline_center(draw, (cascade_cx, cascade_bbox[1] + 52), ["Cascade"], FONT_HEAD)

    multiline_center(draw, (unified_cx, unified_cy - 18), ["Unified Eval"], FONT_HEAD)
    text_center(draw, (unified_cx, unified_cy + 18), "test and select", FONT_SMALL, fill=MUTED)

    for label, color, x0, y0 in result_specs:
        draw.ellipse((x0 + 16, y0 + 22, x0 + 34, y0 + 40), fill=color)
        draw.text((x0 + 48, y0 + 18), label, font=FONT_SMALL, fill=TEXT)

    draw_arrow(draw, (216, y_mid), (245, y_mid))

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
