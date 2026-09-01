"""Reaction Theater — vessels, heat source, phase strips for the Chemistry Lab.

Pure HTML / SVG / CSS. No third-party deps; rendered into Streamlit via
either ``st.markdown(unsafe_allow_html=True)`` (works for the simple
helpers) or ``st.components.v1.html`` (recommended for the full
``render_theater`` scene, which carries its own ``<style>`` block with
animation keyframes — an iframe avoids style collisions).

Public surface:
- ``render_theater(...)``     full hero scene HTML string
- ``theater_height()``        recommended iframe height for components.html
- ``heat_source_svg(T_K)``    standalone flame / thermometer widget
- ``phase_strip_svg(item, T_K)``  solid|liquid|gas strip with current tick
"""

from __future__ import annotations

import re

from . import data_loader


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

_PHASE_DEFAULT_COLOR = {
    "solid":   "#9aa3b5",
    "liquid":  "#5a8fd8",
    "gas":     "#e8eef8",
    "aqueous": "#7fb3e3",
    "plasma":  "#d066ff",
    "unknown": "#b4b8c0",
}


def _phase_at(item: dict, temperature_K: float) -> str:
    """Return current phase from melting/boiling vs T; fall back to STP phase."""
    mp = item.get("melting_point_K")
    bp = item.get("boiling_point_K")
    if mp is None or bp is None:
        return str(item.get("phase_at_stp") or "unknown")
    T = float(temperature_K)
    if float(mp) >= float(bp):
        # Sublimer at 1 atm (e.g. CO₂: triple point above the sublimation
        # point) — no liquid phase exists at ambient pressure.
        return "solid" if T < float(bp) else "gas"
    if T < float(mp):
        return "solid"
    if T < float(bp):
        return "liquid"
    return "gas"


def _safe_color(c: str | None, phase: str) -> str:
    """Sanitize a color name from Claude; fall back to a phase-appropriate hue."""
    if not c:
        return _PHASE_DEFAULT_COLOR.get(phase, _PHASE_DEFAULT_COLOR["unknown"])
    s = c.strip()
    low = s.lower()
    if low in {"", "none", "transparent"}:
        return _PHASE_DEFAULT_COLOR.get(phase, _PHASE_DEFAULT_COLOR["unknown"])
    if low == "colorless":
        if phase == "gas":
            return "rgba(230,238,250,0.35)"
        if phase == "liquid":
            return "rgba(180,200,230,0.55)"
        return "#cfd4dc"
    # Only allow strings that look like a CSS color token (named color, hex,
    # or rgb()/hsl() call). Anything else — multi-word names Claude invents,
    # or stray markup — falls back to the phase default instead of silently
    # rendering transparent (or injecting into the inline style).
    if re.fullmatch(r"#[0-9a-fA-F]{3,8}|[a-zA-Z]+|(?:rgb|rgba|hsl|hsla)\([0-9,.%\s]*\)", s):
        return s
    return _PHASE_DEFAULT_COLOR.get(phase, _PHASE_DEFAULT_COLOR["unknown"])


# ---------------------------------------------------------------------------
# heat source widget
# ---------------------------------------------------------------------------

