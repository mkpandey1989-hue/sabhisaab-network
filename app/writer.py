"""Script likhna: Gemini (free key) se. Fail ho to taiyaar script bank. Har script audit se pehle jaanchi jaati hai."""
import json
import os
import pathlib
import random
import re
import requests
from .config import FORBIDDEN_WORDS, GEMINI_FALLBACK_MODELS, BRANDS
from .log import log
from . import state

BANK = pathlib.Path(__file__).parent / "scripts" / "bank"
PERSONA = {
    "sunonatak": "A short FICTIONAL Hindi story (common Indian first names only) where a character makes a money "
                 "mistake or smart move; end with a clear lesson (सबक) and invite to the matching free tool at sabhisaab.com.",
    "money": "A clear Hindi explainer about personal finance (SIP, FD, PPF, EMI, tax, interest) with one simple "
             "numeric example. Educational only: no stock tips, no guaranteed returns.",
    "deals": "Hindi smart-shopping / saving tips with a quick math example (discount, GST, cashback, bill). "
             "No specific product or brand claims.",
    "pahadi": "Hindi info about Uttarakhand/pahadi land units (नाली, मुट्ठी, बीघा), farming or government schemes. "
              "Use only well-known facts; if unsure about a number, do not state it.",
}

FORMATS = ["one real calculation step by step with actual numbers (example person with a fictional first name)",
           "myth vs fact: 3 common beliefs and the truth", "3 mistakes people make and how to avoid them",
           "quiz: ask a question in scene 1, reveal the answer at the end", "comparison of two options with numbers",
           "short fictional family story ending with a money lesson", "quick checklist the viewer can follow today"]

PROMPT = """You write scripts for a Hindi YouTube Shorts channel "{brand_name}".
Style: {persona}
Topic: {topic}
Return ONLY JSON with keys:
 "title": catchy Hindi title, max 70 chars, main search keyword first,
 "description": 2 short Hindi lines,
 "thumb": {{"lines": [2 short lines, max 3 words each, put the most shocking/curious word inside *stars*],
            "emoji": one emoji showing the emotion, "tag": 1-2 word Hindi label like "सावधान!" or "जानिए!",
            "badge": optional short number like "₹4,200" or ""}},
 "scenes": 5 to 7 items of {{"show": on-screen Hindi text max 90 chars (Devanagari, numbers in digits),
            "say": same meaning written for speaking: numbers and English abbreviations written in Devanagari words
            (EMI -> ई एम आई, 50,000 -> पचास हज़ार)}},
 "tags": 8 search tags (Hindi + Hinglish),
 "hook": first scene must create curiosity in under 3 seconds.
Rules: Devanagari Hindi. No real person's name, no politics, no religion, no medical advice, no guarantees.
Last scene only: one short, calm line that a free tool for THIS topic is at sabhisaab.com (say: "सब हिसाब डॉट कॉम");
call it "calculator" only if the topic is a calculation - otherwise just "free tool" / "jaankari".
Never ask viewers to comment "LINK", never promise a DM, never say "link par click karke paise" or any earning/loan offer
(Meta treats link-bait + DM + money promises as scam). No sales pitch anywhere else in the video.
TOPIC MATCH (strict): title, thumbnail and EVERY scene must be about the given topic. If the topic is not about money or
calculation (GK, history, festival, culture, facts, songs), do NOT turn it into a calculator promotion - teach the topic itself.
Originality (YouTube/Meta inauthentic-content rules): real worked example with actual numbers, a fresh angle, no filler,
no copy of earlier videos; never repeat the same opening line pattern.
{extra}"""

LONG_RULES = """THIS IS A LONG YOUTUBE VIDEO (8-12 minutes, horizontal). Make 35 to 50 scenes in sections:
hook (3 scenes) -> problem -> 4-6 clear sections with examples and numbers -> common mistakes -> summary -> call to action.
Each "show" max 110 chars. Title max 90 chars with main keyword first."""


def _gemini(prompt):
    from .brain import ask_gemini        # wahi model-seedhi: sabse naya pehle, seema khatam to neeche
    return ask_gemini(prompt, json_mode=True, temperature=0.9)


def validate(s, fmt="short"):
    errs = []
    lo, hi = (25, 60) if fmt == "long" else (4, 8)
    if not isinstance(s.get("scenes"), list) or not lo <= len(s["scenes"]) <= hi:
        errs.append(f"scenes {lo}-{hi} chahiye")
    for sc in s.get("scenes", []):
        if not sc.get("show") or len(sc["show"]) > 130:
            errs.append("scene text lamba/khaali")
        if not re.search(r"[\u0900-\u097F]", sc.get("show", "")):
            errs.append("Hindi nahi")
    if not s.get("title") or len(s["title"]) > 100:
        errs.append("title galat")
    blob = json.dumps(s, ensure_ascii=False).lower()
    if any(w in blob for w in FORBIDDEN_WORDS):
        errs.append("mana naam")
    return errs


def write(brand, topic, fmt="short", style=""):
    from . import seo
    try:
        kw = seo.keywords_for(topic["topic"])
        extra = (f"People currently search on YouTube: {', '.join(kw)}. Use the best matching phrase in the title "
                 "and tags naturally (no keyword stuffing).\n" if kw else "")
        if style:
            extra += f"Mood/style of this video: {style}.\n"
        n = state.get("fmt_i") or 0
        state.put("fmt_i", n + 1)
        extra += "FORMAT of this video (follow strictly): " + FORMATS[(n + hash(brand)) % len(FORMATS)] + "\n"
        from .company import rules_text
        if rules_text():
            extra += "Owner's permanent rules (must follow): " + rules_text() + "\n"
        ins = state.get("insights") or {}
        if ins:      # pichhle hafte ke views se seekh (bina code badle bot behtar hota jaata hai)
            extra += ("Lessons from our own past videos: do more of: " + "; ".join(ins.get("do_more", [])[:4]) +
                      ". Avoid: " + "; ".join(ins.get("avoid", [])[:3]) + ". Title tips: " +
                      "; ".join(ins.get("title_tips", [])[:3]) + ".\n")
        if fmt == "long":
            extra += LONG_RULES
        s = _gemini(PROMPT.format(brand_name=BRANDS[brand]["name"], persona=PERSONA[brand], topic=topic["topic"],
                                  extra=extra))
        s["brand"], s["page"], s["format"] = brand, topic["page"], fmt
        s["tags"] = list(dict.fromkeys((s.get("tags") or []) + kw))[:15]
        s.setdefault("thumb", {})
        errs = validate(s, fmt)
        if errs:
            raise RuntimeError(", ".join(errs))
        s["source"] = "gemini"
        return s
    except Exception as e:
        log(f"writer: Gemini se nahi bana ({e}), bank se")
        from .pipeline import _sig
        used = [h.get("sig") for h in state.get("history", [])]
        files = [f for f in (sorted(BANK.glob(f"{brand}_*.json")) or sorted(BANK.glob("*.json")))
                 if _sig(json.loads(f.read_text(encoding="utf-8"))) not in used]
        if not files:
            raise RuntimeError("Gemini nahi chala aur bank ki script pehle ja chuki hain - dobara post nahi karenge")
        s = json.loads(random.choice(files).read_text(encoding="utf-8"))
        s["brand"] = brand
        s["source"] = "bank"
        if fmt == "long":
            raise RuntimeError("Lambi video ke liye Gemini script zaroori hai (bank mein lambi script nahi)")
        return s
