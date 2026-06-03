# Tennis Coaching Reels Editor

Produces Instagram Reels (9:16, 1080×1920) from raw coaching footage with:
- **Hook text** — big attention-grabbing opener for first 2.5 s
- **Drill name banner** — top strip on every frame
- **Per-segment captions** — bottom text changes with each clip section
- **Coaching cue** — persistent yellow label at the bottom
- **Slow-motion** — any segment at any speed (e.g. `slowmo=0.4`)
- **Zoom** — push in on key moments (e.g. `zoom=1.4`)
- **Concat** — all segments joined into one 30–60 s reel automatically

## Requirements

```bash
pip3 install moviepy opencv-python-headless Pillow numpy imageio-ffmpeg
```

## Quick start

1. Put your source videos in this folder (or use full paths).
2. Open `edit_reels.py` and edit the `CUT_LIST` section:

```python
Reel(
    source="my_session.mp4",
    output_name="serve_technique",
    segments=[
        Segment(start=12,  end=22),                       # normal intro
        Segment(start=22,  end=27, slowmo=0.4, zoom=1.4), # slow-mo zoom on mistake
        Segment(start=27,  end=50),                        # correction / outro
    ],
    hook="Your serve is leaking power HERE",
    drill_name="Serve Technique Drill",
    coaching_cue="Watch the trophy position",
    caption_lines=[
        "Here's what most players do...",
        "SLOW MO — elbow drops too early",
        "Keep the elbow HIGH through contact",
    ],
    accent_color=(255, 59, 48),   # red  |  try (0,122,255) for blue
)
```

3. Run:

```bash
python3 edit_reels.py
```

Finished reels land in `output_reels/`.

## Google Drive workflow

Download videos from Drive, drop them here, edit the cut list, run the script.
If you have `rclone` configured you can pull directly:

```bash
rclone copy "gdrive:Tennis content/" . --include "*.mp4"
python3 edit_reels.py
```
