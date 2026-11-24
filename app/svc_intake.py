"""v3.8.1: har kaam ka apna sawal-form + documents (owner 24 Nov: "resume ki detail kaha likhega... koi bhi format, attachment").

Website (services-list + gupt page /q) is spec se form banata hai. Har sawal optional - customer jitna jaane utna likhe,
baaki "file bhejiye / WhatsApp par bhejiye / baat karke". Gupt/sarkari number (Aadhaar, PAN, bank, OTP, password) KABHI nahi maangte.
"""
import json

NEVER = ("Aadhaar / PAN / bank number, OTP ya password yahan kabhi mat likhiye - hum kabhi nahi maangte. "
         "Form par number zaroori ho to aap khud portal par daalenge.")

# (key, label, type, hint)  type: t = chhota text, a = lamba text, f = file(s)
SPEC = {
    "resume": {"ids": ["m-resume", "m-resume2", "p-cv", "w-port"], "title": "Resume ke liye", "ask": [
        ("naam", "Poora naam", "t", "Jaise: Ramesh Kumar"),
        ("contact", "Mobile / email (resume par chhapna ho to)", "t", ""),
        ("padhai", "Padhai (class/degree, saal, school/college)", "a", "Jaise: 12th 2022 GIC Almora, BA 2025"),
        ("kaam", "Kaam ka anubhav (kahan, kitna samay, kya kaam)", "a", "Fresher ho to 'fresher' likhiye"),
        ("skill", "Skill / computer / bhasha", "a", "Jaise: Excel, Tally, Hindi-English typing"),
        ("naukri", "Kis naukri ke liye?", "t", "Jaise: data entry, teacher, driver"),
        ("file", "Purana resume / photo / certificate (ho to)", "f", "Photo kheench kar bhi bhej sakte hain")],
        "ready": ["Ek saaf photo (optional)", "Purana resume ho to"]},
    "biodata": {"ids": ["m-biodata"], "title": "Biodata ke liye", "ask": [
        ("naam", "Naam, janm tithi, kad", "a", ""), ("parivar", "Parivar ki jaankari", "a", "Pita/mata ka naam, kaam, bhai-behen"),
        ("padhai", "Padhai aur kaam", "a", ""), ("file", "Photo (1-2)", "f", "")], "ready": ["1-2 achhi photo"]},
    "form": {"ids": ["m-form", "m-exam", "m-scholar", "m-yojana"], "title": "Form madad ke liye", "ask": [
        ("portal", "Kaun sa form / website / yojana?", "t", "Jaise: UP scholarship, SSC GD, PM Kisan"),
        ("date", "Last date (pata ho to)", "t", ""),
        ("samay", "Kab baat karein? (aap saath rahenge, OTP aap daalenge)", "t", "Jaise: aaj shaam 6 ke baad"),
        ("file", "Photo, signature, marksheet ki photo (form mein lagni ho to)", "f", "Size hum theek kar denge")],
        "ready": ["Photo aur signature (saaf)", "Marksheet / certificate jo form maange", "Wahi mobile jis par OTP aayega"]},
    "docs": {"ids": ["m-docs"], "title": "Photo/sign size ke liye", "ask": [
        ("size", "Form kya size maangta hai?", "t", "Jaise: photo 20-50 KB, 200x230"),
        ("file", "Photo / signature", "f", "")], "ready": ["Photo / signature"]},
    "itr": {"ids": ["m-itr1", "m-itr2"], "title": "ITR madad ke liye", "ask": [
        ("aay", "Aay kahan se? (salary / pension / dukaan / byaaj / share)", "a", ""),
        ("saal", "Kaun sa saal? (jaise FY 2025-26)", "t", ""),
        ("samay", "Kab baat karein? (aap apne account mein khud login karenge)", "t", ""),
        ("file", "Form 16 / bank byaaj certificate (ho to)", "f", "Password wali PDF ho to password yahan nahi, baat mein")],
        "ready": ["Form 16 (salary ho to)", "Bank ka byaaj (interest) certificate", "Income tax site ka login aapke paas"]},
    "mobile": {"ids": ["m-mobile", "m-any"], "title": "Mobile/computer madad ke liye", "ask": [
        ("dikkat", "Kya dikkat hai? apne shabdon mein", "a", "Jaise: phone hang hota hai, UPI app nahi chal raha"),
        ("device", "Phone / laptop ka naam (pata ho to)", "t", ""),
        ("samay", "Kab call karein?", "t", ""),
        ("file", "Dikkat ka screenshot / photo / voice note", "f", "")], "ready": ["Phone charge rakhiye", "Screenshot ho to"]},
    "study": {"ids": ["m-study"], "title": "Project/PPT ke liye", "ask": [
        ("vishay", "Vishay (topic) aur class", "t", ""), ("slide", "Kitne page/slide? kab tak?", "t", ""),
        ("file", "Teacher ka format / notes / photo", "f", "")], "ready": ["Teacher ka diya format"]},
    "letter": {"ids": ["m-letter", "m-typing"], "title": "Patra/typing ke liye", "ask": [
        ("kisko", "Kisko likhna hai, kis baare mein?", "a", ""), ("bhasha", "Hindi ya English?", "t", ""),
        ("file", "Hath ka likha page / purana patra ki photo", "f", "")], "ready": []},
    "any": {"ids": ["custom"], "title": "Apne kaam ke baare mein", "ask": [
        ("kya", "Kya kaam hai? apne shabdon mein (Hindi chalega)", "a", "Jaise: dukaan ka bill chahiye, form mein photo nahi lag rahi"),
        ("kab", "Kab tak chahiye?", "t", ""),
        ("file", "Koi photo / PDF / voice note (ho to)", "f", "")], "ready": []},
    "web": {"ids": [], "title": "Website / app / design ke liye", "ask": [
        ("dhanda", "Dhande ka naam aur kya bechte/karte hain", "a", ""),
        ("pasand", "Koi site/app jo pasand ho (link ya naam)", "t", ""),
        ("zaroori", "Zaroori cheezein (WhatsApp order, booking, bill, stock...)", "a", ""),
        ("file", "Logo / photo / price list / purana bill", "f", "")], "ready": ["Logo (ho to)", "Saman/seva ki list aur rate"]},
}
FILE_RULES = {"max_files": 10, "max_mb": 8, "types": "image/*,application/pdf,.doc,.docx,.xls,.xlsx,.txt,audio/*"}


