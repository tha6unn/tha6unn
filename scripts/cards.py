"""Builds the auto-updating profile cards and refreshes the README's live sections.

Runs daily in .github/workflows/profile.yml. Locally:
    GITHUB_TOKEN=... python scripts/cards.py --out dist
    python scripts/cards.py --demo --out dist     # fake data, no network

Writes <out>/{stats,streak,activity,languages}-{dark,light}.svg and rewrites the
blocks between <!-- LIVE:* --> markers in README.md.
"""

import argparse
import datetime as dt
import json
import os
import random
import re
import urllib.request
from pathlib import Path

from theme import FONT, MONO, THEMES, esc, gradient

ROOT = Path(__file__).resolve().parent.parent
LOGIN = os.environ.get("PROFILE_LOGIN", "tha6unn")
API = "https://api.github.com/graphql"
SKIP_LANGS = {"Jupyter Notebook", "HTML", "CSS", "SCSS", "Batchfile", "PowerShell", "Shell", "Dockerfile", "PLpgSQL", "Procfile"}


# --------------------------------------------------------------------------- data

def gql(query: str, variables: dict, token: str) -> dict:
    req = urllib.request.Request(
        API,
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.load(r)
    if body.get("errors"):
        raise RuntimeError(body["errors"])
    return body["data"]


PROFILE_Q = """
query($login: String!) {
  user(login: $login) {
    createdAt
    followers { totalCount }
    pullRequests { totalCount }
    repositories(ownerAffiliations: OWNER, isFork: false, first: 100, orderBy: {field: PUSHED_AT, direction: DESC}) {
      totalCount
      nodes {
        name description url isPrivate stargazerCount pushedAt homepageUrl
        primaryLanguage { name color }
        languages(first: 12, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name color } } }
      }
    }
  }
}"""

YEAR_Q = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar { weeks { contributionDays { date contributionCount } } }
    }
  }
}"""


def fetch(token: str) -> dict:
    user = gql(PROFILE_Q, {"login": LOGIN}, token)["user"]
    start = dt.datetime.fromisoformat(user["createdAt"].replace("Z", "+00:00")).year
    today = dt.datetime.now(dt.timezone.utc)
    days = {}
    for year in range(start, today.year + 1):
        frm = dt.datetime(year, 1, 1, tzinfo=dt.timezone.utc)
        to = min(dt.datetime(year, 12, 31, 23, 59, 59, tzinfo=dt.timezone.utc), today)
        cal = gql(YEAR_Q, {"login": LOGIN, "from": frm.isoformat(), "to": to.isoformat()}, token)
        for week in cal["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]:
            for d in week["contributionDays"]:
                days[d["date"]] = d["contributionCount"]
    return {"user": user, "days": days}


def demo() -> dict:
    rnd = random.Random(7)
    today = dt.date.today()
    days = {}
    for i in range(800):
        d = today - dt.timedelta(days=i)
        days[d.isoformat()] = 0 if rnd.random() < 0.45 else rnd.choice([1, 2, 3, 5, 8, 13])
    for i in range(9):
        days[(today - dt.timedelta(days=i)).isoformat()] = 4
    langs = [("TypeScript", "#3178c6", 900), ("Python", "#3572A5", 700), ("JavaScript", "#f1e05a", 420),
             ("PLpgSQL", "#336790", 90), ("Java", "#b07219", 40), ("Go", "#00ADD8", 20)]
    nodes = [
        {"name": f"project-{i}", "description": "Demo repository", "url": "#", "isPrivate": i % 2 == 0,
         "stargazerCount": i, "pushedAt": (today - dt.timedelta(days=i * 9)).isoformat() + "T00:00:00Z",
         "homepageUrl": None, "primaryLanguage": {"name": "TypeScript", "color": "#3178c6"},
         "languages": {"edges": [{"size": s * 1000, "node": {"name": n, "color": c}} for n, c, s in langs]}}
        for i in range(8)
    ]
    user = {"createdAt": "2022-06-01T00:00:00Z", "followers": {"totalCount": 5},
            "pullRequests": {"totalCount": 214}, "repositories": {"totalCount": 75, "nodes": nodes}}
    return {"user": user, "days": days}


def summarise(data: dict) -> dict:
    days = sorted((dt.date.fromisoformat(k), v) for k, v in data["days"].items())
    today = dt.date.today()
    days = [(d, c) for d, c in days if d <= today]

    longest = run = 0
    longest_end = longest_start = run_start = None
    for d, c in days:
        if c > 0:
            if run == 0:
                run_start = d
            run += 1
            if run > longest:
                longest, longest_start, longest_end = run, run_start, d
        else:
            run = 0

    # Current streak survives a quiet "today" (the day isn't over yet).
    current, cur_start = 0, None
    lookup = dict(days)
    cursor = today if lookup.get(today, 0) > 0 else today - dt.timedelta(days=1)
    while lookup.get(cursor, 0) > 0:
        current += 1
        cur_start = cursor
        cursor -= dt.timedelta(days=1)

    year_total = sum(c for d, c in days if d.year == today.year)
    weeks = []
    window_start = today - dt.timedelta(days=7 * 52 - 1)
    for i in range(52):
        ws = window_start + dt.timedelta(days=7 * i)
        weeks.append((ws, sum(lookup.get(ws + dt.timedelta(days=j), 0) for j in range(7))))

    repos = data["user"]["repositories"]["nodes"]
    lang_bytes, lang_color = {}, {}
    for r in repos:
        for e in r["languages"]["edges"]:
            n = e["node"]["name"]
            if n in SKIP_LANGS:
                continue
            lang_bytes[n] = lang_bytes.get(n, 0) + e["size"]
            lang_color[n] = e["node"]["color"] or "#8b949e"

    return {
        "total": sum(c for _, c in days),
        "year_total": year_total,
        "current": current, "cur_start": cur_start,
        "longest": longest, "longest_start": longest_start, "longest_end": longest_end,
        "first_day": days[0][0] if days else today,
        "weeks": weeks,
        "repos": data["user"]["repositories"]["totalCount"],
        "stars": sum(r["stargazerCount"] for r in repos),
        "prs": data["user"]["pullRequests"]["totalCount"],
        "langs": sorted(((n, b, lang_color[n]) for n, b in lang_bytes.items()), key=lambda x: -x[1]),
        "public": [r for r in repos if not r["isPrivate"]],
        "today": today,
    }


# ------------------------------------------------------------------------ drawing

def frame(t: dict, w: int, h: int, title: str, body: str, label: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(label)}">
<title>{esc(label)}</title>
<defs>{gradient("acc", t["accents"])}{gradient("accv", t["accents"], x2="0%", y2="100%")}</defs>
<style>
.h {{ font: 700 15px {FONT}; fill: {t["text"]}; }}
.k {{ font: 500 13px {FONT}; fill: {t["muted"]}; }}
.v {{ font: 700 26px {FONT}; fill: {t["text"]}; }}
.big {{ font: 800 44px {FONT}; fill: {t["text"]}; }}
.s {{ font: 500 12px {MONO}; fill: {t["muted"]}; }}
.in {{ animation: in .8s cubic-bezier(.2,.7,.2,1) both; }}
@keyframes in {{ from {{ opacity: 0; transform: translateY(8px); }} to {{ opacity: 1; transform: none; }} }}
@media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
</style>
<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="16" fill="{t["bg"]}" stroke="{t["border"]}"/>
<rect x="24" y="22" width="4" height="16" rx="2" fill="url(#accv)"/>
<text x="36" y="35" class="h">{esc(title)}</text>
{body}
</svg>
"""


