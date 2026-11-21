"""v2.1.7: bina Gemini ke pakka India calendar - Google-search wala Gemini free seema mein fail hota hai (audit: 3 din mein
~50 'calendar find' fail) to bhi roz ke khaas din chhoote nahi.
FIXED = har saal usi tareekh (rashtriya/antarrashtriya din, saura parv). DATED = chandra panchang wale (har saal alag) -
sirf jo pakke srot se mile (Diwali 2026: kai panchang/news, 6-15 Nov). Naye saal ke tyohaar Claude yahan jode.
Har entry: (hindi naam, english naam, samuday, bada din?, brand ya 'all', shubhkamna/jaankari text, video ka vishay)."""

FIXED = {
    "01-01": [("नववर्ष", "New Year", "rashtriya", True, "all", "नए साल की हार्दिक शुभकामनाएँ! इस साल अपने पैसों का हिसाब भी नया और साफ़ रखें।",
               "Naye saal ka budget plan")],
    "01-09": [("प्रवासी भारतीय दिवस", "Pravasi Bharatiya Divas", "rashtriya", False, "money", "विदेश में बसे सभी भारतीयों को प्रवासी भारतीय दिवस की शुभकामनाएँ।", "")],
    "01-12": [("राष्ट्रीय युवा दिवस", "National Youth Day", "rashtriya", True, "money", "स्वामी विवेकानंद जयंती और राष्ट्रीय युवा दिवस की शुभकामनाएँ! युवा उम्र से बचत शुरू करें।",
               "Pehli naukri se SIP kaise shuru karein")],
    "01-23": [("पराक्रम दिवस", "Parakram Diwas (Netaji Jayanti)", "rashtriya", False, "all", "नेताजी सुभाष चंद्र बोस जयंती (पराक्रम दिवस) पर उन्हें नमन।", "")],
    "01-26": [("गणतंत्र दिवस", "Republic Day", "rashtriya", True, "all", "गणतंत्र दिवस की हार्दिक शुभकामनाएँ! संविधान ने हमें जो अधिकार दिए, उन्हें जानें।",
               "Republic Day sale mein asli discount ka hisaab")],
    "02-28": [("राष्ट्रीय विज्ञान दिवस", "National Science Day", "rashtriya", False, "sunonatak", "राष्ट्रीय विज्ञान दिवस की शुभकामनाएँ - सवाल पूछते रहिए!", "")],
    "03-08": [("अंतरराष्ट्रीय महिला दिवस", "International Women's Day", "antarrashtriya", True, "money", "महिला दिवस की शुभकामनाएँ! हर महिला का अपना बचत खाता और निवेश हो।",
               "Mahilaon ke liye bachat aur nivesh yojana")],
    "03-15": [("विश्व उपभोक्ता अधिकार दिवस", "World Consumer Rights Day", "antarrashtriya", False, "deals", "उपभोक्ता अधिकार दिवस: बिल ज़रूर लें, MRP और गारंटी जाँचें।",
               "Online shopping mein apne adhikar")],
    "03-31": [("वित्त वर्ष का आख़िरी दिन", "Financial Year End", "rashtriya", True, "money", "आज वित्त वर्ष का आख़िरी दिन है - टैक्स बचत के निवेश और ज़रूरी काम आज ही पूरे करें।",
               "31 March se pehle tax bachat ke kaam")],
    "04-01": [("नया वित्त वर्ष", "New Financial Year", "rashtriya", False, "money", "नया वित्त वर्ष शुरू - इस साल का टैक्स और बचत प्लान अभी बनाएँ।", "")],
    "04-14": [("आंबेडकर जयंती / बैसाखी", "Ambedkar Jayanti / Baisakhi", "rashtriya", True, "all", "डॉ. भीमराव आंबेडकर जयंती पर नमन, और बैसाखी की हार्दिक शुभकामनाएँ।", "")],
    "04-22": [("पृथ्वी दिवस", "Earth Day", "antarrashtriya", False, "pahadi", "पृथ्वी दिवस: पेड़ लगाएँ, पानी बचाएँ - पहाड़ बचेंगे तो हम बचेंगे।", "")],
    "05-01": [("मज़दूर दिवस", "Labour Day", "rashtriya", True, "money", "मज़दूर दिवस पर हर मेहनतकश को सलाम।", "Kamgar ke liye PF aur pension ki jaankari")],
    "05-11": [("राष्ट्रीय प्रौद्योगिकी दिवस", "National Technology Day", "rashtriya", False, "sunonatak", "राष्ट्रीय प्रौद्योगिकी दिवस की शुभकामनाएँ।", "")],
    "06-05": [("विश्व पर्यावरण दिवस", "World Environment Day", "antarrashtriya", True, "pahadi", "पर्यावरण दिवस: एक पेड़ आज ज़रूर लगाएँ।", "")],
    "06-21": [("अंतरराष्ट्रीय योग दिवस", "International Yoga Day", "antarrashtriya", True, "all", "योग दिवस की शुभकामनाएँ - तन और धन दोनों का संतुलन रखें।", "")],
    "07-01": [("डॉक्टर्स डे / सीए डे", "Doctors' Day / CA Day", "rashtriya", False, "money", "सभी डॉक्टरों और चार्टर्ड अकाउंटेंट्स को धन्यवाद और शुभकामनाएँ।", "")],
    "07-31": [("ITR की आख़िरी तारीख़ (सामान्य)", "ITR due date (usual)", "rashtriya", True, "money", "आयकर रिटर्न की सामान्य आख़िरी तारीख़ - अगर तारीख़ नहीं बढ़ी तो आज ही भरें।",
               "ITR aakhri din: zaroori baatein")],
    "08-15": [("स्वतंत्रता दिवस", "Independence Day", "rashtriya", True, "all", "स्वतंत्रता दिवस की हार्दिक शुभकामनाएँ! जय हिंद।",
               "Independence Day sale ka asli hisaab")],
    "08-29": [("राष्ट्रीय खेल दिवस", "National Sports Day", "rashtriya", False, "sunonatak", "राष्ट्रीय खेल दिवस की शुभकामनाएँ।", "")],
    "09-05": [("शिक्षक दिवस", "Teachers' Day", "rashtriya", True, "all", "शिक्षक दिवस पर सभी गुरुजनों को नमन।", "Bachchon ki padhai ka fund kaise banayein")],
    "09-14": [("हिंदी दिवस", "Hindi Diwas", "rashtriya", True, "all", "हिंदी दिवस की शुभकामनाएँ! अपनी भाषा में हिसाब समझना सबसे आसान।", "")],
    "10-02": [("गांधी जयंती", "Gandhi Jayanti", "rashtriya", True, "all", "गांधी जयंती और लाल बहादुर शास्त्री जयंती पर नमन।", "")],
    "10-31": [("राष्ट्रीय एकता दिवस / विश्व बचत दिवस", "Rashtriya Ekta Diwas / World Savings Day", "rashtriya", True, "money",
               "राष्ट्रीय एकता दिवस और विश्व बचत दिवस - आज से हर महीने थोड़ी बचत का संकल्प लें।", "Har mahine bachat ka aasaan niyam")],
    "11-09": [("उत्तराखंड स्थापना दिवस", "Uttarakhand Foundation Day", "uttarakhand", True, "pahadi",
               "उत्तराखंड स्थापना दिवस की हार्दिक शुभकामनाएँ! देवभूमि के हर निवासी को बधाई।", "Uttarakhand sthapna diwas: zameen aur yojana ki jaankari")],
    "11-14": [("बाल दिवस", "Children's Day", "rashtriya", True, "all", "बाल दिवस की शुभकामनाएँ! बच्चों को छोटी उम्र से बचत सिखाएँ।",
               "Bachchon ko paise ki samajh kaise dein")],
    "11-26": [("संविधान दिवस", "Constitution Day", "rashtriya", False, "all", "संविधान दिवस की शुभकामनाएँ।", "")],
    "12-24": [("राष्ट्रीय उपभोक्ता दिवस", "National Consumer Day", "rashtriya", False, "deals", "राष्ट्रीय उपभोक्ता दिवस: ठगी हो तो उपभोक्ता हेल्पलाइन 1915 पर शिकायत करें।", "")],
    "12-25": [("क्रिसमस", "Christmas", "isai", True, "all", "क्रिसमस की हार्दिक शुभकामनाएँ!", "")],
    "12-31": [("साल का आख़िरी दिन", "New Year's Eve", "rashtriya", False, "money", "साल का आख़िरी दिन - इस साल की बचत का हिसाब लगाइए।", "")],
}

