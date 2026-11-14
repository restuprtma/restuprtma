#!/usr/bin/env python3
"""Regenerate the profile README assets from live GitHub data.

    gh api graphql -f query='{ user(login:"restuprtma"){ contributionsCollection{
        contributionCalendar{ totalContributions weeks{ contributionDays{ date contributionCount } } } } } }' \
      | python3 scripts/gen-assets.py

Writes assets/heatmap-{dark,light}.svg and assets/stack-{dark,light}.svg.
"""

import json
import sys
from datetime import date

USER = "restuprtma"
STACK = [
    ("Go", "#00ADD8"),
    ("TypeScript", "#3178C6"),
    ("Python", "#3776AB"),
    ("PHP", "#777BB4"),
    ("Dart", "#0175C2"),
    ("Java", "#ED8B00"),
]
MEMBER_SINCE = 2023
FONT = "-apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif"


def blend(fg: str, bg: str, alpha: float) -> str:
    f = [int(fg[i : i + 2], 16) for i in (1, 3, 5)]
    b = [int(bg[i : i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(b[i] + (f[i] - b[i]) * alpha):02x}" for i in range(3))


def heatmap(cal, theme):
    dark = theme == "dark"
    base = "#0d1117" if dark else "#ffffff"
    zero = "#161b22" if dark else "#ebedf0"
    accent = "#58A6FF" if dark else "#0969da"
    muted = "#6e7681" if dark else "#6e7781"
    text = "#e6edf3" if dark else "#1f2328"
    ramp = [zero, blend(accent, base, 0.22), blend(accent, base, 0.45), blend(accent, base, 0.7), accent]

    weeks = cal["weeks"]
    days = [d for w in weeks for d in w["contributionDays"]]
    active = sum(1 for d in days if d["contributionCount"] > 0)
    peak = max(d["contributionCount"] for d in days) or 1
    level = lambda n: 0 if n == 0 else max(1, min(4, -(-n * 4 // peak)))

    left, top, step, size = 30, 22, 15, 12
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="830" height="150" viewBox="0 0 830 150" role="img" aria-label="{cal["totalContributions"]} contributions in the last year">']
    out.append(f'<g font-family="{FONT}">')

    seen = set()
    for i, week in enumerate(weeks):
        first = week["contributionDays"][0]["date"]
        month = date.fromisoformat(first).strftime("%b")
        if month not in seen:
            seen.add(month)
            out.append(f'<text x="{left + i * step}" y="10" font-size="10" fill="{muted}">{month}</text>')
        for d in week["contributionDays"]:
            row = (date.fromisoformat(d["date"]).weekday() + 1) % 7  # Sunday first
            out.append(
                f'<rect x="{left + i * step}" y="{top + row * step}" width="{size}" height="{size}" rx="2.5" '
                f'fill="{ramp[level(d["contributionCount"])]}"><title>{d["date"]}: {d["contributionCount"]}</title></rect>'
            )

    for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        out.append(f'<text x="0" y="{top + row * step + 10}" font-size="9" fill="{muted}">{name}</text>')

    y = 126
    out.append(
        f'<text x="{left}" y="{y}" font-size="12" fill="{text}">{cal["totalContributions"]} contributions</text>'
        f'<text x="{left + 148}" y="{y}" font-size="12" fill="{muted}">·  {active} active days  ·  since {MEMBER_SINCE}</text>'
    )
    lx = 700
    out.append(f'<text x="{lx - 26}" y="{y}" font-size="10" fill="{muted}">Less</text>')
    for i, c in enumerate(ramp):
        out.append(f'<rect x="{lx + i * step}" y="{y - 10}" width="{size}" height="{size}" rx="2.5" fill="{c}"/>')
    out.append(f'<text x="{lx + 5 * step + 4}" y="{y}" font-size="10" fill="{muted}">More</text>')
    out.append("</g></svg>")
    return "\n".join(out)


def stack(theme):
    dark = theme == "dark"
    border = "#30363d" if dark else "#d0d7de"
    fill = "#0d1117" if dark else "#ffffff"
    text = "#e6edf3" if dark else "#1f2328"

    pad, gap, height, width = 13, 9, 30, 0
    chips, x = [], 6
    for name, color in STACK:
        w = round(len(name) * 7.3) + 30
        chips.append(
            f'<rect x="{x}" y="4" width="{w}" height="{height}" rx="{height // 2}" fill="{fill}" stroke="{border}"/>'
            f'<circle cx="{x + 14}" cy="{4 + height // 2}" r="4" fill="{color}"/>'
            f'<text x="{x + 24}" y="{4 + height // 2 + 4.5}" font-size="12.5" fill="{text}">{name}</text>'
        )
        x += w + gap
    total = x - gap + 6
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total}" height="{height + 8}" '
        f'viewBox="0 0 {total} {height + 8}" role="img" aria-label="Go, TypeScript, Python, PHP, Dart, Java">'
        f'<g font-family="{FONT}">' + "".join(chips) + "</g></svg>"
    )


def main():
    payload = json.load(sys.stdin)
    cal = payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    for theme in ("dark", "light"):
        with open(f"assets/heatmap-{theme}.svg", "w") as f:
            f.write(heatmap(cal, theme))
        with open(f"assets/stack-{theme}.svg", "w") as f:
            f.write(stack(theme))
    print(f'wrote assets for {cal["totalContributions"]} contributions, {len(cal["weeks"])} weeks')


if __name__ == "__main__":
    main()