def kind_for(item_id, cat=""):
    for k, v in SPEC.items():
        if item_id in v["ids"]:
            return k
    if item_id in ("", "any", "custom"):
        return "any"
    return "web" if cat in ("web", "soft", "calc", "bot", "ecom", "design", "docs", "trade", "setup", "fix", "content") else "any"


# v3.8.8 (owner: "kuch kami hai to system bole pura bharo"): har kaam ka EK sabse zaroori sawal - khaali ho to wahi field ke neeche
# Hindi mein "ye zaroor likhiye". Baaki sab marzi par (jitna pata ho).
REQ = {"resume": "naam", "biodata": "naam", "form": "portal", "docs": "size", "itr": "aay", "mobile": "dikkat", "study": "vishay",
       "letter": "kisko", "web": "dhanda"}          # "any" mein upar wala "Kya chahiye" hi kaafi


def js():
    """Website ke liye window.SVC_INTAKE (svc-intake.js)."""
    from . import svc
    by = {i["id"]: kind_for(i["id"], i["cat"]) for i in svc.rates()["items"]}
    out = {"spec": {k: {"title": v["title"], "ask": [list(a) for a in v["ask"]], "ready": v["ready"], "req": [REQ.get(k)] if REQ.get(k) else []}
                    for k, v in SPEC.items()},
           "by": by, "never": NEVER, "files": FILE_RULES}
    return "window.SVC_INTAKE=" + json.dumps(out, ensure_ascii=False) + ";\n"
