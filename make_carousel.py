"""
Instagram Carousel Generator — Forehand Fixes Ep.1: The Cramped Forehand
7 slides, 1080×1350 (4:5), saved to output_carousel/
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math

OUT = Path("output_carousel")
OUT.mkdir(exist_ok=True)

W, H = 1080, 1350

# ── Brand palette ─────────────────────────────────────────────────────────────
TEAL    = (18,  95,  105)
ORANGE  = (220,  80,  30)
CREAM   = (252, 248, 240)
WHITE   = (255, 255, 255)
BLACK   = (20,  20,  20)
RED_X   = (210,  40,  40)
GREEN_V = (30,  160,  80)
LIGHT_TEAL = (220, 240, 242)
DARK    = (30,  30,  30)
GREY    = (130, 130, 130)

# ── Font loader ───────────────────────────────────────────────────────────────
def font(size, bold=False):
    candidates = [
        f"/usr/share/fonts/truetype/dejavu/DejaVuSans-{'Bold' if bold else ''}.ttf",
        f"/usr/share/fonts/truetype/liberation/LiberationSans-{'Bold' if bold else 'Regular'}.ttf",
    ]
    for c in candidates:
        if Path(c).exists():
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                pass
    return ImageFont.load_default()

def font_oblique(size):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-BoldItalic.ttf",
    ]
    for c in candidates:
        if Path(c).exists():
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                pass
    return font(size, bold=True)

# ── Drawing helpers ───────────────────────────────────────────────────────────
def centered_text(draw, y, text, fnt, color=BLACK, max_w=W-80):
    """Draw text centered horizontally, word-wrapped."""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        bb = draw.textbbox((0, 0), test, font=fnt)
        if bb[2] > max_w and cur:
            lines.append(cur); cur = w
        else:
            cur = test
    if cur: lines.append(cur)
    lh = draw.textbbox((0,0),"Ay",font=fnt)[3] + 8
    for line in lines:
        bb = draw.textbbox((0,0), line, font=fnt)
        x = (W - (bb[2]-bb[0])) // 2
        draw.text((x, y), line, font=fnt, fill=color)
        y += lh
    return y

def pill(draw, cx, cy, w, h, color, radius=18):
    draw.rounded_rectangle([cx-w//2, cy-h//2, cx+w//2, cy+h//2], radius=radius, fill=color)

def badge(draw, cx, cy, text, fnt, bg, fg=WHITE, pad_x=28, pad_y=14):
    bb = draw.textbbox((0,0), text, font=fnt)
    tw, th = bb[2]-bb[0], bb[3]-bb[1]
    bw, bh = tw+pad_x*2, th+pad_y*2
    draw.rounded_rectangle([cx-bw//2, cy-bh//2, cx+bw//2, cy+bh//2], radius=bh//2, fill=bg)
    draw.text((cx-tw//2, cy-th//2-2), text, font=fnt, fill=fg)

def top_bar(draw, label="3 FIXES · EP.1"):
    draw.rectangle([0,0,W,72], fill=TEAL)
    f = font(28, bold=True)
    bb = draw.textbbox((0,0), label, font=f)
    draw.text(((W-(bb[2]-bb[0]))//2, 20), label, font=f, fill=WHITE)

def swipe_nudge(draw, slide_num, total=7):
    """Bottom strip with dot indicator + swipe prompt."""
    draw.rectangle([0, H-70, W, H], fill=TEAL)
    dot_r, gap = 7, 22
    total_w = total*dot_r*2 + (total-1)*gap
    sx = (W - total_w) // 2
    for i in range(total):
        cx = sx + i*(dot_r*2+gap) + dot_r
        cy = H - 35
        color = WHITE if i == slide_num else (100,150,155)
        draw.ellipse([cx-dot_r, cy-dot_r, cx+dot_r, cy+dot_r], fill=color)
    if slide_num < total-1:
        f = font(22)
        txt = "swipe →"
        bb = draw.textbbox((0,0), txt, font=f)
        draw.text((W - bb[2] - bb[0] - 30, H-52), txt, font=f, fill=(200,230,232))

# ── Stick-figure drawing ──────────────────────────────────────────────────────
def stick_person(draw, cx, cy, scale=1.0, color=DARK, elbow_tucked=False,
                 second_hand=False, label=None, label_color=DARK):
    """
    Draw a side-view stick figure tennis player.
    elbow_tucked=True  → bad form (elbow glued to ribs)
    second_hand=True   → non-dominant hand also on racket during turn
    """
    s = scale
    lw = max(2, int(3*s))

    # Head
    hr = int(22*s)
    draw.ellipse([cx-hr, cy-hr, cx+hr, cy+hr], outline=color, width=lw)

    # Torso
    torso_top = cy + hr
    torso_bot = cy + int(90*s)
    draw.line([cx, torso_top, cx, torso_bot], fill=color, width=lw)

    # Legs
    lfoot_x = cx - int(25*s)
    rfoot_x = cx + int(25*s)
    foot_y   = torso_bot + int(70*s)
    draw.line([cx, torso_bot, lfoot_x, foot_y], fill=color, width=lw)
    draw.line([cx, torso_bot, rfoot_x, foot_y], fill=color, width=lw)

    # Arms + racket
    shoulder_y = torso_top + int(18*s)
    if elbow_tucked:
        # Bad: right elbow pinned, no rotation
        elbow_x = cx + int(8*s)
        elbow_y = shoulder_y + int(30*s)
        hand_x  = cx + int(50*s)
        hand_y  = shoulder_y + int(20*s)
        # left arm hangs
        draw.line([cx, shoulder_y, cx - int(35*s), shoulder_y+int(40*s)], fill=color, width=lw)
    else:
        # Good: elbow free, shoulder turned
        elbow_x = cx + int(30*s)
        elbow_y = shoulder_y + int(10*s)
        hand_x  = cx + int(65*s)
        hand_y  = shoulder_y - int(10*s)
        # left arm extended (or on racket)
        if second_hand:
            draw.line([cx, shoulder_y, cx+int(20*s), shoulder_y-int(20*s)], fill=GREEN_V, width=lw+1)

    draw.line([cx, shoulder_y, elbow_x, elbow_y], fill=color, width=lw)
    draw.line([elbow_x, elbow_y, hand_x, hand_y], fill=color, width=lw)

    # Racket (oval)
    rw, rh = int(18*s), int(30*s)
    draw.ellipse([hand_x, hand_y-rh, hand_x+rw*2, hand_y+rh], outline=ORANGE, width=lw)
    # handle
    draw.line([hand_x+rw, hand_y+rh, hand_x+rw+int(20*s), hand_y+rh+int(20*s)], fill=ORANGE, width=lw)

    if label:
        f = font(int(26*s), bold=True)
        bb = draw.textbbox((0,0), label, font=f)
        draw.text((cx - (bb[2]-bb[0])//2, foot_y+8), label, font=f, fill=label_color)


def cross_mark(draw, cx, cy, size=28, lw=5):
    draw.line([cx-size, cy-size, cx+size, cy+size], fill=RED_X, width=lw)
    draw.line([cx+size, cy-size, cx-size, cy+size], fill=RED_X, width=lw)

def check_mark(draw, cx, cy, size=28, lw=5):
    draw.line([cx-size, cy, cx-size//3, cy+size], fill=GREEN_V, width=lw)
    draw.line([cx-size//3, cy+size, cx+size, cy-size//2], fill=GREEN_V, width=lw)

def arrow(draw, x1, y1, x2, y2, color=ORANGE, lw=4, head=16):
    draw.line([x1, y1, x2, y2], fill=color, width=lw)
    angle = math.atan2(y2-y1, x2-x1)
    for da in [0.45, -0.45]:
        ax = x2 - head*math.cos(angle-da)
        ay = y2 - head*math.sin(angle-da)
        draw.line([x2, y2, int(ax), int(ay)], fill=color, width=lw)

def grip_hand(draw, cx, cy, tight=True, scale=1.0):
    """Draw a simplified hand gripping a racket handle."""
    s = scale
    # handle rect
    hw, hh = int(16*s), int(80*s)
    draw.rounded_rectangle([cx-hw//2, cy-hh//2, cx+hw//2, cy+hh//2], radius=6, fill=(160,120,60))
    # fingers
    fc = RED_X if tight else GREEN_V
    knuckle_w = int(28*s)
    for i, fy in enumerate([cy-30, cy-10, cy+10, cy+30]):
        fy = int(fy*s*0.7 + cy*0.3)  # scale around cy
        fw = int((knuckle_w - i*2)*s)
        draw.ellipse([cx-fw//2-int(12*s), fy-int(10*s),
                      cx-hw//2+int(4*s),  fy+int(10*s)], fill=fc)
    # thumb
    draw.ellipse([cx-int(14*s), cy-int(38*s), cx+int(4*s), cy-int(18*s)], fill=fc)

def divider(draw, y, color=LIGHT_TEAL, lw=2):
    draw.line([60, y, W-60, y], fill=color, width=lw)


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 1 — HOOK / COVER
# ════════════════════════════════════════════════════════════════════════════
def slide_01():
    img = Image.new("RGB", (W, H), TEAL)
    draw = ImageDraw.Draw(img)

    # Background texture — subtle diagonal lines
    for i in range(-H, W, 60):
        draw.line([(i,0),(i+H,H)], fill=(20,100,110), width=1)

    # Big white card
    draw.rounded_rectangle([50, 120, W-50, H-90], radius=28, fill=CREAM)

    # Episode pill
    badge(draw, W//2, 175, "FIXES SERIES · EP. 1", font(26, bold=True), TEAL)

    # Main headline
    f_big = font(108, bold=True)
    draw.text((W//2 - 165, 210), "3", font=font(200, bold=True), fill=ORANGE)

    centered_text(draw, 390, "FIXES", font(90, bold=True), TEAL, max_w=W-80)
    divider(draw, 500, ORANGE, 4)

    centered_text(draw, 525, "for the", font(38), GREY, max_w=W-80)
    centered_text(draw, 580, "CRAMPED FOREHAND", font(52, bold=True), DARK, max_w=W-80)

    # Stick figure teaser
    stick_person(draw, 280, 850, scale=1.1, color=(180,180,180), elbow_tucked=True, label="BEFORE", label_color=RED_X)
    draw.text((390, 860), "→", font=font(80, bold=True), fill=ORANGE)
    stick_person(draw, 550+150, 850, scale=1.1, color=TEAL, elbow_tucked=False, label="AFTER", label_color=GREEN_V)

    centered_text(draw, 1080, "Your elbow is the problem.", font_oblique(36), GREY, max_w=W-100)
    centered_text(draw, 1130, "Here are the 3 fixes.", font(36, bold=True), ORANGE, max_w=W-100)

    swipe_nudge(draw, 0)
    top_bar(draw)
    img.save(OUT / "slide_01_cover.jpg", quality=95)
    print("  ✓ slide 01 — cover")


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 2 — THE PROBLEM
# ════════════════════════════════════════════════════════════════════════════
def slide_02():
    img = Image.new("RGB", (W, H), CREAM)
    draw = ImageDraw.Draw(img)
    top_bar(draw, "THE PROBLEM")

    badge(draw, W//2, 130, "WHY YOUR FOREHAND FEELS CRAMPED", font(28, bold=True), ORANGE)

    centered_text(draw, 175, "You squeeze the grip →\nshoulders tense up →\nelbow clamps to your ribs.", font(40, bold=True), DARK, max_w=W-100)

    divider(draw, 390, TEAL, 3)

    # Diagram: top-down view of body showing elbow tucked vs free
    # Side-view stick figures: bad then good
    # BAD panel
    bx = 210
    draw.rounded_rectangle([60, 420, bx*2-30, 900], radius=18, fill=(255,235,230))
    stick_person(draw, bx, 680, scale=1.05, color=DARK, elbow_tucked=True)
    cross_mark(draw, bx+60, 500)
    centered_text(draw, 905, "Elbow GLUED\nto ribs", font(32, bold=True), RED_X, max_w=320)

    # GOOD panel
    gx = W - 210
    draw.rounded_rectangle([gx-bx+30, 420, W-60, 900], radius=18, fill=(225,245,230))
    stick_person(draw, gx, 680, scale=1.05, color=TEAL, elbow_tucked=False)
    check_mark(draw, gx-60, 500)
    centered_text(draw, 905, "Elbow FREE\nto turn", font(32, bold=True), GREEN_V, max_w=320)

    # Arrow labels pointing at elbows
    draw.text((100, 430), "❌ WRONG", font=font(30, bold=True), fill=RED_X)
    draw.text((W-310, 430), "✅ RIGHT", font=font(30, bold=True), fill=GREEN_V)

    divider(draw, 1010, TEAL, 2)
    centered_text(draw, 1030, "No elbow room = no shoulder turn = no power.", font_oblique(34), DARK, max_w=W-80)
    centered_text(draw, 1095, "3 fixes coming up →", font(34, bold=True), ORANGE, max_w=W-80)

    swipe_nudge(draw, 1)
    img.save(OUT / "slide_02_problem.jpg", quality=95)
    print("  ✓ slide 02 — the problem")


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 3 — FIX 1: LOOSEN THE GRIP
# ════════════════════════════════════════════════════════════════════════════
def slide_03():
    img = Image.new("RGB", (W, H), CREAM)
    draw = ImageDraw.Draw(img)
    top_bar(draw, "FIX 1 OF 3")

    badge(draw, W//2, 130, "FIX 1 · LOOSEN THE GRIP", font(30, bold=True), ORANGE)

    centered_text(draw, 175, "A death-grip sends tension\nstraight up your arm and\nlocks the elbow to your body.", font(38), DARK, max_w=W-80)

    divider(draw, 370, TEAL, 3)

    # Two hand drawings: tight vs relaxed
    # Tight grip — left side
    draw.rounded_rectangle([60, 400, 480, 870], radius=18, fill=(255,235,230))
    grip_hand(draw, 270, 640, tight=True, scale=1.5)
    cross_mark(draw, 270, 430)
    draw.text((100, 400), "❌ TIGHT", font=font(32, bold=True), fill=RED_X)
    centered_text(draw, 878, "White knuckles\n= locked elbow", font(30, bold=True), RED_X, max_w=360)

    # Loose grip — right side
    draw.rounded_rectangle([600, 400, W-60, 870], radius=18, fill=(225,245,230))
    grip_hand(draw, 810, 640, tight=False, scale=1.5)
    check_mark(draw, 810, 430)
    draw.text((630, 400), "✅ LOOSE", font=font(32, bold=True), fill=GREEN_V)
    centered_text(draw, 878, "Relaxed grip\n= free arm", font(30, bold=True), GREEN_V, max_w=360)

    divider(draw, 1000, TEAL, 2)

    # The memorable cue
    draw.rounded_rectangle([60, 1018, W-60, 1120], radius=16, fill=TEAL)
    centered_text(draw, 1035, "Hold it like a bird —", font_oblique(38), WHITE, max_w=W-100)
    centered_text(draw, 1082, "firm enough not to drop it, soft enough not to crush it.", font(30), (200,235,238), max_w=W-100)

    swipe_nudge(draw, 2)
    img.save(OUT / "slide_03_fix1_grip.jpg", quality=95)
    print("  ✓ slide 03 — fix 1 grip")


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 4 — FIX 2: ELBOW IN FRONT
# ════════════════════════════════════════════════════════════════════════════
def slide_04():
    img = Image.new("RGB", (W, H), CREAM)
    draw = ImageDraw.Draw(img)
    top_bar(draw, "FIX 2 OF 3")

    badge(draw, W//2, 130, "FIX 2 · ELBOW IN FRONT", font(30, bold=True), ORANGE)

    centered_text(draw, 175, "If you start with the elbow\ntucked, you'll turn with it tucked.\nStart free — stay free.", font(38), DARK, max_w=W-80)

    divider(draw, 365, TEAL, 3)

    # Diagram: top-down body silhouette showing elbow position
    # We draw simplified top-down circles for body + elbow positions
    def top_down_torso(cx, cy, elbow_front=False, color=DARK):
        # body oval
        draw.ellipse([cx-35, cy-55, cx+35, cy+55], fill=color, outline=WHITE, width=2)
        # shoulders bar
        draw.line([cx-65, cy-40, cx+65, cy-40], fill=color, width=8)
        # elbow dots
        if elbow_front:
            # elbows in front of body
            ey = cy - 80
            draw.ellipse([cx-70, ey-14, cx-42, ey+14], fill=GREEN_V, outline=WHITE, width=2)
            draw.ellipse([cx+42, ey-14, cx+70, ey+14], fill=GREEN_V, outline=WHITE, width=2)
            draw.text((cx-90, ey+18), "free", font=font(24), fill=GREEN_V)
        else:
            # elbows pinned to ribs
            draw.ellipse([cx-68, cy-14, cx-40, cy+14], fill=RED_X, outline=WHITE, width=2)
            draw.ellipse([cx+40, cy-14, cx+68, cy+14], fill=RED_X, outline=WHITE, width=2)
            draw.text((cx-75, cy+18), "pinned", font=font(22), fill=RED_X)
        # head
        draw.ellipse([cx-20, cy-82, cx+20, cy-42], fill=color, outline=WHITE, width=2)

    # Bad position
    draw.rounded_rectangle([60, 390, 490, 840], radius=18, fill=(255,235,230))
    top_down_torso(275, 620, elbow_front=False, color=(60,60,60))
    cross_mark(draw, 275, 420)
    draw.text((90, 395), "❌ TUCKED", font=font(30, bold=True), fill=RED_X)
    centered_text(draw, 848, "Elbows pinned\nto ribs", font(30, bold=True), RED_X, max_w=380)
    draw.text((90, 730), "TOP VIEW", font=font(22), fill=GREY)

    # Good position
    draw.rounded_rectangle([590, 390, W-60, 840], radius=18, fill=(225,245,230))
    top_down_torso(805, 620, elbow_front=True, color=TEAL)
    check_mark(draw, 805, 420)
    draw.text((610, 395), "✅ IN FRONT", font=font(30, bold=True), fill=GREEN_V)
    centered_text(draw, 848, "Elbows slightly\nin front", font(30, bold=True), GREEN_V, max_w=380)
    draw.text((615, 730), "TOP VIEW", font=font(22), fill=GREY)

    divider(draw, 1000, TEAL, 2)

    draw.rounded_rectangle([60, 1018, W-60, 1120], radius=16, fill=TEAL)
    centered_text(draw, 1040, "Check your ready position first.", font(38, bold=True), WHITE, max_w=W-100)
    centered_text(draw, 1088, "The swing is already too late to fix it.", font(30), (200,235,238), max_w=W-100)

    swipe_nudge(draw, 3)
    img.save(OUT / "slide_04_fix2_elbow.jpg", quality=95)
    print("  ✓ slide 04 — fix 2 elbow")


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 5 — FIX 3: TURN WITH OTHER HAND (the big one)
# ════════════════════════════════════════════════════════════════════════════
def slide_05():
    img = Image.new("RGB", (W, H), CREAM)
    draw = ImageDraw.Draw(img)
    top_bar(draw, "FIX 3 OF 3  ·  THE BIG ONE")

    draw.rounded_rectangle([60, 85, W-60, 148], radius=14, fill=ORANGE)
    centered_text(draw, 97, "FIX 3 · TURN WITH YOUR OTHER HAND", font(28, bold=True), WHITE, max_w=W-80)

    centered_text(draw, 170, "Let your non-dominant hand\ntake the racket back.\nIt pulls the elbow UP and\nturns your shoulders for you.", font(37), DARK, max_w=W-80)

    divider(draw, 390, ORANGE, 3)

    # Side-view: bad (drop left hand early) vs good (both hands on turn)
    bx, gx = 220, W-220

    # Bad
    draw.rounded_rectangle([50, 415, 460, 910], radius=18, fill=(255,235,230))
    stick_person(draw, bx, 680, scale=1.0, color=DARK, elbow_tucked=True, second_hand=False, label="WRONG", label_color=RED_X)
    cross_mark(draw, bx+55, 445)
    draw.text((70, 420), "❌ Early drop", font=font(28, bold=True), fill=RED_X)
    centered_text(draw, 915, "Drop left hand\nearly → elbow\ncollapses", font(28), RED_X, max_w=360)

    # Good
    draw.rounded_rectangle([620, 415, W-50, 910], radius=18, fill=(225,245,230))
    stick_person(draw, gx, 680, scale=1.0, color=TEAL, elbow_tucked=False, second_hand=True, label="RIGHT", label_color=GREEN_V)
    check_mark(draw, gx-55, 445)
    draw.text((640, 420), "✅ Both hands", font=font(28, bold=True), fill=GREEN_V)
    centered_text(draw, 915, "Keep left hand\non racket →\nelbow stays free", font(28), GREEN_V, max_w=360)

    # Arrow showing the pull direction on good side
    arrow(draw, gx-20, 560, gx-60, 490, color=GREEN_V, lw=4)
    draw.text((gx-130, 460), "pulls\nelbow\nup", font=font(24, bold=True), fill=GREEN_V)

    divider(draw, 1045, TEAL, 2)
    draw.rounded_rectangle([60, 1060, W-60, 1145], radius=16, fill=TEAL)
    centered_text(draw, 1074, "This is the money fix.", font(38, bold=True), WHITE, max_w=W-100)
    centered_text(draw, 1118, "Both hands on the turn = full shoulder rotation.", font(28), (200,235,238), max_w=W-100)

    swipe_nudge(draw, 4)
    img.save(OUT / "slide_05_fix3_otherhand.jpg", quality=95)
    print("  ✓ slide 05 — fix 3 other hand")


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 6 — CHECKLIST RECAP
# ════════════════════════════════════════════════════════════════════════════
def slide_06():
    img = Image.new("RGB", (W, H), TEAL)
    draw = ImageDraw.Draw(img)

    # Background texture
    for i in range(-H, W, 60):
        draw.line([(i,0),(i+H,H)], fill=(20,100,110), width=1)

    draw.rounded_rectangle([50, 80, W-50, H-80], radius=28, fill=CREAM)
    top_bar(draw, "YOUR 3-STEP CHECKLIST")

    centered_text(draw, 110, "SAVE THIS. USE IT.", font(44, bold=True), ORANGE, max_w=W-80)
    divider(draw, 185, ORANGE, 4)

    items = [
        ("1", "LOOSEN THE GRIP",    "Hold it like a bird.\nLoose grip = free arm."),
        ("2", "ELBOW IN FRONT",     "Ready position check.\nStart free, stay free."),
        ("3", "TURN WITH\nOTHER HAND", "The big one.\nBoth hands back = full turn."),
    ]

    y = 210
    for num, title, desc in items:
        # Number circle
        nr = 44
        ncx, ncy = 115, y + 68
        draw.ellipse([ncx-nr, ncy-nr, ncx+nr, ncy+nr], fill=ORANGE)
        nb = draw.textbbox((0,0), num, font=font(52, bold=True))
        draw.text((ncx-(nb[2]-nb[0])//2, ncy-(nb[3]-nb[1])//2-4), num, font=font(52, bold=True), fill=WHITE)

        # Text block
        tx = 185
        draw.text((tx, y+10), title, font=font(46, bold=True), fill=TEAL)
        y2 = y + 70
        for line in desc.split("\n"):
            draw.text((tx, y2), line, font=font(32), fill=DARK)
            y2 += 40

        # Check circle (empty — viewer fills in mentally)
        cr = 22
        ccx, ccy = W-110, y+68
        draw.ellipse([ccx-cr, ccy-cr, ccx+cr, ccy+cr], outline=GREEN_V, width=4)
        check_mark(draw, ccx, ccy, size=14, lw=4)

        y += 230
        if y < H - 200:
            divider(draw, y - 20, LIGHT_TEAL, 2)

    centered_text(draw, 1165, "Do all 3 → cramped to clean.", font_oblique(38), ORANGE, max_w=W-80)

    swipe_nudge(draw, 5)
    img.save(OUT / "slide_06_checklist.jpg", quality=95)
    print("  ✓ slide 06 — checklist")


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 7 — CTA
# ════════════════════════════════════════════════════════════════════════════
def slide_07():
    img = Image.new("RGB", (W, H), DARK)
    draw = ImageDraw.Draw(img)

    # Diagonal teal accent strips
    for i in range(-H, W+200, 80):
        draw.line([(i,0),(i+H,H)], fill=(25,80,88), width=2)

    # Card
    draw.rounded_rectangle([50, 140, W-50, H-100], radius=28, fill=CREAM)
    top_bar(draw, "3 FIXES · EP.1 COMPLETE")

    # Big tick
    tcx, tcy = W//2, 360
    tr = 90
    draw.ellipse([tcx-tr, tcy-tr, tcx+tr, tcy+tr], fill=GREEN_V)
    check_mark(draw, tcx, tcy, size=50, lw=9)

    centered_text(draw, 475, "Your forehand goes\nfrom cramped to clean.", font(50, bold=True), TEAL, max_w=W-80)

    divider(draw, 630, ORANGE, 4)

    # Summary pills
    for i, txt in enumerate(["LOOSE GRIP", "ELBOW IN FRONT", "TWO-HAND TURN"]):
        px, py = W//2, 680 + i*100
        badge(draw, px, py, txt, font(34, bold=True), TEAL, WHITE, pad_x=36, pad_y=18)

    divider(draw, 1010, TEAL, 2)

    centered_text(draw, 1030, "Which fix do you need most?", font(38, bold=True), ORANGE, max_w=W-80)
    centered_text(draw, 1090, "Drop a 1, 2, or 3 in the comments.", font(34), DARK, max_w=W-100)

    draw.rounded_rectangle([100, 1155, W-100, 1235], radius=30, fill=ORANGE)
    centered_text(draw, 1172, "FOLLOW for Fix Series Ep.2 →", font(34, bold=True), WHITE, max_w=W-120)

    swipe_nudge(draw, 6)
    img.save(OUT / "slide_07_cta.jpg", quality=95)
    print("  ✓ slide 07 — CTA")


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"\n🎾  Generating carousel — output: {OUT.resolve()}\n")
    slide_01()
    slide_02()
    slide_03()
    slide_04()
    slide_05()
    slide_06()
    slide_07()
    print(f"\n✅  All 7 slides done → {OUT}/\n")
