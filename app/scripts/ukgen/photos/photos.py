"""Owner ki apni photo/video (14 Nov 2026) -> website ki webp. Niyam: chehra nahi, awaaz nahi (video se sirf frame),
jagah ka naam nahi, watermark/poster/number-plate wala hissa kaata, EXIF/GPS poora hata (naya file, sirf pixel)."""
import glob, json
from PIL import Image, ImageFilter, ImageEnhance
S = "/home/claude/media/src/"; F = "/home/claude/media/frames/"; O = "/home/claude/media/out/"
# (naam, srot, crop(l,t,r,b), alt, ilaka, vishay)
P = [
 ("pahadi-dhalaan-cheed-ka-jungle", S+"08e4d76e", (0.06,0.0,1.0,0.80), "Pahadi dhalaan par cheed (chir) ka ghana jungle aur neeche seedhi-daar khet", "mid", ["climate","geo","land","main"]),
 ("pahadon-se-ghiri-ghati-ke-khet", S+"af084a5e", (0,0,1,1), "Pahadon se ghiri ghati mein base gaon aur khet, subah ki dhoop mein", "mid", ["main","hyperlocal","geo","sarkari"]),
 ("ghati-mein-basa-pahadi-kasba", S+"1e7b4d76", (0,0,1,1), "Ghati mein basa pahadi kasba, aage khet aur kele ke ped", "mid", ["main","aadhunik","hyperlocal","transport"]),
 ("pahadi-ghati-ke-khule-khet", S+"4ef76ce4", (0,0.08,1,1), "Pahadi ghati ke khule khet aur peeche cheed ke jungle wale pahad", "mid", ["land","economy","bhavishya"]),
 ("pahad-par-seedhi-daar-khet", S+"ed0160cb", (0,0,1,1), "Pahad ki dhalaan par bane seedhi-daar khet (terrace farming)", "mid", ["land","buzurg","food","career"]),
 ("seedhi-daar-khet-aur-lakdi-ka-dher", S+"14962710", (0,0,1,0.86), "Ghar ke paas kele ke ped, jalane ki lakdi ka dher aur neeche seedhi-daar khet", "mid", ["buzurg","aadhunik","land"]),
 ("pahadi-aangan-kele-gende-ke-phool", S+"162710e0", (0,0,1,1), "Pahadi aangan: kele ke ped, lakdi ka dher, gende ke phool aur saamne pahad", "mid", ["culture","buzurg","food","shabd"]),
 ("gaon-ka-mandir-aur-barf-ki-chotiyan", S+"9dea16ff", (0,0,1,1), "Gaon ka chhota mandir, paas mein ek pakka ghar aur door barf se dhaki chotiyan", "mid", ["history","culture","vaidya","prasiddh"]),
 ("jhaadi-par-peele-jungli-phal", S+"e8a61b95", (0,0.12,1,0.68), "Pahad ki ghaas mein jhaadi par lage chhote peele jungli phal", "mid", ["climate","food","vaidya"]),
 ("pooja-mein-phoolon-ka-shringar", S+"0ed12763", (0,0,1,1), "Pooja mein gende aur gulab ke phoolon se saji chunri aur shringar", "any", ["culture","history","vaidya","shabd"]),
 ("gende-ki-mala-se-saje-ganesh", S+"c017cd09", (0,0,0.80,1), "Pooja mein gende ki mala se saje Ganesh ji", "any", ["culture","vaidya","prasiddh"]),
 ("terai-mein-suryast-aur-ghar", S+"2c6132fa", (0,0,1,1), "Maidani (Terai) ilake mein shaam ka suryast, kachchi sadak aur naye ghar", "plain", ["main","aadhunik","hyperlocal","transport"]),
 ("terai-ka-aasman-aur-ganna", S+"d29c3146", (0,0,1,1), "Terai ke aasman mein shaam ke baadal aur ganne ke ped", "plain", ["climate","geo","prasiddh","career"]),
 ("barsaat-mein-hara-aangan", S+"3ca1620b", (0,0,1,0.88), "Barsaat mein bheega aangan aur hare ped", "plain", ["climate","buzurg","vaidya","shabd","sarkari"]),
 ("nadi-ghaat-pul-aur-kasba", S+"7b759b90", (0,0.06,1,0.46), "Pahadi nadi ka ghaat, paidal pul aur kinare basa kasba", "mid", ["history","tourism","geo","bhavishya"]),
 ("nadi-ghaat-par-shiv-moorti", S+"9bd8e9b8", (0,0.22,0.46,0.485), "Nadi ghaat par Shiv ji ki moorti aur peeche pahad", "any", ["history","culture","tourism"]),
 ("cheed-ke-jungle-mein-mandir", S+"944e4ef5", (0,0.02,0.98,0.50), "Cheed ke jungle ke neeche naarangi shikhar wala mandir", "mid", ["tourism","history","prasiddh"]),
 ("khet-mein-saanp-saavdhani", S+"681d6dac", (0,0.14,1,0.56), "Gili mitti wale khet mein saanp: khet mein kaam karte samay saavdhani", "plain", ["climate","land"]),
 ("gehri-ghati-mein-behti-nadi", F+"13216298_02", (0,0,1,1), "Gehri pahadi ghati mein behti nadi aur hare pahad", "high", ["geo","transport","bhavishya"]),
 ("pahad-ki-dhalaan-par-ghar", F+"13216298_12", (0,0,1,1), "Pahad ki dhalaan par bana ghar aur ghana jungle", "mid", ["hyperlocal","aadhunik","sarkari"]),
 ("barf-ki-choti-aur-nadi-ghati", F+"37935006_12", (0,0,1,1), "Barf wali choti ke neeche nadi ki ghati aur door basa kasba", "high", ["tourism","geo","main"]),
 ("pathron-mein-tez-pahadi-nadi", F+"37935006_19", (0,0,1,1), "Pathron ke beech behti tez pahadi nadi aur kinare paidal rasta", "high", ["geo","bhavishya","climate"]),
 ("oonche-pahad-ke-neeche-tirth-kasba", F+"6733259e_08", (0,0,1,0.76), "Oonche bhure pahad ke neeche basa tirth kasba", "high", ["tourism","transport","history","main"]),
 ("baadalon-mein-barf-ki-chotiyan", F+"6733259e_01", (0,0,1,0.58), "Baadalon ke beech barf se dhaki nukili chotiyan", "high", ["climate","geo","main"]),
 ("dhalaan-par-rang-birange-ghar", F+"383cb950_19", (0,0,1,0.86), "Pahad ki dhalaan par bane rang-birange pahadi ghar", "mid", ["hyperlocal","aadhunik","main","sarkari"]),
 ("ek-ke-peeche-ek-pahad", F+"383cb950_02", (0,0,1,1), "Ek ke peeche ek pahadon ki paraten aur seedhi-daar khet", "mid", ["geo","career","shabd"]),
 ("oonchai-par-banj-ke-ped", F+"34407c52_04", (0,0,1,0.72), "Oonchai par banj (oak) jaise ghane ped", "high", ["climate","vaidya"]),
 ("shaam-ko-door-himalaya", F+"34407c52_12", (0,0.18,1,0.70), "Oonchai se shaam ke samay door dikhti Himalaya ki chotiyan", "high", ["tourism","prasiddh","career"]),
 ("jungle-mein-yatri-tent-camp", F+"9180732c_14", (0,0,1,1), "Jungle ke beech yatriyon ke liye tent camp", "high", ["aadhunik","tourism"]),
 ("pathron-ke-beech-jungli-jeev", F+"ad1a15bf_21", (0,0,1,1), "Pathron aur jhaadiyon ke beech chhota jungli jeev", "high", ["climate"]),
 ("barf-wale-pahadon-mein-bus", F+"e505f75e_20", (0,0,1,0.74), "Barf wale pahadon ke beech sarkari bus", "high", ["transport"]),
 ("pahadi-gaon-ki-dhalaan", F+"e9542575_17", (0,0,1,0.72), "Pahadi gaon ki dhalaan, ped aur chhote khet", "high", ["buzurg","hyperlocal","land","shabd"]),
 ("nadi-kinare-mandir-aur-shahar", F+"fdf0c431_16", (0,0,1,1), "Nadi ke kinare bane mandir aur upar basa shahar", "mid", ["history","tourism","culture"]),
 ("terai-ke-khet-ganna-poplar", F+"2fcef40e_02", (0,0.05,1,0.62), "Terai ke khet: ganna aur poplar ke ped", "plain", ["land","economy","food"]),
 ("pahad-se-dikhta-ghati-ka-gaon", F+"71828000_04", (0,0,1,1), "Pahad se dikhta ghati ka gaon aur door ki pahadiyan", "mid", ["main","prasiddh","buzurg","economy"]),
]
def src(p):
    return glob.glob(p + "*.jpg")[0]
if __name__ == "__main__":
    meta = []
    for name, s, (l, t, r, b), alt, reg, top in P:
        im = Image.open(src(s)).convert("RGB")
        W, H = im.size
        im = im.crop((int(l*W), int(t*H), int(r*W), int(b*H)))
        if max(im.size) > 1200:
            im.thumbnail((1200, 1200), Image.LANCZOS)
        if "/frames/" in s:
            im = im.filter(ImageFilter.UnsharpMask(radius=1.2, percent=60, threshold=2))
        im = ImageEnhance.Contrast(im).enhance(1.03)
        clean = Image.new("RGB", im.size); clean.paste(im)            # naya image: koi EXIF/GPS/maker note nahi
        q = 78
        while True:
            clean.save(O + name + ".webp", "WEBP", quality=q, method=6)
            if __import__("os").path.getsize(O + name + ".webp") < 160_000 or q <= 60:
                break
            q -= 6
        meta.append({"file": name + ".webp", "w": clean.size[0], "h": clean.size[1], "alt": alt, "region": reg, "topics": top,
                     "src": s.split("/")[-1]})
    json.dump(meta, open(O + "photos.json", "w"), ensure_ascii=False, indent=1)
    print(len(meta))
