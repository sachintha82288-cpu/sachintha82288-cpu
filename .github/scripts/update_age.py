#!/usr/bin/env python3
"""Keep the profile's age-dependent artwork permanently correct.

Sachintha's birth date lives here, in ONE place. Everything age-related is
regenerated from it:

    README.md
      <!-- AGE_BADGE:START --> ... <!-- AGE_BADGE:END -->   shields.io badge
      <!-- AGE_TEXT:START  --> ... <!-- AGE_TEXT:END  -->   profile table cell

    generated/terminal.svg      animated self-typing terminal card

Run it by hand any time:

    python3 .github/scripts/update_age.py

It is normally run by `.github/workflows/refresh-profile.yml` (daily). Because
the age only changes once a year, the workflow only produces a new commit on
the birthday -- the repo does not fill up with daily noise.

Anything between a marker pair is owned by this script: edit the constants
below, not the generated text in the README.
"""

from __future__ import annotations

import datetime as dt
import pathlib
import re
import sys

# ── the only facts this script needs ────────────────────────────────────────
BIRTH_DATE = dt.date(2009, 12, 11)
ALIAS = "Sachintha"
BASE = "Kegalle, Sri Lanka"
SCHOOL = "Dr. N. M. Perera Central College"
RANK = "student // self-taught developer"
STATUS = "building the future"

ACCENT = "00F0FF"  # cyber cyan
DARK = "050A14"    # deep-space navy
GOLD = "00FF88"    # matrix green

ROOT = pathlib.Path(__file__).resolve().parents[2]
README = ROOT / "README.md"
TERMINAL_SVG = ROOT / "generated" / "terminal.svg"
# ────────────────────────────────────────────────────────────────────────────

MONO = "ui-monospace, 'Cascadia Code', Menlo, Consolas, monospace"


def age_on(today: dt.date) -> int:
    """Full years lived as of `today`."""
    reached = (today.month, today.day) >= (BIRTH_DATE.month, BIRTH_DATE.day)
    return today.year - BIRTH_DATE.year - (0 if reached else 1)


# ── animated terminal card ──────────────────────────────────────────────────

def build_terminal_svg(today: dt.date) -> str:
    age = age_on(today)
    rows = [
        ("ALIAS", ALIAS, "#E6EDF3"),
        ("AGE", f"{age} years", "#00F0FF"),
        ("BORN", BIRTH_DATE.isoformat(), "#E6EDF3"),
        ("BASE", BASE, "#E6EDF3"),
        ("SCHOOL", SCHOOL, "#E6EDF3"),
        ("RANK", RANK, "#E6EDF3"),
        ("STATUS", STATUS, "#00FF88"),
    ]

    prompt = "$ sudo ./identify --verbose"
    prompt_px = int(len(prompt) * 8.4) + 14

    box_x, box_y, box_w, box_h = 40, 92, 560, 270
    row_y0, row_dy = 156, 28

    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="640" height="430" '
        'viewBox="0 0 640 430" role="img" aria-label="Terminal: sachintha profile card">',
        '  <defs>',
        '    <linearGradient id="tbg" x1="0" y1="0" x2="0" y2="1">',
        '      <stop offset="0" stop-color="#070D1A"/>',
        '      <stop offset="1" stop-color="#030710"/>',
        '    </linearGradient>',
        '    <linearGradient id="tscan" x1="0" y1="0" x2="0" y2="1">',
        '      <stop offset="0" stop-color="#00F0FF" stop-opacity="0"/>',
        '      <stop offset="0.5" stop-color="#00F0FF" stop-opacity="0.35"/>',
        '      <stop offset="1" stop-color="#00F0FF" stop-opacity="0"/>',
        '    </linearGradient>',
        f'    <clipPath id="tclip"><rect x="2" y="2" width="636" height="426" rx="14"/></clipPath>',
        f'    <clipPath id="typeclip"><rect x="40" y="52" width="0" height="30">',
        f'      <animate attributeName="width" values="0;{prompt_px}" dur="0.9s" '
        f'begin="0.3s" fill="freeze" calcMode="spline" keySplines="0.3 0.1 0.3 1"/>',
        '    </rect></clipPath>',
        '  </defs>',
        '  <rect x="2" y="2" width="636" height="426" rx="14" fill="url(#tbg)" '
        f'stroke="#{ACCENT}" stroke-opacity="0.45" stroke-width="2"/>',
    ]

    # window chrome
    out += [
        '  <g clip-path="url(#tclip)">',
        '    <rect x="2" y="2" width="636" height="426" fill="none"/>',
        '    <rect x="2" y="0" width="636" height="46" fill="#00F0FF" opacity="0.05"/>',
        '    <line x1="2" y1="46" x2="638" y2="46" stroke="#00F0FF" stroke-opacity="0.3" stroke-width="1"/>',
        '    <rect x="2" y="0" width="636" height="60" fill="url(#tscan)" opacity="0.14">',
        '      <animateTransform attributeName="transform" type="translate" values="0 -70; 0 440" dur="7s" repeatCount="indefinite"/>',
        '    </rect>',
        '  </g>',
        '  <rect x="24" y="17" width="11" height="11" rx="2.5" fill="none" stroke="#00F0FF" stroke-opacity="0.7" stroke-width="1.6"/>',
        '  <rect x="42" y="17" width="11" height="11" rx="2.5" fill="none" stroke="#00FF88" stroke-opacity="0.7" stroke-width="1.6"/>',
        '  <rect x="60" y="17" width="11" height="11" rx="2.5" fill="none" stroke="#8B949E" stroke-opacity="0.7" stroke-width="1.6"/>',
        f'  <text x="320" y="28" text-anchor="middle" font-family="{MONO}" font-size="14" '
        'fill="#8B949E">sachintha@kegalle: ~</text>',
    ]

    # typed prompt
    out += [
        f'  <g clip-path="url(#typeclip)"><text x="40" y="72" font-family="{MONO}" '
        f'font-size="16" fill="#{ACCENT}">{prompt}</text></g>',
        f'  <rect x="{40 + prompt_px + 4}" y="58" width="10" height="17" fill="#{ACCENT}">',
        '    <animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1.1s" begin="1.3s" repeatCount="indefinite"/>',
        '  </rect>',
    ]

    # panel
    out += [
        f'  <rect x="{box_x}" y="{box_y}" width="{box_w}" height="{box_h}" rx="10" fill="#00F0FF" '
        f'fill-opacity="0.03" stroke="#{ACCENT}" stroke-opacity="0.4" stroke-width="1.5"/>',
        f'  <text x="320" y="{box_y + 26}" text-anchor="middle" font-family="{MONO}" font-size="15" '
        f'letter-spacing="3" fill="#{ACCENT}" opacity="0">[ sachintha@kegalle ]'
        f'<animate attributeName="opacity" values="0;1" dur="0.4s" begin="1.1s" fill="freeze"/></text>',
        f'  <line x1="{box_x + 18}" y1="{box_y + 40}" x2="{box_x + box_w - 18}" y2="{box_y + 40}" '
        f'stroke="#{ACCENT}" stroke-opacity="0.25" stroke-width="1"/>',
    ]

    # rows, staggered reveal
    for i, (label, value, color) in enumerate(rows):
        y = row_y0 + i * row_dy
        begin = f"{1.35 + 0.22 * i:.2f}s"
        out += [
            f'  <g opacity="0"><animate attributeName="opacity" values="0;1" dur="0.35s" begin="{begin}" fill="freeze"/>',
            f'    <text x="{box_x + 24}" y="{y}" font-family="{MONO}" font-size="15" fill="#8B949E">{label}</text>',
            f'    <text x="{box_x + 150}" y="{y}" font-family="{MONO}" font-size="15" fill="{color}">{value}</text>',
            '  </g>',
        ]

    # trailing prompt + blinking cursor
    out += [
        f'  <text x="{box_x}" y="398" font-family="{MONO}" font-size="16" fill="#8B949E">'
        f'sachintha@kegalle:~$</text>',
        f'  <rect x="{box_x + 200}" y="384" width="11" height="19" fill="#{GOLD}">',
        '    <animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1.1s" begin="3.2s" repeatCount="indefinite"/>',
        '  </rect>',
        '</svg>',
        '',
    ]
    return "\n".join(out)


