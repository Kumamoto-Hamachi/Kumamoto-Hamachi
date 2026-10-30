"""Design tokens and SVG helpers shared by the build scripts.

The palette mirrors ghostty.org (near-black grays plus a single cobalt accent).
Everything is standard library only so the daily workflow needs no install step.

The fonts in scripts/fonts/ are subsets of JetBrains Mono (SIL OFL 1.1), made with:
  pyftsubset JetBrainsMono-Regular.ttf --layout-features='' --no-hinting \
    --unicodes='U+0020-007E,U+00B7,U+2500,U+2588,U+2591,U+276F,U+2022' \
    --desubroutinize --flavor=woff2 --output-file=JetBrainsMono-Regular.subset.woff2
"""

from base64 import b64encode
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

SCRIPTS = Path(__file__).resolve().parent
ASSETS = SCRIPTS.parent / "assets"

BG = "#0F0F11"
BLOCK = "#16161A"
HR = "#242428"
BORDER = "#4C4C50"
TITLEBAR = "#2E2E32"
MUTED = "#828286"
TEXT = "#C3C3C4"
HEADING = "#F0F0F4"
BRAND = "#3551F3"
BRAND_TEXT = "#8295F8"  # BRAND is too dark for small text on BG (under 3:1)
FISH = "#E6C07B"
FIRE_CORE = "#FFF3D6"
FIRE_MID = "#F2C35B"
FIRE_OUTER = "#EB8A3C"
FIRE_RIM = "#D9534F"
LOG = "#8E8E92"

WIDTH = 846  # width of a profile README column on a desktop viewport
TITLEBAR_HEIGHT = 36
FONT_STACK = 'JBM,"JetBrains Mono",ui-monospace,SFMono-Regular,Menlo,Consolas,monospace'


def font_face():
    faces = []
    for weight, name in ((400, "Regular"), (700, "Bold")):
        data = (SCRIPTS / "fonts" / f"JetBrainsMono-{name}.subset.woff2").read_bytes()
        faces.append(
            f"@font-face{{font-family:JBM;font-weight:{weight};"
            f'src:url(data:font/woff2;base64,{b64encode(data).decode()}) format("woff2")}}'
        )
    return "".join(faces)


def base_style(extra=""):
    return (
        f"<style>{font_face()}"
        f"text{{font-family:{FONT_STACK};white-space:pre}}"
        f"{extra}</style>"
    )


def text(x, y, content, *, size=13, fill=TEXT, weight=None, anchor=None):
    attrs = f'x="{x:g}" y="{y:g}" font-size="{size:g}" fill="{fill}"'
    if weight:
        attrs += f' font-weight="{weight}"'
    if anchor:
        attrs += f' text-anchor="{anchor}"'
    return f"<text {attrs}>{escape(content)}</text>"


def flame_icon(cx, cy):
    """The little flame next to each window title, like the ghost in Ghostty's."""
    return (
        f'<g transform="translate({cx} {cy})">'
        f'<path fill="{FIRE_OUTER}" d="M.6-8C1.4-4.6 6.4-3.4 6.4 1.8 6.4 5.6 3.4 8 0 8S-6.4 5.6-6.4 1.8'
        f'C-6.4-.6-5-2.2-3.8-3.6-3.4-2.4-2.6-1.8-1.8-1.4-1.8-4-1.2-6.4.6-8Z"/>'
        f'<path fill="{FIRE_MID}" d="M0-1.4C1 .4 3.6 1.2 3.6 3.8 3.6 5.9 1.9 7.2 0 7.2S-3.6 5.9-3.6 3.8'
        f'C-3.6 1.8-1.2.8 0-1.4Z"/>'
        f'<g fill="{TITLEBAR}"><circle cx="-1.5" cy="3.6" r=".8"/><circle cx="1.5" cy="3.6" r=".8"/></g>'
        f"</g>"
    )


def window_controls(width):
    y = TITLEBAR_HEIGHT / 2
    stroke = f'fill="none" stroke="{TEXT}" stroke-width="1.3" stroke-linecap="round"'
    x = width - 22
    return (
        f'<g {stroke}>'
        f'<rect x="14.5" y="{y - 6}" width="12" height="12" rx="2.5"/>'
        f'<path d="M20.5 {y - 3}v6M17.5 {y}h6"/>'
        f'<path d="M{x - 66} {y - 5.5}h4.5v4.5h-4.5zM{x - 58.5} {y - 5.5}h4.5v4.5h-4.5z'
        f'M{x - 66} {y + 1}h4.5v4.5h-4.5zM{x - 58.5} {y + 1}h4.5v4.5h-4.5z"/>'
        f'<path d="M{x - 34} {y - 4.5}h11M{x - 34} {y}h11M{x - 34} {y + 4.5}h11"/>'
        f"</g>"
        f'<circle cx="{x}" cy="{y}" r="8.5" fill="{BORDER}"/>'
        f'<path d="M{x - 3} {y - 3}l6 6m0-6l-6 6" {stroke}/>'
    )


def window(title, height, body, *, width=WIDTH, style="", label=None):
    """A terminal window modelled on the GTK chrome ghostty.org draws on Linux."""
    w, h, bar = width, height, TITLEBAR_HEIGHT
    title_width = len(title) * 7.8
    label = label or title
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" xml:space="preserve" viewBox="0 0 {w} {h}" '
        f'width="{w}" height="{h}" role="img" aria-label={quoteattr(label)}>'
        f"{base_style(style)}"
        f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="10" fill="{BG}"/>'
        f'<path d="M.5 {bar}V10.5a10 10 0 0 1 10-10H{w - 10.5}a10 10 0 0 1 10 10V{bar}z" fill="{TITLEBAR}"/>'
        f'<path d="M.5 {bar}H{w - .5}" stroke="{HR}"/>'
        f"{window_controls(w)}"
        f"{flame_icon((w - title_width) / 2 - 16, bar / 2)}"
        f'{text(w / 2, bar / 2 + 4.5, title, size=13, fill=HEADING, weight=700, anchor="middle")}'
        f"{body}"
        f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="10" fill="none" stroke="{BORDER}"/>'
        f"</svg>"
    )
