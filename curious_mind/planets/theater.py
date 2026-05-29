"""Planet Forge & Sky View — the Living Planet theater hero for the Planets lab.

Pure HTML/SVG/CSS animation that renders a backdrop of stars, the host star
(spectral-color glow), the planet (surface tinted by temperature / atmosphere /
water), an atmosphere ring (thickness scaled by surface pressure), optional
moons, and a dramatic caption strip. No external assets, no JS.
"""

from __future__ import annotations

import html
import math
import random


THEATER_HEIGHT = 380


def planet_theater_height() -> int:
    return THEATER_HEIGHT


# ---------------------------------------------------------------------------
# Color helpers
# ---------------------------------------------------------------------------

_ATMOSPHERE_BAND_COLOR: dict[str, str] = {
    "earth_like": "#86b6ff",
    "venus_like": "#d6b07a",
    "mars_like": "#d68a6a",
    "titan_like": "#e6a85a",
    "hydrogen_helium": "#c9a07a",
    "reducing_archean": "#c98c5a",
    "ice_world": "#bcd9ff",
}


def _surface_colors(temp_C: float, atm_id: str, water_pct: int) -> tuple[str, str]:
    """Return (highlight, shadow) hex colors for the planet surface."""
    if atm_id == "hydrogen_helium":
        return ("#e6c79a", "#7a4a26")
    if temp_C < -80:
        return ("#dceeff", "#3a5a82")            # frozen
    if temp_C < -10:
        if water_pct > 30:
            return ("#a8c8e8", "#2c4a6e")        # snowball with ice/ocean
        return ("#cbb89a", "#5a4a2a")            # cold desert
    if temp_C < 35:
        if water_pct > 50:
            return ("#74c2ff", "#143a6b")        # ocean / Earth-like
        if water_pct > 10:
            return ("#86b08a", "#2a4a30")        # green continents
        return ("#caa672", "#5a3a1a")            # arid temperate
    if temp_C < 120:
        return ("#d4a86c", "#5a3015")            # warm desert
    if temp_C < 350:
        return ("#e07a3a", "#4a1408")            # hot orange
    if temp_C < 800:
        return ("#f0a05a", "#7a2010")            # venus-like
    return ("#fff0a0", "#a04018")                # incandescent


def _star_color(spectral_class: str, color_hex: str | None = None) -> str:
    if color_hex:
        return color_hex
    return {
        "O": "#9bb0ff",
        "B": "#aabfff",
        "A": "#cad7ff",
        "F": "#fff4ea",
        "G": "#ffe28a",
        "K": "#ffb86b",
        "M": "#ff7a4d",
    }.get(spectral_class, "#ffe28a")


def _planet_size_px(radius_earth: float) -> int:
    val = 120 + 70 * math.log10(max(radius_earth, 0.1) / 0.5)
    return int(max(90, min(240, val)))


def _atmosphere_thickness_px(pressure_atm: float, atm_id: str) -> int:
    if atm_id == "hydrogen_helium" or pressure_atm <= 0.001:
        return 0
    val = 4 + 8 * math.log10(max(pressure_atm, 0.001) + 1)
    return int(max(0, min(26, val)))


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