# ── README markers ──────────────────────────────────────────────────────────

def build_blocks(today: dt.date) -> dict[str, str]:
    age = age_on(today)
    born = BIRTH_DATE.strftime("%d %B %Y")

    badge_url = (
        f"https://img.shields.io/badge/AGE-{age}%20YEARS-{ACCENT}"
        f"?style=for-the-badge&labelColor={DARK}"
    )
    return {
        "AGE_BADGE": f'<img src="{badge_url}" alt="Age: {age} years" />',
        "AGE_TEXT": f"**{age} years old**  ·  born {born}",
    }


def apply_blocks(markdown: str, blocks: dict[str, str]) -> tuple[str, list[str], list[str]]:
    """Replace every marker-wrapped region. Returns (text, updated, missing).

    If both markers sit on the same line (e.g. inside a Markdown table cell) the
    replacement stays inline -- adding a newline there would break the table.
    """
    updated: list[str] = []
    missing: list[str] = []

    for name, content in blocks.items():
        pattern = re.compile(
            rf"(<!--\s*{re.escape(name)}:START\s*-->)(.*?)(<!--\s*{re.escape(name)}:END\s*-->)",
            re.DOTALL,
        )
        if not pattern.search(markdown):
            missing.append(name)
            continue

        def _sub(match: re.Match[str], content: str = content) -> str:
            inline = "\n" not in match.group(0)
            glue = "" if inline else "\n"
            return f"{match.group(1)}{glue}{content}{glue}{match.group(3)}"

        markdown = pattern.sub(_sub, markdown)
        updated.append(name)

    return markdown, updated, missing


def write_if_changed(path: pathlib.Path, content: str) -> bool:
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def main() -> int:
    today = dt.date.today()
    age = age_on(today)
    changed: list[str] = []

    if not README.exists():
        print(f"::error::README.md not found at {README}", file=sys.stderr)
        return 1

    original = README.read_text(encoding="utf-8")
    rendered, updated, missing = apply_blocks(original, build_blocks(today))
    if rendered != original:
        README.write_text(rendered, encoding="utf-8")
        changed.append("README.md")

    if write_if_changed(TERMINAL_SVG, build_terminal_svg(today)):
        changed.append(str(TERMINAL_SVG.relative_to(ROOT)))

    for name in missing:
        print(f"::warning::marker pair '{name}:START/END' is missing from README.md")

    if not changed:
        print(f"everything already up to date (age {age} on {today}).")
        return 0

    print(f"updated {', '.join(changed)} (age {age} on {today}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