def heat_source_svg(temperature_K: float, *, width: int = 120, height: int = 120) -> str:
    """Animated SVG whose appearance reflects the current temperature regime."""
    T = float(temperature_K)
    if T < 273:
        return f"""
<svg viewBox="0 0 100 100" width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
  <defs><radialGradient id="ib" cx="50%" cy="60%" r="55%">
    <stop offset="0%" stop-color="#cfe7ff"/><stop offset="100%" stop-color="#5a8fd8"/>
  </radialGradient></defs>
  <ellipse cx="50" cy="68" rx="42" ry="20" fill="url(#ib)"/>
  <g fill="#eaf3ff" stroke="#88b4e8" stroke-width="1.4">
    <path d="M50 28 v22 M40 34 l20 14 M40 48 l20 -14"/>
  </g>
  <text x="50" y="96" text-anchor="middle" font-size="10" fill="#88b4e8">{T:.0f} K · ice bath</text>
</svg>
"""
    if T < 373:
        return f"""
<svg viewBox="0 0 100 100" width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
  <rect x="45" y="12" width="10" height="62" rx="4" fill="#1f2937" stroke="#374151"/>
  <circle cx="50" cy="82" r="12" fill="#ef4444"/>
  <rect x="48" y="28" width="4" height="52" fill="#ef4444"/>
  <text x="50" y="99" text-anchor="middle" font-size="10" fill="#c0c8d6">{T:.0f} K · ambient</text>
</svg>
"""
    if T < 1000:
        return f"""
<svg viewBox="0 0 100 100" width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
  <style>
    .fo {{ animation: flick 0.45s ease-in-out infinite alternate; transform-origin:50% 90%; }}
    .fi {{ animation: flick 0.32s ease-in-out infinite alternate; transform-origin:50% 90%; }}
    @keyframes flick {{ from {{ transform: scaleY(1) scaleX(1); }}
                        to   {{ transform: scaleY(1.10) scaleX(0.94); }} }}
  </style>
  <rect x="30" y="76" width="40" height="10" fill="#374151"/>
  <path class="fo" d="M50 80 C30 70 28 40 50 18 C72 40 70 70 50 80 Z" fill="#ffcc33"/>
  <path class="fi" d="M50 78 C40 70 38 50 50 32 C62 50 60 70 50 78 Z" fill="#3aa6ff" opacity="0.85"/>
  <text x="50" y="96" text-anchor="middle" font-size="10" fill="#e5e7eb">{T:.0f} K · bunsen</text>
</svg>
"""
    if T < 4000:
        return f"""
<svg viewBox="0 0 100 100" width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
  <defs><radialGradient id="fu" cx="50%" cy="55%" r="55%">
    <stop offset="0%" stop-color="#fff2c2"/>
    <stop offset="55%" stop-color="#ff8a1c"/>
    <stop offset="100%" stop-color="#7a1d0a"/>
  </radialGradient></defs>
  <style>
    .gl {{ animation: pul 0.6s ease-in-out infinite alternate; transform-origin:50% 50%; }}
    @keyframes pul {{ from {{ opacity:0.78; }} to {{ opacity:1; }} }}
  </style>
  <rect x="12" y="28" width="76" height="52" rx="6" fill="#1f1208" stroke="#3a2316"/>
  <ellipse class="gl" cx="50" cy="55" rx="30" ry="18" fill="url(#fu)"/>
  <text x="50" y="94" text-anchor="middle" font-size="10" fill="#fcd34d">{T:.0f} K · furnace</text>
</svg>
"""
    # plasma
    return f"""
<svg viewBox="0 0 100 100" width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
  <defs><radialGradient id="pl" cx="50%" cy="50%" r="55%">
    <stop offset="0%" stop-color="#ffffff"/>
    <stop offset="45%" stop-color="#d066ff"/>
    <stop offset="100%" stop-color="#3b0764"/>
  </radialGradient></defs>
  <style>
    .ar {{ animation: zap 0.18s linear infinite alternate; }}
    @keyframes zap {{ from {{ opacity:0.4; transform: translateY(0); }}
                      to   {{ opacity:1;   transform: translateY(-2px); }} }}
  </style>
  <circle cx="50" cy="50" r="32" fill="url(#pl)"/>
  <g class="ar" stroke="#fff" stroke-width="1.6" fill="none" opacity="0.85">
    <polyline points="30,60 40,42 36,38 52,22"/>
    <polyline points="70,40 62,55 66,58 50,72"/>
  </g>
  <text x="50" y="96" text-anchor="middle" font-size="10" fill="#f5d0fe">{T:.0f} K · plasma</text>
</svg>
"""


# ---------------------------------------------------------------------------
# per-reactant phase strip (solid | liquid | gas)
# ---------------------------------------------------------------------------

