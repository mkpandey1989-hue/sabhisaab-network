"""Daur 2 (14 Nov shaam): owner ke Drive 'Claudi Ai' folder (138 file = 74 alag photo, 64 dohri) + chat ki 14 photo.
Har photo aankh se dekhi: 45 Drive + 7 chat chuni. Chhodi: insaan/chehra (162104, 162219, 162226), kooda (162019),
dhundhli/dohri, ghaat-mandir ki bheed, nirman ka malba, 10MB+ file (161005, 161948). Niyam wahi: EXIF/GPS hata kar naya webp,
watermark (vivo/naam-tareekh) wala kona kaata, jagah ka naam alt mein nahi."""
import json, os
from PIL import Image, ImageOps, ImageEnhance
D = "/home/claude/drive/raw/"; C = "/mnt/user-data/attachments/c7e0840e-234c-5257-9ce9-b15a5a6fec61/"
O = os.path.dirname(os.path.abspath(__file__)) + "/"
M = "mid"
P = [
 ("cheed-ke-chhote-ped-ghaas-ki-dhalaan", D+"162007.jpg", (0,0,1,1), "Ghaas wali seedhi-daar dhalaan par cheed ke chhote ped", M, ["climate","land"]),
 ("subah-ki-dhoop-mein-ghati-ke-khet", D+"160959.jpg", (0,0,1,0.73), "Subah ki dhoop mein pahadi ghati ke seedhi-daar khet", M, ["main","land","buzurg"]),
 ("pahadi-gaon-aur-khet-panorama", D+"161014.jpg", (0,0,0.60,1), "Pahadi gaon, khet aur cheed wali pahadi ka chauda nazara", M, ["main","hyperlocal","geo"]),
 ("cheed-ki-dhalaan-se-nadi-ghati", D+"161100.jpg", (0,0,1,1), "Cheed wali dhalaan se dikhti nadi ghati", M, ["geo","tourism"]),
 ("nadi-kinare-seedhi-daar-khet", D+"161105.jpg", (0,0,1,1), "Nadi kinare seedhi-daar khet aur pahadon ki kataar", M, ["geo","land","main"]),
 ("ghati-ke-khet-aur-ghaas-ke-loote", D+"161110.jpg", (0,0,1,1), "Pahadon se ghiri ghati mein khet aur sookhi ghaas ke loote", M, ["land","buzurg","economy"]),
 ("pathal-chhat-wala-pahadi-ghar", D+"161118.jpg", (0,0,1,1), "Pathal ki chhat wala pahadi ghar, kele ke ped aur ghaas ke loote", M, ["buzurg","culture","hyperlocal","shabd"]),
 ("cheed-wali-pahadi-aur-gaon", D+"161125.jpg", (0,0,1,1), "Cheed wali pahadi ke neeche basa gaon", M, ["hyperlocal","main"]),
 ("cheed-ka-ghana-jungle-pahadi", D+"161134.jpg", (0,0,1,1), "Cheed ke ghane jungle wali pahadi aur ghaas ki seedhiyan", M, ["climate","geo"]),
 ("nadi-ghati-ke-kinare-khet", D+"161154.jpg", (0,0,1,1), "Nadi ghati ke kinare seedhi-daar khet aur gaon", M, ["geo","land"]),
 ("khet-mein-ghaas-ke-loote", D+"161156.jpg", (0,0,1,1), "Ghati ke khet mein ghaas ke loote aur peeche cheed ke jungle", M, ["land","buzurg","food"]),
 ("dhundh-mein-ghati-ke-khet", D+"161203.jpg", (0,0,1,0.70), "Subah ki dhundh mein ghati ke khet aur pagdandi", M, ["climate","land"]),
 ("dhalaan-par-cheed-ka-jungle", D+"161219.jpg", (0,0,1,1), "Dhalaan par cheed ka ghana jungle", M, ["climate","bhavishya"]),
 ("neele-aasman-mein-cheed-pahadi", D+"161228.jpg", (0,0,1,1), "Neele aasman ke neeche cheed se dhaki pahadi", M, ["climate","geo","tourism"]),
 ("ghati-ke-khet-aur-bijli-line", D+"161339.jpg", (0,0,1,1), "Pahadi ghati ke khet, pagdandi aur bijli ki line", M, ["sarkari","aadhunik","land"]),
 ("dhalaan-par-cheed-ka-jawan-ped", D+"161353.jpg", (0.28,0,1,1), "Ghaas wali dhalaan par cheed ka jawan ped", M, ["climate"]),
 ("dhaar-par-cheed-aur-rambans", D+"161416.jpg", (0,0,1,1), "Dhaar par cheed ke ped aur ghaas mein rambans ke paudhe", M, ["climate","vaidya"]),
 ("narangi-phalon-wali-jungli-jhaadi", D+"161426.jpg", (0,0,1,1), "Seedhi-daar khet ke kinare narangi phalon wali jungli jhaadi", M, ["food","climate"]),
 ("dhalaan-par-basa-pahadi-gaon", D+"161429.jpg", (0,0,1,1), "Dhalaan par basa pahadi gaon aur peeche jungle wale pahad", M, ["hyperlocal","main","aadhunik"]),
 ("ghar-ke-paas-ghaas-ke-loote", D+"161445.jpg", (0,0.07,1,1), "Gaon ke ghar ke paas ghaas ke loote aur neeche seedhi-daar khet", M, ["buzurg","land","shabd"]),
 ("dhoop-mein-sookhi-pahadi-ghaas", D+"161606.jpg", (0,0,1,1), "Pahadi dhalaan par sookhi ghaas aur subah ki dhoop", M, ["climate"]),
 ("cheed-ke-do-lambe-ped", D+"161626.jpg", (0,0,1,1), "Neele aasman ke neeche cheed ke do lambe ped", M, ["climate","geo"]),
 ("rambans-ka-paudha", D+"161700.jpg", (0,0,1,1), "Pahadi dhalaan par rambans (agave) ka paudha", M, ["vaidya","climate","economy"]),
 ("rambans-aur-ghati-ke-khet", D+"161709.jpg", (0,0,1,1), "Rambans ke paudhe ke peeche ghati ke seedhi-daar khet aur pahad", M, ["main","land","tourism"]),
 ("dhaar-par-cheed-ki-kataar", D+"161716.jpg", (0,0,1,1), "Ghaas wali dhaar par cheed ke pedon ki kataar", M, ["geo","climate","tourism"]),
 ("purane-khet-ke-paas-cheed", D+"161728.jpg", (0,0,1,1), "Purane khet ki seedhiyon ke paas cheed ka jawan ped", M, ["land","buzurg"]),
 ("kaante-wali-jhaadi-aur-ghati", D+"161753.jpg", (0,0,1,1), "Kaante wali jungli jhaadi ke peeche ghati ke khet aur gaon", M, ["food","hyperlocal"]),
 ("chhode-hue-purane-khet", D+"161821.jpg", (0,0,1,1), "Pahadi dhalaan par chhode hue purane khet ki seedhiyan", M, ["buzurg","land","aadhunik","bhavishya"]),
 ("dhoop-mein-cheed-ka-ghana-ped", D+"161831.jpg", (0,0,1,1), "Dhoop mein chamakta cheed ka ghana ped", M, ["climate"]),
 ("jungli-jhaadi-ki-pattiyan", D+"161911.jpg", (0,0,1,1), "Dhoop mein chamakti jungli jhaadi ki pattiyan aur peeche cheed ki dhalaan", M, ["vaidya","climate"]),
 ("subah-ki-dhoop-mein-pahadi-gaon", D+"161934.jpg", (0,0,1,1), "Subah ki dhoop mein pahadi gaon, seedhi-daar khet aur door pahadon ki kataar", M, ["main","hyperlocal","tourism","prasiddh"]),
 ("badalon-ke-neeche-pahadi-ghati", D+"161936.jpg", (0,0,1,1), "Badalon wale aasman ke neeche pahadi ghati aur dhalaan par gaon", M, ["main","geo","climate","tourism"]),
 ("cheed-ki-dhalaan-aur-pahadi-ghar", D+"161939.jpg", (0,0,1,1), "Cheed ke ped wali dhalaan aur kinare bane pahadi ghar", M, ["aadhunik","hyperlocal","sarkari"]),
 ("seedhi-daar-dhalaan-par-cheed", D+"161944.jpg", (0,0,1,1), "Seedhi-daar dhalaan par cheed ke jawan aur purane ped", M, ["climate","land"]),
 ("ghana-jawan-cheed", D+"162003.jpg", (0,0,1,1), "Dhalaan par ghana jawan cheed ka ped", M, ["climate"]),
 ("khet-ki-seedhiyon-par-do-ped", D+"162010.jpg", (0,0,1,1), "Khet ki purani seedhiyon par khade do lambe ped", M, ["land","buzurg"]),
 ("jhaadi-par-peele-jungli-ber", D+"162025.jpg", (0,0,1,1), "Jhaadi par lage peele jungli phal aur peeche khet ki seedhiyan", M, ["food","vaidya"]),
 ("seedhi-daar-dhalaan-cheed-ke-paudhe", D+"162035.jpg", (0,0,1,1), "Seedhi-daar ghaas wali dhalaan par cheed ke jawan ped", M, ["climate","bhavishya"]),
 ("shaam-ki-dhundh-mein-pahadon-ki-parten", D+"162211.jpg", (0,0,1,1), "Shaam ki dhundh mein pahadon ki parten aur neeche nadi ghati", M, ["geo","tourism","career"]),
 ("lantana-ke-narangi-phool", D+"162240.jpg", (0,0,1,1), "Pahadi jhaadi mein lantana (kuri) ke narangi-peele phool", M, ["climate","bhavishya"]),
 ("kaner-ke-laal-phool-aur-cheed", D+"162301.jpg", (0,0,1,1), "Kaner ke laal phool aur peeche cheed se dhaki pahadi", M, ["culture","climate"]),
 ("phoolon-se-dhaka-purana-naula", D+"162324.jpg", (0,0,1,1), "Phoolon ki bel se dhaka gaon ka purana naula (paani ka srot)", M, ["buzurg","culture","history","sarkari"]),
 ("kaner-ke-gulabi-phool", D+"162328.jpg", (0,0,1,1), "Neele aasman ke neeche kaner ke gulabi phool", M, ["culture","vaidya"]),
 ("naule-ki-jaali-aur-hansraj", D+"162400.jpg", (0,0,1,1), "Purane naule ki jaali ke peeche hansraj (fern) aur upar lantana ke phool", M, ["buzurg","vaidya","history"]),
 ("ghaas-mein-sahi-porcupine", D+"162419.jpg", (0,0,1,1), "Pahadi dhalaan ki ghaas mein charti sahi (porcupine)", M, ["climate"]),
 # chat ki photo (vivo watermark wala neeche ka kona kaata)
 ("chidiyaghar-mein-monal", C+"db42eec1-image.jpg", (0,0.18,1,0.58), "Chidiyaghar ke baade mein Himalayan Monal (rajya pakshi)", "high", ["climate","career"]),
 ("badalon-mein-ghira-pahadi-shahar", C+"6e35bfa2-image.jpg", (0,0.12,1,0.52), "Badalon mein ghira pahadi shahar", M, ["tourism","climate","main"]),
 ("badalon-ke-neeche-jheel-aur-shahar", C+"d2bd5f89-image.jpg", (0,0.05,1,0.52), "Badalon ke neeche jheel aur kinare basa shahar", M, ["tourism","geo"]),
 ("himalayi-kala-bhaalu", C+"9902311e-image.jpg", (0,0,0.88,0.82), "Ghaas ke beech Himalayi kala bhaalu", M, ["climate"]),
 ("baade-mein-charta-hiran", C+"1cfcfe92-image.jpg", (0,0.18,1,0.62), "Hare bade mein charta hiran", M, ["climate"]),
 ("cheed-wali-dhalaan-par-gaon", C+"12569c9b-image.jpg", (0,0,1,0.86), "Cheed wali dhalaan par basa pahadi gaon aur sookhe khet", M, ["hyperlocal","buzurg","main"]),
 ("seedhi-daar-khet-aur-gulabi-phool", C+"0253ec8d-image.jpg", (0,0.53,1,0.94), "Seedhi-daar khet aur jhaadi par gulabi phool", M, ["land","food"]),
]
DROP = ['baade-mein-charta-hiran', 'badalon-mein-ghira-pahadi-shahar', 'chidiyaghar-mein-monal', 'dhoop-mein-sookhi-pahadi-ghaas', 'ghaas-mein-sahi-porcupine', 'pahadi-gaon-aur-khet-panorama']   # dekhne ke baad hata: patli patti, dhundhli, jaali ke peeche, jeev bahut chhota
P = [p for p in P if p[0] not in DROP]
if __name__ == "__main__":
    meta = json.load(open(O + "photos.json"))
    have = {m["file"] for m in meta}
    for name, s, (l, t, r, b), alt, reg, top in P:
        im = ImageOps.exif_transpose(Image.open(s)).convert("RGB")
        W, H = im.size
        im = im.crop((int(l*W), int(t*H), int(r*W), int(b*H)))
        if max(im.size) > 1200:
            im.thumbnail((1200, 1200), Image.LANCZOS)
        im = ImageEnhance.Contrast(im).enhance(1.03)
        clean = Image.new("RGB", im.size); clean.paste(im)
        q = 78
        while True:
            clean.save(O + name + ".webp", "WEBP", quality=q, method=6)
            if os.path.getsize(O + name + ".webp") < 160_000 or q <= 60:
                break
            q -= 6
        if name + ".webp" not in have:
            meta.append({"file": name + ".webp", "w": clean.size[0], "h": clean.size[1], "alt": alt, "region": reg,
                         "topics": top, "src": os.path.basename(s).split(".")[0][:8]})
    json.dump(meta, open(O + "photos.json", "w"), ensure_ascii=False, indent=0)
    print(len(meta))
