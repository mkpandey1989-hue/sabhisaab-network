"""v2.3.0 Step 3 (v11 se, sudhaar ke saath): Procedural Audio, 45+ Phonetic Dictionary, Indian Number-to-Words Converter,
Dynamic Prosody Pacing, Shepard Riser + Pin-Drop Silence + Impact Hit & Sidechain BGM Mixer (WA0003 Sec 6 & 8).
100% Zero Copyright Risk: Har sound numpy math se real-time banta hai."""
import math
import re
import numpy as np

SR = 24000

# 45+ Hindi Phonetic Dictionary for Finance, Sarkari Exams, Units & Tech Acronyms
PRONOUNCE_MAP = {
    r"\b24K\b": "चौबीस कैरेट",
    r"\b22K\b": "बाईस कैरेट",
    r"\b18K\b": "अठारह कैरेट",
    r"\bkW\b": "किलोवाट",
    r"\bEMI\b": "ई एम आई",
    r"\bSIP\b": "एस आई पी",
    r"\bFD\b": "एफ डी",
    r"\bRD\b": "आर डी",
    r"\bPPF\b": "पी पी एफ",
    r"\bNPS\b": "एन पी एस",
    r"\bEPFO\b": "ई पी एफ ओ",
    r"\bEPF\b": "ई पी एफ",
    r"\bRBI\b": "आर बी आई",
    r"\bSEBI\b": "सेबी",
    r"\bDICGC\b": "डी आई सी जी सी",
    r"\bCIBIL\b": "सिबिल",
    r"\bGST\b": "जी एस टी",
    r"\bMRP\b": "एम आर पी",
    r"\bOTP\b": "ओ टी पी",
    r"\bUPI\b": "यू पी आई",
    r"\bATM\b": "ए टी एम",
    r"\bKYC\b": "के वाई सी",
    r"\bPAN\b": "पैन",
    r"\bITR\b": "आई टी आर",
    r"\bTDS\b": "टी डी एस",
    r"\bLTCG\b": "एल टी सी जी",
    r"\bSTCG\b": "एस टी सी जी",
    r"\bSSY\b": "एस एस वाई",
    r"\bSCSS\b": "एस सी एस एस",
    r"\bNSC\b": "एन एस सी",
    r"\bKVP\b": "के वी पी",
    r"\bIQ\b": "आई क्यू",
    r"\bGK\b": "जी के",
    r"\bLED\b": "एल ई डी",
    r"\bAC\b": "ए सी",
    r"\bHUID\b": "एच यू आई डी",
    r"\bIBPS\b": "आई बी पी एस",
    r"\bSBI\b": "एस बी आई",
    r"\bPO\b": "पी ओ",
    r"\bSSC\b": "एस एस सी",
    r"\bCGL\b": "सी जी एल",
    r"\bCHSL\b": "सी एच एस एल",
    r"\bMTS\b": "एम टी एस",
    r"\bRRB\b": "आर आर बी",
    r"\bNTPC\b": "एन टी पी सी",
    r"\bUKPSC\b": "यू के पी एस सी",
    r"\bUKSSSC\b": "यू के एस एस एस सी",
    r"\bBODMAS\b": "बोडमास",
    r"\bhttps?://sabhisaab\.com/?\b": "सब हिसाब डॉट कॉम",
    r"\bsabhisaab\.com\b": "सब हिसाब डॉट कॉम",
}

_HI_0_99 = [
    "शून्य", "एक", "दो", "तीन", "चार", "पाँच", "छह", "सात", "आठ", "नौ",
    "दस", "ग्यारह", "बारह", "तेरह", "चौदह", "पंद्रह", "सोलह", "सत्रह", "अठारह", "उन्नीस",
    "बीस", "इक्कीस", "बाईस", "तेईस", "चौबीस", "पच्चीस", "छब्बीस", "सत्ताईस", "अट्ठाईस", "उनतीस",
    "तीस", "इकतीस", "बत्तीस", "तैंतीस", "चौंतीस", "पैंतीस", "छत्तीस", "सैंतीस", "अड़तीस", "उनतालीस",
    "चालीस", "इकतालीस", "बयालीस", "तैंतालीस", "चवालीस", "पैंतालीस", "छियालीस", "सैंतालीस", "अड़तालीस", "उनचास",
    "पचास", "इक्यावन", "बावन", "तिरेपन", "चौवन", "पचपन", "छप्पन", "सत्तावन", "अट्ठावन", "उनसठ",
    "साठ", "इकसठ", "बासठ", "तिरेसठ", "चौंसठ", "पैंसठ", "छियासठ", "सड़सठ", "अड़सठ", "उनहत्तर",
    "सत्तर", "इकहत्तर", "बहत्तर", "तिहत्तर", "चौहत्तर", "पचहत्तर", "छिहत्तर", "सतहत्तर", "अठहत्तर", "उनासी",
    "अस्सी", "इक्यासी", "बयासी", "तिरासी", "चौरासी", "पचासी", "छियासी", "सतासी", "अठासी", "नवासी",
    "नब्बे", "इक्यानबे", "बानबे", "तिरानबे", "चौरानबे", "पंचानबे", "छियानबे", "सत्तानबे", "अट्ठानबे", "निन्यानबे"
]


