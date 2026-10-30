"""Render the panels that only change when edited: assets/whoami.svg, stack.svg and the link buttons."""

import json

from build_hero import render_logo
from theme import (
    ASSETS,
    BLOCK,
    BORDER,
    BRAND,
    BRAND_TEXT,
    HEADING,
    HR,
    MUTED,
    SCRIPTS,
    TEXT,
    TITLEBAR_HEIGHT,
    WIDTH,
    base_style,
    text,
    window,
)

PROFILE = [
    ("Role", "Site Reliability Engineer"),
    ("Location", "Japan"),
    ("Daily", "Python, TypeScript, HCL (Terraform)"),
    ("Scripting", "Shell/Bash"),
    ("Infra", "Kubernetes, AWS, Docker"),
    ("Practices", "IaC, GitOps, Observability, SLI/SLO"),
    ("Focus", "Platform Engineering, Reliability at Scale,"),
    ("", "Developer Experience"),
]

STACK = [
    (
        "languages & frameworks",
        [
            ("python", "Python"),
            ("typescript", "TypeScript"),
            ("django", "Django"),
            ("vuedotjs", "Vue.js"),
            ("gnubash", "Shell"),
        ],
    ),
    (
        "infrastructure & cloud",
        [
            ("amazonwebservices", "AWS"),
            ("kubernetes", "Kubernetes"),
            ("terraform", "Terraform"),
            ("docker", "Docker"),
            ("helm", "Helm"),
        ],
    ),
    (
        "monitoring & ci/cd",
        [
            ("datadog", "Datadog"),
            ("sentry", "Sentry"),
            ("githubactions", "Actions"),
            ("argo", "ArgoCD"),
            ("git", "GitOps"),
        ],
    ),
]

BUTTONS = [
    ("zenn", "Zenn", True),
    ("x", "X", False),
    ("lapras", "LAPRAS", False),
]


def build_whoami():
    pad, line = 24, 20
    top = TITLEBAR_HEIGHT + 34
    parts = [
        text(pad, top, "$", size=14, fill=BRAND_TEXT, weight=700),
        text(pad + 17, top, "whoami", size=14, fill=HEADING),
    ]

    logo_top = top + 34
    logo_rows = 15
    for color, rows in render_logo(34, logo_rows, 0.46):
        for i, row in enumerate(rows):
            if row:
                parts.append(text(pad, logo_top + i * 16.5, row, size=13.8, fill=color))

    info_x = 322
    info_top = top + 34
    parts.append(text(info_x, info_top, "kumamoto", size=15, fill=HEADING, weight=700))
    parts.append(text(info_x + 72, info_top, "@", size=15, fill=MUTED))
    parts.append(text(info_x + 81, info_top, "japan", size=15, fill=HEADING, weight=700))
    parts.append(f'<path d="M{info_x} {info_top + 11}h{WIDTH - info_x - pad}" stroke="{HR}"/>')
    for i, (key, value) in enumerate(PROFILE):
        y = info_top + 34 + i * line
        if key:
            parts.append(text(info_x, y, key, size=13.8, fill=BRAND_TEXT))
        parts.append(text(info_x + 100, y, value, size=13.8, fill=TEXT))

    prompt_y = round(logo_top + logo_rows * 16.5 + 18)
    parts.append(text(pad, prompt_y, "$", size=14, fill=BRAND_TEXT, weight=700))
    parts.append(
        f'<rect class="c" x="{pad + 17}" y="{prompt_y - 12}" width="8.4" height="16" fill="{TEXT}"/>'
    )
    style = (
        "@media (prefers-reduced-motion:no-preference){"
        ".c{animation:c 1.2s steps(1,end) infinite}}"
        "@keyframes c{50%{opacity:0}}"
    )
    svg = window(
        "kumamoto: ~",
        prompt_y + 24,
        "".join(parts),
        style=style,
        label=" / ".join(f"{k}: {v}" for k, v in PROFILE if k),
    )
    (ASSETS / "whoami.svg").write_text(svg, encoding="utf-8")


def build_stack():
    icons = json.loads((SCRIPTS / "icons.json").read_text())
    pad, gap = 24, 10
    tile_w, tile_h = (WIDTH - pad * 2 - gap * 4) / 5, 46
    parts = []
    y = TITLEBAR_HEIGHT + 30
    parts.append(text(pad, y, "$", size=14, fill=BRAND_TEXT, weight=700))
    parts.append(text(pad + 17, y, "ls ~/stack", size=14, fill=HEADING))
    y += 34
    labels = []
    for group, items in STACK:
        parts.append(text(pad, y, f"{group}/", size=12.5, fill=MUTED))
        y += 12
        for i, (icon, label) in enumerate(items):
            x = pad + i * (tile_w + gap)
            labels.append(label)
            parts.append(
                f'<rect x="{x:.1f}" y="{y}" width="{tile_w:.1f}" height="{tile_h}" rx="6" '
                f'fill="{BLOCK}" stroke="{HR}"/>'
                f'<g transform="translate({x + 13:.1f} {y + 14}) scale(.75)">'
                f'<path d="{icons[icon]}" fill="{TEXT}"/></g>'
                + text(round(x + 41, 1), y + 28, label, size=13, fill=TEXT)
            )
        y += tile_h + 28
    svg = window("kumamoto: ~/stack", y - 4, "".join(parts), label="Tech stack: " + ", ".join(labels))
    (ASSETS / "stack.svg").write_text(svg, encoding="utf-8")


def build_buttons():
    for slug, label, primary in BUTTONS:
        width = max(round(len(label) * 8.4 + 56), 96)
        height = 40
        border = BRAND if primary else BORDER
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
            f'width="{width}" height="{height}" role="img" aria-label="{label}">'
            f"{base_style()}"
            f'<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="6" '
            f'fill="{"#15161F" if primary else BLOCK}" stroke="{border}"/>'
            + text(width / 2, 25, label, size=14, fill=HEADING, weight=700, anchor="middle")
            + "</svg>"
        )
        (ASSETS / f"btn-{slug}.svg").write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    ASSETS.mkdir(exist_ok=True)
    build_whoami()
    build_stack()
    build_buttons()
    print("whoami.svg, stack.svg, btn-*.svg")
