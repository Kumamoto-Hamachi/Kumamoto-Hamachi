"""Render assets/hero.svg: a looping ASCII campfire character, drawn the way ghostty.org draws its ghost.

Each character cell samples a distance field: a flame with a cut-out face on crossed logs, rising
sparks, a shimmering cobalt halo, and a yellowtail (hamachi) swimming past while the fire watches it.
Frames are stacked in the SVG and toggled with CSS, since a README image cannot run JS.
"""

from math import atan2, hypot, pi, sin
from xml.sax.saxutils import escape

from theme import (
    ASSETS,
    BRAND,
    FIRE_CORE,
    FIRE_MID,
    FIRE_OUTER,
    FIRE_RIM,
    FISH,
    LOG,
    TITLEBAR_HEIGHT,
    WIDTH,
    window,
)

COLS, ROWS = 100, 36
FONT_SIZE = 13.8
CELL_W = FONT_SIZE * 0.6
CELL_H = 16.5
ASPECT = CELL_H / CELL_W
PAD_X = (WIDTH - COLS * CELL_W) / 2
PAD_Y = 14

FPS = 12
FRAMES = 60
FISH_ART = "><(((o>"

BASE_Y = 16  # where the flame meets the logs, in columns below the center of the scene

# One short CSS class per color, because these repeat thousands of times in the file.
LAYERS = {
    "g": LOG,
    "b": BRAND,
    "k": FIRE_CORE,
    "m": FIRE_MID,
    "o": FIRE_OUTER,
    "r": FIRE_RIM,
}

# x, phase offset, trips per loop, sideways drift
SPARKS = [
    (-6, 0.00, 2, 5),
    (9, 0.37, 3, -4),
    (-13, 0.61, 2, 6),
    (3, 0.83, 3, 3),
    (16, 0.18, 2, -5),
    (-2, 0.49, 3, -6),
    (11, 0.72, 2, 4),
    (-9, 0.28, 3, 4),
    (6, 0.05, 2, -3),
]

# x, height, width, sway, waves per loop, wave offset, and the same for the height flicker.
# Every rate is a whole number per loop so the last frame runs back into the first.
TONGUES = [
    (0, 46, 15, 6, 5, 0.0, 2.4, 5, 0.0),
    (-8, 36, 9, 5, 6, 1.7, 3.0, 7, 2.0),
    (9, 38, 9, 5, 7, 3.9, 3.0, 8, 0.5),
    (-17, 24, 7, 4, 8, 5.2, 3.0, 9, 4.0),
    (18, 27, 7, 4, 6, 2.6, 3.0, 11, 1.0),
]


def ellipse(x, y, a, b):
    return (hypot(x / a, y / b) - 1) * min(a, b)


def smooth_min(a, b, k):
    h = max(k - abs(a - b), 0) / k
    return min(a, b) - h * h * k / 4


def capsule(x, y, ax, ay, bx, by, radius):
    px, py = x - ax, y - ay
    dx, dy = bx - ax, by - ay
    h = max(0, min(1, (px * dx + py * dy) / (dx * dx + dy * dy)))
    return hypot(px - dx * h, py - dy * h) - radius


def arc(x, y, r, thickness):
    """Lower half of a ring, used for the mouth."""
    if y < 0:
        return hypot(abs(x) - r, y) - thickness
    return abs(hypot(x, y) - r) - thickness


def noise(c, r, i):
    return ((c * 73856093) ^ (r * 19349663) ^ (i * 83492791)) % 1000 / 1000


def blink_amount(t):
    """1 is fully open. Blinks twice in quick succession, then rests."""
    amount = 1.0
    for start in (0.42, 0.52):
        phase = (t - start) / 0.05
        if 0 <= phase <= 1:
            amount = min(amount, abs(2 * phase - 1))
    return amount


def tongue(x, y, base_x, height, width, amplitude, wave):
    """Approximate distance to a teardrop flame whose upper part bends along a rising wave."""
    v = (BASE_Y - y) / height
    if v <= 0:
        return hypot(x - base_x, y - BASE_Y)
    if v >= 1:
        return hypot(x - base_x - amplitude * sin(2 * pi * 1.3 + wave), y - BASE_Y + height)
    bend = amplitude * v**1.6 * sin(2 * pi * 1.3 * v + wave)
    half_width = width * 2.35 * v**0.45 * (1 - v) ** 0.95
    return abs(x - base_x - bend) - half_width


