"""Shared colours and fonts for every SVG this repo generates."""

FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"

# Accent gradient: coral (avatar background) -> violet -> cyan.
ACCENTS = ("#FF5A5F", "#8B5CF6", "#22D3EE")

THEMES = {
    "dark": {
        "bg": "#0D1117",
        "panel": "#161B22",
        "border": "#30363D",
        "grid": "#1F2630",
        "text": "#E6EDF3",
        "muted": "#8B949E",
        "accents": ACCENTS,
        "good": "#3FB950",
        "glow_opacity": "0.35",
    },
    "light": {
        "bg": "#FFFFFF",
        "panel": "#F6F8FA",
        "border": "#D0D7DE",
        "grid": "#EEF1F4",
        "text": "#1F2328",
        "muted": "#59636E",
        "accents": ("#E5484D", "#7C3AED", "#0891B2"),
        "good": "#1A7F37",
        "glow_opacity": "0.18",
    },
}


def gradient(gid: str, accents, x2: str = "100%", y2: str = "0%") -> str:
    a, b, c = accents
    return (
        f'<linearGradient id="{gid}" x1="0%" y1="0%" x2="{x2}" y2="{y2}">'
        f'<stop offset="0%" stop-color="{a}"/><stop offset="50%" stop-color="{b}"/>'
        f'<stop offset="100%" stop-color="{c}"/></linearGradient>'
    )


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