def int_to_hindi(n: int) -> str:
    """Converts integer (0 to 99,99,999) into natural Indian-system Hindi words (सौ, हज़ार, लाख)."""
    if n < 0:
        return "ऋण " + int_to_hindi(-n)
    if n < 100:
        return _HI_0_99[n]
    parts = []
    if n >= 100000:
        lakhs = n // 100000
        parts.append(int_to_hindi(lakhs) + " लाख")
        n %= 100000
    if n >= 1000:
        th = n // 1000
        parts.append(int_to_hindi(th) + " हज़ार")
        n %= 1000
    if n >= 100:
        h = n // 100
        parts.append(_HI_0_99[h] + " सौ")
        n %= 100
    if n > 0:
        parts.append(_HI_0_99[n])
    return " ".join(parts)


def _on(k, default=True):
    """Owner ki awaaz setting (state 'awaaz'): sfx, music, phonetic, pace, trim."""
    try:
        from . import state
        return bool((state.get("awaaz") or {}).get(k, default))
    except Exception:
        return default


def normalize_pronunciation(text: str) -> str:
    """Replaces English acronyms, math symbols (², ³, %, ₹, ×, ÷), and numbers with pure Devanagari phonetics.
    v2.3.0 sudhaar: acronym sirf BADE akshar mein (Hinglish 'po', 'pan', 'ac' shabd nahi badalte); 7.5 -> saat dashamlav paanch."""
    if not isinstance(text, str):
        return ""
    if not _on("phonetic"):
        return text
    out = text
    # 1. Replace URLs and acronyms first
    for pat, rep in PRONOUNCE_MAP.items():
        out = re.sub(pat, rep, out, flags=re.I if "sabhisaab" in pat else 0)
    # 1b. dashamlav (7.5%, 8.25) - ank alag-alag na tootein
    out = re.sub(r"\b(\d{1,7})\.(\d{1,3})\b",
                 lambda m: int_to_hindi(int(m.group(1))) + " दशमलव " + " ".join(_HI_0_99[int(c)] for c in m.group(2)), out)
    # 2. Currency ₹50,000 -> 50000 रुपये
    out = re.sub(r"₹\s*([0-9][0-9,]*)", r"\1 रुपये", out)
    # 3. Math powers & operators
    out = out.replace("²", " का वर्ग ").replace("³", " का घन ")
    out = out.replace("%", " प्रतिशत ").replace("×", " गुणा ").replace("÷", " भाग ").replace("=", " बराबर ")
    # 4. Convert comma-formatted or plain numbers up to 7 digits into Hindi words
    def _num_rep(m):
        raw = m.group(0).replace(",", "")
        if not raw.isdigit():
            return m.group(0)
        val = int(raw)
        if val > 9999999:
            return raw
        return int_to_hindi(val)
    out = re.sub(r"\b\d{1,2}(?:,\d{2,3})+\b|\b\d{1,6}\b", _num_rep, out)
    return re.sub(r"\s+", " ", out).strip()


def scene_voice_speed(scene_idx: int, total_scenes: int, scene_text: str, base_speed: float = 1.0) -> float:
    if not _on("pace"):
        return round(base_speed, 2)
    return _scene_voice_speed(scene_idx, total_scenes, scene_text, base_speed)


def _scene_voice_speed(scene_idx: int, total_scenes: int, scene_text: str, base_speed: float = 1.0) -> float:
    """WA0003 Sec 6 Dynamic Prosody:
    - Scene 0 (Hook): 1.06x energetic
    - Answer Reveal ('सही जवाब'/'सबक'): 0.95x deliberate emphasis
    - Standard/Countdown scenes: 1.00x clear."""
    txt = (scene_text or "").lower()
    if scene_idx == 0:
        return round(base_speed * 1.06, 2)
    if any(w in txt for w in ("सही जवाब", "सही उत्तर", "सबक")) and scene_idx >= total_scenes - 2:
        return round(base_speed * 0.95, 2)
    return round(base_speed, 2)