def sample_fire(x, y, t, eye_dx=0.0, eye_open=1.0):
    """Distances at a point, in columns: (flame, flame with the face cut out, logs)."""
    phase = 2 * pi * t
    flame = 99.0
    for base_x, height, width, sway, waves, offset, flicker, rate, flicker_offset in TONGUES:
        h = height + flicker * sin(rate * phase + flicker_offset)
        flame = smooth_min(flame, tongue(x, y, base_x, h, width, sway, offset - waves * phase), 2)

    eye_x, eye_y = abs(x - eye_dx) - 8, y - 2
    eye = ellipse(eye_x, eye_y, 3.4, max(0.4, 4.2 * eye_open))
    mouth = arc(x - eye_dx * 0.6, y - 9, 4, 1)
    shape = max(flame, -eye, -mouth)
    if eye_open > 0.6:
        # A catch-light on the side nearest the fish keeps the eyes from reading as holes.
        side = 8 if x > eye_dx else -8
        shape = min(shape, hypot(x - eye_dx - side - eye_dx * 0.5, eye_y + 1.2) - 1)

    logs = min(
        capsule(x, y, -21, BASE_Y + 10, 21, BASE_Y, 2.6),
        capsule(x, y, 21, BASE_Y + 10, -21, BASE_Y, 2.6),
    )
    return flame, shape, logs


def flame_cell(shape, heat, c, r, i):
    """(char, layer) for a flame cell, or None outside it. Hotter cells are denser and brighter."""
    if shape > 0.75:
        return None
    if shape > 0.25:
        return ("·" if noise(c, r, i) < 0.6 else "~"), "r"
    if heat > 7:
        return ("$" if shape < -1.3 else "@"), "k"
    if heat > 3:
        return "@", "m"
    if heat > 1.2:
        return "%*"[noise(c, r, i) < 0.5], "o"
    return "=*+"[int(noise(c, r, i) * 3)], "r"


def log_char(d, c, r):
    if d > 0.75:
        return None
    if d > 0.25:
        return "·" if noise(c, r, 0) < 0.6 else "~"
    if d > -0.45:
        return "=*+"[int(noise(c, r, 1) * 3)]
    if d > -1.3:
        return "@"
    return "$"


def halo_char(d, theta, c, r, i, t):
    phase = 2 * pi * t
    center = 4.2 + 0.7 * sin(3 * theta + phase) + 0.35 * sin(7 * theta - 2 * phase)
    offset = abs(d - center)
    if offset > 1.25:
        return None
    # Two gaps orbit the fire so the ring reads as motion, not a static outline.
    if sin(2 * theta - phase) < -0.9:
        return None
    n = noise(c, r, i)
    if offset < 0.5:
        return "%*"[n < 0.45]
    if offset < 0.9:
        return "=*"[n < 0.2]
    return "+=x~"[int(n * 4)]


def blank_layers(cols, rows):
    return {name: [[" "] * cols for _ in range(rows)] for name in LAYERS}


def paint_fire(layers, r, c, x, y, t, i, *, scale=1.0, eye_dx=0.0, eye_open=1.0):
    """Paint the logs or flame at this cell, logs in front. Returns False if the cell stays empty."""
    flame, shape, logs = sample_fire(x, y, t, eye_dx, eye_open)
    ch = log_char(logs * scale, c, r)
    if ch is not None:
        layers["g"][r][c] = ch
        return True
    # Fire cools as it rises, so the tips burn red whatever their width. The face sits in a
    # white-hot patch of its own, which is what makes the cut-out eyes and mouth readable.
    heat = -flame - max(0, -y) * 0.16 + max(0, 16 - hypot((x - eye_dx) / 1.5, y - 5))
    cell = flame_cell(shape * scale, heat, c, r, i)
    if cell is None:
        return False
    layers[cell[1]][r][c] = cell[0]
    return True


def paint_sparks(layers, painted, cx, cy, t):
    for x0, offset, trips, drift in SPARKS:
        age = (t * trips + offset) % 1
        x = x0 + drift * age * sin(3 * pi * age + offset * 9)
        c, r = round(cx + x), round(cy - age * 32 / ASPECT)
        if (r, c) in painted:
            continue
        ch, layer = ("*", "m") if age < 0.35 else ("+", "o") if age < 0.7 else ("·", "r")
        layers[layer][r][c] = ch
        painted.add((r, c))