DIFF = "पंचांग के अनुसार कुछ जगह यह एक दिन आगे-पीछे मनाया जाता है।"
DATED = {        # 2026: kai panchang + Business Standard (27 Oct 2026) se milan
    "2026-11-06": [("धनतेरस", "Dhanteras", "hindu", True, "deals", "धनतेरस की हार्दिक शुभकामनाएँ! खरीदारी से पहले कीमत और ऑफ़र का सही हिसाब ज़रूर लगाएँ।",
                    "Dhanteras par sona/bartan: asli kharch ka hisaab")],
    "2026-11-07": [("छोटी दिवाली", "Choti Diwali", "hindu", False, "all", "छोटी दिवाली की शुभकामनाएँ! " + DIFF, "")],
    "2026-11-08": [("दीपावली", "Diwali", "hindu", True, "all", "दीपावली की हार्दिक शुभकामनाएँ! माँ लक्ष्मी आपके घर सुख-समृद्धि लाएँ।",
                    "Diwali bonus ko sahi jagah kaise lagayein")],
    "2026-11-09": [("गोवर्धन पूजा", "Govardhan Puja", "hindu", False, "all", "गोवर्धन पूजा की शुभकामनाएँ! " + DIFF, "")],
    "2026-11-10": [("भाई दूज", "Bhai Dooj", "hindu", True, "all", "भाई दूज की शुभकामनाएँ! " + DIFF, "Bhai Dooj gift: bahan ke naam nivesh")],
    "2026-11-15": [("छठ पूजा", "Chhath Puja", "hindu", True, "all", "छठ महापर्व की हार्दिक शुभकामनाएँ! सूर्य देव और छठी मइया सबका कल्याण करें।", "")],
}


def events(day):
    """day 'YYYY-MM-DD' -> calendar_in jaisi event list (pakki, bina Gemini)."""
    out = []
    for row in FIXED.get(day[5:], []) + DATED.get(day, []):
        hi, en, comm, major, brand, text, vt = row
        out.append({"name_hi": hi, "name_en": en, "community": comm, "major": major, "brand": brand, "text": text,
                    "muhurat": "", "differs": DIFF if DIFF in text else "", "video_topic": vt, "sources": ["built-in calendar"]})
    return out
