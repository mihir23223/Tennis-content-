"""
Tennis Coaching Reels Editor
Produces Instagram Reels (9:16, 1080x1920) with hooks, captions, zoom, and slow-mo.

Usage:  python3 edit_reels.py
Edit CUT_LIST below to define your clips.
"""

import os
import subprocess
import json
import textwrap
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import cv2

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
OUT_DIR = Path("output_reels")
OUT_DIR.mkdir(exist_ok=True)

REEL_W, REEL_H = 1080, 1920   # 9:16 vertical
FPS = 30


# ── Font helpers ─────────────────────────────────────────────────────────────

def _find_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]
    for c in candidates:
        if Path(c).exists():
            return ImageFont.truetype(c, size)
    return ImageFont.load_default()


# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class Segment:
    start: float          # source timestamp in seconds
    end: float
    slowmo: float = 1.0   # 0.5 = half speed, 1.0 = normal
    zoom: float = 1.0     # 1.0 = no zoom, 1.3 = 30% zoom-in


@dataclass
class Reel:
    source: str
    output_name: str
    segments: list[Segment]
    hook: str = ""
    caption_lines: list[str] = field(default_factory=list)
    drill_name: str = ""
    coaching_cue: str = ""
    accent_color: tuple = (255, 59, 48)    # RGB red


# ════════════════════════════════════════════════════════════════════════════
#  ✏️  EDIT YOUR CUT LIST HERE
# ════════════════════════════════════════════════════════════════════════════
CUT_LIST: list[Reel] = [
    Reel(
        source="drill1.mp4",
        output_name="forehand_crosscourt",
        segments=[
            Segment(start=10,  end=18),
            Segment(start=18,  end=22, slowmo=0.4, zoom=1.4),
            Segment(start=22,  end=45),
        ],
        hook="Most players get this WRONG",
        drill_name="Forehand Cross-Court Drill",
        coaching_cue="Watch the hip rotation",
        caption_lines=[
            "Here's the setup...",
            "SLOW MO — see the elbow drop?",
            "The fix: lead with hips, not arm",
        ],
        accent_color=(255, 59, 48),
    ),
    Reel(
        source="drill1.mp4",
        output_name="recovery_footwork",
        segments=[
            Segment(start=90,  end=100),
            Segment(start=100, end=106, slowmo=0.5, zoom=1.3),
            Segment(start=106, end=130),
        ],
        hook="Your footwork is costing you points",
        drill_name="Recovery Footwork Drill",
        coaching_cue="Split-step EVERY time",
        caption_lines=[
            "Watch the recovery position...",
            "SLOW MO — no split-step here",
            "Land ready, not flat-footed",
        ],
        accent_color=(0, 122, 255),
    ),
    # ── Add more reels below ─────────────────────────────────────────────────
]
# ════════════════════════════════════════════════════════════════════════════


# ── ffmpeg helpers ────────────────────────────────────────────────────────────

def run(cmd: list[str], label: str = "") -> None:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[ERROR] {label}\n{result.stderr[-1500:]}")
        raise RuntimeError(f"ffmpeg failed: {label}")


def cut_and_scale(src: str, seg: Segment, idx: int, tmp_dir: Path) -> Path:
    """Cut segment, apply slowmo + zoom, export 9:16 clip."""
    raw = tmp_dir / f"seg_{idx}_raw.mp4"
    out = tmp_dir / f"seg_{idx}_scaled.mp4"
    duration = seg.end - seg.start

    # Step 1: cut
    run([
        FFMPEG, "-y",
        "-ss", str(seg.start), "-t", str(duration),
        "-i", src,
        "-c:v", "libx264", "-c:a", "aac",
        "-avoid_negative_ts", "make_zero",
        str(raw),
    ], f"cut {idx}")

    # Build scale+zoom+crop filter
    z = seg.zoom
    vf = (
        f"scale={int(REEL_W * z)}:{int(REEL_H * z)}:force_original_aspect_ratio=increase,"
        f"crop={REEL_W}:{REEL_H}"
    )

    if seg.slowmo != 1.0:
        pts = 1.0 / seg.slowmo
        vf += f",setpts={pts:.4f}*PTS"
        atempo = seg.slowmo
        if atempo < 0.5:
            audio_filter = f"atempo=0.5,atempo={atempo/0.5:.4f}"
        else:
            audio_filter = f"atempo={atempo:.4f}"
        run([
            FFMPEG, "-y", "-i", str(raw),
            "-vf", vf, "-af", audio_filter,
            "-c:v", "libx264", "-c:a", "aac",
            str(out),
        ], f"slowmo+zoom {idx}")
    else:
        run([
            FFMPEG, "-y", "-i", str(raw),
            "-vf", vf,
            "-c:v", "libx264", "-c:a", "aac",
            str(out),
        ], f"scale+crop {idx}")

    return out


