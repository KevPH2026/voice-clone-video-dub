#!/usr/bin/env python3
"""Build a 9:16 XHS video WITH audio (PIL frame-by-frame approach).

Strategy:
- For video segments: extract original frames, composite with PIL
  (aurora bg + top/bottom label band), and pass the original audio
  stream through (map 0:a).
- For title/CTA cards: silent audio (anullsrc) + static PNG.
- Concat all 4 segments with concat demuxer (all use the same encode
  params so -c copy works).
"""
import subprocess
import shutil
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from random import randint, seed

W, H = 1080, 1920
ROOT = Path("/Users/k/Desktop/vcvd-project")
OUT = ROOT / "xiaohongshu" / "xhs_video.mp4"
TMP = ROOT / "xiaohongshu" / "tmp"
TMP.mkdir(parents=True, exist_ok=True)

FONT_HEAVY = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
FONT_CN_HEAVY = "/System/Library/Fonts/STHeiti Medium.ttc"
FONT_CN_LIGHT = "/System/Library/Fonts/STHeiti Light.ttc"
PURPLE = (138, 79, 255)
TEAL = (64, 224, 208)
WHITE = (245, 245, 250)
SOFT = (200, 210, 230)
DIM = (160, 175, 200)


def make_aurora_bg(w, h, blobs):
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


