"""v2.5.3: YouTube Partner Program progress (sirf padhna). 1 Feb 2027 se naye applicant: 1,000 subs + 8,000 watch hours (365 din) ya
20M Shorts views (90 din); 31 Jan 2027 tak purani seema 4,000 hours / 10M. Fan-funding: 500 subs.
v2.5.7: jis brand ka /analytics login ho uska watch-hours/Shorts-views YouTube Analytics API se (andaza; asli ginti Studio -> Earn mein).
Jiska login nahi, uska sirf subscribers + deadline."""
import datetime

from .config import BRANDS

OLD = {"subs": 1000, "hours": 4000, "shorts": 10_000_000}
NEW = {"subs": 1000, "hours": 8000, "shorts": 20_000_000}
CUTOVER = datetime.date(2027, 2, 1)


def days_left(today=None):
    return (CUTOVER - (today or datetime.date.today())).days


def analytics_progress(brand, today=None):
    """-> {'hours': 365 din long-form+live watch hours, 'shorts90': 90 din Shorts views} ya None (analytics login nahi / galti)."""
    try:
        from . import analytics as AN
        if not AN.has(brand):
            return None
        end = today or datetime.date.today()

        def rows(days):
            j = AN._get(brand, "https://youtubeanalytics.googleapis.com/v2/reports", ids="channel==MINE",
                        startDate=str(end - datetime.timedelta(days=days)), endDate=str(end), dimensions="creatorContentType",
                        metrics="views,estimatedMinutesWatched")
            return {r[0]: (r[1], r[2]) for r in j.get("rows", [])}
        y, q = rows(365), rows(90)
        mins = sum(v[1] for k, v in y.items() if k != "SHORTS")
        return {"hours": mins / 60.0, "shorts90": int(q.get("SHORTS", (0, 0))[0])}
    except Exception:
        return None


def line(brand, st, today=None):
    subs = st.get("subs", 0)
    t = f"• {BRANDS[brand]['name']}: {subs} subs ({subs * 100 // OLD['subs']}% / 1,000), {st.get('videos', 0)} video"
    ap = analytics_progress(brand, today)
    if ap:
        t += (f"\n   ⏱ ~{ap['hours']:.0f} watch hours / 365 din (4,000 chahiye), Shorts {ap['shorts90']:,} views / 90 din (10M)")
    return t


def report(today=None):
    from . import youtube
    d = days_left(today)
    L = ["🎯 YPP HAAL (sirf padhna)",
         (f"31 Jan 2027 tak (aur {d} din) purani seema se apply ho sakta hai: 1,000 subs + 4,000 watch hours ya 10M Shorts views (90 din)."
          if d > 0 else "1 Feb 2027 se nayi seema: 1,000 subs + 8,000 hours ya 20M Shorts views (90 din).")]
    rows = []
    for b in BRANDS:
        try:
            if youtube.has_login(b):
                st = youtube.channel_stats(b)
                rows.append((st.get("subs", 0), line(b, st, today)))
        except Exception:
            rows.append((-1, f"• {BRANDS[b]['name']}: abhi padh nahi paya"))
    rows.sort(key=lambda x: -x[0])
    L += [r[1] for r in rows]
    if rows and rows[0][0] >= 0:
        L.append(f"➡️ Sabse aage: {rows[0][1][2:].split(':')[0]}. Watch hours / Shorts views ka andaza upar (analytics login wale); asli ginti YouTube Studio → Earn mein. Analytics login nahi to /analytics.")
    L.append("Fan-funding (Super Thanks/membership) 500 subs + 3,000 hours / 3M Shorts views par - seema nahi badli.")
    return "\n".join(L)
