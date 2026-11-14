"""v3.3.2 (owner 14 Nov / Gemini audit: 'mixed language'): template ki English headings ka Hinglish roop.
Page ki bhasha hi-Latn hai; search ke English shabd (PIN Code, ILP, GDP, RTO, IFSC, UNESCO, BRO) waise hi rakhe."""
import re
HEAD_HI = {
 "neighboring districts of uttarakhand sharing borders": "Padosi Zile: Kin Zilon se Seema Milti Hai",
 "latitude, longitude & total geographical area (in sq. km)": "Latitude-Longitude aur Kul Kshetrafal (Sq Km)",
 "district overview, state nickname & core identity": "Zile ki Pehchan: Ek Nazar Mein",
 "complete list of development blocks (vikas khand)": "Vikas Khand (Development Blocks) ki Poori Suchi",
 "unclimbed peaks, sacred peaks & mountaineering expedition rules": "Anchhui aur Pavitra Chotiyan, Parvatarohan ke Niyam",
 "traditional sweets, festive snacks & offerings": "Paramparik Mithai, Tyohar ke Pakwan aur Prasad",
 "telecom, mobile network & broadband reality check": "Mobile Network aur Internet: Asli Sthiti",
 "snout locations, length in km & trekking access to major glaciers": "Pramukh Glacier: Snout, Lambai aur Trek ka Raasta",
 "railway connectivity & future rail projects": "Railway Station aur Aane Wali Rail Pariyojanayein",
 "perennial snow-fed rivers & rain-fed rivers": "Barf se Bharne Wali aur Barish se Bharne Wali Nadiyan",
 "month-by-month travel guide (january to december)": "Mahine-dar-Mahine Yatra Guide (January se December)",
 "lowest point (river bed valley) to highest point (peak elevation)": "Sabse Neecha aur Sabse Ooncha Bindu (Unchai)",
 "high-altitude trans-himalayan passes & ancient trade routes": "Oonche Himalayi Darre aur Purane Vyapar Marg",
 "high-altitude mysterious kunds, glacial tals & boating lakes": "Oonchai ke Kund, Glacier Tal aur Boating Wali Jheelein",
 "geology, soil types & seismic profile": "Bhoo-vigyan, Mitti ke Prakar aur Bhookamp Zone",
 "fuel stations, ev charging & mechanic hubs": "Petrol Pump, EV Charging aur Mechanic",
 "forest types & sacred groves (dev van)": "Jungle ke Prakar aur Dev Van (Pavitra Van)",
 "environmental challenges & human-wildlife conflict": "Paryavaran ki Chunautiyan aur Insaan-Jaanwar Sangharsh",
 "district disaster management authority (ddma) control room & toll-free helplines": "Aapda Control Room (DDMA) aur Toll-Free Helpline",
 "district & sessions court location, family courts & tehsil legal clinics": "Zila Nyayalay, Family Court aur Muft Kanooni Sahayata",
 "demographics, ethnic groups & scheduled tribes": "Aabadi, Samuday aur Anusuchit Janjati",
 "cinema, books, media & digital creators": "Cinema, Kitabein, Media aur Digital Creators",
 "block-wise & post-office-wise postal pin code table": "Block aur Dak Ghar ke Hisaab se PIN Code Table",
 "summer, monsoon, autumn, winter & spring temperature/rainfall matrix": "Har Mausam ka Taapmaan aur Barish",
 "snowline altitude in winter & live weather monitoring stations": "Sardi mein Barf ki Unchai aur Mausam Kendra",
 "major bus stands, taxi unions & booking counters": "Pramukh Bus Adde, Taxi Stand aur Booking",
 "local gad, gadheras (mountain streams) & gorge formations": "Gad, Gadhere (Pahadi Naale) aur Gehri Ghatiyan",
 "law enforcement, security & border forces": "Police, Suraksha aur Seema Bal",
 "land use pattern: forest cover %, cultivable land, barren & alpine zones": "Zameen ka Upyog: Jungle, Kheti, Banjar aur Bugyal Kshetra",
 "inner line permits (ilp), forest permits & safety rules": "Inner Line Permit (ILP), Van Anumati aur Suraksha Niyam",
 "famous local halwais, iconic tea stalls & 50-year-old shops": "Mashhoor Halwai, Chai ki Dukaanein aur Purane Bazaar",
 "district economy, gdp, per capita income & livelihood": "Arthvyavastha: GDP, Per Capita Aay aur Rozgar",
 "distance & driving time matrix from major cities": "Bade Shehron se Doori aur Gaadi se Samay",
 "core vs buffer zones, unesco status, entry gates & forest rest houses (frh)": "Core-Buffer Zone, UNESCO Darja, Entry Gate aur Van Vishram Grih (FRH)",
 "complete pin code & std code directory": "PIN Code aur STD Code ki Poori Suchi",
 "vidhan sabha (assembly) seats breakdown & sc/st reserved constituencies": "Vidhan Sabha Seatein aur SC/ST Aarakshit Kshetra",
 "urban local bodies & civic administration": "Nagar Nikay aur Shahri Prashasan",
 "traditional folk dances": "Paramparik Lok Nritya",
 "traditional attire & textiles": "Paramparik Pehnawa aur Kapde",
 "total inhabited villages vs uninhabited (forest/ghost) villages": "Aabaad aur Gair-Aabaad (Khaali) Gaon",
 "section 143 (agricultural to non-agricultural land use conversion) & tehsil circle rates": "Dhara 143 (Kheti se Gair-Kheti Zameen) aur Circle Rate",
 "road network, highways, bridges & border roads (bro)": "Sadak, Highway, Pul aur Seema Sadak (BRO)",
 "pre-history, megaliths, cup-marks & rock shelters": "Pragaitihasik Kaal, Shila-Chitra aur Shailashray",
 "national parks, wildlife sanctuaries & conservation reserves": "National Park, Wildlife Sanctuary aur Sanrakshit Kshetra",
 "named snow peaks with exact altitude in meters/feet": "Barfeeli Chotiyan aur Unki Unchai (Meter/Feet)",
 "micro-climatic zones & 12-month weather calendar": "Mausam ke Zone aur 12 Mahine ka Mausam",
 "mammals, reptiles & endangered wildlife": "Jaanwar, Sarisrip aur Sankatgrast Vanyajeev",
 "major & minor river confluences and their bathing/uttarayan/shraddha significance": "Nadiyon ke Sangam aur Snan-Shraddh ka Mahatva",
 "languages, sub-dialects & common local phrases": "Bhasha, Up-boliyan aur Roz ke Shabd",
 "hill driving endorsement rules & green cess / eco-tax applicability": "Pahadi Driving ke Niyam aur Green Cess / Eco-Tax",
 "govt schemes, one district one product (odop) & startups": "Sarkari Yojanayein, ODOP aur Startup",
 "geographical coordinates & spatial extent": "Bhaugolik Sthiti aur Vistaar",
 "electricity, solar power & winter water supply reality": "Bijli, Solar aur Sardi mein Paani ki Sthiti",
 "education: universities, colleges, boarding schools & institutes": "Shiksha: University, College, Boarding School aur Sansthan",
 "bus services, shared taxis & local transit": "Bus Seva, Shared Taxi aur Sthaniya Yatayat",
 "upcoming mega infrastructure projects (2026-2035)": "Aane Wali Badi Pariyojanayein (2026-2035)",
 "sports stadiums, high-altitude training & adventure academies": "Khel Stadium, High-Altitude Training aur Adventure Academy",
 "population, sex ratio, literacy & rural/urban split": "Aabadi, Ling Anupaat, Saaksharta aur Gaon-Shahar",
 "political & electoral profile": "Rajneetik aur Chunavi Parichay",
 "patwari chowkis (revenue police system vs regular police jurisdiction areas)": "Patwari Chowki: Revenue Police aur Regular Police ka Kshetra",
 "mining, minerals & forest produce (van nigam)": "Khanan, Khanij aur Van Upaj (Van Nigam)",
 "major bugyals, summer grazing traditions (anwal/bakarwal) & supreme court night-camping bans": "Pramukh Bugyal, Charai ki Parampara aur Raat ki Camping par Adalati Rok",
 "main central thrust (mct), fault lines & seismic zone (zone iv / v) status": "Main Central Thrust (MCT), Fault Line aur Bhookamp Zone (IV/V)",
 "judiciary & legal infrastructure": "Nyayalay aur Kanooni Vyavastha",
 "international borders (tibet/china or nepal) & inter-state borders (hp/up)": "Antarrashtriya Seema (Tibet/China ya Nepal) aur Antarrajyiya Seema",
 "executive summary & district identity": "Saar aur Zile ki Pehchan",
 "deity-protected sacred forests (dev van / hariyali devi vans where cutting a single leaf is taboo)": "Devta ke Sanrakshit Pavitra Van (Dev Van)",
 "complete trekking directory (easy, moderate & difficult)": "Trekking ki Poori Suchi (Aasan, Madhyam aur Kathin)",
 "chir pine forest fires (vanal), land subsidence zones, cloudburst history & leopard/wild boar/monkey crop damage": "Chir ke Jungle ki Aag (Vanal), Bhoo-dhansav, Badal Phatna aur Jaanwaron se Fasal Nuksan",
 "botanical & zoological local table": "Paudhe aur Jaanwar: Sthaniya Naam",
 "block-wise major villages & gram panchayats directory": "Block-wise Pramukh Gaon aur Gram Panchayat",
 "road-head vs walk-in villages for slow travel, artists, birdwatchers & writers": "Sadak Wale aur Paidal Wale Gaon: Slow Travel, Kalakar aur Birdwatcher ke Liye",
 "nap land (measured private land), benap land & kesar-e-hind land explained": "Naap Zameen, Benaap Zameen aur Kesar-e-Hind Zameen ka Matlab",
 "imf-listed peaks, forest permits, porter/hap rates & base camp logistics": "IMF ki Chotiyan, Van Anumati, Porter/HAP aur Base Camp",
 "building bylaws, map approval & seismic rules": "Building Bylaws, Naksha Manzoori aur Bhookamp Niyam",
 "voice search & hinglish query bank (people also ask)": "Log Ye Bhi Poochhte Hain",
 "the traditional 'barahnaja' (12-grain mixed ecological cropping system)": "Paramparik ‘Barahnaja’: 12 Anaj ki Mili-Juli Kheti",
 "sub-registrar offices (zameen registry offices)": "Sub-Registrar Daftar (Zameen Registry)",
 "revenue police vs regular police": "Revenue Police aur Regular Police ka Farak",
 "population, sex ratio (high female ratio due to male migration), literacy & rural/urban split": "Aabadi, Ling Anupaat (Palayan ka Asar), Saaksharta aur Gaon-Shahar",
 "popular towns vs quiet ridge-top hamlets with 180-degree himalayan views": "Lokpriya Kasbe aur Shaant Pahadi Gaon (Himalaya ke Nazaron Wale)",
 "main central thrust (mct), fault lines & seismic zone status": "Main Central Thrust (MCT), Fault Line aur Bhookamp Zone",
 "local 'khals' (saddles/passes between two ridge villages used by locals)": "Sthaniya ‘Khal’: Do Pahadi Gaon ke Beech ke Raaste",
 "international borders & inter-state borders": "Antarrashtriya aur Antarrajyiya Seema",
 "historic trade routes, salt routes & old suspension bridges (jhula pul)": "Purane Vyapar Marg, Namak Marg aur Jhula Pul",
 "essential local words, greetings & proverbs": "Zaroori Sthaniya Shabd, Abhivadan aur Kahawatein",
 "education: universities, colleges & institutes": "Shiksha: University, College aur Sansthan",
 "deserted stone villages turned into eco-tourism / heritage restoration projects": "Khaali Pathar ke Gaon jo Eco-Tourism / Heritage Project Bane",
 "deity-protected sacred forests (dev van)": "Devta ke Sanrakshit Pavitra Van (Dev Van)",
 "coaching centers, public libraries & reading rooms": "Coaching, Sarkari Pustakalay aur Reading Room",
 "banking ifsc codes, regional rural banks & post office savings": "Bank, IFSC Code, Gramin Bank aur Dak Ghar Bachat",
 "ancestral village (mool niwas / thaat) identity & inter-valley marriage rules": "Mool Gaon (Mool Niwas / Thaat) ki Pehchan aur Vivah ki Paramparayein",
 "altitude, distance from district hq, entry fee, parking & ideal duration for each spot": "Har Jagah ki Unchai, Mukhyalaya se Doori, Entry Fee, Parking aur Samay",
}
PREFIX_HI = [
 (r"^rules for outsiders buying land in uttarakhand\b", "Bahari Logon ke Liye Zameen Kharidne ke Niyam"),
 (r"^district rto / arto code\b[^,]*, office location & licensing services", "RTO / ARTO Code, Daftar aur Licence Sevayein"),
 (r"^weekend escape \(3 days\), family & temple circuit \(5 days\), backpacker/trekker circuit \(7 days\)", "Weekend (3 Din), Parivar-Mandir Yatra (5 Din), Trekker Circuit (7 Din)"),
]
def _norm(t):
    return re.sub(r"\s+", " ", t.replace("‘", "'").replace("’", "'").strip().lower())

