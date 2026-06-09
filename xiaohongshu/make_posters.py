#!/usr/bin/env python3
"""Generate 3 candidate Xiaohongshu cover posters for
kev-youtube-video-clone-translate. All 1242x1660 (3:4 standard).
"""
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
from pathlib import Path

# Standard XHS cover size
W, H = 1242, 1660
OUT_DIR = Path("/Users/k/Desktop/vcvd-project/xiaohongshu")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# macOS system fonts
FONT_HEAVY = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
FONT_REG = "/System/Library/Fonts/Supplemental/Arial.ttf"
# 中文用 STHeiti (macOS 自带, Pixel 精确中文渲染, 免费)
FONT_CN_HEAVY = "/System/Library/Fonts/STHeiti Medium.ttc"  # 中等粗细 = 粗
FONT_CN_LIGHT = "/System/Library/Fonts/STHeiti Light.ttc"   # 细
FONT_CN_BOLD = "/System/Library/Fonts/STHeiti Medium.ttc"   # 替代 Bold

PINGFANG = "/System/Library/AssetsV2/com_apple_MobileAsset_Font8/86ba2c91f017a3749571a82f2c6d890ac7ffb2fb.asset/AssetData/PingFang.ttc"

# Colors
WHITE = (255, 255, 255, 255)
BG_DARK = (12, 14, 22, 255)
AURORA_PURPLE = (138, 79, 255)
AURORA_TEAL = (64, 224, 208)
AURORA_PINK = (255, 105, 180)
GOLD = (212, 175, 55)


def make_gradient_bg(w, h, colors, vertical=True):
    """Linear gradient between two colors."""
    img = Image.new("RGBA", (w, h), colors[0])
    pixels = img.load()
    if vertical:
        for y in range(h):
            t = y / max(1, h - 1)
            r = int(colors[0][0] * (1 - t) + colors[1][0] * t)
            g = int(colors[0][1] * (1 - t) + colors[1][1] * t)
            b = int(colors[0][2] * (1 - t) + colors[1][2] * t)
            for x in range(w):
                pixels[x, y] = (r, g, b, 255)
    return img


def add_noise_stars(img, count=120):
    """Add tiny stars on top of a gradient bg."""
    from random import randint, seed
    seed(42)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for _ in range(count):
        x = randint(0, img.size[0] - 1)
        y = randint(0, img.size[1] - 1)
        r = randint(1, 2)
        alpha = randint(80, 220)
        draw.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, alpha))
    img = Image.alpha_composite(img, overlay)
    return img