def render_frame(i):
    t = i / FRAMES
    cx, cy = (COLS - 1) / 2, (ROWS - 1) / 2
    layers = blank_layers(COLS, ROWS)

    # The fish crosses once per loop with a little sway, and the fire's eyes follow it.
    fish_x = int(-len(FISH_ART) + (COLS + len(FISH_ART) * 2) * t)
    fish_row = ROWS - 2 + round(0.6 * sin(8 * pi * t))
    eye_dx = max(-1.6, min(1.6, (fish_x + 3 - COLS / 2) / 25))
    eye_open = blink_amount(t)

    painted = set()
    for r in range(ROWS):
        for c in range(COLS):
            x, y = c - cx, (r - cy) * ASPECT
            if paint_fire(layers, r, c, x, y, t, i, eye_dx=eye_dx, eye_open=eye_open):
                painted.add((r, c))

    paint_sparks(layers, painted, cx, cy, t)

    for r in range(ROWS):
        for c in range(COLS):
            if (r, c) not in painted:
                x, y = c - cx, (r - cy) * ASPECT
                halo = halo_char(ellipse(x, y, 38, 29.5), atan2(y, x), c, r, i, t)
                if halo is not None:
                    layers["b"][r][c] = halo

    return layers, (fish_x, fish_row)


def render_logo(cols, rows, scale):
    """A small still of the fire as (color, lines), for where fastfetch would print a distro logo."""
    layers = blank_layers(cols, rows)
    cx, cy = (cols - 1) / 2, (rows - 1) / 2
    for r in range(rows):
        for c in range(cols):
            x, y = (c - cx) / scale, (r - cy) * ASPECT / scale - 1
            paint_fire(layers, r, c, x, y, 0.1, 0, scale=scale)
    return [
        (LAYERS[name], ["".join(cells).rstrip() for cells in grid]) for name, grid in layers.items()
    ]


def row_elements(rows):
    parts = []
    for r, cells in enumerate(rows):
        line = "".join(cells)
        stripped = line.strip()
        if not stripped:
            continue
        x = PAD_X + (len(line) - len(line.lstrip())) * CELL_W
        y = TITLEBAR_HEIGHT + PAD_Y + (r + 0.8) * CELL_H
        parts.append(f'<text x="{x:.2f}" y="{y:.1f}">{escape(stripped)}</text>')
    return "".join(parts)


def fish_element(fish_x, fish_row):
    start, end = max(fish_x, 0), min(fish_x + len(FISH_ART), COLS)
    if start >= end:
        return ""
    visible = FISH_ART[start - fish_x : end - fish_x]
    x = PAD_X + start * CELL_W
    y = TITLEBAR_HEIGHT + PAD_Y + (fish_row + 0.8) * CELL_H
    return f'<text class="h" x="{x:.2f}" y="{y:.1f}">{escape(visible)}</text>'


def build():
    duration = FRAMES / FPS
    frames = []
    for i in range(FRAMES):
        layers, (fish_x, fish_row) = render_frame(i)
        delay = -(FRAMES - i) * duration / FRAMES if i else 0
        groups = "".join(f'<g class="{name}">{row_elements(grid)}</g>' for name, grid in layers.items())
        frames.append(
            f'<g class="f{" s" if i == 0 else ""}" style="animation-delay:{delay:.3f}s">'
            f"{groups}{fish_element(fish_x, fish_row)}</g>"
        )

    step = 100 / FRAMES
    colors = "".join(f".{name}{{fill:{color}}}" for name, color in LAYERS.items())
    style = (
        f"#a text{{font-size:{FONT_SIZE}px}}"
        f"{colors}.h{{fill:{FISH}}}"
        ".f{visibility:hidden}.s{visibility:visible}"
        "@media (prefers-reduced-motion:no-preference){"
        f".f{{animation:p {duration:g}s steps(1,end) infinite}}"
        "}"
        f"@keyframes p{{0%{{visibility:visible}}{step:.3f}%,100%{{visibility:hidden}}}}"
    )
    height = TITLEBAR_HEIGHT + PAD_Y * 2 + ROWS * CELL_H
    svg = window(
        "kumamoto",
        round(height),
        f'<g id="a">{"".join(frames)}</g>',
        style=style,
        label="Animated ASCII art of a campfire character in a terminal window, watching a fish swim past",
    )
    ASSETS.mkdir(exist_ok=True)
    (ASSETS / "hero.svg").write_text(svg, encoding="utf-8")
    print(f"hero.svg: {len(svg) / 1024:.0f} KiB")


if __name__ == "__main__":
    build()
