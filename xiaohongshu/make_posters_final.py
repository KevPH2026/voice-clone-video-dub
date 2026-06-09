#!/usr/bin/env python3
"""Final XHS cover posters — 2 versions, both fixed.

V3-Final: minimalist × huge type, aurora gradient, three-color type.
V2-Final: hero + code block, fix all the tofu (□) glyphs.
"""
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
from pathlib import Path

W, H = 1242, 1660
OUT_DIR = Path("/Users/k/Desktop/vcvd-project/xiaohongshu")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# macOS system fonts
FONT_HEAVY = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT_REG = "/System/Library/Fonts/Supplemental/Arial.ttf"
FONT_CN_HEAVY = "/System/Library/Fonts/STHeiti Medium.ttc"
FONT_CN_LIGHT = "/System/Library/Fonts/STHeiti Light.ttc"
FONT_CODE = "/System/Library/Fonts/Supplemental/Courier New Bold.ttf"

# Colors
AURORA_PURPLE = (138, 79, 255)
AURORA_TEAL = (64, 224, 208)
AURORA_PINK = (255, 105, 180)
GOLD = (212, 175, 55)


def make_gradient_bg(w, h, colors):
    img = Image.new("RGBA", (w, h), colors[0])
    pixels = img.load()
    for y in range(h):
        t = y / max(1, h - 1)
        r = int(colors[0][0] * (1 - t) + colors[1][0] * t)
        g = int(colors[0][1] * (1 - t) + colors[1][1] * t)
        b = int(colors[0][2] * (1 - t) + colors[1][2] * t)
        for x in range(w):
            pixels[x, y] = (r, g, b, 255)
    return img


def add_noise_stars(img, count):
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
    return Image.alpha_composite(img, overlay)


