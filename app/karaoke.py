"""v2.9.0 (5 Nov plan V4): KARAOKE SUBTITLE - jo shabd bola ja raha hai wahi peela chamke (awaaz ke saath padhna aasaan,
bina awaaz dekhne walon ke liye bhi). Shorts mein site-patti aur neeche ke brand-naam ke beech (y ~1462) - YouTube ke neeche
wale buttons/caption ke upar. Har shabd ka samay us scene ki asli awaaz ki lambai se (akshar ke hisaab se baanta).
Kuch bhi galat ho to video bina subtitle ke banti hai - schedule kabhi nahi tootta. Flash nahi (sirf rang badalta hai).
"""
import re

from PIL import Image, ImageDraw

from . import text as T

FPS = 10
Y = 1462
BOX_H = 96
MAX_WORDS = 5


def _words(say):
    s = re.sub(r"https?://\S+|[#@]\S+", "", str(say or ""))
    s = re.sub(r"[\"“”'‘’()\[\]{}<>|*_~`]", "", s)
    return [w for w in s.split() if w.strip(".,!?।:;-–—")]


_SENT_END = re.compile(r"[।!?…]+$")


def _groups(ws):
    """v3.1.1 (owner ki reel 12 Nov): pehle har 5 shabd par patti kat-ti thi - vaakya beech se toot-ta tha
    ('जवाब कमेंट में लिखिए। दो' | 'गलत विकल्प हटा दिए अब' | 'बताओ!'). Ab: patti VAAKYA ke ant par hi badalti hai; lamba vaakya
    barabar hisson mein (9 shabd = 5+4, 6 = 3+3) taaki akela shabd na latke. -> [[shabd, ...], ...]"""
    sents, cur = [], []
    for w in ws:
        cur.append(w)
        if _SENT_END.search(w):
            sents.append(cur)
            cur = []
    if cur:
        sents.append(cur)
    out = []
    for snt in sents:
        n = len(snt)
        parts = -(-n // MAX_WORDS)                # ceil
        base, extra = divmod(n, parts)
        i = 0
        for g in range(parts):
            size = base + (1 if g < extra else 0)
            out.append(snt[i:i + size])
            i += size
    return out


def timeline(scenes, durs):
    """-> [(start, end, group_words, idx_in_group)] har shabd ka (scene ki awaaz ke andar akshar ke hisaab se)."""
    out, st = [], 0.0
    for sc, d in zip(scenes, durs):
        ws = _words(sc.get("say") or sc.get("show"))
        if ws and d > 0.4:
            lead, tail = 0.12, 0.15              # TTS shuru/ant ki chhoti chuppi
            span = max(0.2, d - lead - tail - float(sc.get("hold") or 0))    # v3.1.1: sochne ki chuppi (hold) mein shabd nahi phailte
            wt = [max(2, len(w)) for w in ws]
            tot = float(sum(wt))
            t = st + lead
            gi = 0
            for grp in _groups(ws):
                for k, w in enumerate(grp):
                    dt = span * wt[gi + k] / tot
                    out.append((round(t, 3), round(t + dt, 3), grp, k))
                    t += dt
                gi += len(grp)
        st += d
    return out


def frame(grp, k, W=1080):
    """Ek subtitle patti (RGBA): bola ja raha shabd peela, baaki safed."""
    img = Image.new("RGBA", (W, BOX_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    sz = 50
    line = " ".join(grp)
    while sz > 30 and T.width(line, sz) > W - 160:
        sz -= 2
    tw = T.width(line, sz)
    x0 = (W - tw) / 2
    d.rounded_rectangle([x0 - 28, 8, x0 + tw + 28, BOX_H - 8], radius=30, fill=(0, 0, 0, 165))
    x = x0
    for i, w in enumerate(grp):
        col = (255, 214, 0) if i == k else (255, 255, 255)
        T.draw(d, (x, (BOX_H - sz * 1.45) / 2), w, sz, col)
        x += T.width(w + " ", sz)
    return img


def make_sequence(scenes, durs, outdir, total, W=1080):
    """outdir/k_00001.png ... (10 fps). Khaali samay = paardarshi. -> (pattern, frame_ginti)"""
    tl = timeline(scenes, durs)
    blank = Image.new("RGBA", (W, BOX_H), (0, 0, 0, 0))
    n = int(total * FPS) + 1
    cache, j = {}, 0
    for f in range(n):
        t = f / FPS
        while j < len(tl) and tl[j][1] <= t:
            j += 1
        cur = tl[j] if j < len(tl) and tl[j][0] <= t < tl[j][1] else None
        key = (tuple(cur[2]), cur[3]) if cur else None
        if key not in cache:
            cache[key] = frame(cur[2], cur[3], W) if cur else blank
        cache[key].save(f"{outdir}/k_{f:05d}.png")
    return f"{outdir}/k_%05d.png", n
