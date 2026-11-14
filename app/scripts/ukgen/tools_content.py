"""4 Uttarakhand tool page: title, H1, description aur naya likha samjhane wala content (kahin aur se copy nahi)."""
TOOLS = {
"char-dham-yatra-kharcha-calculator": dict(
 title="Char Dham Yatra Kharcha Calculator 2027",
 h1="Char Dham Yatra Kharcha Calculator: Kitna Kharch Aayega?",
 desc="Char Dham yatra ka andaazan budget: dham chuniye, log, gaadi aur hotel bataiye, aur Kedarnath-Yamunotri ke ghoda, palki ya heli ka kharcha jod kar hisaab dekhiye.",
 after="uttarakhand-char-dham-panch-kedar",
 sections=[
  ("Ye calculator kya jodta hai", [
   "Ye calculator chaar hisson ko jodta hai: sadak ka safar, rukne ka kharch, khana aur Kedarnath-Yamunotri ke paidal raaste ka saadhan. Sadak ki doori Haridwar ko aadhaar maan kar lagbhag km mein li gayi hai, aur aap Delhi, Rishikesh, Dehradun jaise shuruaati shahar chunte hain to us hisaab se doori badh jaati hai.",
   "Gaadi ke kharch mein apni car, taxi, tempo traveller ya bus ka andaaza alag hai. Hotel mein budget, madhyam aur achha teen star hain. Kedarnath ke lagbhag 16 km aur Yamunotri ke lagbhag 6 km ke raaste ke liye paidal, ghoda-khachchar, palki/dandi ya Kedarnath ke liye helicopter chun sakte hain.",
   "Din ki ginti calculator khud sujhata hai, par aap apni yojana ke hisaab se badal sakte hain. Har din badhne par hotel aur khane ka kharch bhi badhta hai."]),
  ("Is hisaab ko kaise padhein", [
   "Nateeja ek andaaza hai, pakka bill nahi. Peak season (May-June) mein hotel aur taxi ka kiraya kaafi badh jaata hai, aur barsaat mein sadak band hone se ek-do din extra lag sakte hain. Isliye budget mein kam se kam 10-15 pratishat extra rakhna samajhdaari hai.",
   "Ghoda, palki aur dandi ki dar zila prashasan tay karta hai aur har saal badal sakti hai. Yatra ke samay counter par likhi sarkari dar hi dekhein aur usi ki parchi lein."]),
  ("Calculator ki shuruaati dar (sab badli ja sakti hain)", [
   "Neeche wo dar hain jo calculator khulte hi bhari hoti hain. Ye aaj ke aam bazaar bhav ka andaaza hain; 'Dar badlein' khol kar aap apne shahar, apni gaadi aur is saal ki sarkari dar ke hisaab se inhe badal sakte hain, aur nateeja usi samay naye hisaab se ban jaata hai."],
   [["Kharcha", "Shuruaati dar", "Kaise ginti hoti hai"],
    ["Khana", "₹600 prati vyakti prati din", "log × din"],
    ["Taxi", "₹15 prati km", "kam se kam 250 km roz; 4-6 log par ek gaadi"],
    ["Tempo Traveller", "₹26 prati km", "12 log par ek gaadi"],
    ["Bus", "₹2.2 prati vyakti prati km", "har yatri ka alag ticket"],
    ["Apni car", "₹96 litre, 13 km/litre", "kul km ÷ average × dar"],
    ["Kedarnath ghoda / palki / heli", "₹6,000 / ₹16,000 / ₹7,500", "prati vyakti, aana-jaana"],
    ["Yamunotri ghoda / palki", "₹2,500 / ₹7,000", "prati vyakti, aana-jaana"],
    ["Parking, toll, pooja", "₹4,000", "poori yatra ka kul"]]),
  ("Ek misaal: 4 log, Kedarnath-Badrinath, 6 din", [
   "Maan lijiye 4 log Haridwar se Kedarnath aur Badrinath ki 6 din ki yatra par ja rahe hain. Khana calculator ki shuruaati dar se 4 log × 6 din × ₹600 = ₹14,400 banta hai. Kedarnath ke liye chaaron ghoda lein to 4 × ₹6,000 = ₹24,000, aur parking-toll-pooja ke ₹4,000 alag. Taxi ka kharch kul km × ₹15 se banta hai - km calculator khud jodta hai, aur roz kam se kam 250 km gina jaata hai.",
   "Hotel ka hisaab raaton ki ginti aur chune gaye star se judta hai. Yahi yatra paidal karne par ghode ke ₹24,000 bach jaate hain, aur heli lene par us hisse ka kharch badh jaata hai. Isi tarah ek-ek vikalp badal kar dekhiye ki kaunsa faisla aapke budget par sabse zyada asar daalta hai."]),
  ("Paise bachane ke seedhe tareeke", [
   "May-June ki bheed se bachkar September-October mein jaane par hotel sasta milta hai aur mausam bhi saaf rehta hai. Do dham (jaise Kedarnath-Badrinath) ki yatra ek saath karne se sadak ka kharch kam padta hai. Group mein tempo traveller lena aksar alag-alag taxi se sasta padta hai.",
   "Helicopter sabse mehnga vikalp hai. Iski booking sirf official raaste se karein; social media par sasti heli tickets ke naam par dhokhe ki shikayatein har saal aati hain."]),
 ],
 faqs=[
  ("Kya Char Dham yatra ke liye registration zaroori hai?", "Haan, Uttarakhand sarkar yatriyon ka panjikaran karwati hai. Registration sirf sarkari portal ya sarkari app se karein aur yatra par uski copy saath rakhein."),
  ("Kedarnath helicopter ki booking kahan se karein?", "Kedarnath heli seva ki booking ka official raasta IRCTC ka heliyatra portal hai. Kisi agent ya social media link par advance paisa na bhejein."),
  ("Calculator ka kharch pakka kyon nahi hota?", "Kiraya, hotel ki dar aur ghoda-palki ki sarkari dar har saal aur mausam ke hisaab se badalti hai. Isliye ye ek andaaza deta hai, pakka bill nahi."),
  ("Char Dham ke liye kitne din chahiye?", "Haridwar se chaaron dham aaram se karne mein aam taur par 9 se 12 din lagte hain. Ek ya do dham ke liye 3 se 6 din kaafi ho sakte hain."),
  ("Buzurgon ke liye kaunsa vikalp theek hai?", "Kedarnath aur Yamunotri ke lambe paidal raaste ke liye palki/dandi ya ghoda behtar hai, aur Kedarnath ke liye heli bhi. Yatra se pehle doctor se jaanch zaroor karayein."),
 ],
 tools=["fuel-cost-calculator", "mausam-weather"]),
"char-dham-kapat-countdown": dict(
 title="Char Dham Kapat Countdown aur Pahadi Tyohar",
 h1="Char Dham Kapat aur Uttarakhand Tyohar Countdown",
 desc="Char Dham ke kapat khulne-band hone aur Phooldei, Harela, Uttarayani jaise pahadi tyoharon ka live countdown, saath mein apni yatra ki tithi ka countdown.",
 after="uttarakhand-char-dham-panch-kedar",
 sections=[
  ("Kapat ki tithi kaise tay hoti hai", [
   "Char Dham ke kapat ki tithi panchang dekh kar mandir samiti aur purohit ghoshit karte hain, isliye har saal tareekh alag hoti hai. Badrinath ki tithi aam taur par Basant Panchami ke din Narendranagar ke rajdarbar mein ghoshit hoti hai. Kedarnath ki tithi Mahashivratri par Ukhimath ke Omkareshwar mandir mein tay hoti hai.",
   "Yamunotri aur Gangotri ke kapat aam taur par Akshaya Tritiya par khulte hain. Sardiyon mein inki pooja neeche ke gaon mein hoti hai: Ma Yamuna ki Kharsali mein aur Ma Ganga ki Mukhba mein."]),
  ("Countdown ko kaise samjhein", [
   "Jin tithiyon ki official ghoshna ho chuki hai, unke aage 'pakka' dikhta hai. Jinki ghoshna abhi baaki hai, unka andaazan mahina likha hai aur ghoshna hote hi unka countdown shuru hota hai. Pahadi tyoharon ki tithi sankranti par aadharit hai; apne ilake ke panchang se ek baar zaroor milayein, kyonki kahin-kahin ek din ka antar ho sakta hai.",
   "Apni yatra ki tithi daal kar aap apna alag countdown bhi dekh sakte hain. Ye sirf aapki screen par chalta hai; koi jaankari kahin save ya bheji nahi jaati."]),
  ("Kapat ki ghoshna aur sardi ka pooja-sthal", [
   "Ye table batati hai ki har dham ki tithi kahan ghoshit hoti hai aur kapat band hone ke baad sardiyon mein bhagwan ki pooja kahan hoti hai. Sardi mein darshan ke liye log inhi gaddi-sthalon par jaate hain."],
   [["Dham", "Kapat khulne ki tithi", "Kahan ghoshna", "Sardi mein pooja"],
    ["Badrinath", "Basant Panchami par tay", "Narendranagar rajdarbar", "Pandukeshwar aur Joshimath"],
    ["Kedarnath", "Mahashivratri par tay", "Omkareshwar mandir, Ukhimath", "Omkareshwar mandir, Ukhimath"],
    ["Gangotri", "Aam taur par Akshaya Tritiya", "Mandir samiti", "Mukhba gaon"],
    ["Yamunotri", "Aam taur par Akshaya Tritiya", "Mandir samiti", "Kharsali gaon"]]),
  ("Kapat kab band hote hain", [
   "Kapat khulne ki tarah band hone ki tithi bhi parampara se judi hai. Gangotri ke kapat aam taur par Diwali ke agle din Annakoot (Govardhan Pooja) par, aur Kedarnath aur Yamunotri ke kapat Bhai Dooj par band hote hain. Badrinath ke kapat band hone ki tithi Vijayadashami par ghoshit hoti hai aur aam taur par November mein padti hai.",
   "Kapat band hone ke din doli yatra nikalti hai jo bhagwan ko sardi ke gaddi-sthal tak le jaati hai. Is din bhi kaafi bheed hoti hai, isliye band hone ki tithi par jaane wale yatri hotel pehle se tay kar lein. Sahi tithi har saal mandir samiti ki ghoshna se hi pakki maanein."]),
  ("Countdown ka sabse achha istemal", [
   "Yatra ki tithi daal kar countdown lagaiye aur usi hisaab se kaam baantiye: 30 din pehle registration aur hotel, 15 din pehle taxi ya bus ki booking, 7 din pehle mausam ki chetavani aur sadak ki sthiti, aur nikalne se ek din pehle dawaiyan, garm kapde aur zaroori kaagaz. Buzurg saath hon to unki sehat ki jaanch bhi pehle hafte mein karwa lijiye.",
   "Tyoharon ka countdown parivaar ke liye bhi kaam ka hai. Phooldei aur Harela jaise parv ki taiyari bachchon ke saath pehle se ki jaaye to wo apni parampara ko yaad rakhte hain. Pravasi parivar is countdown se gaon aane ki tithi pehle se tay kar sakte hain."]),
  ("Yatra ki taiyari kab shuru karein", [
   "Kapat khulne ke pehle do hafte mein sabse zyada bheed hoti hai. Registration, hotel aur heli ki booking ghoshna ke turant baad karna aasaan rehta hai. Barsaat (July-August) mein bhooskhalan ka khatra zyada hota hai, isliye mausam vibhag ki chetavani dekh kar hi nikalein."]),
 ],
 faqs=[
  ("Badrinath ke kapat kholne ki tithi kab ghoshit hoti hai?", "Aam taur par Basant Panchami ke din Narendranagar rajdarbar mein panchang dekh kar ghoshna hoti hai."),
  ("Kedarnath ke kapat ki tithi kahan tay hoti hai?", "Mahashivratri ke din Ukhimath ke Omkareshwar mandir mein Kedarnath ke kapat khulne ki tithi tay hoti hai."),
  ("Sardi mein Kedarnath ki pooja kahan hoti hai?", "Kapat band hone ke baad Baba Kedar ki pooja Ukhimath ke Omkareshwar mandir mein hoti hai."),
  ("Phooldei aur Harela kab manaye jaate hain?", "Phooldei Chaitra mahine ki sankranti par aur Harela Shravan ki sankranti ke aas-paas manaya jaata hai. Sahi tithi apne panchang se dekhein."),
  ("Kya ye countdown meri yatra ki tithi save karta hai?", "Nahi. Aapki daali hui tithi sirf usi samay aapki screen par countdown dikhane ke kaam aati hai, kahin bheji ya rakhi nahi jaati."),
 ],
 tools=["din-bache-calculator"]),
"kumaoni-garhwali-shabdkosh": dict(
 title="Kumaoni Garhwali Shabdkosh: 1000+ Pahadi Shabd",
 h1="Kumaoni-Garhwali Shabdkosh: Pahadi Shabd aur Unke Arth",
 desc="Kumaoni aur Garhwali ke 1,000 se zyada pahadi shabd unke Hindi aur English arth ke saath khojiye: rishte, ghar, kheti, prakriti aur bolchaal ke shabd, zila-wise.",
 after="uttarakhand-pahadi-shabdkosh",
 sections=[
  ("Shabdkosh kaise istemal karein", [
   "Upar ke dabbe mein pahadi shabd ya uska Hindi arth likhiye. Boli (Kumaoni, Garhwali, Terai, Haridwar), zila aur prakar (rishte-naate ya roz ke shabd) chun kar nateeje chhote kiye ja sakte hain. Har shabd ke saath likha hai ki wo kis zile ke page se liya gaya hai.",
   "Abhi ismein Almora, Bageshwar, Nainital, Pithoragarh, Udham Singh Nagar, Chamoli, Pauri Garhwal, Rudraprayag, Tehri Garhwal, Dehradun aur Haridwar ke pages ke shabd hain. Champawat aur Uttarkashi ke shabd aage judenge."]),
  ("Rishton ke kuch shabd: Kumaoni aur Garhwali", [
   "Ye kuch aam rishton ke shabd hain jo shabdkosh ke data mein alag-alag zilon se aaye hain. Ek hi rishte ke liye ilake ke hisaab se do-teen roop milte hain, isliye sab roop saath likhe gaye hain."],
   [["Hindi", "Kumaoni", "Garhwali"],
    ["Maa", "Ija / Ijja, kuch jagah Aama", "Bwe / Boi, Maa"],
    ["Pita", "Bauji, Babu", "Baba, Bubaji"],
    ["Beta", "Chyal", "Chhora"],
    ["Chhoti bahan", "Bhuli", "Bhuli"],
    ["Bahu", "Bwari", "Bwari"],
    ["Maayka", "Mait", "Maiti, Mait"],
    ["Dadi", "Aama, Jiya", "Dadi, Aama"]]),
  ("Prakriti aur ghar ke 10 roz ke shabd (Kumaoni)", [
   "Ye shabd zila pages ki shabd-suchi se liye gaye hain aur pahad ke roz ke jeevan mein sabse zyada bole jaate hain. Garhwal mein inmein se kai shabd thode alag uchcharan ke saath milte hain."],
   [["Shabd", "Arth"],
    ["Gham", "Dhoop"],
    ["Hyun", "Barf"],
    ["Danda", "Pahadi dhaar (ridge)"],
    ["Gad / Gadhera", "Pahadi nala"],
    ["Naula", "Pathar se bana paani ka paramparik srot"],
    ["Dhara", "Pahad se behti paani ki dhaar"],
    ["Goth", "Ghar ka neeche ka kamra, jahan pashu aur anaaj rehte the"],
    ["Okhal", "Anaaj kootne ke liye pathar ka gaddha"],
    ["Gharat", "Gadhere ke paani se chalne wali chakki"],
    ["Mait", "Ladki ka maayka"]]),
  ("Ek shabd ke kai roop kyon milte hain", [
   "Pahad mein har kuch gaon par boli ka rang badal jaata hai. Isliye ek hi cheez ke liye do-teen shabd, ya ek shabd ke thode alag uchcharan milna aam baat hai. Agar aapke gaon mein koi shabd alag tarah bola jaata hai, to wo bhi utna hi sahi hai.",
   "Ye shabdkosh bolchaal ke shabdon ki suchi hai, bhasha-vigyan ka pramanik granth nahi. Kisi shabd ka arth galat lage to contact page se batayein, hum jaanch kar sudhaar denge."]),
  ("Shabd sikhne ka aasaan tareeka", [
   "Roz 'Aaj ka shabd' dekhiye aur use din mein ek baar kisi baat mein boliye. Ghar ke buzurg se poochhiye ki unke gaon mein ye shabd kaise bola jaata tha, aur alag roop mile to use bhi yaad rakhiye. Bachchon ke saath rishton ke naam (Ija, Bauji, Bhula, Bhuli) se shuruaat karna sabse aasaan hai, kyonki ye roz kaam aate hain.",
   "Khoj mein Hindi arth likh kar bhi shabd dhoondh sakte hain - jaise 'paani ka srot' likhne par naula aur dhara dono milte hain. Zila chun kar dekhiye ki ek hi cheez ke liye Kumaon aur Garhwal mein alag shabd kaise hain."]),
  ("Purane shabd kyon bachane zaroori hain", [
   "Gharat, naula, dhara, okhal, thaatal jaise kai shabd un cheezon ke naam hain jo ab gaon se kam hoti ja rahi hain. Jab cheez chali jaati hai to uska naam bhi bhoolne lagta hai. Bachchon ke saath ye shabd boliye aur buzurgon se unke arth poochhiye; isi se boli zinda rehti hai."]),
 ],
 faqs=[
  ("Kumaoni mein maa ko kya kehte hain?", "Kumaoni mein maa ko aam taur par Ija (kahin Ijja ya Aama) kaha jaata hai, jabki Garhwali mein Bwe, Boi ya Maa."),
  ("Kumaoni aur Garhwali mein kya antar hai?", "Dono Madhya Pahadi samooh ki boliyan hain. Bahut se shabd milte-julte hain, par roz ke kai shabd, uchcharan aur vyakaran ke kuch roop alag hain."),
  ("Is shabdkosh mein shabd kahan se liye gaye hain?", "Sab Hisaab ke Uttarakhand zila pages se. Har shabd ke saath uske zile ka naam diya gaya hai."),
  ("Mujhe koi shabd galat laga to kya karein?", "Contact page par shabd aur aapke ilake ka naam likh kar bhejein. Jaanch ke baad sudhaar kiya jaata hai."),
  ("Kya ye shabdkosh offline chalta hai?", "Page ek baar khul jaane ke baad khoj aapke phone mein hi chalti hai, alag se internet ki zaroorat nahi padti."),
 ],
 tools=["nali-mutthi-converter"]),
"uttarakhand-gk-quiz": dict(
 title="Uttarakhand GK Quiz: Roz 10 Sawal (UKSSSC)",
 h1="Uttarakhand GK Quiz: Roz Ke 10 Sawal Vyakhya Ke Saath",
 desc="Uttarakhand GK ka roz ka quiz: itihas, zile, nadiyan, andolan aur tyoharon par 10 sawal, har jawab ki vyakhya ke saath. UKSSSC, UKPSC aur Patwari taiyari ke liye.",
 after="uttarakhand-gk-ukpsc",
 sections=[
  ("Quiz kaise kaam karta hai", [
   "Har din aapko 10 sawal milte hain, aur din badalne par sawalon ka set bhi badal jaata hai. Har sawal ke chaar vikalp hain. Jawab chunte hi sahi vikalp aur ek chhoti vyakhya dikhti hai, taaki sirf yaad karne ki jagah baat samajh mein aaye.",
   "Abhi bank mein 109 sawal hain jo Sab Hisaab ke Uttarakhand pages ke tathyon se banaye gaye hain. Practice ke liye 'Aur 10 sawal' dabakar agla set le sakte hain."]),
  ("Taiyari mein iska sahi istemal", [
   "Quiz ko roz ki aadat banaiye: 10 sawal, phir galat hue sawalon ki vyakhya dobara padhiye. Jis vishay mein zyada galti ho, us zile ya topic ka page khol kar poora section padhiye. Ek hafte baad wahi sawal dobara aane par farak khud dikhega.",
   "Dhyan rahe ki ye abhyas ke sawal hain, asli pichhle prashn-patra nahi. Pariksha ka syllabus, tithi aur patrata hamesha UKSSSC aur UKPSC ki official site par notification se hi dekhein."]),
  ("Uttarakhand ke kuch pakke tathya (jaldi dohraane ke liye)", [
   "Quiz shuru karne se pehle ye table ek baar dekh lein. Inhi tathyon par kai sawal bante hain, aur pariksha mein bhi ye aksar poochhe jaate hain."],
   [["Tathya", "Jawab"],
    ["Rajya ka gathan", "9 November 2000 (Bharat ka 27va rajya)"],
    ["Naam Uttaranchal se Uttarakhand", "1 January 2007"],
    ["Mandal aur zile", "2 mandal (Garhwal, Kumaon), 13 zile"],
    ["High Court", "Nainital"],
    ["Grishmkalin rajdhani", "Gairsain (Bharadisain)"],
    ["Sabse oonchi choti", "Nanda Devi, lagbhag 7,816 meter"],
    ["Rajya pushp / pakshi / pashu / vriksh", "Brahmakamal / Himalayan Monal / Kasturi mrig / Buransh"]]),
  ("13 zile: mukhyalay aur vidhan sabha seat", [
   "Zilon ke mukhyalay aur seaton ki ginti par sawal har pariksha mein aate hain. Rajya mein kul 70 vidhan sabha seat hain; neeche har zile ki ginti hai (Uttarakhand ke mukhya nirvachan adhikari ki suchi ke anusar)."],
   [["Zila", "Mukhyalay", "Mandal", "Vidhan sabha seat"],
    ["Almora", "Almora", "Kumaon", "6"],
    ["Bageshwar", "Bageshwar", "Kumaon", "2"],
    ["Champawat", "Champawat", "Kumaon", "2"],
    ["Nainital", "Nainital", "Kumaon", "6"],
    ["Pithoragarh", "Pithoragarh", "Kumaon", "4"],
    ["Udham Singh Nagar", "Rudrapur", "Kumaon", "9"],
    ["Chamoli", "Gopeshwar", "Garhwal", "3"],
    ["Dehradun", "Dehradun", "Garhwal", "10"],
    ["Haridwar", "Haridwar", "Garhwal", "11"],
    ["Pauri Garhwal", "Pauri", "Garhwal", "6"],
    ["Rudraprayag", "Rudraprayag", "Garhwal", "2"],
    ["Tehri Garhwal", "New Tehri", "Garhwal", "6"],
    ["Uttarkashi", "Uttarkashi", "Garhwal", "3"]]),
  ("Galti se seekhne ka tareeka", [
   "Quiz mein galat jawab sharm ki baat nahi, seekhne ka sabse achha mauka hai. Har galat sawal ki vyakhya ko apni copy mein ek line mein likh lijiye aur hafte ke ant mein sirf wahi lines dohraiye. Isse yaad karne ka samay kam lagta hai aur kamzor vishay saaf dikhte hain.",
   "Ek aur kaam ki aadat: kisi bhi tareekh ya sankhya wale sawal ke saath us ghatna ki wajah bhi yaad kijiye. Jaise rajya andolan ki tareekh ke saath ye bhi ki andolan kis maang par tha. Wajah yaad ho to tareekh bhi zyada der tak yaad rehti hai."]),
  ("Pariksha ke hisaab se taiyari ka kram", [
   "Pehle hafte rajya ke gathan, zilon aur mandalon ke tathya pakke kijiye; doosre hafte nadiyan, glacier aur parvat; teesre hafte itihas aur andolan (Kumaon Parishad, Coolie Begar, Chipko, rajya andolan); chauthe hafte tyohar, mele, lok-kala aur boli. Har hafte ke ant mein usi vishay ke sawal quiz mein dobara dekhiye.",
   "UKSSSC aur Patwari jaisi pariksha mein zila-star ke sawal bhi aate hain. Isliye apne zile ki guide (tehsil, block, mandir, mele) zaroor padhiye - us zile ka GK page bhi isi site par hai."]),
  ("Kis tarah ke sawal milenge", [
   "Rajya ka gathan, zilon ka banna, mukhyalaya aur RTO code, nadiyan aur unke udgam, Char Dham aur Panch Kedar, Chipko aur rajya andolan, prasiddh vyakti, mele aur tyohar, aur pahadi boli ke shabd. Sawal chhote aur seedhe rakhe gaye hain taaki mobile par aasaani se ho jayein."]),
 ],
 faqs=[
  ("Roz kitne sawal aate hain?", "Har din 10 sawal ka naya set aata hai. Zyada practice ke liye 'Aur 10 sawal' daba sakte hain."),
  ("Kya ye UKPSC ke asli pichhle sawal hain?", "Nahi. Ye Uttarakhand ke tathyon par bane abhyas prashn hain. Asli pichhle prashn-patra aayog ki official site par dekhein."),
  ("Uttarakhand rajya kab bana?", "9 November 2000 ko Uttarakhand Bharat ka 27va rajya bana. 1 January 2007 se iska naam Uttaranchal se badal kar Uttarakhand hua."),
  ("Galat jawab wale sawal dobara kaise dekhein?", "Quiz ke ant mein galat hue sawal unki vyakhya ke saath dobara dikhte hain, taaki aap unhe phir se padh sakein."),
  ("Kya quiz ke liye login chahiye?", "Nahi. Quiz bina login ke chalta hai aur aapka koi data kahin save nahi hota."),
 ],
 tools=["age-calculator"]),
}
