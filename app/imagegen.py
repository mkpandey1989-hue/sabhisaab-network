"""AI chitra (Gemini image model) - 3D/cinematic background, taaki reel 'asli/premium' lage. Free na chale to chupchap
purana tareeka. Har chitra AI-label ke saath (description + platform flag).
v2.3.0 Step 2 (v11 se): Gemini quota khatam ho to CPU par 9 viral visual style (procedural_scene) + Pinterest 1000x1500
infographic pin (make_infographic_pin)."""
import base64
import math
import os
import pathlib
import random
import time
import requests
from PIL import Image, ImageDraw, ImageFilter
from . import state, text as T
from .config import BRANDS, VISUAL_STYLES, SITE
from .log import log

STYLE = ("vertical 9:16, cute 3D Pixar-style illustration, soft cinematic lighting, rich colours, high detail, "
         "Indian setting, family-friendly, NO text, NO letters, NO logos, NO real people or celebrities. Scene: ")


def _models():
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        return []
    c = state.get("img_models") or {}
    if time.time() - c.get("t", 0) < 86400:
        return c.get("m", [])
    try:
        j = requests.get("https://generativelanguage.googleapis.com/v1beta/models", params={"key": key, "pageSize": 200},
                         timeout=30).json()
        ms = [m["name"].split("/")[-1] for m in j.get("models", [])
              if "image" in m["name"] and "generateContent" in m.get("supportedGenerationMethods", [])]
        ms.sort(reverse=True)
    except Exception:
        ms = []
    state.put("img_models", {"t": time.time(), "m": ms})
    return ms