def phase_strip_svg(item: dict, temperature_K: float, *, width: int = 220, height: int = 42) -> str:
    """Three-segment bar with a tick at the current T. Returns "" if no data."""
    mp = item.get("melting_point_K")
    bp = item.get("boiling_point_K")
    if mp is None or bp is None:
        return ""
    mp = float(mp); bp = float(bp); T = float(temperature_K)
    axis_max = max(bp * 1.4, 1000.0, T * 1.05)

    def x(t: float) -> float:
        frac = max(0.0, min(1.0, t / axis_max))
        return 8 + (width - 16) * frac

    mp_x = x(mp)
    bp_x = x(bp)
    cur_x = x(T)
    return f"""
<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
  <rect x="8" y="14" width="{mp_x - 8:.1f}" height="10" fill="#9aa3b5" opacity="0.7"/>
  <rect x="{mp_x:.1f}" y="14" width="{bp_x - mp_x:.1f}" height="10" fill="#5a8fd8" opacity="0.7"/>
  <rect x="{bp_x:.1f}" y="14" width="{width - 8 - bp_x:.1f}" height="10" fill="#a3b8d8" opacity="0.7"/>
  <line x1="{cur_x:.1f}" y1="9" x2="{cur_x:.1f}" y2="30" stroke="#fde68a" stroke-width="2"/>
  <polygon points="{cur_x - 5:.1f},9 {cur_x + 5:.1f},9 {cur_x:.1f},4" fill="#fde68a"/>
  <text x="8" y="40" font-size="9" fill="#cbd5e1">solid</text>
  <text x="{(mp_x + bp_x) / 2:.1f}" y="40" text-anchor="middle" font-size="9" fill="#cbd5e1">liquid</text>
  <text x="{width - 8:.1f}" y="40" text-anchor="end" font-size="9" fill="#cbd5e1">gas</text>
</svg>
"""


# ---------------------------------------------------------------------------
# vessel SVGs (per reactant / product)
# ---------------------------------------------------------------------------

def _vessel_svg(label: str, color: str, phase: str, *, width: int = 110, height: int = 170) -> str:
    """Return one beaker / test tube SVG showing the given phase."""
    if phase == "gas" or phase == "plasma":
        fill = (
            f'<rect x="22" y="20" width="56" height="118" fill="{color}" opacity="0.45"/>'
            '<g fill="#ffffff" opacity="0.7">'
            '<circle cx="34" cy="50"  r="2"><animate attributeName="cy" values="120;30;120" dur="3s"   repeatCount="indefinite"/></circle>'
            '<circle cx="66" cy="75"  r="1.6"><animate attributeName="cy" values="130;30;130" dur="3.6s" repeatCount="indefinite"/></circle>'
            '<circle cx="50" cy="100" r="1.4"><animate attributeName="cy" values="135;35;135" dur="4.1s" repeatCount="indefinite"/></circle>'
            '<circle cx="42" cy="120" r="1.6"><animate attributeName="cy" values="138;40;138" dur="3.3s" repeatCount="indefinite"/></circle>'
            '</g>'
        )
    elif phase == "solid":
        fill = (
            f'<rect x="26" y="100" width="48" height="38" fill="{color}" stroke="#1f2937" stroke-width="1.4"/>'
            f'<rect x="30" y="96"  width="40" height="6"  fill="{color}" stroke="#1f2937" stroke-width="1.2"/>'
        )
    else:  # liquid / aqueous / unknown
        fill = (
            f'<rect x="22" y="80" width="56" height="58" fill="{color}"/>'
            f'<ellipse cx="50" cy="80" rx="28" ry="5" fill="{color}"/>'
            '<ellipse cx="44" cy="82" rx="10" ry="2" fill="#ffffff" opacity="0.35"/>'
        )
    return f"""
<svg viewBox="0 0 100 175" width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <clipPath id="vc">
      <path d="M22 20 L22 132 Q22 144 34 144 L66 144 Q78 144 78 132 L78 20 Z"/>
    </clipPath>
  </defs>
  <g clip-path="url(#vc)">{fill}</g>
  <path d="M22 20 L22 132 Q22 144 34 144 L66 144 Q78 144 78 132 L78 20"
        fill="none" stroke="#cbd5e1" stroke-width="2"/>
  <rect x="18" y="14" width="64" height="8" rx="2" fill="#94a3b8"/>
  <text x="50" y="170" text-anchor="middle" font-size="11" fill="#e5e7eb">{label}</text>
</svg>
"""


# ---------------------------------------------------------------------------
# effects layer dispatch (Claude-driven)
# ---------------------------------------------------------------------------

