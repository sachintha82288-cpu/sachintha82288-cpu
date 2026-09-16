#!/usr/bin/env python3
"""Generate the SYSTEM METRICS cards (generated/stats.svg, generated/languages.svg).

The old README pulled stat cards from a hosted Vercel instance. Hosted
instances get paused, rate-limited or shut down (github-readme-stats.vercel.app
has been returning 503 DEPLOYMENT_PAUSED since Nov 2025), which silently
breaks the profile. These cards are generated from the GitHub API instead and
committed to the repository, so they can never be switched off by a third
party.

Data comes from public endpoints only:

    GET  /users/{user}                -> followers, public repos, account age
    GET  /users/{user}/repos          -> stars (forks excluded)
    GET  /repos/{user}/{repo}/languages -> language byte counts (forks excluded)
    POST /graphql                     -> commits in the last year
                                          (contributionsCollection)

Run locally or in Actions:

    GITHUB_TOKEN=... python3 .github/scripts/generate_cards.py

It is normally run by `.github/workflows/generate-cards.yml` (daily + on push
to main). The script only writes a file when its content changed, so the
follow-up commit step stays quiet most days.
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import urllib.request

USER = "sachintha82288-cpu"
OUT_DIR = pathlib.Path(__file__).resolve().parents[2] / "generated"

ACCENT = "#00F0FF"   # cyber cyan
GREEN = "#00FF88"    # matrix green
TEXT = "#E6EDF3"
MUTED = "#8B949E"
BG_TOP = "#0A1526"
BG_BOTTOM = "#04080F"
TRACK = "#0D1626"

MONO = "ui-monospace, 'Cascadia Code', 'JetBrains Mono', Menlo, Consolas, monospace"

# GitHub Linguist colors, so language bars stay recognizable
LANG_COLORS = {
    "Python": "#3572A5", "JavaScript": "#f1e05a", "TypeScript": "#3178c6",
    "HTML": "#e34c26", "CSS": "#563d7c", "Shell": "#89e051", "Java": "#b07219",
    "C": "#555555", "C++": "#f34b7d", "C#": "#178600", "Go": "#00ADD8",
    "Kotlin": "#A97BFF", "Dart": "#00B4AB", "PHP": "#4F5D95", "Ruby": "#701516",
    "Swift": "#F05138", "Rust": "#dea584", "Lua": "#000080", "Jupyter Notebook": "#DA5B0B",
    "PowerShell": "#012456", "Batchfile": "#C1F12E", "Dockerfile": "#384d54",
    "MDX": "#fcb32c", "Markdown": "#083fa1", "Vue": "#41b883", "SCSS": "#c6538c",
}


# ── GitHub API ───────────────────────────────────────────────────────────────

def token() -> str:
    tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if tok:
        return tok.strip()
    try:
        return subprocess.run(
            ["gh", "auth", "token"], capture_output=True, text=True, check=True
        ).stdout.strip()
    except Exception:
        sys.exit("error: no GITHUB_TOKEN / GH_TOKEN and `gh auth token` failed")


def api(path: str, tok: str):
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={
            "Authorization": f"Bearer {tok}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "profile-cards",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as res:
        return json.loads(res.read().decode())


def graphql(query: str, tok: str):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query}).encode(),
        headers={
            "Authorization": f"Bearer {tok}",
            "User-Agent": "profile-cards",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as res:
        return json.loads(res.read().decode())


def collect() -> dict:
    tok = token()

    user = api(f"/users/{USER}", tok)
    repos = [r for r in api(f"/users/{USER}/repos?per_page=100&sort=pushed", tok)
             if not r.get("fork")]
    stars = sum(r.get("stargazers_count", 0) for r in repos)

    langs: dict[str, int] = {}
    for repo in repos[:30]:  # keep API usage bounded
        try:
            for name, nbytes in api(f"/repos/{repo['full_name']}/languages", tok).items():
                langs[name] = langs.get(name, 0) + nbytes
        except Exception:
            continue

    try:
        data = graphql(
            '{ user(login: "%s") { contributionsCollection { totalCommitContributions } } }'
            % USER,
            tok,
        )
        commits = data["data"]["user"]["contributionsCollection"]["totalCommitContributions"]
    except Exception:
        commits = 0

    try:
        data = graphql(
            '{ user(login: "%s") { contributionsCollection { contributionCalendar { '
            "totalContributions weeks { contributionDays { date contributionCount } } } } } }"
            % USER,
            tok,
        )
        cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
        weeks = [
            [{"date": d["date"], "count": d["contributionCount"]} for d in w["contributionDays"]]
            for w in cal["weeks"]
        ]
        calendar = {"total": cal["totalContributions"], "weeks": weeks}
    except Exception:
        calendar = {"total": 0, "weeks": []}

    return {
        "followers": user.get("followers", 0),
        "repos": user.get("public_repos", len(repos)),
        "stars": stars,
        "commits": commits,
        "calendar": calendar,
        "langs": sorted(langs.items(), key=lambda kv: kv[1], reverse=True)[:6],
        "lang_total": sum(langs.values()),
    }


# ── SVG helpers ──────────────────────────────────────────────────────────────

def svg_head(w: int, h: int, label: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{label}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{BG_TOP}"/>
      <stop offset="1" stop-color="{BG_BOTTOM}"/>
    </linearGradient>
    <pattern id="grid" width="30" height="30" patternUnits="userSpaceOnUse">
      <path d="M30 0H0V30" fill="none" stroke="{ACCENT}" stroke-opacity="0.07" stroke-width="1"/>
    </pattern>
    <clipPath id="clip"><rect x="1.5" y="1.5" width="{w - 3}" height="{h - 3}" rx="14"/></clipPath>
  </defs>
  <rect x="1.5" y="1.5" width="{w - 3}" height="{h - 3}" rx="14" fill="url(#bg)" stroke="{ACCENT}" stroke-opacity="0.4" stroke-width="1.5"/>
  <g clip-path="url(#clip)"><rect width="{w}" height="{h}" fill="url(#grid)"/></g>
'''


def led(cx: float, cy: float, color: str = GREEN, dur: float = 2.0) -> str:
    return f'''  <circle cx="{cx}" cy="{cy}" r="4.5" fill="{color}">
    <animate attributeName="opacity" values="1;0.35;1" dur="{dur}s" repeatCount="indefinite"/>
    <animate attributeName="r" values="4.5;3.6;4.5" dur="{dur}s" repeatCount="indefinite"/>
  </circle>
'''


def big_number(x: float, y: float, value: int, label: str) -> str:
    return f'''  <text x="{x}" y="{y}" font-family="{MONO}" font-size="13" letter-spacing="2.5" fill="{MUTED}">{label}</text>
  <text x="{x}" y="{y + 44}" font-family="{MONO}" font-size="40" font-weight="700" fill="{TEXT}">{value}</text>
  <rect x="{x}" y="{y + 54}" width="34" height="3" rx="1.5" fill="{GREEN}" opacity="0.85">
    <animate attributeName="opacity" values="0.85;0.3;0.85" dur="2.6s" repeatCount="indefinite"/>
  </rect>
'''


def make_stats(d: dict) -> str:
    w, h = 620, 340
    out = svg_head(w, h, f"GitHub statistics for {USER}: commits, repositories, stars and followers")
    out += f'''  <text x="30" y="46" font-family="{MONO}" font-size="17" fill="{ACCENT}">$ ./fetch_stats --live</text>
  <rect x="{w - 52}" y="33" width="10" height="18" fill="{ACCENT}">
    <animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1.1s" repeatCount="indefinite"/>
  </rect>
  {led(w - 30, 40)}
  <line x1="30" y1="62" x2="{w - 30}" y2="62" stroke="{ACCENT}" stroke-opacity="0.2" stroke-width="1"/>
'''
    out += big_number(30, 96, d["commits"], "COMMITS // 12 MO")
    out += big_number(330, 96, d["repos"], "PUBLIC REPOS")
    out += big_number(30, 202, d["stars"], "STARS EARNED")
    out += big_number(330, 202, d["followers"], "FOLLOWERS")
    out += f'''  <line x1="30" y1="304" x2="{w - 30}" y2="304" stroke="{ACCENT}" stroke-opacity="0.2" stroke-width="1"/>
  <text x="30" y="326" font-family="{MONO}" font-size="13" fill="{MUTED}">github.com/{USER}</text>
  <text x="{w - 30}" y="326" text-anchor="end" font-family="{MONO}" font-size="12" fill="{GREEN}" opacity="0.75">DATA // GITHUB API</text>
</svg>
'''
    return out


def make_languages(d: dict) -> str:
    langs = d["langs"]
    total = d["lang_total"] or 1
    w = 620
    h = 96 + len(langs) * 42 + 18
    out = svg_head(w, h, f"Most used languages of {USER}")
    out += f'''  <text x="30" y="46" font-family="{MONO}" font-size="17" fill="{ACCENT}">$ ./top_langs --sort=bytes</text>
  <rect x="{w - 52}" y="33" width="10" height="18" fill="{ACCENT}">
    <animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1.1s" repeatCount="indefinite"/>
  </rect>
  <line x1="30" y1="62" x2="{w - 30}" y2="62" stroke="{ACCENT}" stroke-opacity="0.2" stroke-width="1"/>
'''
    track_x, track_w = 190, 330
    for i, (name, nbytes) in enumerate(langs):
        pct = nbytes / total * 100
        y = 96 + i * 42
        fill_w = max(6, round(track_w * pct / 100))
        color = LANG_COLORS.get(name, ACCENT)
        out += f'''  <text x="30" y="{y + 16}" font-family="{MONO}" font-size="15" fill="{TEXT}">{name}</text>
  <rect x="{track_x}" y="{y + 5}" width="{track_w}" height="10" rx="5" fill="{TRACK}" stroke="{ACCENT}" stroke-opacity="0.15"/>
  <rect x="{track_x}" y="{y + 5}" width="{fill_w}" height="10" rx="5" fill="{color}">
    <animate attributeName="width" values="0;{fill_w}" dur="0.9s" begin="{0.15 * i:.2f}s" fill="freeze" calcMode="spline" keySplines="0.25 0.1 0.25 1"/>
  </rect>
  <text x="{w - 30}" y="{y + 16}" text-anchor="end" font-family="{MONO}" font-size="13" fill="{MUTED}">{pct:.1f}%</text>
'''
    out += f'</svg>\n'
    return out


def make_contributions(cal: dict) -> str:
    """Self-hosted animated activity heatmap, built from the real contribution calendar."""
    import datetime as dt

    weeks = cal.get("weeks") or []
    total = cal.get("total") or sum(d["count"] for w in weeks for d in w)
    cell, gap, pitch = 11, 3.5, 14.5
    left = 46          # room for day labels
    top = 64           # room for month labels
    w = left + len(weeks) * pitch + 30
    h = top + 7 * pitch + 66

    def level(n: int) -> int:
        if n <= 0:
            return 0
        if n == 1:
            return 1
        if n <= 3:
            return 2
        if n <= 6:
            return 3
        return 4

    lv_fill = ["#0D1626", "#0E4A57", "#0F7C8C", "#00C9A7", "#00FF88"]
    lv_stroke = [ACCENT, "#00F0FF", "#00F0FF", "#00FF88", "#00FF88"]

    out = svg_head(w, h, f"Contribution activity grid of {USER} over the last year")
    out += f'''  <text x="30" y="40" font-family="{MONO}" font-size="17" fill="{ACCENT}">$ ./activity --last-year</text>
  <text x="{w - 56}" y="40" text-anchor="end" font-family="{MONO}" font-size="15" fill="{GREEN}">{total} contributions</text>
  {led(w - 36, 35)}
'''
    # month labels
    out += '  <g font-family="%s" font-size="11" fill="%s">\n' % (MONO, MUTED)
    seen = set()
    for wi, week in enumerate(weeks):
        if not week:
            continue
        d0 = dt.date.fromisoformat(week[0]["date"])
        if d0.month not in seen:
            seen.add(d0.month)
            out += f'    <text x="{left + wi * pitch}" y="{top - 10}">{d0.strftime("%b")}</text>\n'
    out += "  </g>\n"
    # day-of-week labels (Mon / Wed / Fri)
    for r, lbl in ((1, "Tue"), (3, "Thu"), (5, "Sat")):
        out += (f'  <text x="{left - 10}" y="{top + r * pitch + 9}" text-anchor="end" '
                f'font-family="{MONO}" font-size="11" fill="{MUTED}">{lbl}</text>\n')
    # cells: always visible; a dimming "boot wave" sweeps left -> right once, then
    # busy columns (3+ contributions in a day) keep gently pulsing forever
    out += '  <g stroke-width="1">\n'
    for wi, week in enumerate(weeks):
        cells = []
        for di, day in enumerate(week):
            lv = level(day["count"])
            x = left + wi * pitch
            y = top + di * pitch
            extra = ""
            if lv > 0 and day["count"] >= 3:
                pulse = min(3.2 + day["count"] * 0.4, 5.5)
                extra = (f'<animate attributeName="opacity" values="1;0.55;1" dur="{pulse:.1f}s" '
                         f'repeatCount="indefinite"/>')
            cells.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell}" height="{cell}" rx="2.5" '
                f'fill="{lv_fill[lv]}" stroke="{lv_stroke[lv]}" stroke-opacity="{0.55 if lv else 0.18}">'
                f'{extra}</rect>'
            )
        begin = f"{0.03 * wi:.2f}s"
        out += (f'    <g><animate attributeName="opacity" values="1;0.12;1" dur="0.5s" '
                f'begin="{begin}" fill="freeze"/>{"".join(cells)}</g>\n')
    out += "  </g>\n"
    # scan line sweeping the grid forever
    grid_w = len(weeks) * pitch
    out += f'''  <g clip-path="url(#clip)">
    <rect x="{left}" y="{top - 16}" width="26" height="{7 * pitch + 6}" fill="{ACCENT}" opacity="0.12">
      <animate attributeName="x" values="{left};{left + grid_w};{left}" dur="9s" repeatCount="indefinite"/>
    </rect>
  </g>
  <line x1="30" y1="{h - 40}" x2="{w - 30}" y2="{h - 40}" stroke="{ACCENT}" stroke-opacity="0.2" stroke-width="1"/>
  <text x="30" y="{h - 18}" font-family="{MONO}" font-size="13" fill="{MUTED}">github.com/{USER}</text>
  <text x="{w - 30}" y="{h - 18}" text-anchor="end" font-family="{MONO}" font-size="12" fill="{GREEN}" opacity="0.75">LIVE // GITHUB API</text>
</svg>
'''
    return out


def main() -> int:
    data = collect()
    OUT_DIR.mkdir(exist_ok=True)

    written = []
    outputs = (
        ("stats.svg", make_stats(data)),
        ("languages.svg", make_languages(data)),
        ("contributions.svg", make_contributions(data["calendar"])),
    )
    for name, svg in outputs:
        path = OUT_DIR / name
        if path.exists() and path.read_text(encoding="utf-8") == svg:
            print(f"{path} unchanged")
            continue
        path.write_text(svg, encoding="utf-8")
        written.append(str(path))
        print(f"wrote {path}")

    total = data["lang_total"] or 1
    lang_summary = [(name, f"{nbytes / total * 100:.0f}%") for name, nbytes in data["langs"]]
    print(f"data: {data['commits']} commits/12mo, {data['repos']} repos, "
          f"{data['stars']} stars, {data['followers']} followers, langs: {lang_summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