def extract_frames(video_path, n_frames, fps=30):
    """Extract n_frames from video via ffmpeg → list of PIL Image."""
    tmp = Path(tempfile.mkdtemp(prefix="xhs_vid_"))
    pattern = tmp / "f_%04d.png"
    cmd = [
        "/opt/homebrew/bin/ffmpeg", "-y", "-i", str(video_path),
        "-vf", f"fps={fps}",
        "-frames:v", str(n_frames),
        str(pattern),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    frames = []
    for i in range(1, n_frames + 1):
        p = tmp / f"f_{i:04d}.png"
        if not p.exists():
            break
        frames.append(Image.open(p).convert("RGB"))
    shutil.rmtree(tmp, ignore_errors=True)
    return frames


def make_video_segment_pngs(video_path, duration, top_big, top_sub,
                             bottom_big, bottom_sub, accent_color, fps=30):
    """Compose a 9:16 video segment frame-by-frame, save as PNGs."""
    n_frames = int(duration * fps)
    src_frames = extract_frames(video_path, n_frames, fps=fps)
    if len(src_frames) < n_frames:
        while len(src_frames) < n_frames:
            src_frames += src_frames
        src_frames = src_frames[:n_frames]

    out_dir = TMP / f"frames_{video_path.stem}"
    out_dir.mkdir(parents=True, exist_ok=True)
    f_big = ImageFont.truetype(FONT_CN_HEAVY, 72)
    f_sub = ImageFont.truetype(FONT_CN_LIGHT, 28)
    f_tag = ImageFont.truetype(FONT_CN_LIGHT, 22)
    f_big_b = ImageFont.truetype(FONT_CN_HEAVY, 56)
    f_sub_b = ImageFont.truetype(FONT_CN_LIGHT, 26)

    for i in range(n_frames):
        img = make_aurora_bg(W, H, [
            (W // 2, 100, 600, PURPLE, 40),
            (W // 2, H - 100, 500, accent_color, 40),
        ])

        # Top label band: aurora bg + small tag + big + sub
        draw = ImageDraw.Draw(img)
        # Tag at very top
        draw.text((W // 2, 60), "kev-youtube-video-clone-translate", font=f_tag,
                  fill=(150, 160, 180, 200), anchor="mm")
        # Big label
        draw.text((W // 2, 130), top_big, font=f_big, fill=accent_color, anchor="mm")
        # Sub
        draw.text((W // 2, 195), top_sub, font=f_sub, fill=SOFT, anchor="mm")

        # Middle: video frame (9:16 from 16:9 source = vertical center crop)
        top_zone = 230
        bot_zone = H - 230
        mid_h = bot_zone - top_zone
        # Source is 16:9. For 9:16 within 1080 wide → take center 608 wide
        # slice, then upscale to 1080.
        frame = src_frames[i]
        fw, fh = frame.size
        # Take 9:16 vertical slice from center
        crop_w = int(fh * 9 / 16)
        x0 = (fw - crop_w) // 2
        frame = frame.crop((x0, 0, x0 + crop_w, fh))
        # Resize to fit mid_h
        scale = mid_h / fh
        new_w = int(crop_w * scale)
        frame = frame.resize((new_w, mid_h), Image.LANCZOS)
        # Add subtle border
        bordered = Image.new("RGBA", (new_w + 4, mid_h + 4),
                              accent_color + (200,))
        bordered.paste(frame, (2, 2))
        img.paste(bordered, ((W - bordered.size[0]) // 2, top_zone), bordered)

        # Bottom label band
        draw = ImageDraw.Draw(img)
        draw.text((W // 2, bot_zone + 50), bottom_big, font=f_big_b,
                  fill=accent_color, anchor="mm")
        draw.text((W // 2, bot_zone + 115), bottom_sub, font=f_sub_b,
                  fill=SOFT, anchor="mm")

        out_path = out_dir / f"f_{i:04d}.png"
        img.convert("RGB").save(out_path, "PNG", quality=85)
    return out_dir


def pngs_to_video_with_audio(pngs_dir, fps, duration, audio_src, out_path):
    """Encode a sequence of PNGs to mp4 with audio from audio_src."""
    png_glob = str(pngs_dir / "f_%04d.png")
    # Two-pass: extract audio first (cut to duration), then combine
    audio_cut = TMP / f"aud_{out_path.stem}.m4a"
    if audio_src and Path(audio_src).exists():
        cmd1 = [
            "/opt/homebrew/bin/ffmpeg", "-y", "-i", str(audio_src),
            "-t", str(duration),
            "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "2",
            str(audio_cut),
        ]
        subprocess.run(cmd1, check=True, capture_output=True)
        audio_input = ["-i", str(audio_cut)]
    else:
        # silent
        audio_input = [
            "-f", "lavfi", "-t", str(duration),
            "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
        ]
    cmd = [
        "/opt/homebrew/bin/ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", png_glob,
        *audio_input,
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest",
        str(out_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return out_path


def concat_segments(segments, output):
    list_file = output.with_suffix(".list.txt")
    with open(list_file, "w") as f:
        for s in segments:
            f.write(f"file '{s.resolve()}'\n")
    cmd = [
        "/opt/homebrew/bin/ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(list_file),
        "-c", "copy",
        str(output),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def main():
    FPS = 30
    # 1. Title card (no audio)
    print("1. title (silent)")
    title_pngs = TMP / "frames_title"
    title_pngs.mkdir(exist_ok=True)
    f_main = ImageFont.truetype(FONT_CN_HEAVY, 124)
    f_sub = ImageFont.truetype(FONT_CN_LIGHT, 36)
    f_tag = ImageFont.truetype(FONT_CN_LIGHT, 28)
    f_stat = ImageFont.truetype(FONT_CN_LIGHT, 28)
    f_url = ImageFont.truetype(FONT_HEAVY, 32)
    for i in range(int(4 * FPS)):
        img = make_aurora_bg(W, H, [
            (W // 4, H // 4, 700, PURPLE, 80),
            (3 * W // 4, H // 2, 500, TEAL, 50),
        ])
        draw = ImageDraw.Draw(img)
        draw.text((W // 2, 110), "kev-youtube-video-clone-translate  ·  开源工具", font=f_tag,
                  fill=(180, 180, 200, 200), anchor="mm")
        draw.line([(W // 4, 150), (3 * W // 4, 150)],
                  fill=(60, 70, 100, 180), width=1)
        draw.text((W // 2, H // 2 - 130), "把英文 YouTube", font=f_main,
                  fill=(245, 245, 250, 255), anchor="mm")
        draw.text((W // 2, H // 2 + 10), "变成中文", font=f_main,
                  fill=PURPLE, anchor="mm")
        draw.text((W // 2, H // 2 + 150), "用她自己的声音", font=f_main,
                  fill=TEAL, anchor="mm")
        draw.text((W // 2, H // 2 + 280), "— 不是配音演员，AI 克隆 —", font=f_sub,
                  fill=SOFT, anchor="mm")
        draw.text((W // 2, H // 2 + 360), "138 段字幕  ·  0 失败  ·  12m 全程  ·  93MB",
                  font=f_stat, fill=DIM, anchor="mm")
        draw.text((W // 2, H - 100), "vcvd-project.vercel.app/demo", font=f_url,
                  fill=PURPLE, anchor="mm")
        img.convert("RGB").save(title_pngs / f"f_{i:04d}.png", "PNG", quality=85)
    seg_title = TMP / "seg_title.mp4"
    pngs_to_video_with_audio(title_pngs, FPS, 4, None, seg_title)
    shutil.rmtree(title_pngs)

    # 2. Before video (with audio)
    print("2. before (audio)")
    before_pngs = make_video_segment_pngs(
        ROOT / "before_15s.mp4",
        duration=8,
        top_big="BEFORE",
        top_sub="原声  ·  英文原声  ·  原说话人音色",
        bottom_big="原声",
        bottom_sub="原始音频  ·  英文学术播客",
        accent_color=PURPLE,
    )
    seg_before = TMP / "seg_before.mp4"
    pngs_to_video_with_audio(before_pngs, FPS, 8, ROOT / "before_15s.mp4",
                              seg_before)
    shutil.rmtree(before_pngs)

    # 3. After video (with audio)
    print("3. after (audio)")
    after_pngs = make_video_segment_pngs(
        ROOT / "after_15s.mp4",
        duration=8,
        top_big="AFTER",
        top_sub="克隆  ·  AI 中文合成  ·  XTTS v2 跨语种",
        bottom_big="克隆",
        bottom_sub="原说话人音色  ·  AI 跨语种",
        accent_color=TEAL,
    )
    seg_after = TMP / "seg_after.mp4"
    pngs_to_video_with_audio(after_pngs, FPS, 8, ROOT / "after_15s.mp4",
                              seg_after)
    shutil.rmtree(after_pngs)

    # 4. CTA (silent)
    print("4. cta (silent)")
    cta_pngs = TMP / "frames_cta"
    cta_pngs.mkdir(exist_ok=True)
    f_main = ImageFont.truetype(FONT_CN_HEAVY, 76)
    f_url = ImageFont.truetype(FONT_HEAVY, 38)
    f_sub = ImageFont.truetype(FONT_CN_LIGHT, 32)
    f_foot = ImageFont.truetype(FONT_CN_LIGHT, 24)
    for i in range(int(5 * FPS)):
        img = make_aurora_bg(W, H, [
            (W // 2, H // 2, 800, PURPLE, 70),
            (W // 2, H // 2, 400, TEAL, 50),
        ])
        draw = ImageDraw.Draw(img)
        draw.text((W // 2, 600), "在线 Demo", font=f_main, fill=WHITE, anchor="mm")
        draw.text((W // 2, 700), "vcvd-project.vercel.app/demo", font=f_url,
                  fill=PURPLE, anchor="mm")
        draw.line([(W // 2 - 40, 780), (W // 2 + 40, 780)], fill=TEAL, width=2)
        draw.text((W // 2, 850), "GitHub  ·  KevPH2026", font=f_sub, fill=SOFT, anchor="mm")
        draw.text((W // 2, 900), "kev-youtube-video-clone-translate", font=f_sub,
                  fill=SOFT, anchor="mm")
        draw.text((W // 2, 1100), "100% 本地  ·  MIT  ·  XTTS v2 跨语种克隆", font=f_foot,
                  fill=DIM, anchor="mm")
        draw.text((W // 2, 1500), "把英文 YouTube 变成中文", font=f_main, fill=PURPLE, anchor="mm")
        draw.text((W // 2, 1600), "用她自己的声音", font=f_main, fill=TEAL, anchor="mm")
        img.convert("RGB").save(cta_pngs / f"f_{i:04d}.png", "PNG", quality=85)
    seg_cta = TMP / "seg_cta.mp4"
    pngs_to_video_with_audio(cta_pngs, FPS, 5, None, seg_cta)
    shutil.rmtree(cta_pngs)

    # Concat
    print("5. concat")
    concat_segments([seg_title, seg_before, seg_after, seg_cta], OUT)
    print(f"final: {OUT}  ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
