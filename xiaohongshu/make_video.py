#!/usr/bin/env python3
"""Build a 9:16 vertical XHS video. Each frame is composed in PIL:
- Top label band: aurora gradient bg + small "BEFORE" / "AFTER" tag
- Middle: the video frame
- Bottom label band: aurora gradient bg + subtitle
Then ffmpeg takes a stream of frames (image2) and a stream of audio and
muxes them.

The PIL approach is much more controllable than ffmpeg filter graphs.
"""
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from random import randint, seed

# 9:16 vertical
W, H = 1080, 1920

ROOT = Path("/Users/k/Desktop/vcvd-project")
OUT = ROOT / "xiaohongshu" / "xhs_video.mp4"
FRAMES_DIR = ROOT / "xiaohongshu" / "frames"
FRAMES_DIR.mkdir(parents=True, exist_ok=True)

FONT_HEAVY = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
FONT_CN_HEAVY = "/System/Library/Fonts/STHeiti Medium.ttc"
FONT_CN_LIGHT = "/System/Library/Fonts/STHeiti Light.ttc"
PURPLE = (138, 79, 255)
TEAL = (64, 224, 208)
WHITE = (245, 245, 250)
SOFT = (200, 210, 230)
DIM = (160, 175, 200)


def make_aurora_bg(w, h, blobs):
    """Vertical gradient + aurora blobs + stars."""
    img = Image.new("RGBA", (w, h), (8, 10, 24, 255))
    px = img.load()
    for y in range(h):
        t = y / h
        r = int(8 * (1 - t) + 2 * t)
        g = int(10 * (1 - t) + 4 * t)
        b = int(24 * (1 - t) + 12 * t)
        for x in range(w):
            px[x, y] = (r, g, b, 255)
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for x, y, r, color, alpha in blobs:
        blob = Image.new("RGBA", (r * 2, r * 2), (0, 0, 0, 0))
        bd = ImageDraw.Draw(blob)
        bd.ellipse([0, 0, r * 2, r * 2], fill=color + (alpha,))
        blob = blob.filter(ImageFilter.GaussianBlur(r // 2))
        overlay.paste(blob, (x - r, y - r), blob)
    img = Image.alpha_composite(img, overlay)
    seed(42)
    sd = ImageDraw.Draw(img)
    for _ in range(80):
        x, y = randint(0, w - 1), randint(0, h - 1)
        r = randint(1, 2)
        a = randint(80, 220)
        sd.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, a))
    return img


