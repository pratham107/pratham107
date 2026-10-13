"""Generate assets/leetcode-streak.svg (streak + day-wise heatmap only, no solved counts)."""
import json, os, sys, urllib.request
from datetime import datetime, timedelta, timezone

USERNAME = os.environ.get("LEETCODE_USER", "Prathamesh28")
OUT = "assets/leetcode-streak.svg"
ORANGE, BG, TXT, MUTED = "#FFA116", "#1A1A1A", "#FFFFFF", "#8C8C8C"

QUERY = """query($u:String!){matchedUser(username:$u){userCalendar{submissionCalendar}}}"""

def fetch_days(user):
    req = urllib.request.Request(
        "https://leetcode.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"u": user}}).encode(),
        headers={"Content-Type": "application/json", "Referer": "https://leetcode.com", "User-Agent": "Mozilla/5.0"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    cal = json.loads(data["data"]["matchedUser"]["userCalendar"]["submissionCalendar"])
    return {datetime.fromtimestamp(int(ts), timezone.utc).date() for ts, n in cal.items() if n > 0}

def streaks(days, today):
    cur = 0
    d = today if today in days else today - timedelta(days=1)
    while d in days:
        cur += 1
        d -= timedelta(days=1)
    best = run = 0
    prev = None
    for d in sorted(days):
        run = run + 1 if prev and d - prev == timedelta(days=1) else 1
        best = max(best, run)
        prev = d
    return cur, best

def render(days, today):
    cur, best = streaks(days, today)
    W, H = 600, 250
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
           f'<rect width="{W}" height="{H}" rx="12" fill="{BG}" stroke="#333"/>',
           f'<style>text{{font-family:Segoe UI,Arial,sans-serif}}</style>',
           f'<text x="24" y="34" fill="{ORANGE}" font-size="18" font-weight="700">LeetCode Streak</text>']
    cols = [(100, len(days), "Active days"), (300, cur, "Current streak"), (500, best, "Longest streak")]
    for x, v, label in cols:
        big = v if label != "Current streak" else v
        out.append(f'<text x="{x}" y="90" text-anchor="middle" fill="{ORANGE if label=="Current streak" else TXT}" font-size="36" font-weight="800">{big}</text>')
        out.append(f'<text x="{x}" y="112" text-anchor="middle" fill="{MUTED}" font-size="13">{label}</text>')
    # heatmap: last 26 weeks, columns = weeks, rows = Mon..Sun
    weeks = 26
    start = today - timedelta(days=today.weekday()) - timedelta(weeks=weeks - 1)
    size, gap = 14, 3
    x0, y0 = (W - weeks * (size + gap)) // 2, 135
    for w in range(weeks):
        for dow in range(7):
            d = start + timedelta(weeks=w, days=dow)
            if d > today:
                continue
            fill = ORANGE if d in days else "#2D2D2D"
            out.append(f'<rect x="{x0 + w*(size+gap)}" y="{y0 + dow*(size+gap)}" width="{size}" height="{size}" rx="3" fill="{fill}"/>')
    out.append("</svg>")
    return "\n".join(out)

if __name__ == "__main__":
    today = datetime.now(timezone.utc).date()
    days = set() if "--empty" in sys.argv else fetch_days(USERNAME)
    os.makedirs("assets", exist_ok=True)
    open(OUT, "w").write(render(days, today))
    print("wrote", OUT, "active days:", len(days))