def trim_silence(audio: np.ndarray, sr: int = SR, threshold: float = 0.009, max_silence_sec: float = 0.15) -> np.ndarray:
    """Trims dead air > 0.15s and normalizes voice peak to 0.92."""
    if audio is None or len(audio) == 0 or not _on("trim"):
        return audio
    is_loud = np.abs(audio) > threshold
    if not np.any(is_loud):
        return audio
    max_sil = int(sr * max_silence_sec)
    # v2.3.0: wahi niyam, numpy se tez (har chup ki lambi patti mein max_sil ke baad wale sample hatao)
    quiet = ~is_loud
    idx = np.arange(len(audio))
    last_loud = np.maximum.accumulate(np.where(is_loud, idx, -1))
    run_len = idx - last_loud
    keep = ~(quiet & (run_len > max_sil))
    trimmed = audio[keep] if np.any(keep) else audio
    peak = float(np.max(np.abs(trimmed)))
    if peak > 1e-4:
        trimmed = (trimmed / peak) * 0.92
    return trimmed.astype("float32")


def brand_sting(sr: int = SR, seed: int = 0) -> np.ndarray:
    """0.30s signature harmonic glow sting at the start of every reel."""
    dur = 0.30
    t = np.linspace(0, dur, int(sr * dur), endpoint=False, dtype="float32")
    f_base = 528.0 + (seed % 7) * 4.0
    env = np.exp(-t * 9.5).astype("float32")
    wave = (0.55 * np.sin(2 * math.pi * f_base * t)
            + 0.30 * np.sin(2 * math.pi * (f_base * 1.5) * t)
            + 0.15 * np.sin(2 * math.pi * (f_base * 2.0) * t)) * env * 0.14
    return wave.astype("float32")


def tick_chime(sr: int = SR) -> np.ndarray:
    """0.08s soft transition pop between scenes."""
    dur = 0.08
    t = np.linspace(0, dur, int(sr * dur), endpoint=False, dtype="float32")
    env = np.exp(-t * 42.0).astype("float32")
    wave = np.sin(2 * math.pi * 880.0 * t) * env * 0.08
    return wave.astype("float32")


def glitch_pop_sfx(sr: int = SR) -> np.ndarray:
    """0.11s crisp pattern-interrupt micro-glitch for Bonus Question / Mid-Video Twist."""
    dur = 0.11
    n = int(sr * dur)
    t = np.linspace(0, dur, n, endpoint=False, dtype="float32")
    env = np.exp(-t * 32.0).astype("float32")
    wave = (0.6 * np.sin(2 * math.pi * 1320.0 * t) + 0.4 * np.sin(2 * math.pi * 1980.0 * t)) * env * 0.09
    return wave.astype("float32")


def whoosh_sfx(sr: int = SR, dur: float = 0.18) -> np.ndarray:
    """Procedural frequency-swept whoosh for scene transitions."""
    n = int(sr * dur)
    t = np.linspace(0, dur, n, endpoint=False, dtype="float32")
    env = np.sin(math.pi * (t / dur)).astype("float32")
    freq = np.linspace(180.0, 620.0, n, dtype="float32")
    phase = 2 * math.pi * np.cumsum(freq) / sr
    wave = np.sin(phase).astype("float32") * env * 0.06
    return wave