_THEATER_CSS = """
<style>
.planet-stage{
  position:relative; width:100%; height:380px; border-radius:14px; overflow:hidden;
  background: radial-gradient(ellipse at 72% 22%, #1f2b58 0%, #060818 55%, #000 100%);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color:#e8edf5;
}
.planet-stage .stars{ position:absolute; inset:0; pointer-events:none; }
.planet-stage .stars span{
  position:absolute; background:#fff; border-radius:50%;
  animation: cm-twink 3s ease-in-out infinite;
}
@keyframes cm-twink{
  0%,100%{ opacity:0.2; } 50%{ opacity:1; }
}
.planet-stage .star-disc{
  position:absolute;
  border-radius:50%;
  animation: cm-star-pulse 4s ease-in-out infinite;
}
@keyframes cm-star-pulse{
  0%,100%{ box-shadow: 0 0 28px 6px var(--star-glow), 0 0 64px 12px var(--star-glow); }
  50%    { box-shadow: 0 0 40px 10px var(--star-glow), 0 0 100px 22px var(--star-glow); }
}
.planet-stage .anchor{
  position:absolute; top:50%; left:38%;
  width:0; height:0;
}
.planet-stage .planet-disc{
  position:absolute; top:0; left:0;
  transform: translate(-50%,-50%);
  border-radius:50%;
  box-shadow: inset -22px -10px 50px rgba(0,0,0,0.55);
  background:
    radial-gradient(circle at 30% 30%, var(--surface-hi) 0%, var(--surface-lo) 60%, #000 110%);
  overflow:hidden;
}
.planet-stage .planet-disc .layer{
  position:absolute; inset:0; border-radius:50%;
}
.planet-stage .planet-disc .clouds{
  background:
    radial-gradient(ellipse 40% 12% at 30% 35%, rgba(255,255,255,0.6), transparent 70%),
    radial-gradient(ellipse 50% 14% at 70% 55%, rgba(255,255,255,0.5), transparent 70%),
    radial-gradient(ellipse 30% 10% at 50% 78%, rgba(255,255,255,0.45), transparent 70%);
  animation: cm-cloud-drift 26s linear infinite;
  mix-blend-mode: screen;
  opacity:0.85;
}
@keyframes cm-cloud-drift{
  0%{ transform: translateX(0); } 100%{ transform: translateX(-30%); }
}
.planet-stage .planet-disc .ice-caps{
  background:
    radial-gradient(ellipse 65% 13% at 50% 5%,  rgba(255,255,255,0.85), transparent 75%),
    radial-gradient(ellipse 65% 13% at 50% 95%, rgba(255,255,255,0.85), transparent 75%);
  mix-blend-mode: screen;
}
.planet-stage .planet-disc .haze{
  background: radial-gradient(circle at 50% 50%, rgba(255,210,150,0.28) 30%, transparent 75%);
  mix-blend-mode: screen;
}
.planet-stage .planet-disc .lava-glow{
  inset:-8%;
  background: radial-gradient(circle, rgba(255,120,40,0.55) 0%, transparent 70%);
  animation: cm-lava-pulse 2.5s ease-in-out infinite;
  mix-blend-mode: screen;
  border-radius:50%;
}
@keyframes cm-lava-pulse{
  0%,100%{ opacity:0.5; } 50%{ opacity:0.95; }
}
.planet-stage .planet-disc .gas-bands{
  background:
    repeating-linear-gradient(
      to bottom,
      rgba(255,255,255,0) 0%,
      rgba(0,0,0,0.18) 8%,
      rgba(255,255,255,0.18) 16%,
      rgba(0,0,0,0) 24%
    );
  mix-blend-mode: overlay;
  opacity:0.7;
}
.planet-stage .atm-ring{
  position:absolute; top:0; left:0;
  transform: translate(-50%,-50%);
  border-radius:50%;
  box-shadow:
    0 0 18px 6px var(--atm-glow),
    inset 0 0 18px 4px var(--atm-glow);
  pointer-events:none;
  animation: cm-atm-breathe 6s ease-in-out infinite;
}
@keyframes cm-atm-breathe{
  0%,100%{ opacity:0.55; } 50%{ opacity:0.9; }
}
.planet-stage .moon-dot{
  position:absolute;
  width:10px; height:10px; border-radius:50%;
  transform: translate(-50%,-50%);
  background: radial-gradient(circle at 30% 30%, #f4f1ea, #6b6960 80%);
  box-shadow: inset -2px -1px 3px rgba(0,0,0,0.4);
}
.planet-stage .caption{
  position:absolute; bottom:0; left:0; right:0;
  padding:10px 16px;
  background: linear-gradient(to top, rgba(0,0,0,0.7), transparent);
  font-size:14px; line-height:1.35;
}
.planet-stage .caption .pin{
  display:inline-block;
  background: rgba(255,255,255,0.14);
  padding:2px 8px; border-radius:999px;
  font-size:11px; letter-spacing:0.06em;
  margin-right:8px;
}
.planet-stage .badge{
  position:absolute; top:16px; left:18px;
  padding:4px 10px; border-radius:999px;
  font-size:12px; letter-spacing:0.06em;
  border:1px solid rgba(255,255,255,0.15);
  background: rgba(0,0,0,0.45);
}
.planet-stage .tidal-mark{
  position:absolute; bottom:64px; left:18px;
  font-size:11px;
  padding:3px 8px; border-radius:999px;
  background: rgba(0,0,0,0.45);
  color:#ffd86b;
  border:1px solid rgba(255,216,107,0.35);
}
.planet-stage .flare-mark{
  position:absolute; bottom:88px; left:18px;
  font-size:11px;
  padding:3px 8px; border-radius:999px;
  background: rgba(0,0,0,0.45);
  color:#ff9a6b;
  border:1px solid rgba(255,154,107,0.4);
}
.planet-stage .star-label{
  position:absolute; top:16px; right:24px;
  font-size:11px; color:#dbe4f0; opacity:0.85;
  text-align:right;
}
</style>
"""


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------