def fmt(n: int) -> str:
    return f"{n:,}"


def short(d) -> str:
    return d.strftime("%b %-d, %Y") if d else "–"


def stats_card(s: dict, t: dict) -> str:
    items = [
        ("Contributions in " + str(s["today"].year), s["year_total"]),
        ("All-time contributions", s["total"]),
        ("Pull requests opened", s["prs"]),
        ("Repositories owned", s["repos"]),
    ]
    body = []
    for i, (k, v) in enumerate(items):
        x, y = 36 + (i % 2) * 270, 92 + (i // 2) * 78
        body.append(
            f'<g class="in" style="animation-delay:{i * 0.1:.1f}s">'
            f'<text x="{x}" y="{y}" class="v">{fmt(v)}</text>'
            f'<text x="{x}" y="{y + 22}" class="k">{esc(k)}</text></g>'
        )
    return frame(t, 600, 230, "Shipping log", "".join(body), f"{s['year_total']} contributions this year")


def streak_card(s: dict, t: dict) -> str:
    cx, cy, r = 300, 106, 46
    cur_range = f"{short(s['cur_start'])} – today" if s["current"] else "starts with the next commit"
    body = f"""
<g class="in">
<text x="96" y="112" text-anchor="middle" class="v">{fmt(s["total"])}</text>
<text x="96" y="136" text-anchor="middle" class="k">Total contributions</text>
<text x="96" y="156" text-anchor="middle" class="s">{short(s["first_day"])} – now</text>
</g>
<line x1="192" y1="70" x2="192" y2="200" stroke="{t["border"]}"/>
<g class="in" style="animation-delay:.15s">
<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{t["grid"]}" stroke-width="8"/>
<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="url(#acc)" stroke-width="8" stroke-linecap="round"
  stroke-dasharray="{2 * 3.1416 * r:.1f}" stroke-dashoffset="{2 * 3.1416 * r:.1f}" transform="rotate(-90 {cx} {cy})">
  <animate attributeName="stroke-dashoffset" to="0" dur="1.4s" fill="freeze" calcMode="spline" keySplines="0.2 0.7 0.2 1" keyTimes="0;1"/>
</circle>
<text x="{cx}" y="{cy + 13}" text-anchor="middle" class="big" style="font-size:38px">{s["current"]}</text>
<text x="{cx}" y="{cy + r + 28}" text-anchor="middle" class="k">Current streak (days)</text>
<text x="{cx}" y="{cy + r + 46}" text-anchor="middle" class="s">{esc(cur_range)}</text>
</g>
<line x1="408" y1="70" x2="408" y2="200" stroke="{t["border"]}"/>
<g class="in" style="animation-delay:.3s">
<text x="504" y="112" text-anchor="middle" class="v">{s["longest"]}</text>
<text x="504" y="136" text-anchor="middle" class="k">Longest streak (days)</text>
<text x="504" y="156" text-anchor="middle" class="s">{s["longest_start"].strftime("%b %-d") if s["longest_start"] else "–"} – {short(s["longest_end"])}</text>
</g>"""
    return frame(t, 600, 230, "Streak", body, f"Current streak {s['current']} days, longest {s['longest']} days")


def activity_card(s: dict, t: dict) -> str:
    w, h = 1200, 230
    left, right, top, bottom = 36, 24, 64, 44
    pw, ph = w - left - right, h - top - bottom
    weeks = s["weeks"]
    peak = max((c for _, c in weeks), default=0) or 1
    slot = pw / len(weeks)
    bw = max(4, slot - 6)
    bars, labels = [], []
    month_seen = set()
    base = top + ph
    for i, (ws, c) in enumerate(weeks):
        x = left + i * slot + (slot - bw) / 2
        bh = 0 if c == 0 else max(4, ph * c / peak)
        if bh:
            # rounded top, square base
            rr = min(4, bw / 2, bh)
            d = (f"M{x:.1f},{base} V{base - bh + rr:.1f} Q{x:.1f},{base - bh:.1f} {x + rr:.1f},{base - bh:.1f} "
                 f"H{x + bw - rr:.1f} Q{x + bw:.1f},{base - bh:.1f} {x + bw:.1f},{base - bh + rr:.1f} V{base} Z")
            bars.append(
                f'<path d="{d}" fill="url(#accv)" opacity="0">'
                f'<title>Week of {short(ws)}: {c} contributions</title>'
                f'<animate attributeName="opacity" from="0" to="1" begin="{i * 0.015:.3f}s" dur=".3s" fill="freeze"/></path>'
            )
        key = (ws.year, ws.month)
        if key not in month_seen and ws.day <= 7:
            month_seen.add(key)
            labels.append(f'<text x="{x:.1f}" y="{h - 18}" class="s">{ws.strftime("%b")}</text>')
    best = max(weeks, key=lambda x: x[1])
    total = sum(c for _, c in weeks)
    body = (
        f'<line x1="{left}" y1="{base}" x2="{w - right}" y2="{base}" stroke="{t["border"]}"/>'
        + "".join(bars) + "".join(labels)
        + f'<text x="{w - right}" y="35" text-anchor="end" class="s">{fmt(total)} in the last 52 weeks · busiest week {fmt(best[1])} ({short(best[0])})</text>'
    )
    return frame(t, w, h, "Weekly contributions, last 52 weeks", body, f"{total} contributions in the last 52 weeks")


def languages_card(s: dict, t: dict) -> str:
    w, h = 1200, 150
    langs = s["langs"][:6]
    other = sum(b for _, b, _ in s["langs"][6:])
    if other:
        langs = langs + [("Other", other, t["muted"])]
    total = sum(b for _, b, _ in langs) or 1
    x, bar = 36.0, []
    bw = w - 72
    for i, (n, b, c) in enumerate(langs):
        seg = bw * b / total
        if seg < 1:
            continue
        bar.append(f'<rect x="{x:.1f}" y="62" width="{max(seg - 2, 1):.1f}" height="12" rx="3" fill="{c}"><title>{esc(n)} {100 * b / total:.1f}%</title></rect>')
        x += seg
    legend = []
    for i, (n, b, c) in enumerate(langs):
        lx, ly = 36 + i * 162, 112
        legend.append(
            f'<g class="in" style="animation-delay:{i * 0.07:.2f}s"><circle cx="{lx + 6}" cy="{ly - 5}" r="6" fill="{c}"/>'
            f'<text x="{lx + 20}" y="{ly}" class="k" style="fill:{t["text"]}">{esc(n)}</text>'
            f'<text x="{lx + 20}" y="{ly + 18}" class="s">{100 * b / total:.1f}%</text></g>'
        )
    return frame(t, w, h, "What I write (by code size)", "".join(bar) + "".join(legend), "Languages by code size")


# ------------------------------------------------------------------------- README

def ago(iso: str, today: dt.date) -> str:
    d = dt.date.fromisoformat(iso[:10])
    n = (today - d).days
    if n <= 0:
        return "today"
    if n == 1:
        return "yesterday"
    if n < 30:
        return f"{n} days ago"
    if n < 365:
        return f"{n // 30} mo ago"
    return f"{n // 365} yr ago"


def live_blocks(s: dict) -> dict:
    rows = []
    for r in s["public"][:5]:
        lang = (r["primaryLanguage"] or {}).get("name", "")
        desc = (r["description"] or "").strip()
        desc = desc if len(desc) <= 90 else desc[:87].rstrip() + "…"
        desc = esc(desc).replace("|", "\\|")
        rows.append(
            f"| [**{r['name']}**]({r['url']}) | {desc or '–'} | {lang or '–'} | {ago(r['pushedAt'], s['today'])} |"
        )
    recent = "\n".join(["| Repo | What it is | Lang | Pushed |", "|---|---|---|---|", *rows])
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%-d %b %Y, %H:%M UTC")
    return {
        "RECENT": recent,
        "UPDATED": f"<sub>Live sections refreshed by GitHub Actions · last run {stamp}</sub>",
    }


def patch_readme(blocks: dict) -> None:
    path = ROOT / "README.md"
    text = path.read_text(encoding="utf-8")
    for key, value in blocks.items():
        text = re.sub(
            rf"(<!-- LIVE:{key}:START -->)(.*?)(<!-- LIVE:{key}:END -->)",
            lambda m: f"{m.group(1)}\n{value}\n{m.group(3)}",
            text,
            flags=re.S,
        )
    path.write_text(text, encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="dist")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--no-readme", action="store_true")
    args = ap.parse_args()

    if args.demo:
        data = demo()
    else:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            raise SystemExit("GITHUB_TOKEN is required (or pass --demo)")
        data = fetch(token)
    s = summarise(data)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for name, t in THEMES.items():
        (out / f"stats-{name}.svg").write_text(stats_card(s, t), encoding="utf-8")
        (out / f"streak-{name}.svg").write_text(streak_card(s, t), encoding="utf-8")
        (out / f"activity-{name}.svg").write_text(activity_card(s, t), encoding="utf-8")
        (out / f"languages-{name}.svg").write_text(languages_card(s, t), encoding="utf-8")
    if not args.no_readme:
        patch_readme(live_blocks(s))
    print(f"cards -> {out}/  total={s['total']} year={s['year_total']} streak={s['current']}/{s['longest']}")


if __name__ == "__main__":
    main()
