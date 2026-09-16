#!/usr/bin/env python3
"""Keep the age shown in README.md permanently correct.

Sachintha's birth date lives here, in ONE place. Every block in README.md
that is wrapped in a marker pair is regenerated from it:

    <!-- AGE_BADGE:START -->  ...generated...  <!-- AGE_BADGE:END -->
    <!-- AGE_TEXT:START  -->  ...generated...  <!-- AGE_TEXT:END  -->
    <!-- TERMINAL:START  -->  ...generated...  <!-- TERMINAL:END  -->

Run it by hand any time:

    python3 .github/scripts/update_age.py

It is normally run by `.github/workflows/update-age.yml`, which fires daily.
Because the age only changes once a year, the workflow only produces a new
commit on the birthday -- the repo does not fill up with daily noise.

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

README = pathlib.Path(__file__).resolve().parents[2] / "README.md"
# ────────────────────────────────────────────────────────────────────────────


def age_on(today: dt.date) -> int:
    """Full years lived as of `today`."""
    reached = (today.month, today.day) >= (BIRTH_DATE.month, BIRTH_DATE.day)
    return today.year - BIRTH_DATE.year - (0 if reached else 1)


def _panel(rows: list[tuple[str, str]], header: str) -> str:
    """Draw an ASCII panel that stays aligned no matter how long the values are.

    Every line is built to exactly `inner + 4` characters:

        +--[ header ]------------------+
        | KEY..... value               |
        +------------------------------+
    """
    label_width = max(len(key) for key, _ in rows) + 3
    lines = [f"{key.ljust(label_width, '.')} {value}" for key, value in rows]
    inner = max(max(len(line) for line in lines), len(header) + 6)

    top = "+--[" + header + "]" + "-" * max(inner + 4 - len(header) - 6, 3) + "+"
    middle = "\n".join(f"| {line.ljust(inner)} |" for line in lines)
    bottom = "+" + "-" * (inner + 2) + "+"

    panel = "\n".join([top, middle, bottom])
    return "\n".join("  " + line for line in panel.splitlines())


def build_blocks(today: dt.date) -> dict[str, str]:
    age = age_on(today)
    born = BIRTH_DATE.strftime("%d %B %Y")

    badge_url = (
        f"https://img.shields.io/badge/AGE-{age}%20YEARS-{ACCENT}"
        f"?style=for-the-badge&labelColor={DARK}"
    )
    panel = _panel(
        [
            ("ALIAS", ALIAS),
            ("AGE", f"{age} years"),
            ("BORN", BIRTH_DATE.isoformat()),
            ("BASE", BASE),
            ("SCHOOL", SCHOOL),
            ("RANK", RANK),
            ("STATUS", STATUS),
        ],
        header=" sachintha@kegalle ",
    )

    return {
        "AGE_BADGE": f'<img src="{badge_url}" alt="Age: {age} years" />',
        "AGE_TEXT": f"**{age} years old**  ·  born {born}",
        "TERMINAL": (
            "```text\n"
            "sachintha@kegalle:~$ sudo ./identify --verbose\n\n"
            f"{panel}\n\n"
            "sachintha@kegalle:~$ █\n"
            "```"
        ),
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


def main() -> int:
    today = dt.date.today()

    if not README.exists():
        print(f"::error::README.md not found at {README}", file=sys.stderr)
        return 1

    original = README.read_text(encoding="utf-8")
    blocks = build_blocks(today)
    rendered, updated, missing = apply_blocks(original, blocks)

    for name in missing:
        print(f"::warning::marker pair '{name}:START/END' is missing from README.md")

    if rendered == original:
        print(f"README.md already up to date (age {age_on(today)} on {today}).")
        return 0

    README.write_text(rendered, encoding="utf-8")
    print(f"Updated {', '.join(updated)} -> age {age_on(today)} on {today}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
