"""
Generates a synthetic 60-second test video and runs the reel editor on it.
Run: python3 test_pipeline.py
"""

import subprocess
from pathlib import Path
import imageio_ffmpeg

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


def make_test_video(path: str, duration: int = 60) -> None:
    """Create a synthetic landscape video with a moving tennis ball."""
    subprocess.run([
        FFMPEG, "-y",
        "-f", "lavfi",
        "-i", f"testsrc2=size=1920x1080:rate=30:duration={duration}",
        "-f", "lavfi", "-i", f"sine=frequency=440:duration={duration}",
        "-c:v", "libx264", "-c:a", "aac",
        "-t", str(duration),
        path,
    ], capture_output=True)
    print(f"  Created test video: {path}")


if __name__ == "__main__":
    print("Building test video...")
    make_test_video("drill1.mp4", duration=150)

    print("Running reel editor...")
    import edit_reels as er

    # Override cut list with safe timestamps for the test video
    er.CUT_LIST = [
        er.Reel(
            source="drill1.mp4",
            output_name="test_forehand",
            segments=[
                er.Segment(start=5,  end=15),
                er.Segment(start=15, end=20, slowmo=0.5, zoom=1.3),
                er.Segment(start=20, end=35),
            ],
            hook="❌ Most players get this WRONG",
            drill_name="Forehand Cross-Court Drill",
            coaching_cue="Watch the hip rotation ↓",
            caption_lines=[
                "Here's the setup...",
                "🔴 SLOW MO — see the elbow drop?",
                "The fix: lead with hips, not arm ✅",
            ],
        ),
    ]

    er.main()
