"""Builds the animated header and footer SVGs in assets/ (light and dark).

Run: python scripts/hero.py
These are static assets: rerun only when the copy below changes.
"""

import math
from pathlib import Path

from theme import FONT, MONO, THEMES, esc, gradient

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

NAME = "Tharun S"
ROLE = "Founder · Full-stack engineer · AI-native builder"
COMMAND = '$ claude --agents 8 "turn this idea into a product"'
CHIPS = ["Founder @ Madhigen Technologies", "AI agents in production", "India · UTC+5:30"]
ORBIT_LABELS = ["Claude", "Agents", "Next.js", "Python", "Supabase", "Vercel"]

W, H = 1200, 420


def hero(theme_name: str) -> str:
    t = THEMES[theme_name]
    a1, a2, a3 = t["accents"]
    cx, cy = 960, 210

    # Typed command: a clip rect grows in character steps, then a cursor blinks.
    char_w = 10.8
    cmd_w = len(COMMAND) * char_w + 4
    steps = len(COMMAND)

    chips, x = [], 64
    for label in CHIPS:
        w = len(label) * 7.6 + 28
        chips.append(
            f'<g transform="translate({x:.0f},322)">'
            f'<rect width="{w:.0f}" height="30" rx="15" fill="{t["panel"]}" stroke="{t["border"]}"/>'
            f'<text x="{w / 2:.0f}" y="20" text-anchor="middle" class="chip">{esc(label)}</text></g>'
        )
        x += w + 10

    rings = []
    for i, (r, dur) in enumerate([(70, 14), (115, 22), (160, 34)]):
        direction = "360" if i % 2 == 0 else "-360"
        rings.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{t["muted"]}" stroke-opacity="0.45" stroke-dasharray="3 7"/>'
            f'<g><animateTransform attributeName="transform" type="rotate" from="0 {cx} {cy}" '
            f'to="{direction} {cx} {cy}" dur="{dur}s" repeatCount="indefinite"/>'
            f'<circle cx="{cx + r}" cy="{cy}" r="6" fill="{t["accents"][i]}"/>'
            f'<circle cx="{cx - r * 0.5:.1f}" cy="{cy + r * math.sin(math.radians(120)):.1f}" r="4" fill="{t["accents"][(i + 1) % 3]}" opacity="0.8"/>'
            f"</g>"
        )

    labels, packets = [], []
    for i, label in enumerate(ORBIT_LABELS):
        ang = math.radians(-90 + i * 60)
        lx, ly = cx + 190 * math.cos(ang), cy + 175 * math.sin(ang)
        anchor = "middle" if abs(math.cos(ang)) < 0.2 else ("start" if math.cos(ang) > 0 else "end")
        if anchor == "start":
            lx -= 20
        elif anchor == "end":
            lx += 20
        labels.append(
            f'<text x="{lx:.0f}" y="{ly + 5:.0f}" text-anchor="{anchor}" class="orbit">{esc(label)}</text>'
        )
        sx, sy = cx + 150 * math.cos(ang), cy + 150 * math.sin(ang)
        packets.append(
            f'<circle r="3" fill="{t["accents"][i % 3]}">'
            f'<animateMotion dur="{2.4 + i * 0.35:.2f}s" repeatCount="indefinite" '
            f'path="M{sx:.1f},{sy:.1f} L{cx},{cy}"/>'
            f'<animate attributeName="opacity" values="0;1;1;0" dur="{2.4 + i * 0.35:.2f}s" repeatCount="indefinite"/>'
            f"</circle>"
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(NAME)}: {esc(ROLE)}">
<title>{esc(NAME)}: {esc(ROLE)}</title>
<defs>
{gradient("accent", t["accents"])}
<radialGradient id="glow1"><stop offset="0%" stop-color="{a1}" stop-opacity="{t["glow_opacity"]}"/><stop offset="100%" stop-color="{a1}" stop-opacity="0"/></radialGradient>
<radialGradient id="glow2"><stop offset="0%" stop-color="{a2}" stop-opacity="{t["glow_opacity"]}"/><stop offset="100%" stop-color="{a2}" stop-opacity="0"/></radialGradient>
<radialGradient id="core"><stop offset="0%" stop-color="{a3}"/><stop offset="60%" stop-color="{a2}"/><stop offset="100%" stop-color="{a1}"/></radialGradient>
<pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse"><path d="M32 0H0V32" fill="none" stroke="{t["grid"]}" stroke-width="1"/></pattern>
<clipPath id="card"><rect width="{W}" height="{H}" rx="24"/></clipPath>
<clipPath id="typed"><rect x="64" y="246" height="36" width="0">
  <animate attributeName="width" values="0;{cmd_w:.0f};{cmd_w:.0f};0" keyTimes="0;0.45;0.92;1" dur="9s" calcMode="spline" keySplines="0 0 1 1;0 0 1 1;0.4 0 0.2 1" repeatCount="indefinite"/>