# ── Overlay rendering via Pillow ──────────────────────────────────────────────

def hex_to_rgb(h: str) -> tuple:
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def draw_pill(draw: ImageDraw.Draw, x: int, y: int, w: int, h: int,
              color: tuple, alpha_img: Image.Image, alpha: int = 180) -> None:
    """Draw a rounded rectangle (pill) on an RGBA overlay image."""
    r = min(h // 2, 22)
    draw.rounded_rectangle([x, y, x + w, y + h], radius=r, fill=(*color, alpha))


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    """Word-wrap text to fit within max_width pixels."""
    words = text.split()
    lines, current = [], ""
    dummy = Image.new("RGB", (1, 1))
    dd = ImageDraw.Draw(dummy)
    for word in words:
        test = f"{current} {word}".strip()
        bbox = dd.textbbox((0, 0), test, font=font)
        if bbox[2] > max_width and current:
            lines.append(current)
            current = word
        else:
            current = test
    if current:
        lines.append(current)
    return lines


def build_overlay_frame(reel: Reel, seg_idx: int, is_first: bool,
                        seg: Segment, t_in_seg: float) -> np.ndarray:
    """
    Returns an RGBA numpy array (REEL_H, REEL_W, 4) with all text overlays.
    Composited on top of the video frame.
    """
    img = Image.new("RGBA", (REEL_W, REEL_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    accent = reel.accent_color
    pad = 28
    max_text_w = REEL_W - pad * 4

    # ── Drill name banner (top) ───────────────────────────────────────────────
    if reel.drill_name:
        font = _find_font(40, bold=True)
        text = reel.drill_name.upper()
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        bx = (REEL_W - tw) // 2 - pad
        by = 48
        bw, bh = tw + pad * 2, th + pad
        draw.rounded_rectangle([bx, by, bx + bw, by + bh],
                                radius=12, fill=(0, 0, 0, 160))
        draw.text((bx + pad, by + pad // 2), text, font=font, fill=(255, 255, 255, 255))

    # ── Hook (big centred, first 2.5 s of first segment) ─────────────────────
    if is_first and reel.hook and t_in_seg < 2.5:
        font_hook = _find_font(64, bold=True)
        lines = wrap_text(reel.hook, font_hook, max_text_w)
        line_h = 80
        total_h = len(lines) * line_h + pad * 2
        bx, by = pad, REEL_H // 2 - total_h // 2 - 60
        bw, bh = REEL_W - pad * 2, total_h
        alpha = int(min(255, 220 * min(1.0, (2.5 - t_in_seg) / 0.5)))
        draw.rounded_rectangle([bx, by, bx + bw, by + bh],
                                radius=16, fill=(*accent, int(alpha * 0.9)))
        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font_hook)
            tw = bbox[2] - bbox[0]
            tx = (REEL_W - tw) // 2
            ty = by + pad + i * line_h
            draw.text((tx, ty), line, font=font_hook, fill=(255, 255, 255, alpha))

    # ── Slow-mo badge ─────────────────────────────────────────────────────────
    if seg.slowmo < 1.0:
        font_badge = _find_font(42, bold=True)
        speed_pct = int(seg.slowmo * 100)
        badge_text = f"  SLOW MO  {speed_pct}%  "
        bbox = draw.textbbox((0, 0), badge_text, font=font_badge)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        bx, by = 40, REEL_H - 260
        bw, bh = tw + 8, th + 20
        draw.rounded_rectangle([bx, by, bx + bw, by + bh],
                                radius=10, fill=(*accent, 230))
        draw.text((bx + 4, by + 10), badge_text, font=font_badge,
                  fill=(255, 255, 255, 255))

    # ── Caption line (bottom, per-segment) ───────────────────────────────────
    caption = ""
    if reel.caption_lines and seg_idx < len(reel.caption_lines):
        caption = reel.caption_lines[seg_idx]
    if caption:
        font_cap = _find_font(50, bold=True)
        lines = wrap_text(caption, font_cap, max_text_w)
        line_h = 65
        total_h = len(lines) * line_h + pad * 2
        bx, by = pad, REEL_H - total_h - 170
        bw, bh = REEL_W - pad * 2, total_h
        draw.rounded_rectangle([bx, by, bx + bw, by + bh],
                                radius=14, fill=(0, 0, 0, 175))
        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font_cap)
            tw = bbox[2] - bbox[0]
            tx = (REEL_W - tw) // 2
            ty = by + pad + i * line_h
            draw.text((tx, ty), line, font=font_cap, fill=(255, 255, 255, 255))

    # ── Coaching cue (small, bottom) ─────────────────────────────────────────
    if reel.coaching_cue:
        font_cue = _find_font(36, bold=False)
        cue = reel.coaching_cue
        bbox = draw.textbbox((0, 0), cue, font=font_cue)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        bx = (REEL_W - tw) // 2 - pad
        by = REEL_H - 110
        bw, bh = tw + pad * 2, th + 20
        draw.rounded_rectangle([bx, by, bx + bw, by + bh],
                                radius=10, fill=(0, 0, 0, 140))
        draw.text((bx + pad, by + 10), cue, font=font_cue, fill=(255, 230, 0, 255))

    return np.array(img)


def composite_overlays(clip_path: Path, reel: Reel, seg_idx: int,
                        is_first: bool, seg: Segment, out_path: Path) -> None:
    """Read video frames, composite overlays, write output."""
    cap = cv2.VideoCapture(str(clip_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or FPS
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    tmp_frames = out_path.parent / f"frames_{seg_idx}"
    tmp_frames.mkdir(exist_ok=True)

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        t = frame_idx / fps
        overlay_rgba = build_overlay_frame(reel, seg_idx, is_first, seg, t)

        # Convert BGR frame to RGBA PIL image
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        base = Image.fromarray(frame_rgb).convert("RGBA")
        overlay = Image.fromarray(overlay_rgba, "RGBA")
        composited = Image.alpha_composite(base, overlay).convert("RGB")

        # Save as PNG sequence
        composited.save(tmp_frames / f"frame_{frame_idx:06d}.png")
        frame_idx += 1

    cap.release()

    # Re-encode PNG sequence + original audio into output
    run([
        FFMPEG, "-y",
        "-framerate", str(fps),
        "-i", str(tmp_frames / "frame_%06d.png"),
        "-i", str(clip_path),
        "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-c:a", "aac",
        "-pix_fmt", "yuv420p",
        "-shortest",
        str(out_path),
    ], f"composite seg {seg_idx}")

    # Cleanup frames
    for f in tmp_frames.iterdir():
        f.unlink()
    tmp_frames.rmdir()


def concat_clips(clips: list[Path], out: Path) -> None:
    list_file = out.parent / "concat_list.txt"
    list_file.write_text("\n".join(f"file '{c.resolve()}'" for c in clips))
    run([
        FFMPEG, "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(list_file),
        "-c:v", "libx264", "-c:a", "aac",
        "-movflags", "+faststart",
        str(out),
    ], "concat")
    list_file.unlink()


def process_reel(reel: Reel) -> None:
    print(f"\n{'='*60}")
    print(f"  Reel:   {reel.output_name}")
    print(f"  Source: {reel.source}")
    print(f"{'='*60}")

    if not Path(reel.source).exists():
        print(f"  [SKIP] File not found: {reel.source}")
        return

    tmp_dir = OUT_DIR / f"_tmp_{reel.output_name}"
    tmp_dir.mkdir(exist_ok=True)

    final_clips = []
    for idx, seg in enumerate(reel.segments):
        print(f"  Seg {idx+1}/{len(reel.segments)}  "
              f"[{seg.start:.1f}s-{seg.end:.1f}s]  "
              f"slowmo={seg.slowmo}x  zoom={seg.zoom}x")

        scaled = cut_and_scale(reel.source, seg, idx, tmp_dir)
        overlaid = tmp_dir / f"seg_{idx}_final.mp4"
        composite_overlays(scaled, reel, idx, idx == 0, seg, overlaid)
        final_clips.append(overlaid)

    final = OUT_DIR / f"{reel.output_name}.mp4"
    concat_clips(final_clips, final)

    for f in tmp_dir.iterdir():
        f.unlink()
    tmp_dir.rmdir()

    mb = final.stat().st_size / 1_048_576
    print(f"\n  Done → {final}  ({mb:.1f} MB)")


def main():
    print(f"\nTennis Reels Editor")
    print(f"ffmpeg: {FFMPEG}")
    print(f"Output: {OUT_DIR.resolve()}\n")
    for reel in CUT_LIST:
        process_reel(reel)
    print(f"\nAll done! Check the '{OUT_DIR}' folder.")


if __name__ == "__main__":
    main()