def add_aurora_blobs(img, blobs):
    """Add soft, blurry aurora-like color blobs."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    for x, y, r, color, alpha in blobs:
        blob = Image.new("RGBA", (r * 2, r * 2), (0, 0, 0, 0))
        d = ImageDraw.Draw(blob)
        d.ellipse([0, 0, r * 2, r * 2], fill=color + (alpha,))
        blob = blob.filter(ImageFilter.GaussianBlur(r // 2))
        overlay.paste(blob, (x - r, y - r), blob)
    img = Image.alpha_composite(img, overlay)
    return img


def vignette(img, strength=0.4):
    """Add subtle dark vignette at corners."""
    w, h = img.size
    mask = Image.new("L", (w, h), 255)
    d = ImageDraw.Draw(mask)
    # Draw radial fade by layers
    steps = 60
    max_offset = int(strength * min(w, h) / 2)
    for i in range(steps):
        offset = int(i / steps * max_offset)
        v = int(255 - (255 * (offset / max_offset) ** 2))
        # Draw a "ring" — actually simpler: just darken the whole image with a radial gradient
    # Use a smoother approach with radial gradient
    grad = Image.new("L", (w, h), 255)
    gd = ImageDraw.Draw(grad)
    cx, cy = w // 2, h // 2
    for r in range(min(w, h) // 2, 0, -1):
        t = r / (min(w, h) // 2)
        v = int(255 * (1 - strength * (1 - t) ** 2))
        gd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=v)
    dark = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    img = Image.composite(img, dark, grad)
    return img


def load_font(path, size):
    return ImageFont.truetype(path, size)


def make_poster_v1():
    """A: Deep dark with aurora gradient + bold title at top, 2 video
    thumbs split side-by-side, accent line at bottom."""
    # BG: deep navy → black, with purple/teal aurora blobs
    bg = make_gradient_bg(W, H, [(8, 10, 24, 255), (2, 4, 12, 255)])
    bg = add_aurora_blobs(bg, [
        (W // 4, H // 4, 600, AURORA_PURPLE, 90),
        (3 * W // 4, H // 2, 500, AURORA_TEAL, 70),
        (W // 2, 3 * H // 4, 700, AURORA_PINK, 60),
    ])
    bg = add_noise_stars(bg, count=180)
    bg = vignette(bg, strength=0.35)

    canvas = bg.convert("RGBA")
    draw = ImageDraw.Draw(canvas)

    # Top tag
    f_tag = load_font(FONT_CN_BOLD, 38)
    draw.text((W // 2, 80), "开 源 项 目", font=f_tag, fill=(255, 255, 255, 230),
              anchor="mm", stroke_width=1, stroke_fill=(138, 79, 255, 200))
    # Project name (English, dramatic)
    f_proj = load_font(FONT_HEAVY, 78)
    draw.text((W // 2, 175), "kev-youtube-", font=f_proj, fill=WHITE, anchor="mm")
    draw.text((W // 2, 245), "video-clone-translate", font=f_proj, fill=WHITE, anchor="mm")

    # Subtitle
    f_sub = load_font(FONT_CN_LIGHT, 36)
    draw.text((W // 2, 340), "把 YouTube 视频变成中文克隆配音", font=f_sub,
              fill=(200, 210, 230, 240), anchor="mm")

    # Divider
    draw.line([(W // 4, 410), (3 * W // 4, 410)], fill=(138, 79, 255, 160), width=2)

    # Before / After video frames
    f_label = load_font(FONT_CN_BOLD, 28)
    f_small = load_font(FONT_CN_LIGHT, 22)
    box_y = 480
    box_h = 720
    box_w = 540
    gap = 40
    bx_left = (W - box_w * 2 - gap) // 2
    bx_right = bx_left + box_w + gap

    # Load thumbs
    before_thumb = Image.open("/Users/k/Desktop/vcvd-project/before_frame.png")
    after_thumb = Image.open("/Users/k/Desktop/vcvd-project/after_frame.png")
    before_thumb = ImageOps.fit(before_thumb, (box_w, box_h), method=Image.LANCZOS)
    after_thumb = ImageOps.fit(after_thumb, (box_w, box_h), method=Image.LANCZOS)

    # Border accent on each
    def with_border(img, color):
        bordered = Image.new("RGBA", (img.size[0] + 6, img.size[1] + 6), color)
        bordered.paste(img, (3, 3))
        return bordered

    before_thumb = with_border(before_thumb, (120, 130, 150, 255))
    after_thumb = with_border(after_thumb, (64, 224, 208, 255))

    canvas.paste(before_thumb, (bx_left - 3, box_y - 3), before_thumb)
    canvas.paste(after_thumb, (bx_right - 3, box_y - 3), after_thumb)

    draw.text((bx_left + box_w // 2, box_y + box_h + 35), "原声 · 英文",
              font=f_label, fill=(200, 210, 230, 240), anchor="mm")
    draw.text((bx_right + box_w // 2, box_y + box_h + 35), "克隆 · 中文 + 字幕",
              font=f_label, fill=(64, 224, 208, 255), anchor="mm")
    draw.text((bx_left + box_w // 2, box_y + box_h + 75), "原说话人音色",
              font=f_small, fill=(150, 160, 180, 220), anchor="mm")
    draw.text((bx_right + box_w // 2, box_y + box_h + 75), "XTTS v2 跨语种克隆",
              font=f_small, fill=(150, 220, 210, 220), anchor="mm")

    # Arrow between
    f_arrow = load_font(FONT_HEAVY, 80)
    arrow_x = (bx_left + box_w + bx_right) // 2
    arrow_y = box_y + box_h // 2
    draw.text((arrow_x, arrow_y), "→", font=f_arrow,
              fill=(255, 255, 255, 255), anchor="mm",
              stroke_width=3, stroke_fill=(138, 79, 255, 255))

    # Numbers bar
    num_y = box_y + box_h + 200
    draw.line([(W // 4, num_y - 30), (3 * W // 4, num_y - 30)], fill=(60, 70, 100, 180), width=1)
    f_num = load_font(FONT_HEAVY, 56)
    f_unit = load_font(FONT_CN_LIGHT, 22)
    items = [("138", "段字幕"), ("0", "次失败"), ("12m", "全程"), ("93MB", "成片")]
    for i, (n, u) in enumerate(items):
        x = W // 4 + i * (W // 2 // 4)
        draw.text((x, num_y), n, font=f_num, fill=(255, 255, 255, 255), anchor="mm")
        draw.text((x, num_y + 50), u, font=f_unit, fill=(150, 160, 180, 220), anchor="mm")

    # Bottom CTA
    f_cta = load_font(FONT_CN_BOLD, 30)
    f_url = load_font(FONT_HEAVY, 22)
    cta_y = H - 180
    draw.text((W // 2, cta_y), "🌐  在线 Demo  ·  100% 本地运行",
              font=f_cta, fill=(255, 255, 255, 240), anchor="mm")
    draw.text((W // 2, cta_y + 50), "vcvd-project.vercel.app/demo",
              font=f_url, fill=(138, 79, 255, 240), anchor="mm")
    draw.text((W // 2, cta_y + 90), "GitHub: KevPH2026/kev-youtube-video-clone-translate",
              font=f_url, fill=(150, 160, 180, 200), anchor="mm")

    out = OUT_DIR / "poster_v1.png"
    canvas.convert("RGB").save(out, "PNG", quality=95)
    print(f"saved {out}")


def make_poster_v2():
    """B: Cinematic dark, single big catwu-clone frame as hero, code-style
    terminal aesthetic overlay, smaller dense text block at bottom."""
    bg = make_gradient_bg(W, H, [(5, 8, 18, 255), (10, 6, 24, 255)])
    bg = add_aurora_blobs(bg, [
        (W // 2, 200, 500, (80, 30, 180), 100),
        (W // 4, 700, 400, (40, 180, 200), 80),
    ])
    bg = add_noise_stars(bg, count=80)
    bg = vignette(bg, strength=0.45)

    canvas = bg.convert("RGBA")
    draw = ImageDraw.Draw(canvas)

    # Hero: a big "catwu clone" frame in upper half
    hero_box = Image.open("/Users/k/Desktop/vcvd-project/after_frame.png")
    hero_box = ImageOps.fit(hero_box, (1100, 600), method=Image.LANCZOS)
    # Subtle neon border
    bordered = Image.new("RGBA", (hero_box.size[0] + 8, hero_box.size[1] + 8),
                          (138, 79, 255, 255))
    bordered.paste(hero_box, (4, 4))
    canvas.paste(bordered, ((W - bordered.size[0]) // 2, 80), bordered)

    # "Look at this" overlay
    f_over = load_font(FONT_CN_BOLD, 38)
    draw.text((W // 2, 720), "↓ 这是同一段视频 ↓", font=f_over,
              fill=(255, 255, 255, 240), anchor="mm")

    # Big punchline
    f_punch = load_font(FONT_CN_HEAVY, 80)
    draw.text((W // 2, 830), "她的声音说中文", font=f_punch, fill=WHITE, anchor="mm")
    f_punch_sub = load_font(FONT_CN_BOLD, 56)
    draw.text((W // 2, 925), "不是配音演员，是 AI 克隆", font=f_punch_sub,
              fill=(64, 224, 208, 255), anchor="mm")

    # Code-style info box
    code_y = 1040
    code_box = Image.new("RGBA", (W - 200, 280), (10, 12, 22, 220))
    cd = ImageDraw.Draw(code_box)
    # Border
    for i in range(2):
        cd.rectangle([i, i, code_box.size[0] - 1 - i, code_box.size[1] - 1 - i],
                      outline=(138, 79, 255, 180 - i * 80), width=1)
    # Title bar
    cd.rectangle([0, 0, code_box.size[0], 36], fill=(138, 79, 255, 60))
    f_tt = ImageFont.truetype(FONT_CN_BOLD, 22)
    cd.text((20, 18), "✦ 0.1.0 / 开源 / MIT", font=f_tt, fill=(220, 210, 255, 240))
    # Body code-style lines
    f_code = ImageFont.truetype("/System/Library/Fonts/Supplemental/Courier New Bold.ttf", 26)
    f_cn = load_font(FONT_CN_LIGHT, 22)
    lines = [
        ("$ git clone", " github.com/KevPH2026/kev-youtube-video-clone-translate", (150, 200, 255, 240), (220, 220, 240, 240)),
        ("$ bash", " scripts/install-deps.sh", (150, 200, 255, 240), (220, 220, 240, 240)),
        ("$ claude", " — give it a YouTube link → done in 30 min", (150, 200, 255, 240), (64, 224, 208, 240)),
    ]
    for i, (cmd, rest, c1, c2) in enumerate(lines):
        y = 80 + i * 50
        cd.text((24, y), cmd, font=f_code, fill=c1)
        cd.text((24 + cmd.__len__() * 16, y), rest, font=f_cn, fill=c2)
    canvas.paste(code_box, (100, code_y), code_box)

    # Bottom CTA
    f_cta = load_font(FONT_CN_BOLD, 30)
    f_url = load_font(FONT_HEAVY, 22)
    cta_y = H - 100
    draw.text((W // 2, cta_y), "🌐  vcvd-project.vercel.app/demo",
              font=f_cta, fill=(255, 255, 255, 250), anchor="mm")

    out = OUT_DIR / "poster_v2.png"
    canvas.convert("RGB").save(out, "PNG", quality=95)
    print(f"saved {out}")


def make_poster_v3():
    """C: Minimalist — pure black bg, single line of huge type, single
    thumbnail. Stays in the user's 'no low, premium' aesthetic."""
    bg = make_gradient_bg(W, H, [(0, 0, 0, 255), (15, 12, 28, 255)])
    bg = add_aurora_blobs(bg, [
        (W // 2, 0, 700, (60, 20, 140), 60),
    ])
    bg = add_noise_stars(bg, count=40)
    bg = vignette(bg, strength=0.55)

    canvas = bg.convert("RGBA")
    draw = ImageDraw.Draw(canvas)

    # Top-left tag
    f_tag = load_font(FONT_CN_BOLD, 26)
    draw.text((80, 90), "kev-youtube-video-clone-translate  ·  开源工具", font=f_tag, fill=(180, 180, 200, 200))
    # Project name (small, top)
    f_proj = load_font(FONT_HEAVY, 36)
    draw.text((80, 145), "kev-youtube-video-clone-translate", font=f_proj, fill=(180, 180, 200, 200))

    # The huge statement
    f_main = load_font(FONT_CN_HEAVY, 130)
    draw.text((W // 2, 480), "把英文 YouTube", font=f_main, fill=WHITE, anchor="mm")
    f_main2 = load_font(FONT_CN_HEAVY, 130)
    draw.text((W // 2, 610), "变成中文", font=f_main2, fill=(138, 79, 255, 255), anchor="mm")
    f_main3 = load_font(FONT_CN_HEAVY, 130)
    draw.text((W // 2, 740), "用她自己的声音", font=f_main3, fill=(64, 224, 208, 255), anchor="mm")

    # Sub: small italic
    f_sub = load_font(FONT_CN_LIGHT, 36)
    draw.text((W // 2, 870), "— 不是配音演员，AI 克隆 —",
              font=f_sub, fill=(200, 210, 230, 230), anchor="mm")

    # A single catwu-clone thumb at bottom
    thumb = Image.open("/Users/k/Desktop/vcvd-project/after_frame.png")
    thumb = ImageOps.fit(thumb, (1080, 600), method=Image.LANCZOS)
    bordered = Image.new("RGBA", (thumb.size[0] + 6, thumb.size[1] + 6),
                          (64, 224, 208, 200))
    bordered.paste(thumb, (3, 3))
    canvas.paste(bordered, ((W - bordered.size[0]) // 2, 980), bordered)

    # Bottom info
    f_url = load_font(FONT_HEAVY, 26)
    cta_y = H - 80
    draw.text((W // 2, cta_y), "vcvd-project.vercel.app/demo",
              font=f_url, fill=(138, 79, 255, 230), anchor="mm")

    out = OUT_DIR / "poster_v3.png"
    canvas.convert("RGB").save(out, "PNG", quality=95)
    print(f"saved {out}")


if __name__ == "__main__":
    make_poster_v1()
    make_poster_v2()
    make_poster_v3()
    print("all done")