_EFFECT_LAYERS = {
    "bubbles":        '<div class="fx fx-bubbles"></div>',
    "fizz":           '<div class="fx fx-bubbles fx-fast"></div>',
    "vapor":          '<div class="fx fx-vapor"></div>',
    "smoke":          '<div class="fx fx-smoke"></div>',
    "flame":          '<div class="fx fx-flame"></div>',
    "flash":          '<div class="fx fx-flash"></div>',
    "explosion":      '<div class="fx fx-explosion"></div>',
    "spark":          '<div class="fx fx-spark"></div>',
    "glow":           '<div class="fx fx-glow"></div>',
    "color_change":   '<div class="fx fx-colorshift"></div>',
    "precipitate":    '<div class="fx fx-precipitate"></div>',
    "crystal_growth": '<div class="fx fx-crystal"></div>',
    "melt":           '<div class="fx fx-melt"></div>',
    "freeze":         '<div class="fx fx-freeze"></div>',
}


# ---------------------------------------------------------------------------
# main entry point
# ---------------------------------------------------------------------------

def theater_height() -> int:
    """Recommended iframe height for ``st.components.v1.html``."""
    return 470


def render_theater(
    *,
    reactants: list[dict],
    product_phase: str,
    product_label: str,
    byproduct_labels: list[str],
    reactant_colors: list[str],
    product_colors: list[str],
    visual_effects: list[str],
    dramatic_moment: str,
    temperature_K: float,
) -> str:
    """Return a full HTML/SVG/CSS block for the Reaction Theater scene.

    ``reactants`` is a list of dicts with at least ``kind`` ('element' or
    'compound') and ``ident`` (symbol or formula).
    """
    # Build reactant vessel column
    react_html_parts: list[str] = []
    for i, r in enumerate(reactants[:3]):
        if r.get("kind") == "element":
            rec = data_loader.element_by_symbol(r["ident"]) or {}
        else:
            rec = data_loader.compound_by_formula(r["ident"]) or {}
        phase = _phase_at(rec, temperature_K)
        color = _safe_color(
            reactant_colors[i] if i < len(reactant_colors) else None, phase
        )
        label = rec.get("name") or rec.get("symbol") or rec.get("formula") or r["ident"]
        vessel = _vessel_svg(label, color, phase)
        strip = phase_strip_svg(rec, temperature_K)
        react_html_parts.append(
            f'<div class="vessel-wrap">{vessel}'
            f'<div class="strip">{strip}</div></div>'
        )
    reactant_html = "".join(react_html_parts) or '<div class="vessel-wrap"><em>no reactants</em></div>'

    # Product vessel
    prod_phase = (product_phase or "unknown").lower()
    prod_color = _safe_color(
        product_colors[0] if product_colors else None, prod_phase
    )
    product_vessel = _vessel_svg(
        product_label or "?", prod_color, prod_phase, width=140, height=190,
    )

    effects_html = "".join(
        _EFFECT_LAYERS[e] for e in visual_effects if e in _EFFECT_LAYERS
    )

    bp_html = ""
    if byproduct_labels:
        chips = "".join(
            f'<span class="bp-chip">{b}</span>' for b in byproduct_labels[:3]
        )
        bp_html = f'<div class="bp-row">{chips}</div>'

    heat = heat_source_svg(temperature_K, width=110, height=110)

    moment_html = (
        f'<div class="moment">{dramatic_moment}</div>' if dramatic_moment else ""
    )

    body = f"""
<div class="theater">
  <div class="reactants">{reactant_html}</div>
  <div class="middle">
    <div class="arrow">
      <svg viewBox="0 0 120 40" width="100%" height="40">
        <defs><marker id="ahead" viewBox="0 0 10 10" refX="8" refY="5"
              markerWidth="6" markerHeight="6" orient="auto">
          <path d="M0,0 L10,5 L0,10 z" fill="#fcd34d"/></marker></defs>
        <line x1="5" y1="20" x2="110" y2="20" stroke="#fcd34d"
              stroke-width="3" marker-end="url(#ahead)"/>
      </svg>
    </div>
    {moment_html}
    <div class="heat">{heat}</div>
  </div>
  <div class="products">
    <div class="vessel-wrap product-vessel">
      {product_vessel}
      {effects_html}
    </div>
    {bp_html}
  </div>
</div>
"""
    return _THEATER_CSS + body