from headings_tpl import TPL as _TPL0
TPL = {_norm(k): v for k, v in _TPL0.items()}


def _tpl(body, D):
    """haath se likha saancha: body mein zile ka naam -> {D}; 'Zila: ' aage laga ho to hata ke dekho."""
    pre = ""
    if not D:
        v = TPL.get(_norm(body))
        return v if v and "{D}" not in v else None
    mm = re.match(r"^(%s|%s):\s+(.*)$" % (re.escape(D), re.escape(D.split()[0])), body)
    if mm:
        pre, body = mm.group(1) + ": ", mm.group(2)
    k = _norm(body)
    for nm in (D, D.split()[0]):
        k = re.sub(r"(?<![a-z])%s(?![a-z])" % re.escape(nm.lower()), "{d}", k)
    for key in (k, k.rstrip(" .:")):
        v = TPL.get(key)
        if v:
            out = v.replace("{D}", D)
            return out if (not pre or D.lower() in out.lower()) else pre + out
    return None


def hinglish(t, D=None):
    t = re.sub(r"^((?:[A-Z]\.)?\d{1,3}(?:\.\d{1,2})?\.?\s+)?FAQ:\s+", r"\1Sawal-Jawab: ", t)
    """'93. District Economy, GDP...' -> '93. Arthvyavastha: GDP...' ; number aur 'Zila:' prefix waise hi."""
    m = re.match(r"^((?:[A-Z]\.)?\d{1,3}(?:\.\d{1,2})?\.?\s+)?(.*)$", t)
    num, body = m.group(1) or "", m.group(2)
    v = _tpl(body, D)
    if v:
        return num + v
    k = _norm(body)
    out = None
    if k in HEAD_HI:
        out = HEAD_HI[k]
    else:
        for rx, rep in PREFIX_HI:
            mm = re.match(rx, k)
            if mm:
                rest = body[mm.end():].strip(" ,&")
                out = rep + ((" (" + rest.strip("()") + ")") if rest and len(rest) < 60 else "")
                break
    if out is None:
        return t
    return num + (_tpl(out, D) or out)          # purane HEAD_HI/PREFIX roop par bhi haath ka saancha (daur 2)


# ---- v3.3.2 audit-4: jaanch ke liye - heading abhi bhi poori English hai? (audit/report mein ginti)
def is_english(body):
    w = re.findall(r"[A-Za-z]+", body.lower())
    en = {"the", "of", "and", "in", "for", "to", "with", "on", "at", "by", "from", "is", "are", "how", "what", "when",
          "where", "which", "why", "your", "you", "our", "best", "guide", "list", "complete", "major", "top", "famous",
          "local", "traditional", "history", "district", "near"}
    hi = {"ka", "ki", "ke", "me", "mein", "aur", "se", "kya", "kaise", "kahan", "kab", "hai", "hain", "ko", "par", "liye",
          "wale", "wali", "kaun", "ek", "jaankari", "nahi", "bhi"}
    return bool(w) and any(x in en for x in w) and not any(x in hi for x in w)