</rect></clipPath>
</defs>
<style>
.name {{ font: 800 68px {FONT}; fill: {t["text"]}; letter-spacing: -1.5px; }}
.role {{ font: 600 23px {FONT}; fill: url(#accent); }}
.cmd {{ font: 500 18px {MONO}; fill: {t["muted"]}; }}
.cmd .p {{ fill: {t["good"]}; }}
.hello {{ font: 600 15px {MONO}; fill: {t["muted"]}; letter-spacing: 1px; }}
.chip {{ font: 600 13px {FONT}; fill: {t["text"]}; }}
.orbit {{ font: 600 13px {MONO}; fill: {t["muted"]}; }}
.cursor {{ animation: blink 1s steps(1) infinite; }}
@keyframes blink {{ 50% {{ opacity: 0; }} }}
.fade {{ animation: rise 1.1s cubic-bezier(.2,.7,.2,1) both; }}
.d1 {{ animation-delay: .15s; }} .d2 {{ animation-delay: .3s; }} .d3 {{ animation-delay: .45s; }}
@keyframes rise {{ from {{ opacity: 0; transform: translateY(14px); }} to {{ opacity: 1; transform: none; }} }}
@media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
</style>
<g clip-path="url(#card)">
<rect width="{W}" height="{H}" fill="{t["bg"]}"/>
<rect width="{W}" height="{H}" fill="url(#grid)"/>
<circle cx="180" cy="40" r="340" fill="url(#glow1)"><animate attributeName="cx" values="180;260;180" dur="16s" repeatCount="indefinite"/></circle>
<circle cx="980" cy="360" r="380" fill="url(#glow2)"><animate attributeName="cy" values="360;300;360" dur="18s" repeatCount="indefinite"/></circle>
<rect x="0" y="0" width="{W}" height="4" fill="url(#accent)"/>
</g>
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="24" fill="none" stroke="{t["border"]}"/>

<g class="fade"><text x="64" y="92" class="hello"><tspan fill="{t["good"]}">●</tspan> HEY, I'M</text></g>
<g class="fade d1"><text x="60" y="168" class="name">{esc(NAME)}</text></g>
<g class="fade d2"><text x="64" y="214" class="role">{esc(ROLE)}</text></g>
<g class="fade d3">
<rect x="56" y="242" width="{cmd_w + 22:.0f}" height="44" rx="10" fill="{t["panel"]}" stroke="{t["border"]}"/>
<g clip-path="url(#typed)"><text x="68" y="270" class="cmd"><tspan class="p">$</tspan>{esc(COMMAND[1:])}</text></g>
<rect x="68" y="254" width="10" height="20" fill="{a1}" class="cursor">
  <animate attributeName="x" values="68;{68 + cmd_w:.0f};{68 + cmd_w:.0f};68" keyTimes="0;0.45;0.92;1" dur="9s" calcMode="spline" keySplines="0 0 1 1;0 0 1 1;0.4 0 0.2 1" repeatCount="indefinite"/>
</rect>
{"".join(chips)}
</g>

<g>
{"".join(rings)}
{"".join(packets)}
<circle cx="{cx}" cy="{cy}" r="34" fill="url(#core)"><animate attributeName="r" values="32;37;32" dur="3s" repeatCount="indefinite"/></circle>
<circle cx="{cx}" cy="{cy}" r="34" fill="none" stroke="{a2}" opacity="0.5"><animate attributeName="r" values="34;70" dur="3s" repeatCount="indefinite"/><animate attributeName="opacity" values="0.6;0" dur="3s" repeatCount="indefinite"/></circle>
<text x="{cx}" y="{cy + 7}" text-anchor="middle" style="font: 800 20px {MONO}; fill: #fff;">&gt;_</text>
{"".join(labels)}
</g>
</svg>
"""


def footer(theme_name: str) -> str:
    t = THEMES[theme_name]
    fw, fh = 1200, 120
    waves = []
    for i, (amp, dur, op) in enumerate([(18, 9, 0.35), (12, 13, 0.55), (8, 7, 0.9)]):
        base = 70 + i * 14

        def path(shift: float) -> str:
            pts = " ".join(
                f"L{x},{base + amp * math.sin((x / fw) * 2 * math.pi * 2 + shift):.1f}"
                for x in range(0, fw + 1, 40)
            )
            return f"M0,{fh} {pts} L{fw},{fh} Z"

        waves.append(
            f'<path fill="url(#fg)" opacity="{op}" d="{path(i)}">'
            f'<animate attributeName="d" dur="{dur}s" repeatCount="indefinite" '
            f'values="{path(i)};{path(i + math.pi)};{path(i)}"/></path>'
        )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{fw}" height="{fh}" viewBox="0 0 {fw} {fh}" role="img" aria-label="Thanks for visiting">
<defs>{gradient("fg", t["accents"])}</defs>
<style>.t {{ font: 600 15px {MONO}; fill: {t["muted"]}; }}</style>
{"".join(waves)}
<text x="{fw / 2:.0f}" y="34" text-anchor="middle" class="t">built with curiosity, coffee and a lot of Claude</text>
</svg>
"""


if __name__ == "__main__":
    ASSETS.mkdir(exist_ok=True)
    for name in THEMES:
        (ASSETS / f"hero-{name}.svg").write_text(hero(name), encoding="utf-8")
        (ASSETS / f"footer-{name}.svg").write_text(footer(name), encoding="utf-8")
    print("wrote", sorted(p.name for p in ASSETS.glob("*.svg")))