# ---------------------------------------------------------------------------
# styles (kept in one block so the whole theater is one HTML payload)
# ---------------------------------------------------------------------------

_THEATER_CSS = """
<style>
.theater {
  display: grid;
  grid-template-columns: minmax(180px, 1.2fr) minmax(170px, 1fr) minmax(200px, 1.3fr);
  gap: 14px;
  align-items: center;
  background: radial-gradient(ellipse at center, #1b2434 0%, #0b1020 100%);
  border-radius: 14px;
  padding: 16px 18px 14px;
  color: #e5e7eb;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
.theater .reactants {
  display: flex; flex-wrap: wrap; gap: 10px; justify-content: center;
}
.theater .vessel-wrap { position: relative; display: flex; flex-direction: column; align-items: center; gap: 4px; }
.theater .strip { line-height: 0; }
.theater .middle { text-align: center; display: flex; flex-direction: column; gap: 8px; align-items: center; }
.theater .arrow svg { display: block; width: 100%; max-width: 180px; }
.theater .moment {
  font-size: 0.9rem; line-height: 1.25;
  color: #fde68a;
  background: rgba(252,211,77,0.08);
  border: 1px solid rgba(252,211,77,0.35);
  border-radius: 8px; padding: 8px 10px; max-width: 240px; font-style: italic;
  animation: momentFade 0.9s ease-out;
}
@keyframes momentFade {
  from { opacity: 0; transform: translateY(6px); }
  to   { opacity: 1; transform: translateY(0); }
}
.theater .products { display: flex; flex-direction: column; align-items: center; gap: 8px; }
.theater .product-vessel { position: relative; width: 160px; height: 200px; }
.theater .bp-row { display: flex; gap: 6px; flex-wrap: wrap; justify-content: center; }
.theater .bp-chip {
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.18);
  color: #f3f4f6; font-size: 0.75rem; padding: 2px 8px; border-radius: 999px;
}

.theater .fx {
  position: absolute; left: 0; top: 0; right: 0; bottom: 0;
  pointer-events: none; border-radius: 8px; overflow: hidden;
}

.theater .fx-bubbles {
  background:
    radial-gradient(circle at 50% 90%, rgba(255,255,255,0.85) 2.2px, transparent 3px),
    radial-gradient(circle at 40% 80%, rgba(255,255,255,0.7) 1.6px, transparent 2.6px),
    radial-gradient(circle at 60% 75%, rgba(255,255,255,0.7) 1.8px, transparent 2.8px),
    radial-gradient(circle at 55% 95%, rgba(255,255,255,0.55) 1.5px, transparent 2.4px);
  animation: bubbleRise 2.4s linear infinite;
}
.theater .fx-bubbles.fx-fast { animation-duration: 1.1s; }
@keyframes bubbleRise {
  from { background-position: 0 0, 0 0, 0 0, 0 0; opacity: 0.9; }
  to   { background-position: 0 -80px, 0 -90px, 0 -70px, 0 -100px; opacity: 0.95; }
}

.theater .fx-vapor {
  background: radial-gradient(ellipse at 50% 0%, rgba(220,235,255,0.55) 0%, rgba(220,235,255,0) 60%);
  animation: vaporDrift 3s ease-in-out infinite alternate;
}
@keyframes vaporDrift {
  from { opacity: 0.45; transform: translateY(-6px) scale(1, 1); }
  to   { opacity: 0.75; transform: translateY(-16px) scale(1.1, 1.15); }
}

.theater .fx-smoke {
  background: radial-gradient(ellipse at 50% -10%, rgba(140,140,160,0.65) 0%, rgba(140,140,160,0) 55%);
  animation: vaporDrift 4s ease-in-out infinite alternate;
}

.theater .fx-flame {
  background:
    radial-gradient(ellipse at 50% 8%, #ffb627 0%, rgba(255,182,39,0) 35%),
    radial-gradient(ellipse at 40% 4%, #ff7b00 0%, rgba(255,123,0,0) 30%),
    radial-gradient(ellipse at 60% 4%, #ffd966 0%, rgba(255,217,102,0) 30%);
  animation: flameLick 0.5s ease-in-out infinite alternate;
}
@keyframes flameLick {
  from { transform: scaleY(1) scaleX(1); opacity: 0.9; }
  to   { transform: scaleY(1.12) scaleX(0.92); opacity: 1; }
}

.theater .fx-flash {
  background: radial-gradient(circle at 50% 50%, rgba(255,255,255,1) 0%, rgba(255,255,255,0) 70%);
  animation: flashPulse 1.4s ease-out infinite;
}
@keyframes flashPulse {
  0%   { opacity: 0; }
  10%  { opacity: 0.95; }
  35%  { opacity: 0; }
  100% { opacity: 0; }
}

.theater .fx-explosion {
  background: radial-gradient(circle at 50% 50%, rgba(255,200,80,0.95) 0%, rgba(255,80,0,0.6) 35%, rgba(0,0,0,0) 60%);
  animation: explode 1.6s ease-out infinite;
}
@keyframes explode {
  0%   { transform: scale(0.4); opacity: 1; }
  60%  { transform: scale(1.4); opacity: 0.4; }
  100% { transform: scale(1.6); opacity: 0; }
}

.theater .fx-spark {
  background:
    radial-gradient(circle at 20% 30%, #fef08a 1.5px, transparent 2px),
    radial-gradient(circle at 80% 40%, #fde68a 1.4px, transparent 2px),
    radial-gradient(circle at 35% 75%, #facc15 1.6px, transparent 2px),
    radial-gradient(circle at 70% 80%, #fde047 1.4px, transparent 2px);
  animation: sparkBurst 1.1s ease-out infinite;
}
@keyframes sparkBurst {
  0%   { opacity: 0; transform: scale(0.6); }
  35%  { opacity: 1; }
  100% { opacity: 0; transform: scale(1.4); }
}

.theater .fx-glow {
  background: radial-gradient(circle at 50% 50%, rgba(180,255,200,0.55) 0%, rgba(180,255,200,0) 60%);
  animation: glowPulse 2.5s ease-in-out infinite alternate;
}
@keyframes glowPulse {
  from { opacity: 0.45; } to { opacity: 0.85; }
}

.theater .fx-colorshift {
  background: linear-gradient(45deg, rgba(255,80,180,0.4), rgba(80,180,255,0.4), rgba(80,255,180,0.4));
  mix-blend-mode: screen;
  animation: huerot 4s linear infinite;
}
@keyframes huerot { from { filter: hue-rotate(0deg); } to { filter: hue-rotate(360deg); } }

.theater .fx-precipitate {
  background:
    radial-gradient(circle at 30% 20%, rgba(240,240,255,0.85) 1.6px, transparent 2.4px),
    radial-gradient(circle at 50% 40%, rgba(240,240,255,0.85) 1.8px, transparent 2.6px),
    radial-gradient(circle at 70% 25%, rgba(240,240,255,0.85) 1.7px, transparent 2.4px);
  animation: precipFall 2s linear infinite;
}
@keyframes precipFall {
  from { background-position: 0 0, 0 0, 0 0; }
  to   { background-position: 0 80px, 0 90px, 0 75px; }
}

.theater .fx-crystal {
  background:
    linear-gradient(135deg, rgba(255,255,255,0) 60%, rgba(255,255,255,0.75) 60%, rgba(255,255,255,0.75) 65%, rgba(255,255,255,0) 65%),
    linear-gradient(45deg,  rgba(255,255,255,0) 50%, rgba(255,255,255,0.55) 50%, rgba(255,255,255,0.55) 53%, rgba(255,255,255,0) 53%);
  animation: crystGrow 3.6s ease-out infinite;
  opacity: 0.85;
}
@keyframes crystGrow {
  0%   { opacity: 0; transform: scale(0.7); }
  60%  { opacity: 0.9; transform: scale(1); }
  100% { opacity: 0.4; transform: scale(1.05); }
}

.theater .fx-melt {
  background: radial-gradient(ellipse at 50% 90%, rgba(239,68,68,0.55) 0%, rgba(239,68,68,0) 50%);
  animation: glowPulse 2s ease-in-out infinite alternate;
}
.theater .fx-freeze {
  background: radial-gradient(ellipse at 50% 50%, rgba(125,211,252,0.6) 0%, rgba(125,211,252,0) 70%);
  animation: glowPulse 2.5s ease-in-out infinite alternate;
}
</style>
"""