def add_aurora_blobs(img, blobs):
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    for x, y, r, color, alpha in blobs:
        blob = Image.new("RGBA", (r * 2, r * 2), (0, 0, 0, 0))
        d = ImageDraw.Draw(blob)
        d.ellipse([0, 0, r * 2, r * 2], fill=color + (alpha,))
        blob = blob.filter(ImageFilter.GaussianBlur(r // 2))
        overlay.paste(blob, (x - r, y - r), blob)
    return Image.alpha_composite(img, overlay)


def vignette(img, strength=0.4):
    w, h = img.size
    grad = Image.new("L", (w, h), 255)
    gd = ImageDraw.Draw(grad)
    cx, cy = w // 2, h // 2
    for r in range(min(w, h) // 2, 0, -1):
        t = r / (min(w, h) // 2)
        v = int(255 * (1 - strength * (1 - t) ** 2))
        gd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=v)
    dark = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    return Image.composite(img, dark, grad)


def make_poster_v3_final():
    """Minimalist × huge type. Three-color type. Bg = deep black with
    a single aurora purple bloom. No emojis (text-only)."""
    bg = make_gradient_bg(W, H, [(0, 0, 0, 255), (15, 12, 28, 255)])
    bg = add_aurora_blobs(bg, [
        (W // 2, 100, 800, AURORA_PURPLE, 50),
        (W // 2, H // 2, 500, AURORA_TEAL, 30),
    ])
    bg = add_noise_stars(bg, count=50)
    bg = vignette(bg, strength=0.55)

    canvas = bg.convert("RGBA")
    draw = ImageDraw.Draw(canvas)

    # Top-left tag
    f_tag = ImageFont.truetype(FONT_CN_LIGHT, 26)
    draw.text((80, 60), "kev-youtube-video-clone-translate  ·  开源工具", font=f_tag, fill=(180, 180, 200, 200))
    f_proj = ImageFont.truetype(FONT_HEAVY, 32)
    draw.text((80, 105), "kev-youtube-video-clone-translate", font=f_proj,
              fill=(180, 180, 200, 200))

    # Thin separator
    draw.line([(80, 165), (W - 80, 165)], fill=(60, 70, 100, 180), width=1)

    # The huge statement (3 lines, three colors)
    f_main = ImageFont.truetype(FONT_CN_HEAVY, 124)
    draw.text((W // 2, 320), "把英文 YouTube", font=f_main, fill=(245, 245, 250, 255), anchor="mm")
    f_main2 = ImageFont.truetype(FONT_CN_HEAVY, 124)
    draw.text((W // 2, 460), "变成中文", font=f_main2, fill=AURORA_PURPLE, anchor="mm")
    f_main3 = ImageFont.truetype(FONT_CN_HEAVY, 124)
    draw.text((W // 2, 600), "用她自己的声音", font=f_main3, fill=AURORA_TEAL, anchor="mm")

    # Sub
    f_sub = ImageFont.truetype(FONT_CN_LIGHT, 36)
    draw.text((W // 2, 720), "— 不是配音演员，AI 克隆 —",
              font=f_sub, fill=(200, 210, 230, 230), anchor="mm")

    # Stats line — replace the broken 138/0/12m/93MB with elegant spaced dots
    f_stat = ImageFont.truetype(FONT_CN_LIGHT, 28)
    stats = "138 段字幕  ·  0 次失败  ·  12 分钟  ·  93 MB 成片"
    draw.text((W // 2, 790), stats, font=f_stat, fill=(160, 175, 200, 220), anchor="mm")

    # Hero thumbnail — placed above bottom CTA, not under it
    thumb = Image.open("/Users/k/Desktop/vcvd-project/after_frame.png")
    thumb = ImageOps.fit(thumb, (1080, 580), method=Image.LANCZOS)
    bordered = Image.new("RGBA", (thumb.size[0] + 6, thumb.size[1] + 6),
                          AURORA_TEAL + (200,))
    bordered.paste(thumb, (3, 3))
    canvas.paste(bordered, ((W - bordered.size[0]) // 2, 850), bordered)

    # "↓ 在线 demo ↓" tag under thumb
    f_url = ImageFont.truetype(FONT_HEAVY, 28)
    draw.text((W // 2, 1490), "vcvd-project.vercel.app/demo", font=f_url,
              fill=AURORA_PURPLE, anchor="mm")
    f_gh = ImageFont.truetype(FONT_REG, 22)
    draw.text((W // 2, 1530), "GitHub:  KevPH2026 / kev-youtube-video-clone-translate",
              font=f_gh, fill=(150, 160, 180, 200), anchor="mm")

    # bottom decorative line
    draw.line([(W // 2 - 30, 1585), (W // 2 + 30, 1585)], fill=AURORA_TEAL, width=2)
    f_foot = ImageFont.truetype(FONT_CN_LIGHT, 22)
    draw.text((W // 2, 1620), "100% 本地运行  ·  XTTS v2 跨语种克隆  ·  MIT",
              font=f_foot, fill=(150, 160, 180, 200), anchor="mm")

    out = OUT_DIR / "poster_v3_final.png"
    canvas.convert("RGB").save(out, "PNG", quality=95)
    print(f"saved {out}")


def make_poster_v2_final():
    """Hero + code block. No emojis, all text. Fixed glyphs."""
    bg = make_gradient_bg(W, H, [(5, 8, 18, 255), (10, 6, 24, 255)])
    bg = add_aurora_blobs(bg, [
        (W // 2, 200, 500, AURORA_PURPLE, 100),
        (W // 4, 700, 400, AURORA_TEAL, 80),
    ])
    bg = add_noise_stars(bg, count=80)
    bg = vignette(bg, strength=0.45)

    canvas = bg.convert("RGBA")
    draw = ImageDraw.Draw(canvas)

    # Hero: a big "catwu clone" frame in upper half
    hero_box = Image.open("/Users/k/Desktop/vcvd-project/after_frame.png")
    hero_box = ImageOps.fit(hero_box, (1100, 600), method=Image.LANCZOS)
    bordered = Image.new("RGBA", (hero_box.size[0] + 8, hero_box.size[1] + 8),
                          AURORA_PURPLE + (255,))
    bordered.paste(hero_box, (4, 4))
    canvas.paste(bordered, ((W - bordered.size[0]) // 2, 80), bordered)

    # Tag
    f_over = ImageFont.truetype(FONT_CN_HEAVY, 38)
    draw.text((W // 2, 720), "↓ 同一段视频  ↓", font=f_over,
              fill=(255, 255, 255, 240), anchor="mm")

    # Big punchline
    f_punch = ImageFont.truetype(FONT_CN_HEAVY, 80)
    draw.text((W // 2, 830), "她的声音说中文", font=f_punch, fill=(255, 255, 255, 255), anchor="mm")
    f_punch_sub = ImageFont.truetype(FONT_CN_HEAVY, 56)
    draw.text((W // 2, 925), "不是配音演员  ·  是 AI 克隆", font=f_punch_sub,
              fill=AURORA_TEAL, anchor="mm")

    # Code-style info box
    code_y = 1040
    code_box = Image.new("RGBA", (W - 200, 320), (10, 12, 22, 235))
    cd = ImageDraw.Draw(code_box)
    for i in range(2):
        cd.rectangle([i, i, code_box.size[0] - 1 - i, code_box.size[1] - 1 - i],
                      outline=AURORA_PURPLE + (180 - i * 80,), width=1)
    cd.rectangle([0, 0, code_box.size[0], 40], fill=AURORA_PURPLE + (60,))
    f_tt = ImageFont.truetype(FONT_CN_LIGHT, 22)
    cd.text((24, 20), "v0.1.0  /  开源  /  MIT", font=f_tt, fill=(220, 210, 255, 240))

    f_code = ImageFont.truetype(FONT_CODE, 24)
    f_cn = ImageFont.truetype(FONT_CN_LIGHT, 22)
    cd.text((24, 90), "$ git clone", font=f_code, fill=(150, 200, 255, 240))
    cd.text((24 + 11 * 16, 90), "  KevPH2026/kev-youtube-video-clone-translate",
            font=f_cn, fill=(220, 220, 240, 240))
    cd.text((24, 145), "$ bash", font=f_code, fill=(150, 200, 255, 240))
    cd.text((24 + 9 * 16, 145), "  scripts/install-deps.sh", font=f_cn,
            fill=(220, 220, 240, 240))
    cd.text((24, 200), "$ claude", font=f_code, fill=(150, 200, 255, 240))
    cd.text((24 + 10 * 16, 200), "  给个 YouTube 链接  30 分钟成片",
            font=f_cn, fill=AURORA_TEAL)
    canvas.paste(code_box, (100, code_y), code_box)

    # Bottom CTA
    f_cta = ImageFont.truetype(FONT_CN_HEAVY, 30)
    f_url = ImageFont.truetype(FONT_HEAVY, 26)
    cta_y = H - 110
    draw.text((W // 2, cta_y), "在线 Demo  ·  100% 本地运行", font=f_cta,
              fill=(255, 255, 255, 250), anchor="mm")
    draw.text((W // 2, cta_y + 50), "vcvd-project.vercel.app/demo", font=f_url,
              fill=AURORA_PURPLE, anchor="mm")

    out = OUT_DIR / "poster_v2_final.png"
    canvas.convert("RGB").save(out, "PNG", quality=95)
    print(f"saved {out}")


if __name__ == "__main__":
    make_poster_v3_final()
    make_poster_v2_final()
    print("done")