def render_planet_theater(
    *,
    star: dict,
    star_color_hex: str,
    distance_AU: float,
    radius_earth: float,
    atmosphere_id: str,
    surface_T_C: float,
    surface_pressure_atm: float,
    water_pct: int,
    moons: int,
    tidally_locked: bool,
    flare_risk: str,
    verdict: str | None = None,
    dramatic: str = "",
    caption: str = "",
    seed: int | None = None,
) -> str:
    """Return a self-contained HTML block for the Planet theater hero."""
    rng = random.Random(seed if seed is not None else hash((
        star.get("name", ""), round(distance_AU, 4), atmosphere_id,
        round(surface_T_C, 1), int(water_pct), int(moons),
    )) & 0xFFFFFF)

    star_glow = _star_color(star.get("spectral_class", "G"), star_color_hex)
    lum = float(star.get("luminosity_solar", 1.0) or 1.0)
    star_size = int(max(34, min(110, 48 + 12 * math.log10(max(lum, 1e-6)))))

    planet_px = _planet_size_px(radius_earth)
    atm_thick = _atmosphere_thickness_px(surface_pressure_atm, atmosphere_id)
    surface_hi, surface_lo = _surface_colors(surface_T_C, atmosphere_id, water_pct)
    atm_color = _ATMOSPHERE_BAND_COLOR.get(atmosphere_id, "#86b6ff")

    # Overlay decisions
    is_gas = atmosphere_id == "hydrogen_helium"
    overlays: list[str] = []
    if is_gas:
        overlays.append('<div class="layer gas-bands"></div>')
    else:
        if water_pct >= 30 and -10 <= surface_T_C <= 60 and atmosphere_id in (
            "earth_like", "reducing_archean",
        ):
            overlays.append('<div class="layer clouds"></div>')
        if surface_T_C < -20 and water_pct > 5:
            overlays.append('<div class="layer ice-caps"></div>')
        if surface_T_C > 250:
            overlays.append('<div class="layer lava-glow"></div>')
        if atmosphere_id in ("titan_like", "venus_like", "reducing_archean"):
            overlays.append('<div class="layer haze"></div>')

    # Twinkling background stars
    star_dots: list[str] = []
    for _ in range(45):
        x = rng.uniform(0, 100)
        y = rng.uniform(0, 100)
        delay = rng.uniform(0, 3)
        size = rng.choice([1, 1, 1, 2])
        star_dots.append(
            f'<span style="left:{x:.1f}%;top:{y:.1f}%;'
            f'width:{size}px;height:{size}px;animation-delay:{delay:.1f}s;"></span>'
        )
    stars_html = "<div class='stars'>" + "".join(star_dots) + "</div>"

    # Moons (placed on a static arc; up to 5)
    moon_html_parts: list[str] = []
    n_moons = max(0, min(int(moons), 5))
    for i in range(n_moons):
        # arc them across the right side of the planet
        angle_deg = -60 + (120 / max(1, n_moons - 1 if n_moons > 1 else 1)) * i if n_moons > 1 else -10
        orbit_r = planet_px // 2 + 30 + i * 4
        rad = math.radians(angle_deg)
        dx = orbit_r * math.cos(rad)
        dy = orbit_r * math.sin(rad)
        moon_html_parts.append(
            f'<div class="moon-dot" style="left:{dx:.0f}px;top:{dy:.0f}px;"></div>'
        )
    moons_html = "".join(moon_html_parts)

    # Atmosphere ring (drawn behind the planet)
    atm_div = ""
    if atm_thick > 0:
        atm_size = planet_px + atm_thick * 2
        atm_div = (
            f'<div class="atm-ring" style="width:{atm_size}px;height:{atm_size}px;'
            f'--atm-glow:{atm_color};"></div>'
        )

    # Verdict pill
    verdict_pill = ""
    if verdict:
        v_color = {
            "habitable": "#16a34a",
            "extremophile_only": "#d97706",
            "non_habitable": "#dc2626",
        }.get(verdict, "#6b7280")
        v_label = {
            "habitable": "🟢 HABITABLE",
            "extremophile_only": "🟡 EXTREMOPHILES ONLY",
            "non_habitable": "🔴 NON-HABITABLE",
        }.get(verdict, verdict.upper())
        verdict_pill = (
            f'<div class="badge" style="background:{v_color}cc;border-color:{v_color};">'
            f'{html.escape(v_label)}</div>'
        )

    # Stress markers
    tidal_html = '<div class="tidal-mark">🔒 tidally locked</div>' if tidally_locked else ''
    flare_html = ''
    if flare_risk in ("high", "very_high_uv"):
        flare_label = "⚡ flare-bombarded host" if flare_risk == "high" else "☢ sterilizing UV"
        flare_html = f'<div class="flare-mark">{flare_label}</div>'

    # Caption + dramatic moment strip
    caption_parts: list[str] = []
    if caption:
        caption_parts.append(f'<span class="pin">{html.escape(caption)}</span>')
    if dramatic:
        caption_parts.append(html.escape(dramatic))
    caption_div = ""
    if caption_parts:
        caption_div = f'<div class="caption">{"".join(caption_parts)}</div>'

    star_label = (
        f'{html.escape(str(star.get("name", "")))}'
        f' · {html.escape(str(star.get("spectral_class", "")))}-class'
        f' · {distance_AU:g} AU'
    )

    star_html = (
        f'<div class="star-disc" style="width:{star_size}px;height:{star_size}px;'
        f'top:{30}px;right:{42}px;'
        f'background: radial-gradient(circle at 32% 32%, #fff, {star_glow} 60%, {star_glow}66 95%);'
        f'--star-glow:{star_glow};"></div>'
        f'<div class="star-label">{star_label}</div>'
    )

    planet_inner = (
        f'<div class="planet-disc" style="width:{planet_px}px;height:{planet_px}px;'
        f'--surface-hi:{surface_hi};--surface-lo:{surface_lo};">'
        + "".join(overlays)
        + '</div>'
    )

    anchor_html = (
        f'<div class="anchor">'
        f'  {atm_div}'
        f'  {planet_inner}'
        f'  {moons_html}'
        f'</div>'
    )

    return (
        _THEATER_CSS
        + f'<div class="planet-stage">'
          f'{stars_html}'
          f'{star_html}'
          f'{verdict_pill}'
          f'{flare_html}'
          f'{tidal_html}'
          f'{anchor_html}'
          f'{caption_div}'
          f'</div>'
    )