# ---------------- v2.3.0 Step 2: v11 ka procedural visual engine (jaisa ka taisa) ----------------
def _hex(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def procedural_scene(brand_key: str, style_name: str, scene_idx: int, prompt_text: str, out_path) -> pathlib.Path:
    """v9.0: High-detail procedural canvas matching all 9 reference screenshots + 4 puzzle board types."""
    W, H = 1080, 1920
    b = BRANDS.get(brand_key, BRANDS["money"])
    acc = _hex(b["accent"])
    c1, c2 = _hex(b["bg"][0]), _hex(b["bg"][1])
    rnd = random.Random(f"{brand_key}:{style_name}:{scene_idx}:{prompt_text[:40]}")

    if style_name in ("auto", "", None):
        styles = [s for s in VISUAL_STYLES if s != "auto"]
        style_name = styles[(scene_idx + abs(hash(brand_key))) % len(styles)]

    img = Image.new("RGB", (W, H), c1)
    d = ImageDraw.Draw(img, "RGBA")
    for y in range(0, H, 4):
        k = y / H
        col = tuple(int(c1[i] + (c2[i] - c1[i]) * k) for i in range(3))
        d.rectangle([0, y, W, y + 4], fill=col)

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)

    if style_name == "stick_mic":
        # Screenshot 1000180245 (aishpockettoons): Warm yellow top banner + clean studio + 2 stick figures + mic
        ld.rectangle([0, 0, W, 620], fill=(254, 248, 198, 55))
        ld.rectangle([0, 620, W, H], fill=(242, 238, 226, 28))
        # Left interviewer stick figure holding microphone
        lx, ly = 270, 1260
        ld.ellipse([lx - 90, ly - 210, lx + 90, ly - 30], fill=(255, 255, 255, 35), outline=(255, 255, 255, 220), width=10)
        ld.ellipse([lx + 15, ly - 140, lx + 30, ly - 120], fill=(255, 255, 255, 230))
        ld.ellipse([lx + 50, ly - 140, lx + 65, ly - 120], fill=(255, 255, 255, 230))
        ld.arc([lx + 5, ly - 105, lx + 60, ly - 70], start=10, end=170, fill=(255, 255, 255, 230), width=6)
        ld.line([(lx, ly - 30), (lx, ly + 220)], fill=(255, 255, 255, 220), width=12)
        ld.line([(lx, ly + 30), (lx + 145, ly - 30)], fill=(255, 255, 255, 220), width=10)
        ld.line([(lx, ly + 220), (lx - 65, ly + 380)], fill=(255, 255, 255, 220), width=10)
        ld.line([(lx, ly + 220), (lx + 65, ly + 380)], fill=(255, 255, 255, 220), width=10)
        # Microphone capsule & handle
        ld.line([(lx + 135, ly - 15), (lx + 170, ly - 85)], fill=(180, 180, 190, 240), width=14)
        ld.ellipse([lx + 145, ly - 125, lx + 195, ly - 75], fill=acc + (245,), outline=(255, 255, 255, 240), width=4)
        # Right interviewee stick figure
        rx, ry = 810, 1260
        ld.ellipse([rx - 90, ry - 210, rx + 90, ry - 30], fill=(255, 255, 255, 35), outline=(255, 255, 255, 220), width=10)
        ld.ellipse([rx - 55, ry - 140, rx - 40, ry - 120], fill=(255, 255, 255, 230))
        ld.ellipse([rx - 15, ry - 140, rx, ry - 120], fill=(255, 255, 255, 230))
        ld.line([(rx - 55, ry - 80), (rx - 5, ry - 80)], fill=(255, 255, 255, 230), width=6)
        ld.line([(rx, ry - 30), (rx, ry + 220)], fill=(255, 255, 255, 220), width=12)
        ld.line([(rx, ry + 220), (rx - 65, ry + 380)], fill=(255, 255, 255, 220), width=10)
        ld.line([(rx, ry + 220), (rx + 65, ry + 380)], fill=(255, 255, 255, 220), width=10)

    elif style_name == "liquid_match":
        # Screenshot 1000180246 (eatsintent): 6 Left & Right shelves with label plaques + glowing liquid splash waves
        wave_cols = [(255, 140, 0), (255, 45, 85), (255, 214, 10), (245, 245, 250), (210, 85, 45), (0, 229, 255)]
        for r_i in range(6):
            y_pos = 270 + r_i * 215
            col = wave_cols[(r_i + scene_idx) % len(wave_cols)]
            # Left & Right wooden shelves + metallic label plaques
            ld.rounded_rectangle([48, y_pos + 70, 345, y_pos + 112], radius=8, fill=(215, 200, 165, 165), outline=(255, 255, 255, 140), width=2)
            ld.rounded_rectangle([735, y_pos + 70, 1032, y_pos + 112], radius=8, fill=(215, 200, 165, 165), outline=(255, 255, 255, 140), width=2)
            # 3D icons on shelves
            ld.ellipse([145, y_pos - 25, 245, y_pos + 68], fill=col + (185,), outline=(255, 255, 255, 210), width=4)
            ld.rounded_rectangle([835, y_pos - 25, 935, y_pos + 68], radius=22, fill=acc + (185,), outline=(255, 255, 255, 210), width=4)
            # Liquid splash wave connecting Left to Right
            pts = []
            for step in range(28):
                t = step / 27.0
                px = 245 + t * 590
                py = y_pos + 20 + math.sin(t * math.pi * 2.2 + r_i) * 34
                pts.append((px, py))
            ld.line(pts, fill=col + (195,), width=16)
            # Splash droplets
            for dr in range(3):
                dx = 390 + dr * 140 + (r_i % 2) * 30
                dy = y_pos - 10 + (dr % 2) * 45
                ld.ellipse([dx - 7, dy - 7, dx + 7, dy + 7], fill=col + (210,))

    elif style_name == "organ_workers":
        # Screenshot 1000180244 (nutritionlab12): 6 horizontal shelves + miniature yellow-helmet workers repairing items
        for r_i in range(6):
            y_pos = 260 + r_i * 215
            ld.rounded_rectangle([55, y_pos, W - 55, y_pos + 175], radius=26, fill=(255, 255, 255, 28), outline=acc + (110,), width=3)
            # Left item + miniature yellow-helmet worker figure
            ld.ellipse([95, y_pos + 28, 215, y_pos + 148], fill=(235, 95, 75, 165), outline=(255, 255, 255, 190), width=3)
            # Worker with yellow helmet
            wx, wy = 235, y_pos + 85
            ld.ellipse([wx - 16, wy - 36, wx + 16, wy - 8], fill=(255, 215, 0, 240))
            ld.rounded_rectangle([wx - 14, wy - 8, wx + 14, wy + 38], radius=6, fill=(40, 120, 220, 230))
            # Center connector line with node
            ld.line([(360, y_pos + 88), (720, y_pos + 88)], fill=(255, 255, 255, 140), width=4)
            ld.ellipse([352, y_pos + 80, 368, y_pos + 96], fill=acc + (240,))
            # Right solution glass/icon
            ld.rounded_rectangle([840, y_pos + 22, 960, y_pos + 152], radius=16, fill=acc + (165,), outline=(255, 255, 255, 210), width=4)

    elif style_name == "mystery_box":
        # Screenshot 1000180247 & 1000180247_2 (tinykids333): Golden gift box + lifted lid + bright light beam + red ribbon bow
        # Inner magical golden light beam
        ld.ellipse([180, 460, 900, 1180], fill=(255, 220, 60, 115))
        # Box body
        ld.rounded_rectangle([260, 830, 820, 1260], radius=24, fill=(218, 160, 28, 215), outline=(255, 235, 130, 240), width=6)
        # Vertical red satin ribbon on box body
        ld.rectangle([505, 830, 575, 1260], fill=(205, 18, 38, 235))
        # Glowing gap between box and lifted lid
        ld.polygon([(260, 830), (820, 830), (840, 775), (240, 795)], fill=(255, 250, 160, 245))
        # Slightly tilted lifted box lid + red ribbon bow
        ld.polygon([(235, 795), (845, 765), (835, 685), (225, 715)], fill=(230, 175, 35, 230), outline=(255, 240, 150, 240))
        ld.ellipse([415, 610, 535, 705], fill=(215, 15, 35, 240), outline=(255, 180, 180, 200), width=4)
        ld.ellipse([545, 605, 665, 700], fill=(215, 15, 35, 240), outline=(255, 180, 180, 200), width=4)
        # Bokeh golden sparkles
        for _ in range(38):
            bx, by, br = rnd.randint(50, W - 50), rnd.randint(120, H - 200), rnd.randint(6, 24)
            ld.ellipse([bx - br, by - br, bx + br, by + br], fill=(255, 230, 110, rnd.randint(80, 195)))

    elif style_name == "festive_dhol":
        # Screenshot 1000180248 (happyminds_club9): Colorful triangle buntings + 3 cute characters + traditional Dhol drum
        for row_y in (190, 290):
            for bx in range(40, W - 40, 85):
                col = [(255, 75, 95, 210), (255, 215, 0, 210), (65, 220, 140, 210), (70, 175, 255, 210)][(bx // 85) % 4]
                ld.polygon([(bx, row_y), (bx + 75, row_y), (bx + 37, row_y + 78)], fill=col)
        # 3 cute festive characters + center Dhol drum
        for cx, cy, sc in ((220, 1120, 0.78), (860, 1120, 0.78), (540, 1080, 1.0)):
            r_head = int(125 * sc)
            ld.ellipse([cx - r_head, cy - r_head * 2, cx + r_head, cy], fill=(255, 215, 45, 215), outline=(255, 255, 255, 200), width=4)
            ld.rounded_rectangle([cx - r_head, cy, cx + r_head, cy + int(220 * sc)], radius=40, fill=(40, 165, 185, 210), outline=(255, 215, 0, 210), width=4)
        # Center Dhol Drum with crisscross ropes
        ld.rounded_rectangle([400, 1090, 680, 1275], radius=36, fill=(165, 95, 45, 240), outline=(255, 230, 160, 240), width=6)
        for lx_i in range(420, 660, 45):
            ld.line([(lx_i, 1090), (lx_i + 35, 1275)], fill=(255, 245, 210, 220), width=4)
            ld.line([(lx_i + 35, 1090), (lx_i, 1275)], fill=(255, 245, 210, 220), width=4)

    elif style_name == "fluffy_heart":
        # Screenshot 1000180249 (chittifunworld): Sea of soft red hearts + cute golden chick with pink bow & sparkling eyes
        for _ in range(26):
            hx, hy, hr = rnd.randint(40, W - 40), rnd.randint(140, H - 140), rnd.randint(80, 175)
            ld.ellipse([hx - hr, hy - hr, hx + hr, hy + hr], fill=(205, 18, 60, rnd.randint(85, 165)))
        # Center golden mascot head + pink bow + big sparkling eyes
        cx, cy = 540, 860
        ld.ellipse([cx - 210, cy - 210, cx + 210, cy + 210], fill=(255, 218, 65, 235), outline=(255, 240, 150, 220), width=6)
        # Pink ribbon bow on top
        ld.polygon([(cx, cy - 205), (cx - 115, cy - 265), (cx - 95, cy - 165)], fill=(255, 55, 145, 245))
        ld.polygon([(cx, cy - 205), (cx + 115, cy - 265), (cx + 95, cy - 165)], fill=(255, 55, 145, 245))
        ld.ellipse([cx - 24, cy - 228, cx + 24, cy - 182], fill=(255, 105, 180, 255))
        # Sparkling eyes
        for ex in (cx - 75, cx + 75):
            ld.ellipse([ex - 38, cy - 45, ex + 38, cy + 35], fill=(25, 15, 15, 250))
            ld.ellipse([ex - 16, cy - 28, ex + 6, cy - 6], fill=(255, 255, 255, 255))

    elif style_name == "living_object":
        # Screenshot 1000180250 (al_tadka2001): 3 anthropomorphic living crops (Paddy, Mustard, Pea pod) on village path
        ld.rectangle([0, int(H * 0.56), W, H], fill=(42, 125, 52, 110))
        ld.polygon([(310, H), (500, int(H * 0.56)), (580, int(H * 0.56)), (770, H)], fill=(198, 142, 88, 145))
        for idx_c, (cx, col_c) in enumerate(((230, (110, 210, 65)), (540, (240, 200, 40)), (850, (60, 195, 75)))):
            ld.rounded_rectangle([cx - 92, 620, cx + 92, 1190], radius=82, fill=col_c + (185,), outline=(255, 255, 255, 200), width=4)
            # Expressive eyes + teardrops
            ld.ellipse([cx - 48, 740, cx - 14, 778], fill=(20, 30, 20, 240))
            ld.ellipse([cx + 14, 740, cx + 48, 778], fill=(20, 30, 20, 240))
            ld.ellipse([cx - 38, 785, cx - 20, 815], fill=(0, 210, 255, 230))
            ld.ellipse([cx + 20, 785, cx + 38, 815], fill=(0, 210, 255, 230))
            if idx_c == 2:
                # 4 green peas inside the pea pod character
                for py_i in range(4):
                    ld.ellipse([cx - 42, 855 + py_i * 75, cx + 42, 925 + py_i * 75], fill=(95, 235, 85, 230), outline=(40, 130, 45, 220), width=3)

    elif style_name == "puzzle_grid":
        # Interactive Visual Puzzle Board: Auto-detects Cup Memory, Triangle Count, Odd-One-Out, or Color Pipe Match
        for gx in range(90, W, 180):
            ld.line([(gx, 220), (gx, H - 320)], fill=acc + (42,), width=2)
        for gy in range(260, H - 300, 180):
            ld.line([(60, gy), (W - 60, gy)], fill=acc + (42,), width=2)
        pt_low = (prompt_text or "").lower()
        if "कटोरी" in pt_low or "गेंद" in pt_low or "cup" in pt_low:
            # 3 Golden Cups (A, B, C) + glowing ball highlight
            for ci, cup_lbl in enumerate(("A", "B", "C")):
                cx = 230 + ci * 310
                cy = 1050
                ld.polygon([(cx - 105, cy + 90), (cx + 105, cy + 90), (cx + 75, cy - 110), (cx - 75, cy - 110)],
                           fill=(235, 180, 35, 225), outline=(255, 245, 170, 240))
                T.draw(ld, (cx - 18, cy - 45), cup_lbl, 64, (20, 20, 20))
            ball_x = 230 + (scene_idx % 3) * 310
            ld.ellipse([ball_x - 42, 1155, ball_x + 42, 1239], fill=(255, 230, 0, 245), outline=(255, 255, 255, 240), width=4)
        elif "त्रिभुज" in pt_low or "आकृति" in pt_low:
            # Subdivided Optical Triangle Grid for counting triangles
            top_pt = (540, 300)
            bl_pt, br_pt = (180, 1180), (900, 1180)
            ld.polygon([top_pt, bl_pt, br_pt], outline=acc + (235,), fill=(255, 255, 255, 22))
            for k_seg in range(1, 5):
                bx = bl_pt[0] + int((br_pt[0] - bl_pt[0]) * (k_seg / 5.0))
                ld.line([top_pt, (bx, 1180)], fill=(255, 230, 0, 210), width=5)
            ld.line([(300, 740), (780, 740)], fill=(0, 229, 255, 210), width=5)
        else:
            # Tangled Color Pipes (1, 2, 3, 4 -> Box A, B, C, D)
            cols = [(255, 55, 85), (0, 210, 255), (0, 245, 135), (255, 215, 0)]
            perm = [1, 3, 0, 2]
            for i in range(4):
                c_top = cols[i]
                x1 = 180 + i * 240
                x2 = 180 + perm[(i + scene_idx) % 4] * 240
                ld.ellipse([x1 - 52, 310, x1 + 52, 414], fill=c_top + (210,), outline=(255, 255, 255, 230), width=5)
                T.draw(ld, (x1 - 16, 326), str(i + 1), 54, (15, 15, 15))
                ld.rounded_rectangle([x2 - 58, 1140, x2 + 58, 1250], radius=20, fill=(20, 28, 42, 220), outline=c_top + (230,), width=5)
                T.draw(ld, (x2 - 18, 1160), chr(65 + i), 54, (255, 255, 255))
                pts = []
                for st_i in range(24):
                    t = st_i / 23.0
                    px = (1 - t) * x1 + t * x2 + math.sin(t * math.pi * 2 + i) * 65
                    py = 414 + t * (1140 - 414)
                    pts.append((px, py))
                ld.line(pts, fill=c_top + (185,), width=14)

    else:
        # mascot_3d (Screenshot 1000180243 kidmimytv): Giant 3D floating badge at top + cute 3D mascot holding bright orb
        ld.rounded_rectangle([310, 250, 770, 560], radius=48, fill=(25, 135, 255, 175), outline=(255, 255, 255, 220), width=6)
        T.draw(ld, (485, 285), "₹" if brand_key in ("money", "deals") else "अ", 160, (255, 255, 255), stroke=6, stroke_fill=(0, 40, 95))
        # Cute 3D mascot body + bright red pomegranate/treasure orb on right hand
        ld.ellipse([260, 760, 640, 1160], fill=(65, 205, 85, 210), outline=(255, 255, 255, 210), width=5)
        ld.ellipse([400, 880, 495, 975], fill=(255, 195, 30, 240))
        ld.ellipse([590, 620, 920, 950], fill=(235, 35, 55, 225), outline=(255, 220, 180, 220), width=6)

    img = Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")
    out_p = pathlib.Path(out_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_p, "PNG")
    return out_p


def make_infographic_pin(brand_key: str, title: str, lines_list: list, out_path) -> pathlib.Path:
    """v9.0 Pinterest 12-Nov-2026 Policy Safe: Generates a 1000x1500 Study Guide / Checklist Infographic Pin."""
    PW, PH = 1000, 1500
    b = BRANDS.get(brand_key, BRANDS["money"])
    acc = _hex(b["accent"])
    c1, c2 = _hex(b["bg"][0]), _hex(b["bg"][1])
    im = Image.new("RGB", (PW, PH), c1)
    d = ImageDraw.Draw(im, "RGBA")
    for y in range(0, PH, 4):
        k = y / PH
        d.rectangle([0, y, PW, y + 4], fill=tuple(int(c1[i] + (c2[i] - c1[i]) * k) for i in range(3)))
    d.rounded_rectangle([36, 36, PW - 36, PH - 36], radius=36, outline=acc + (220,), width=6)
    d.rounded_rectangle([70, 75, PW - 70, 235], radius=28, fill=(0, 0, 0, 150), outline=acc + (180,), width=3)
    sz_t, t_lns = T.fit(title[:80], PW - 200, 130, start=54, smallest=34)
    ty = 95
    for ln in t_lns:
        T.draw(d, ((PW - T.width(ln, sz_t)) / 2, ty), ln, sz_t, acc, stroke=3, stroke_fill=(0, 0, 0))
        ty += int(sz_t * 1.28)
    y_card = 270
    for idx, item_txt in enumerate((lines_list or [])[:5], 1):
        d.rounded_rectangle([70, y_card, PW - 70, y_card + 195], radius=24, fill=(255, 255, 255, 25), outline=acc + (120,), width=2)
        d.ellipse([95, y_card + 55, 175, y_card + 135], fill=acc)
        T.draw(d, (122, y_card + 64), str(idx), 46, (15, 15, 15))
        sz_b, b_lns = T.fit(item_txt[:110], PW - 310, 155, start=38, smallest=26)
        by = y_card + 35
        for bln in b_lns:
            T.draw(d, (205, by), bln, sz_b, (255, 255, 255), stroke=2, stroke_fill=(0, 0, 0))
            by += int(sz_b * 1.3)
        y_card += 218
    d.rounded_rectangle([70, PH - 145, PW - 70, PH - 65], radius=24, fill=acc)
    T.draw(d, ((PW - T.width(f"पूरा कैलकुलेटर व गाइड: {SITE}/", 38)) / 2, PH - 130), f"पूरा कैलकुलेटर व गाइड: {SITE}/", 38, (15, 15, 15))
    out_p = pathlib.Path(out_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    im.save(out_p, "JPEG", quality=93)
    return out_p



LAST_KIND = {"k": ""}


def _procedural(prompt, out_path, brand_key, style_name, scene_idx):
    try:
        st = style_name if style_name not in ("auto", "", None) else (state.get("visual_style") or "auto")
        p = str(procedural_scene(brand_key, st, scene_idx, prompt, out_path))
        LAST_KIND["k"] = "procedural"
        return p
    except Exception as e:
        log(f"procedural_scene fallback: {e}")
        return None


def clean_prompt(p):
    """v2.4.2: chitra-prompt se ank, ₹, %, # aur Devanagari ank hatao - warna AI unhe chitra mein bada likh deta ('5000')."""
    import re as _re
    p = _re.sub(r"[₹$%#@*0-9०-९]+", " ", str(p or ""))
    p = _re.sub(r"\b(rs|inr|lakh|crore|hazaar|hazar)\b", " ", p, flags=_re.I)
    return _re.sub(r"\s{2,}", " ", p).strip()


def make(prompt, out_path, brand_key="money", style_name="auto", scene_idx=0, procedural_fallback=True):
    """Pehle Gemini 3D chitra; seema/galti par (procedural_fallback) CPU wala 9-style visual (v11 jaisa)."""
    prompt = clean_prompt(prompt) + " (illustration only, no text, no numbers, no letters)"
    LAST_KIND["k"] = ""
    if style_name not in ("auto", "", None, "ai"):        # owner ne Studio mein koi khaas style pakka kiya -> wahi
        return _procedural(prompt, out_path, brand_key, style_name, scene_idx)
    if time.time() < state.get("img_block_until", 0):
        cf = cf_image(prompt, out_path)           # v2.4.0: Gemini band -> pehle Cloudflare AI-art
        if cf:
            return cf
        return _procedural(prompt, out_path, brand_key, style_name, scene_idx) if procedural_fallback else None
    from .guard import scrub_for_ai               # v2.3.0: Gemini Blindfold
    prompt = scrub_for_ai(prompt)
    key = os.environ.get("GEMINI_API_KEY")
    pathlib.Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    zero = q429 = n = 0
    for m in _models():
        n += 1
        try:
            r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent",
                              params={"key": key}, timeout=120,
                              json={"contents": [{"parts": [{"text": STYLE + prompt}]}],
                                    "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]}})
            j = r.json()
            if r.status_code != 200:
                q429 += r.status_code == 429
                zero += "limit: 0" in str(j) or "limit:0" in str(j)
                log(f"img {m}: {r.status_code} {str(j)[:120]}")
                continue
            for p in j["candidates"][0]["content"]["parts"]:
                if p.get("inlineData"):
                    with open(out_path, "wb") as f:
                        f.write(base64.b64decode(p["inlineData"]["data"]))
                    state.put("img_last_model", m)
                    LAST_KIND["k"] = "ai"
                    return out_path
        except Exception as e:
            log(f"img {m}: {e}")
    # v2.1.2: free account par image model ki seema aksar 0 hoti hai (audit: 3 din mein ~48 bekaar koshish)
    wait = 7 * 86400 if zero else (24 * 3600 if n and q429 == n else 6 * 3600)
    state.put("img_block_until", time.time() + wait)
    cf = cf_image(prompt, out_path)               # v2.4.0: Gemini seema khatam -> Cloudflare AI-art
    if cf:
        return cf
    return _procedural(prompt, out_path, brand_key, style_name, scene_idx) if procedural_fallback else None


# ---------------- v2.4.0: AI-ART bina Gemini - Cloudflare Workers AI (Flux) - owner ke CF account ki free roz ki seema ----------------
CF_IMG_MODELS = ["@cf/black-forest-labs/flux-1-schnell", "@cf/stabilityai/stable-diffusion-xl-base-1.0"]
STYLE_TAIL = (", cinematic 3D render, dramatic neon rim lighting, glossy, high detail, dark moody background, "
              "centered subject, clean surfaces, absolutely no text, no letters, no numbers, no words, no typography, "
              "no signs, no watermark, no logo")


def cf_image(prompt, out_path):
    """Cloudflare Workers AI se chitra. -> path ya None. Seema/galti par 3 ghante aaram."""
    if time.time() < (state.get("cf_img_cool") or 0):
        return None
    try:
        from .website import _cf
        from .guard import scrub_for_ai
        tok, acc = _cf()
        if not (tok and acc):
            return None
        p = clean_prompt(scrub_for_ai(prompt))[:900] + STYLE_TAIL
        for m in CF_IMG_MODELS:
            r = requests.post(f"https://api.cloudflare.com/client/v4/accounts/{acc}/ai/run/{m}", timeout=120,
                              headers={"Authorization": f"Bearer {tok}"}, json={"prompt": p, "steps": 4} if "flux" in m else {"prompt": p})
            ct = r.headers.get("content-type", "")
            data = None
            if r.status_code == 200 and "json" in ct:
                j = r.json()
                b64 = (j.get("result") or {}).get("image")
                if b64:
                    data = base64.b64decode(b64)
            elif r.status_code == 200 and ct.startswith("image/"):
                data = r.content
            if data and len(data) > 5000:
                pathlib.Path(out_path).parent.mkdir(parents=True, exist_ok=True)
                with open(out_path, "wb") as fh:
                    fh.write(data)
                state.update("cf_img_count", lambda n: (n or 0) + 1, 0)
                LAST_KIND["k"] = "cf_ai"
                return str(out_path)
            if r.status_code in (429, 403) or "limit" in r.text.lower():
                break
        state.put("cf_img_cool", time.time() + 3 * 3600)
    except Exception as e:
        log(f"cf_image: {e}")
        state.put("cf_img_cool", time.time() + 3600)
    return None
