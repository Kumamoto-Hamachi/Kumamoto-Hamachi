"""Render assets/activity.svg from live GitHub and LAPRAS data. Run daily by .github/workflows/activity.yml.

Any fetch error aborts the run, so a bad day leaves the last good panel in place.
Locally: GH_TOKEN=$(gh auth token) python3 scripts/build_activity.py
"""

import json
import os
from collections import Counter
from datetime import date
from urllib.request import Request, urlopen

from theme import (
    ASSETS,
    BRAND,
    BRAND_TEXT,
    HEADING,
    HR,
    MUTED,
    TEXT,
    TITLEBAR_HEIGHT,
    WIDTH,
    text,
    window,
)

USER = "Kumamoto-Hamachi"
LAPRAS_ID = "kumamoto3"

QUERY = """
query($login: String!) {
  user(login: $login) {
    repositories(
      ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC, first: 100,
      orderBy: {field: PUSHED_AT, direction: DESC}
    ) {
      nodes { primaryLanguage { name } }
    }
    contributionsCollection {
      totalPullRequestContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""

# Same ramp as the hero: density and brightness rise together, from HR-gray to near white.
LEVELS = [
    ("·", "#34343A"),
    ("~", "#2E41B8"),
    ("+", BRAND),
    ("x", "#6277F6"),
    ("%", "#9AA9FA"),
    ("@", "#E3E7FE"),
]


def fetch_json(request):
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def fetch_github():
    request = Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"bearer {os.environ['GH_TOKEN']}", "User-Agent": USER},
    )
    payload = fetch_json(request)
    if "errors" in payload:
        raise RuntimeError(payload["errors"])
    return payload["data"]["user"]


def fetch_lapras():
    request = Request(
        f"https://lapras.com/public/{LAPRAS_ID}.json", headers={"User-Agent": "Mozilla/5.0"}
    )
    data = fetch_json(request)
    return [
        ("Engineering", data["e_score"]),
        ("Business", data["b_score"]),
        ("Influence", data["i_score"]),
    ]


def streaks(days):
    """Today may simply not have happened yet, so a zero there does not end the current run."""
    current = 0
    for i, day in enumerate(reversed(days)):
        if day["contributionCount"]:
            current += 1
        elif i:
            break
    longest = run = 0
    for day in days:
        run = run + 1 if day["contributionCount"] else 0
        longest = max(longest, run)
    return current, longest


def level_of(count, thresholds):
    if not count:
        return 0
    return 1 + sum(count > t for t in thresholds)


def quartiles(counts):
    active = sorted(c for c in counts if c)
    if not active:
        return [0, 0, 0, 0]
    return [active[len(active) * q // 5] for q in (1, 2, 3, 4)]


def heatmap(weeks, x0, y0):
    pitch_x, pitch_y = (WIDTH - x0 - 24) / len(weeks), 17
    counts = [d["contributionCount"] for w in weeks for d in w["contributionDays"]]
    thresholds = quartiles(counts)
    parts = []
    last_month = None
    for col, week in enumerate(weeks):
        month = date.fromisoformat(week["contributionDays"][0]["date"]).strftime("%b")
        if month != last_month and col < len(weeks) - 2:
            if last_month is not None:
                parts.append(text(round(x0 + col * pitch_x, 1), y0 - 8, month, size=11.5, fill=MUTED))
            last_month = month
        for day in week["contributionDays"]:
            row = (date.fromisoformat(day["date"]).weekday() + 1) % 7
            char, color = LEVELS[level_of(day["contributionCount"], thresholds)]
            parts.append(
                text(round(x0 + col * pitch_x, 1), y0 + 12 + row * pitch_y, char, size=13.8, fill=color)
            )
    for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        parts.append(text(24, y0 + 12 + row * pitch_y, name, size=11.5, fill=MUTED))

    legend_x = WIDTH - 24 - (len(LEVELS) * 13 + 74)
    legend_y = y0 + 12 + 7 * pitch_y + 8
    parts.append(text(legend_x, legend_y, "less", size=11.5, fill=MUTED))
    for i, (char, color) in enumerate(LEVELS):
        parts.append(text(legend_x + 36 + i * 13, legend_y, char, size=13.8, fill=color))
    parts.append(text(legend_x + 42 + len(LEVELS) * 13, legend_y, "more", size=11.5, fill=MUTED))
    return "".join(parts), legend_y


def bar(x, y, value, maximum, width=24):
    filled = round(width * value / maximum) if maximum else 0
    return text(x, y, "=" * filled, size=13.8, fill=BRAND) + text(
        round(x + filled * 8.28, 2), y, "·" * (width - filled), size=13.8, fill="#34343A"
    )


def build():
    user = fetch_github()
    lapras = fetch_lapras()

    collection = user["contributionsCollection"]
    calendar = collection["contributionCalendar"]
    weeks = calendar["weeks"]
    days = [d for w in weeks for d in w["contributionDays"]]
    current, longest = streaks(days)
    # Counter keeps insertion order for ties, so the most recently pushed language wins them.
    languages = Counter(
        r["primaryLanguage"]["name"] for r in user["repositories"]["nodes"] if r["primaryLanguage"]
    ).most_common(3)

    pad = 24
    y = TITLEBAR_HEIGHT + 30
    parts = [
        text(pad, y, "$", size=14, fill=BRAND_TEXT, weight=700),
        text(pad + 17, y, "git log --author=kumamoto --since=1.year", size=14, fill=HEADING),
    ]

    y += 44
    metrics = [
        (f"{calendar['totalContributions']:,}", "contributions"),
        (f"{current}d", "current streak"),
        (f"{longest}d", "longest streak"),
        (f"{collection['totalPullRequestContributions']:,}", "public pull requests"),
    ]
    column = (WIDTH - pad * 2) / len(metrics)
    for i, (value, label) in enumerate(metrics):
        x = round(pad + i * column, 1)
        parts.append(text(x, y, value, size=26, fill=HEADING, weight=700))
        parts.append(text(x, y + 22, label, size=12, fill=MUTED))

    y += 64
    grid, y = heatmap(weeks, 62, y)
    parts.append(grid)

    y += 18
    parts.append(f'<path d="M{pad} {y}H{WIDTH - pad}" stroke="{HR}"/>')
    y += 32

    right = WIDTH // 2 + 12
    parts.append(text(pad, y, "repos by language", size=12.5, fill=MUTED))
    parts.append(text(right, y, "lapras score", size=12.5, fill=MUTED))
    top = max(count for _, count in languages)
    rows = max(len(languages), len(lapras))
    for i, (name, count) in enumerate(languages):
        row_y = y + 26 + i * 22
        parts.append(text(pad, row_y, name[:10], size=13.8, fill=TEXT))
        parts.append(bar(pad + 92, row_y, count, top, width=24))
        parts.append(text(pad + 92 + 24 * 8.28 + 10, row_y, str(count), size=13.8, fill=TEXT))
    for i, (name, score) in enumerate(lapras):
        row_y = y + 26 + i * 22
        parts.append(text(right, row_y, name, size=13.8, fill=TEXT))
        parts.append(bar(right + 100, row_y, score, 5, width=20))
        parts.append(text(right + 100 + 20 * 8.28 + 10, row_y, f"{score:.2f}", size=13.8, fill=TEXT))

    height = y + 26 + rows * 22 + 4
    label = (
        f"{calendar['totalContributions']} contributions in the last year, "
        f"current streak {current} days, longest streak {longest} days"
    )
    svg = window("kumamoto: ~/activity", height, "".join(parts), label=label)
    ASSETS.mkdir(exist_ok=True)
    (ASSETS / "activity.svg").write_text(svg, encoding="utf-8")
    print(label, languages, lapras)


if __name__ == "__main__":
    build()