def make_title_card(duration, fps=30):
    """4-second title card. 1080x1920 with the 3-line huge type."""
    n_frames = int(duration * fps)
    for i in range(n_frames):
        img = make_aurora_bg(W, H, [
            (W // 4, H // 4, 700, PURPLE, 80),
            (3 * W // 4, H // 2, 500, TEAL, 50),
        ])
        draw = ImageDraw.Draw(img)
        f_main = ImageFont.truetype(FONT_CN_HEAVY, 124)
        f_tag = ImageFont.truetype(FONT_CN_LIGHT, 28)
        f_sub = ImageFont.truetype(FONT_CN_LIGHT, 36)
        f_stat = ImageFont.truetype(FONT_CN_LIGHT, 28)

        # Tag at top
        draw.text((W // 2, 110), "kev-youtube-video-clone-translate  ·  开源工具", font=f_tag,
                  fill=(180, 180, 200, 200), anchor="mm")
        draw.line([(W // 4, 150), (3 * W // 4, 150)],
                  fill=(60, 70, 100, 180), width=1)

        # 3 lines of huge type, vertical center
        draw.text((W // 2, H // 2 - 130), "把英文 YouTube", font=f_main,
                  fill=(245, 245, 250, 255), anchor="mm")
        draw.text((W // 2, H // 2 + 10), "变成中文", font=f_main,
                  fill=PURPLE, anchor="mm")
        draw.text((W // 2, H // 2 + 150), "用她自己的声音", font=f_main,
                  fill=TEAL, anchor="mm")
        draw.text((W // 2, H // 2 + 280), "— 不是配音演员，AI 克隆 —", font=f_sub,
                  fill=SOFT, anchor="mm")
        # Stats
        draw.text((W // 2, H // 2 + 360), "138 段字幕  ·  0 失败  ·  12m 全程  ·  93MB",
                  font=f_stat, fill=DIM, anchor="mm")
        # Bottom
        f_url = ImageFont.truetype(FONT_HEAVY, 32)
        draw.text((W // 2, H - 100), "vcvd-project.vercel.app/demo", font=f_url,
                  fill=PURPLE, anchor="mm")

        # Save
        frame_path = FRAMES_DIR / f"title_{i:04d}.png"
        img.convert("RGB").save(frame_path, "PNG", quality=85)


def extract_frames(video_path, n_frames, fps=30):
    """Extract n_frames from video_path via ffmpeg, return list of
    PIL Image (RGB)."""
    # Use a temp dir
    import tempfile
    tmp = Path(tempfile.mkdtemp(prefix="xhs_vid_"))
    pattern = tmp / "f_%04d.png"
    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-vf", f"fps={fps}",
        "-frames:v", str(n_frames),
        str(pattern),
    ]
    print("$ ffmpeg extract:", video_path)
    subprocess.run(cmd, check=True, capture_output=True)
    frames = []
    for i in range(1, n_frames + 1):
        p = tmp / f"f_{i:04d}.png"
        if not p.exists():
            break
        frames.append(Image.open(p).convert("RGB"))
    return frames, tmp


def make_video_segment(video_path, duration, top_big, top_sub, bottom_big,
                       bottom_sub, accent_color, fps=30):
    """Make a vertical 9:16 video segment. Top: top_big + top_sub.
    Middle: video frame. Bottom: bottom_big + bottom_sub."""
    n_frames = int(duration * fps)
    src_frames, tmp = extract_frames(video_path, n_frames, fps=fps)
    if len(src_frames) < n_frames:
        # Loop
        while len(src_frames) < n_frames:
            src_frames = src_frames + src_frames
        src_frames = src_frames[:n_frames]
    import shutil
    shutil.rmtree(tmp, ignore_errors=True)

    for i in range(n_frames):
        img = make_aurora_bg(W, H, [
            (W // 2, 100, 600, PURPLE, 40),
            (W // 2, H - 100, 500, accent_color, 40),
        ])

        # Top label
        draw = ImageDraw.Draw(img)
        f_big = ImageFont.truetype(FONT_CN_HEAVY, 64)
        f_sub = ImageFont.truetype(FONT_CN_LIGHT, 26)

        # Small tag at top
        f_tag = ImageFont.truetype(FONT_CN_LIGHT, 22)
        draw.text((W // 2, 60), "kev-youtube-video-clone-translate", font=f_tag,
                  fill=(150, 160, 180, 200), anchor="mm")

        # Big label
        draw.text((W // 2, 130), top_big, font=f_big, fill=accent_color, anchor="mm")
        draw.text((W // 2, 185), top_sub, font=f_sub, fill=SOFT, anchor="mm")

        # Middle: video frame
        # Layout: top label zone = 0..230, video zone = 230..1690, bottom zone = 1690..1920
        top_zone = 230
        bot_zone = H - 230
        mid_h = bot_zone - top_zone
        # 16:9 frame inside 1080 wide
        vw, vh = 1080, int(1080 * 9 / 16)
        # If vh > mid_h, we scale by mid_h
        if vh > mid_h:
            scale = mid_h / vh
            vw, vh = int(vw * scale), int(vh * scale)
        frame = src_frames[i]
        frame = ImageOps.fit(frame, (vw, vh), method=Image.LANCZOS)
        # Add subtle border
        bordered = Image.new("RGBA", (vw + 4, vh + 4), accent_color + (180,))
        bordered.paste(frame, (2, 2))
        img.paste(bordered, ((W - bordered.size[0]) // 2, top_zone + (mid_h - bordered.size[1]) // 2),
                  bordered)

        # Bottom label
        draw = ImageDraw.Draw(img)
        f_big_b = ImageFont.truetype(FONT_CN_HEAVY, 56)
        f_sub_b = ImageFont.truetype(FONT_CN_LIGHT, 26)
        draw.text((W // 2, bot_zone + 50), bottom_big, font=f_big_b,
                  fill=accent_color, anchor="mm")
        draw.text((W // 2, bot_zone + 110), bottom_sub, font=f_sub_b,
                  fill=SOFT, anchor="mm")

        # Save
        frame_path = FRAMES_DIR / f"seg_{i:04d}.png"
        img.convert("RGB").save(frame_path, "PNG", quality=85)


def make_cta_card(duration, fps=30):
    """5-second CTA card."""
    n_frames = int(duration * fps)
    for i in range(n_frames):
        img = make_aurora_bg(W, H, [
            (W // 2, H // 2, 800, PURPLE, 70),
            (W // 2, H // 2, 400, TEAL, 50),
        ])
        draw = ImageDraw.Draw(img)
        f_main = ImageFont.truetype(FONT_CN_HEAVY, 76)
        f_url = ImageFont.truetype(FONT_HEAVY, 38)
        f_sub = ImageFont.truetype(FONT_CN_LIGHT, 32)
        f_foot = ImageFont.truetype(FONT_CN_LIGHT, 24)

        draw.text((W // 2, 600), "在线 Demo", font=f_main, fill=WHITE, anchor="mm")
        draw.text((W // 2, 700), "vcvd-project.vercel.app/demo", font=f_url,
                  fill=PURPLE, anchor="mm")
        # Decorative line
        draw.line([(W // 2 - 40, 780), (W // 2 + 40, 780)], fill=TEAL, width=2)
        draw.text((W // 2, 850), "GitHub  ·  KevPH2026", font=f_sub, fill=SOFT, anchor="mm")
        draw.text((W // 2, 900), "kev-youtube-video-clone-translate", font=f_sub,
                  fill=SOFT, anchor="mm")
        # Stats
        draw.text((W // 2, 1100), "100% 本地  ·  MIT  ·  XTTS v2 跨语种克隆", font=f_foot,
                  fill=DIM, anchor="mm")
        # Bottom
        draw.text((W // 2, 1500), "把英文 YouTube 变成中文", font=f_main, fill=PURPLE, anchor="mm")
        draw.text((W // 2, 1600), "用她自己的声音", font=f_main, fill=TEAL, anchor="mm")

        frame_path = FRAMES_DIR / f"cta_{i:04d}.png"
        img.convert("RGB").save(frame_path, "PNG", quality=85)


def frames_to_video(frame_glob, audio_path, output):
    """Encode a sequence of PNGs to a 30fps mp4 with optional audio."""
    cmd = [
        "ffmpeg", "-y",
        "-framerate", "30",
        "-i", frame_glob,
    ]
    if audio_path and Path(audio_path).exists():
        cmd += ["-i", str(audio_path), "-c:a", "aac", "-b:a", "128k",
                "-shortest"]
    cmd += [
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-vf", "scale=1080:1920",
        str(output),
    ]
    print("$", " ".join(cmd))
    subprocess.run(cmd, check=True)


def concat_segments(segments, output):
    """Concat a list of (path, duration) using concat demuxer."""
    list_file = output.with_suffix(".list.txt")
    with open(list_file, "w") as f:
        for path, _ in segments:
            f.write(f"file '{path.resolve()}'\n")
    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(list_file),
        "-c", "copy",
        str(output),
    ]
    subprocess.run(cmd, check=True)


def main():
    # 1. Title card 4s
    print("1. Title card")
    make_title_card(4)
    title = OUT.parent / "seg_title.mp4"
    frames_to_video(str(FRAMES_DIR / "title_%04d.png"), None, title)
    # Clean
    for f in FRAMES_DIR.glob("title_*.png"):
        f.unlink()

    # 2. Before video 8s
    print("2. Before video")
    make_video_segment(
        str(ROOT / "before_15s.mp4"),
        duration=8,
        top_big="BEFORE",
        top_sub="原声  ·  英文原声  ·  原说话人音色",
        bottom_big="原声",
        bottom_sub="原始音频  ·  英文学术播客",
        accent_color=PURPLE,
    )
    before = OUT.parent / "seg_before.mp4"
    frames_to_video(str(FRAMES_DIR / "seg_%04d.png"), None, before)
    for f in FRAMES_DIR.glob("seg_*.png"):
        f.unlink()

    # 3. After video 8s
    print("3. After video")
    make_video_segment(
        str(ROOT / "after_15s.mp4"),
        duration=8,
        top_big="AFTER",
        top_sub="克隆  ·  AI 中文合成  ·  XTTS v2 跨语种",
        bottom_big="克隆",
        bottom_sub="原说话人音色  ·  AI 跨语种",
        accent_color=TEAL,
    )
    after = OUT.parent / "seg_after.mp4"
    frames_to_video(str(FRAMES_DIR / "seg_%04d.png"), None, after)
    for f in FRAMES_DIR.glob("seg_*.png"):
        f.unlink()

    # 4. CTA 5s
    print("4. CTA")
    make_cta_card(5)
    cta = OUT.parent / "seg_cta.mp4"
    frames_to_video(str(FRAMES_DIR / "cta_%04d.png"), None, cta)
    for f in FRAMES_DIR.glob("cta_*.png"):
        f.unlink()

    # Concat
    print("5. Concat")
    concat_segments([(title, 4), (before, 8), (after, 8), (cta, 5)], OUT)
    print(f"final: {OUT}  ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