def tick_tock_loop(dur_sec: float, sr: int = SR) -> np.ndarray:
    """Subtle dopamine tick-tock clock pulse (120 BPM) mixed under countdown/thinking scenes."""
    n = max(1, int(sr * dur_sec))
    out = np.zeros(n, dtype="float32")
    step = int(sr * 0.5)
    pulse_len = min(int(sr * 0.04), step // 2)
    t_p = np.linspace(0, 0.04, pulse_len, endpoint=False, dtype="float32")
    env = np.exp(-t_p * 65.0).astype("float32")
    for idx, pos in enumerate(range(0, n - pulse_len, step)):
        freq = 1050.0 if idx % 2 == 0 else 780.0
        out[pos:pos + pulse_len] += np.sin(2 * math.pi * freq * t_p).astype("float32") * env * 0.055
    return out


def shepard_riser_reveal(sr: int = SR) -> np.ndarray:
    """WA0003 Sec 8 Reveal Formula: 0.65s Shepard Riser -> 0.18s Pin-Drop Silence -> 0.22s Impact Hit."""
    r_n = int(sr * 0.65)
    t_r = np.linspace(0, 0.65, r_n, endpoint=False, dtype="float32")
    f1 = np.linspace(220.0, 440.0, r_n, dtype="float32")
    f2 = np.linspace(440.0, 880.0, r_n, dtype="float32")
    riser = (0.5 * np.sin(2 * math.pi * np.cumsum(f1) / sr)
             + 0.4 * np.sin(2 * math.pi * np.cumsum(f2) / sr)).astype("float32") * (t_r / 0.65) * 0.09
    sil = np.zeros(int(sr * 0.18), dtype="float32")
    i_n = int(sr * 0.22)
    t_i = np.linspace(0, 0.22, i_n, endpoint=False, dtype="float32")
    env_i = np.exp(-t_i * 18.0).astype("float32")
    impact = (0.7 * np.sin(2 * math.pi * 110.0 * t_i) + 0.3 * np.sin(2 * math.pi * 660.0 * t_i)) * env_i * 0.14
    return np.concatenate([riser, sil, impact]).astype("float32")


def mix_scene_audio(voice_arr: np.ndarray, scene_idx: int, total_scenes: int, scene_text: str, sr: int = SR) -> np.ndarray:
    """Applies scene-aware procedural SFX (Brand sting on scene 0, tick-tock on countdown, glitch pop on bonus,
    Shepard riser + pin-drop silence + impact on reveal) plus sidechain-ducked harmonic pad (-18 dB under voice)."""
    if voice_arr is None or len(voice_arr) == 0:
        return voice_arr
    if not _on("sfx") and not _on("music"):
        return voice_arr
    txt = (scene_text or "").lower()
    if not _on("sfx"):
        return _pad(voice_arr, sr)
    if any(w in txt for w in ("सेकंड", "सोचिए", "टिक", "विकल्प", "बताइए", "?", "कहाँ", "second", "sochiye")) and scene_idx in (1, 2):
        tt = tick_tock_loop(len(voice_arr) / sr, sr)
        if len(tt) == len(voice_arr):
            voice_arr = voice_arr + tt
    if scene_idx == 0:
        voice_arr = np.concatenate([brand_sting(sr, len(txt)), voice_arr])
    elif any(w in txt for w in ("सही जवाब", "सही उत्तर", "सबक:", "उदाहरण:")) and scene_idx >= total_scenes - 2:
        voice_arr = np.concatenate([shepard_riser_reveal(sr), voice_arr])
    elif "बोनस" in txt or "⚡" in txt:
        voice_arr = np.concatenate([glitch_pop_sfx(sr), voice_arr])
    else:
        voice_arr = np.concatenate([tick_chime(sr), whoosh_sfx(sr), voice_arr])

    return _pad(voice_arr, sr) if _on("music") else np.clip(voice_arr, -0.98, 0.98).astype("float32")


def _pad(voice_arr, sr=SR):
    """Awaaz ke neeche dheema harmonic pad - awaaz aate hi apne aap dheema (sidechain duck, ~-18 dB)."""
    n = len(voice_arr)
    t = np.linspace(0, n / sr, n, endpoint=False, dtype="float32")
    pad = (0.6 * np.sin(2 * math.pi * 174.61 * t) + 0.4 * np.sin(2 * math.pi * 261.63 * t)).astype("float32")
    voice_env = np.minimum(1.0, np.abs(voice_arr) * 4.0)
    duck_gain = (0.025 * (1.0 - 0.65 * voice_env)).astype("float32")
    mixed = np.clip(voice_arr + pad * duck_gain, -0.98, 0.98)
    return mixed.astype("float32")



# ---------------- v2.3.0 Step 3: asli loudness naap (v11 mein ye jaanch hamesha 'pass' likhti thi) ----------------
def measure_lufs(video_path):
    """ffmpeg ebur128 se integrated loudness (LUFS). None = naap nahi paya."""
    import subprocess
    try:
        r = subprocess.run(["nice", "-n", "15", "ffmpeg", "-hide_banner", "-nostats", "-i", str(video_path), "-af", "ebur128=peak=true",
                            "-f", "null", "-"], capture_output=True, text=True, timeout=300)
        m = re.findall(r"I:\s*(-?\d+(?:\.\d+)?)\s*LUFS", r.stderr or "")
        return float(m[-1]) if m else None
    except Exception:
        return None


def settings_text():
    from . import state
    a = state.get("awaaz") or {}
    names = {"sfx": "Sound effect (sting, whoosh, tick-tock, riser)", "music": "Dheema music (awaaz ke neeche)",
             "phonetic": "Shabd sudhaar (SIP=एस आई पी, ₹ ank Hindi mein)", "pace": "Scene ke hisaab se raftaar",
             "trim": "Bekaar chup hatao"}
    L = ["🔊 AWAAZ (v11 se) — har video par:"] + [f"• {v}: {'CHALU' if a.get(k, True) else 'BAND'}" for k, v in names.items()]
    L.append("• Aakhir mein -14 LUFS (YouTube/Instagram ka maanak) - hamesha")
    L.append("Badlo: 'awaaz sfx band' / 'awaaz music band' / 'awaaz phonetic band' / 'awaaz pace band' / 'awaaz trim band' (ya chalu) - dohri pushti")
    return "\n".join(L)
