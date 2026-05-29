"""Apparatus Theater for the Physics Lab.

Each scenario gets a hero SVG/CSS animation rendered above the existing
analysis charts. All renderers consume the deterministic simulator output
(see ``simulators.py``) plus the relevant user inputs, and return a single
self-contained HTML string suitable for ``st.components.v1.html``.

Public:
- ``render_theater(scenario, sim, inp, result)`` — dispatcher
- ``theater_height(scenario)`` — recommended iframe height in px
- Per-scenario renderers: ``render_projectile_theater(...)`` etc.
"""

from __future__ import annotations

import math
from html import escape

# ---------------------------------------------------------------------------
# Layout constants
# ---------------------------------------------------------------------------

_HEIGHTS: dict[str, int] = {
    "projectile": 360,
    "incline": 340,
    "rollercoaster": 360,
    "collision": 320,
    "spring": 320,
    "photoelectric": 360,
    "de_broglie": 340,
}


def theater_height(scenario: str) -> int:
    return _HEIGHTS.get(scenario, 340)


# ---------------------------------------------------------------------------
# Frame / banner helpers
# ---------------------------------------------------------------------------

def _frame(body: str, caption: str = "", dramatic: str = "") -> str:
    """Wrap a scene in the standard theater frame with caption + moment."""
    cap = f'<div class="phy-caption">{escape(caption)}</div>' if caption else ""
    dm = f'<div class="phy-moment">💡 {escape(dramatic)}</div>' if dramatic else ""
    return f'{_THEATER_CSS}<div class="phy-theater">{cap}{body}{dm}</div>'


def _safe_div(a: float, b: float, default: float = 0.0) -> float:
    return a / b if b else default


# ---------------------------------------------------------------------------
# Projectile — cannon + parabolic flight
# ---------------------------------------------------------------------------

def render_projectile_theater(
    sim: dict, v0: float, angle_deg: float, *, caption: str = "", dramatic: str = ""
) -> str:
    xs = sim.get("trajectory_x") or [0.0]
    ys = sim.get("trajectory_y") or [0.0]
    rng = float(sim.get("range_m", max(xs) or 1.0)) or 1.0
    peak = float(sim.get("max_height_m", max(ys) or 1.0)) or 1.0
    t_flight = max(float(sim.get("t_flight_s", 2.0)), 0.4)

    # Map physics coords → SVG coords (520 × 240 stage, 30 px ground band).
    sw, sh = 520, 240
    margin = 18
    plot_w = sw - 2 * margin
    plot_h = sh - 50  # leave room for ground + cannon
    sx = plot_w / max(rng, 0.1)
    sy = plot_h / max(peak, 0.1)

    def to_xy(x, y):
        return margin + x * sx, (sh - 30) - y * sy

    path_d = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in (to_xy(a, b) for a, b in zip(xs, ys)))

    # Cannon at origin, pointed at angle
    cx, cy = to_xy(0.0, 0.0)
    bx, by = to_xy(rng, 0.0)
    barrel_len = 38
    bxh = cx + barrel_len * math.cos(math.radians(angle_deg))
    byh = cy - barrel_len * math.sin(math.radians(angle_deg))

    duration = f"{t_flight:.2f}s"

    body = f"""
<svg viewBox="0 0 {sw} {sh}" width="100%" height="100%" preserveAspectRatio="xMidYMid meet"
     xmlns="http://www.w3.org/2000/svg">
  <!-- sky gradient -->
  <defs>
    <linearGradient id="sky" x1="0" x2="0" y1="0" y2="1">
      <stop offset="0%" stop-color="#0a1430"/>
      <stop offset="100%" stop-color="#1d3163"/>
    </linearGradient>
  </defs>
  <rect x="0" y="0" width="{sw}" height="{sh-30}" fill="url(#sky)"/>
  <!-- ground -->
  <rect x="0" y="{sh-30}" width="{sw}" height="30" fill="#3b2415"/>
  <line x1="0" y1="{sh-30}" x2="{sw}" y2="{sh-30}" stroke="#8b5a2b" stroke-width="2"/>
  <!-- target zone -->
  <circle cx="{bx:.1f}" cy="{sh-32}" r="8" fill="none" stroke="#fcd34d" stroke-width="2"/>
  <circle cx="{bx:.1f}" cy="{sh-32}" r="3" fill="#fcd34d"/>
  <!-- trajectory ghost -->
  <path d="{path_d}" fill="none" stroke="#fcd34d" stroke-width="1.5" stroke-dasharray="3 4" opacity="0.55"/>
  <!-- cannon barrel -->
  <line x1="{cx:.1f}" y1="{cy:.1f}" x2="{bxh:.1f}" y2="{byh:.1f}"
        stroke="#475569" stroke-width="10" stroke-linecap="round"/>
  <circle cx="{cx:.1f}" cy="{cy:.1f}" r="13" fill="#1f2937" stroke="#94a3b8" stroke-width="2"/>
  <!-- ball with motion along path -->
  <circle r="6" fill="#f97316" stroke="#fff7ed" stroke-width="1.5">
    <animateMotion dur="{duration}" repeatCount="indefinite"
                   keyPoints="0;1" keyTimes="0;1" calcMode="linear"
                   path="{path_d}"/>
  </circle>
  <!-- labels -->
  <text x="{margin}" y="20" fill="#cbd5e1" font-size="12" font-family="ui-monospace,monospace">
    Range: {rng:.1f} m · Peak: {peak:.1f} m · Flight: {t_flight:.2f} s
  </text>
</svg>
"""
    return _frame(body, caption=caption, dramatic=dramatic)


# ---------------------------------------------------------------------------
# Incline — block on a ramp
# ---------------------------------------------------------------------------

def render_incline_theater(
    sim: dict, angle_deg: float, mass: float, *, caption: str = "", dramatic: str = ""
) -> str:
    verdict = str(sim.get("verdict", "static")).lower()
    accel = float(sim.get("accel_m_s2", 0.0))

    sw, sh = 520, 240
    base_y = sh - 30
    ramp_w = 420
    # Ramp triangle from origin
    ox = 40
    oy = base_y
    rx = ox + ramp_w
    ry = base_y - ramp_w * math.tan(math.radians(angle_deg))
    ry = max(ry, 20)  # don't go off-canvas
    # Block size
    bw, bh = 48, 32
    # Block resting position (near top of ramp by default)
    t = 0.18  # 18% down from the top
    bx_c = rx - (rx - ox) * t
    by_c = ry + (oy - ry) * t

    # Block orientation along ramp
    rot = -angle_deg

    # Animation: slide from top to bottom of ramp if moving
    sliding = verdict in ("kinetic", "sliding", "moving") or accel > 0.05
    # Duration: ~ sqrt(2L/a) with a floor
    if sliding and accel > 0:
        slide_t = max(0.8, min(4.0, math.sqrt(2 * ramp_w / max(accel * 30, 1)) ))
    else:
        slide_t = 0.0

    anim_class = "sliding" if sliding else "static"
    # Precompute pixel deltas along the slope (CSS has no tan()).
    slide_dist = ramp_w * 0.55
    slide_dx = slide_dist * math.cos(math.radians(angle_deg))
    slide_dy = slide_dist * math.sin(math.radians(angle_deg))
    anim_style = (
        f'animation: phy-slide {slide_t:.2f}s ease-in infinite;'
        f' --sdx:{slide_dx:.1f}px; --sdy:{slide_dy:.1f}px;'
        if sliding else ''
    )

    arrow_color = "#22c55e" if verdict == "static" else "#f97316"
    verdict_label = {
        "static": "🟢 STATIC — friction holds",
        "kinetic": "🟠 SLIDING — kinetic friction",
        "sliding": "🟠 SLIDING — kinetic friction",
        "applied": "🟣 PUSHED",
        "moving": "🟠 SLIDING",
    }.get(verdict, verdict.upper())

    # Friction tick marks under the ramp
    ticks = "".join(
        f'<line x1="{ox + i * 28:.0f}" y1="{base_y + 4}" x2="{ox + i * 28 + 10:.0f}" y2="{base_y + 14}" stroke="#94a3b8" stroke-width="1.5"/>'
        for i in range(int(ramp_w / 28))
    )

    body = f"""
<svg viewBox="0 0 {sw} {sh}" width="100%" height="100%" preserveAspectRatio="xMidYMid meet"
     xmlns="http://www.w3.org/2000/svg">
  <rect x="0" y="0" width="{sw}" height="{sh}" fill="#101827"/>
  <!-- ground -->
  <line x1="0" y1="{base_y}" x2="{sw}" y2="{base_y}" stroke="#64748b" stroke-width="2"/>
  {ticks}
  <!-- ramp -->
  <polygon points="{ox},{oy} {rx},{oy} {rx},{ry:.1f}" fill="#1f2937" stroke="#475569" stroke-width="2"/>
  <text x="{rx - 80}" y="{oy - 8}" fill="#94a3b8" font-size="12">{angle_deg:.0f}°</text>
  <!-- block: outer SVG transform sets initial position, inner CSS group animates the slide -->
  <g transform="translate({bx_c:.1f},{by_c:.1f})">
    <g class="phy-incline-block {anim_class}" style="{anim_style}">
      <g transform="rotate({rot:.1f})">
        <rect x="{-bw/2:.0f}" y="{-bh:.0f}" width="{bw}" height="{bh}" rx="4"
              fill="#facc15" stroke="#92400e" stroke-width="2"/>
        <text x="0" y="{-bh/2 + 4:.0f}" text-anchor="middle" font-size="11"
              fill="#1c1917" font-weight="700">{mass:.1f} kg</text>
      </g>
    </g>
  </g>
  <!-- verdict chip -->
  <rect x="{sw - 220}" y="14" width="200" height="26" rx="13" fill="rgba(0,0,0,0.55)" stroke="{arrow_color}"/>
  <text x="{sw - 120}" y="32" text-anchor="middle" font-size="12" fill="{arrow_color}" font-weight="700">{verdict_label}</text>
  <text x="{sw - 120}" y="{sh - 8}" text-anchor="middle" font-size="11" fill="#94a3b8">
    a = {accel:.2f} m/s²
  </text>
</svg>
"""
    return _frame(body, caption=caption, dramatic=dramatic)


# ---------------------------------------------------------------------------
# Rollercoaster — multi-segment track with KE/PE bars
# ---------------------------------------------------------------------------

def render_rollercoaster_theater(
    sim: dict, *, caption: str = "", dramatic: str = ""
) -> str:
    heights = [float(h) for h in sim.get("heights_m", [20, 5, 12])]
    ke = [float(k) for k in sim.get("ke_J", [0, 0, 0])]
    pe = [float(p) for p in sim.get("pe_J", [0, 0, 0])]
    reachable = list(sim.get("reachable", [True] * len(heights)))
    h_max = max(heights + [1.0])
    e_max = max([ke[i] + pe[i] for i in range(len(heights))] + [1.0])

    sw, sh = 520, 260
    base_y = sh - 30
    pad_x = 30
    plot_w = sw - 2 * pad_x
    seg_w = plot_w / max(len(heights) - 1, 1)
    plot_h = sh - 90  # leave room for bars

    # Compute track points (smooth-ish via cubic between each pair)
    pts = [
        (pad_x + i * seg_w, base_y - heights[i] / h_max * plot_h)
        for i in range(len(heights))
    ]
    # Build a polyline through the hill tops
    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    path_d = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pts)

    # Cart animates along the path. Skip unreachable tail.
    last_reachable = max((i for i, ok in enumerate(reachable) if ok), default=0)
    visit_pts = pts[: last_reachable + 1]
    # If only one point reachable, end the ride there
    if len(visit_pts) < 2:
        visit_pts = visit_pts + [visit_pts[0]]
    cart_path = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in visit_pts)
    duration = f"{2.6 + 0.6 * (last_reachable):.2f}s"

    # KE / PE bars under each waypoint
    bars_html = []
    bar_w = 22
    bar_h = 38
    for i, (x, _) in enumerate(pts):
        ke_h = max(2.0, ke[i] / e_max * bar_h)
        pe_h = max(2.0, pe[i] / e_max * bar_h)
        bx = x - bar_w - 4
        by = base_y + 6
        bars_html.append(
            f'<rect x="{bx:.1f}" y="{by + (bar_h - pe_h):.1f}" width="{bar_w}" height="{pe_h:.1f}" fill="#60a5fa"/>'
            f'<rect x="{bx + bar_w + 4:.1f}" y="{by + (bar_h - ke_h):.1f}" width="{bar_w}" height="{ke_h:.1f}" fill="#fb923c"/>'
            f'<text x="{x:.1f}" y="{by + bar_h + 12:.1f}" text-anchor="middle" font-size="10" fill="#cbd5e1">'
            f'{("✓" if reachable[i] else "✕")} {heights[i]:.1f}m'
            f'</text>'
        )

    body = f"""
<svg viewBox="0 0 {sw} {sh}" width="100%" height="100%" preserveAspectRatio="xMidYMid meet"
     xmlns="http://www.w3.org/2000/svg">
  <rect x="0" y="0" width="{sw}" height="{sh}" fill="#0b1020"/>
  <line x1="0" y1="{base_y}" x2="{sw}" y2="{base_y}" stroke="#64748b" stroke-width="2"/>
  <!-- track -->
  <polyline points="{poly}" fill="none" stroke="#94a3b8" stroke-width="3"/>
  <!-- cart -->
  <g>
    <rect x="-12" y="-10" width="24" height="14" rx="3" fill="#ef4444" stroke="#fff" stroke-width="1.5"/>
    <circle cx="-6" cy="6" r="3" fill="#1f2937"/>
    <circle cx="6"  cy="6" r="3" fill="#1f2937"/>
    <animateMotion dur="{duration}" repeatCount="indefinite" rotate="auto"
                   keyPoints="0;1" keyTimes="0;1" calcMode="linear"
                   path="{cart_path}"/>
  </g>
  {''.join(bars_html)}
  <!-- legend -->
  <rect x="{pad_x}" y="10" width="10" height="10" fill="#60a5fa"/>
  <text x="{pad_x + 14}" y="20" font-size="11" fill="#cbd5e1">PE</text>
  <rect x="{pad_x + 40}" y="10" width="10" height="10" fill="#fb923c"/>
  <text x="{pad_x + 54}" y="20" font-size="11" fill="#cbd5e1">KE</text>
  <text x="{sw - pad_x}" y="20" text-anchor="end" font-size="11" fill="#94a3b8">
    friction-loss/segment: {sim.get("friction_loss_per_segment_J", 0):.0f} J
  </text>
</svg>
"""
    return _frame(body, caption=caption, dramatic=dramatic)


# ---------------------------------------------------------------------------
# Collision — two carts with momentum arrows
# ---------------------------------------------------------------------------

def render_collision_theater(
    sim: dict, m1: float, m2: float, v1: float, v2: float,
    *, caption: str = "", dramatic: str = ""
) -> str:
    v1p = float(sim.get("v1_prime", -v1))
    v2p = float(sim.get("v2_prime", -v2))
    ke_before = float(sim.get("ke_before", 0.0))
    ke_after = float(sim.get("ke_after", 0.0))
    e_lost = float(sim.get("ke_lost", 0.0))
    e = float(sim.get("restitution", 1.0))

    sw, sh = 520, 220
    base_y = sh - 30
    # Cart sizes scaled by mass
    s1 = max(28, min(72, 24 + 6 * m1))
    s2 = max(28, min(72, 24 + 6 * m2))
    h_cart = 40
    # Start positions
    left_start  = 60
    right_start = sw - 60 - s2
    # Meeting point near center
    meet = sw / 2 - (s1 + s2) / 2 + 4
    # Post-collision positions (proportional to v')
    end1 = meet + v1p * 18
    end2 = meet + s1 + 8 + v2p * 18

    def arrow(x: float, y: float, mag: float, color: str) -> str:
        # Horizontal arrow from (x,y) of length ∝ mag
        L = max(min(mag * 8, 70), -70) if mag else 0
        if abs(L) < 4:
            return ""
        x2 = x + L
        head_dir = 1 if L > 0 else -1
        return (
            f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x2:.1f}" y2="{y:.1f}" '
            f'stroke="{color}" stroke-width="2.5"/>'
            f'<polygon points="{x2:.1f},{y:.1f} {x2 - 6*head_dir:.1f},{y-4:.1f} {x2 - 6*head_dir:.1f},{y+4:.1f}" fill="{color}"/>'
        )

    body = f"""
<svg viewBox="0 0 {sw} {sh}" width="100%" height="100%" preserveAspectRatio="xMidYMid meet"
     xmlns="http://www.w3.org/2000/svg">
  <rect x="0" y="0" width="{sw}" height="{sh}" fill="#0b1020"/>
  <line x1="0" y1="{base_y}" x2="{sw}" y2="{base_y}" stroke="#64748b" stroke-width="2"/>
  <!-- track ties -->
  {''.join(f'<line x1="{i*20}" y1="{base_y+2}" x2="{i*20+12}" y2="{base_y+12}" stroke="#475569" stroke-width="1"/>' for i in range(int(sw/20)))}
  <!-- cart 1 (blue) -->
  <g class="phy-cart1" style="--x0:{left_start:.1f}px; --xm:{meet:.1f}px; --xe:{end1:.1f}px;">
    <rect y="{base_y - h_cart}" width="{s1}" height="{h_cart}" rx="4" fill="#3b82f6" stroke="#fff" stroke-width="2"/>
    <text x="{s1/2:.0f}" y="{base_y - h_cart/2 + 4:.0f}" text-anchor="middle" font-size="12" fill="white" font-weight="700">{m1:.1f} kg</text>
    <circle cx="{s1*0.25:.0f}" cy="{base_y + 4}" r="5" fill="#1f2937"/>
    <circle cx="{s1*0.75:.0f}" cy="{base_y + 4}" r="5" fill="#1f2937"/>
  </g>
  <!-- cart 2 (red) -->
  <g class="phy-cart2" style="--x0:{right_start:.1f}px; --xm:{meet + s1 + 8:.1f}px; --xe:{end2:.1f}px;">
    <rect y="{base_y - h_cart}" width="{s2}" height="{h_cart}" rx="4" fill="#ef4444" stroke="#fff" stroke-width="2"/>
    <text x="{s2/2:.0f}" y="{base_y - h_cart/2 + 4:.0f}" text-anchor="middle" font-size="12" fill="white" font-weight="700">{m2:.1f} kg</text>
    <circle cx="{s2*0.25:.0f}" cy="{base_y + 4}" r="5" fill="#1f2937"/>
    <circle cx="{s2*0.75:.0f}" cy="{base_y + 4}" r="5" fill="#1f2937"/>
  </g>
  <!-- momentum arrows row -->
  <text x="18" y="18" fill="#cbd5e1" font-size="11">Momentum before:</text>
  {arrow(160, 22, v1 * m1, "#60a5fa")}
  {arrow(240, 22, v2 * m2, "#fca5a5")}
  <text x="320" y="18" fill="#cbd5e1" font-size="11">After:</text>
  {arrow(370, 22, v1p * m1, "#60a5fa")}
  {arrow(450, 22, v2p * m2, "#fca5a5")}
  <!-- energy stats -->
  <text x="{sw/2:.0f}" y="{sh - 8}" text-anchor="middle" font-size="11" fill="#94a3b8">
    KE: {ke_before:.1f} J → {ke_after:.1f} J  (lost {e_lost:.1f} J · e={e:.2f})
  </text>
</svg>
"""
    return _frame(body, caption=caption, dramatic=dramatic)


# ---------------------------------------------------------------------------
# Spring — oscillating block on a coil
# ---------------------------------------------------------------------------

def render_spring_theater(
    sim: dict, m: float, k: float, *, caption: str = "", dramatic: str = ""
) -> str:
    period = max(float(sim.get("period_s", 1.0)), 0.2)
    amp = max(float(sim.get("amplitude_m", 0.1)), 0.01)

    sw, sh = 520, 220
    base_y = sh - 50
    wall_x = 60
    # Equilibrium position of block (right of spring)
    rest_x = sw / 2 + 20
    # Scale amplitude into pixels (cap at 110 px)
    amp_px = min(amp * 400, 110)

    body = f"""
<svg viewBox="0 0 {sw} {sh}" width="100%" height="100%" preserveAspectRatio="xMidYMid meet"
     xmlns="http://www.w3.org/2000/svg">
  <rect x="0" y="0" width="{sw}" height="{sh}" fill="#0b1020"/>
  <!-- ground -->
  <line x1="0" y1="{base_y + 30}" x2="{sw}" y2="{base_y + 30}" stroke="#64748b" stroke-width="2"/>
  <!-- wall -->
  <rect x="0" y="{base_y - 60}" width="{wall_x}" height="90" fill="#374151"/>
  {''.join(f'<line x1="0" y1="{base_y - 60 + i*8}" x2="{wall_x}" y2="{base_y - 52 + i*8}" stroke="#1f2937" stroke-width="1"/>' for i in range(11))}
  <!-- spring group (scales horizontally with block) -->
  <g class="phy-spring-group" style="--rest:{rest_x:.1f}px; --amp:{amp_px:.1f}px; --period:{period:.2f}s; transform-origin: {wall_x}px {base_y - 20}px;">
    <polyline points="{wall_x},{base_y - 20} {wall_x+12},{base_y - 30} {wall_x+24},{base_y - 10} {wall_x+36},{base_y - 30} {wall_x+48},{base_y - 10} {wall_x+60},{base_y - 30} {wall_x+72},{base_y - 10} {wall_x+84},{base_y - 30} {wall_x+96},{base_y - 10} {wall_x+108},{base_y - 30} {wall_x+120},{base_y - 20}"
              stroke="#cbd5e1" stroke-width="2.5" fill="none"/>
  </g>
  <!-- block oscillates around rest_x -->
  <g class="phy-block" style="--rest:{rest_x:.1f}px; --amp:{amp_px:.1f}px; --period:{period:.2f}s;">
    <rect x="-25" y="{base_y - 36}" width="50" height="36" rx="3"
          fill="#facc15" stroke="#92400e" stroke-width="2"/>
    <text x="0" y="{base_y - 14}" text-anchor="middle" font-size="11"
          fill="#1c1917" font-weight="700">{m:.1f} kg</text>
  </g>
  <!-- equilibrium tick -->
  <line x1="{rest_x:.1f}" y1="{base_y + 4}" x2="{rest_x:.1f}" y2="{base_y + 18}" stroke="#fcd34d" stroke-dasharray="2 3"/>
  <text x="{rest_x:.1f}" y="{base_y + 30}" text-anchor="middle" font-size="10" fill="#fcd34d">equilibrium</text>
  <!-- labels -->
  <text x="{sw - 16}" y="20" text-anchor="end" font-size="11" fill="#cbd5e1" font-family="ui-monospace,monospace">
    T = {period:.2f}s · A = {amp:.2f}m · k = {k:.0f} N/m
  </text>
</svg>
"""
    return _frame(body, caption=caption, dramatic=dramatic)


# ---------------------------------------------------------------------------
# Photoelectric — photons → ejected electrons
# ---------------------------------------------------------------------------

def _freq_to_color(f_Hz: float) -> str:
    """Approximate visible-light color from frequency. Falls back outside visible."""
    if f_Hz < 4.0e14:
        return "#8b0000"  # IR / deep red
    if f_Hz > 7.9e14:
        return "#a78bfa"  # UV / violet
    # Map visible band to wavelength (nm) then to RGB
    wl_nm = 3.0e17 / f_Hz  # c/f in nm
    # Crude piecewise color map
    if wl_nm >= 645: return "#ff2d2d"
    if wl_nm >= 580: return "#ff8c00"
    if wl_nm >= 510: return "#ffd400"
    if wl_nm >= 490: return "#00d26a"
    if wl_nm >= 440: return "#1e88e5"
    return "#8a4dff"


def render_photoelectric_theater(
    sim: dict, freq_hz: float, intensity_rel: float, phi_eV: float,
    *, caption: str = "", dramatic: str = ""
) -> str:
    emits = bool(sim.get("emits_electrons", False))
    ke = float(sim.get("ke_max_eV", 0.0))
    threshold = float(sim.get("threshold_freq_Hz", 0.0))
    photon_eV = float(sim.get("photon_eV", 0.0))
    color = _freq_to_color(freq_hz)

    sw, sh = 520, 260
    metal_y = sh - 60
    metal_h = 40

    # Number of photons proportional to intensity (cap 6)
    n_photons = max(1, min(6, int(round(intensity_rel * 6))))
    photon_html = []
    for i in range(n_photons):
        x = 60 + i * (sw - 120) / max(n_photons - 1, 1)
        delay = (i * 0.18) % 1.2
        photon_html.append(
            f'<g class="phy-photon" style="--x:{x:.1f}px; --delay:{delay:.2f}s;">'
            f'  <circle r="6" cx="{x:.1f}" cy="20" fill="{color}" stroke="#fff" stroke-width="1.2" opacity="0.9"/>'
            f'</g>'
        )

    electron_html = []
    if emits:
        # Speed proportional to KE; bigger KE = higher rise
        rise = max(60, min(160, 60 + ke * 35))
        for i in range(n_photons):
            x = 60 + i * (sw - 120) / max(n_photons - 1, 1)
            delay = (i * 0.18 + 0.45) % 1.2
            electron_html.append(
                f'<g class="phy-electron" style="--x:{x:.1f}px; --rise:{rise:.0f}px; --delay:{delay:.2f}s;">'
                f'  <circle r="4" cx="{x:.1f}" cy="{metal_y:.0f}" fill="#22d3ee" stroke="#0e7490" stroke-width="1"/>'
                f'  <text x="{x:.1f}" y="{metal_y - 8:.0f}" text-anchor="middle" font-size="9" fill="#67e8f9">e⁻</text>'
                f'</g>'
            )

    verdict_color = "#22c55e" if emits else "#ef4444"
    verdict_text = (
        f"✓ EJECTS · KE_max = {ke:.2f} eV"
        if emits else
        f"✕ NO EJECTION · f below threshold ({threshold:.2e} Hz)"
    )

    body = f"""
<svg viewBox="0 0 {sw} {sh}" width="100%" height="100%" preserveAspectRatio="xMidYMid meet"
     xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="metal" x1="0" x2="0" y1="0" y2="1">
      <stop offset="0%" stop-color="#94a3b8"/>
      <stop offset="100%" stop-color="#475569"/>
    </linearGradient>
  </defs>
  <rect x="0" y="0" width="{sw}" height="{sh}" fill="#040713"/>
  <!-- metal slab -->
  <rect x="20" y="{metal_y}" width="{sw - 40}" height="{metal_h}" fill="url(#metal)" stroke="#cbd5e1" stroke-width="1.5"/>
  <text x="{sw/2:.0f}" y="{metal_y + metal_h/2 + 5:.0f}" text-anchor="middle" font-size="13" fill="#1f2937" font-weight="700">
    φ = {phi_eV:.2f} eV
  </text>
  <!-- photons -->
  {''.join(photon_html)}
  <!-- electrons -->
  {''.join(electron_html)}
  <!-- verdict chip -->
  <rect x="{sw - 290}" y="14" width="270" height="26" rx="13" fill="rgba(0,0,0,0.55)" stroke="{verdict_color}"/>
  <text x="{sw - 155}" y="32" text-anchor="middle" font-size="12" fill="{verdict_color}" font-weight="700">
    {verdict_text}
  </text>
  <text x="20" y="20" font-size="11" fill="#cbd5e1">
    f = {freq_hz:.2e} Hz · photon = {photon_eV:.2f} eV · intensity = {intensity_rel:.0%}
  </text>
</svg>
"""
    return _frame(body, caption=caption, dramatic=dramatic)


# ---------------------------------------------------------------------------
# de Broglie — particle ↔ wave morph
# ---------------------------------------------------------------------------

def render_de_broglie_theater(
    sim: dict, mass_kg: float, v_mps: float,
    *, caption: str = "", dramatic: str = "", particle_name: str = "particle"
) -> str:
    wl = float(sim.get("wavelength_m", 1e-12))
    p = float(sim.get("momentum_kg_m_s", mass_kg * v_mps))
    relativistic = bool(sim.get("relativistic_regime", False))

    sw, sh = 520, 240
    cy = sh / 2 - 10

    # Map wavelength logarithmically to pixel period.
    # Reference: 1 nm (1e-9) → 60 px, 1 pm (1e-12) → 25 px, scales otherwise.
    log_wl = math.log10(max(wl, 1e-40))
    # Compress log-range: 1e-9 (-9) → 60 px; 1e-34 (-34) → 6 px. Linear in log.
    period_px = max(6.0, min(160.0, 6.0 + (log_wl + 34) * 2.16))
    n_waves = int(max(2, min(40, (sw - 80) / period_px)))
    # Build wave path: sine with that period
    points = []
    amp = 20
    for x in range(40, sw - 40, 3):
        y = cy + amp * math.sin(2 * math.pi * (x - 40) / period_px)
        points.append((x, y))
    wave_d = "M " + " L ".join(f"{x},{y:.1f}" for x, y in points)

    # Compare to known scales
    if wl > 1e-9:
        scale_note = f"larger than an atom ({wl*1e9:.2f} nm)"
    elif wl > 1e-10:
        scale_note = f"atomic-scale ({wl*1e10:.2f} Å) — diffracts off crystals"
    elif wl > 1e-15:
        scale_note = f"sub-atomic ({wl*1e12:.2g} pm)"
    else:
        scale_note = f"smaller than a proton — invisible wave behavior"

    rel_chip = (
        '<text x="20" y="200" font-size="11" fill="#fcd34d">⚠ v > 0.1c — classical p=mv breaks down</text>'
        if relativistic else ""
    )

    body = f"""
<svg viewBox="0 0 {sw} {sh}" width="100%" height="100%" preserveAspectRatio="xMidYMid meet"
     xmlns="http://www.w3.org/2000/svg">
  <rect x="0" y="0" width="{sw}" height="{sh}" fill="#080d24"/>
  <!-- axis line -->
  <line x1="40" y1="{cy:.0f}" x2="{sw-40}" y2="{cy:.0f}" stroke="#334155" stroke-width="1"/>
  <!-- traveling wave -->
  <path d="{wave_d}" fill="none" stroke="#22d3ee" stroke-width="2.2" class="phy-wave"/>
  <!-- particle as a glowing dot riding the wave -->
  <circle r="6" fill="#fcd34d" stroke="#92400e" stroke-width="1.5">
    <animate attributeName="cx" from="40" to="{sw-40}" dur="3s" repeatCount="indefinite"/>
    <animate attributeName="cy"
             values="{';'.join(f'{cy + amp * math.sin(2*math.pi*(i*30)/period_px):.1f}' for i in range(11))}"
             dur="3s" repeatCount="indefinite"/>
  </circle>
  <!-- labels -->
  <text x="20" y="24" font-size="11" fill="#cbd5e1" font-family="ui-monospace,monospace">
    {particle_name} · m = {mass_kg:.2e} kg · v = {v_mps:.2e} m/s
  </text>
  <text x="20" y="42" font-size="11" fill="#a5f3fc" font-family="ui-monospace,monospace">
    λ = {wl:.2e} m · p = {p:.2e} kg·m/s
  </text>
  <text x="20" y="184" font-size="11" fill="#94a3b8" font-style="italic">
    {scale_note}
  </text>
  {rel_chip}
</svg>
"""
    return _frame(body, caption=caption, dramatic=dramatic)


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

def render_theater(scenario: str, sim: dict, inp: dict, *, caption: str = "", dramatic: str = "") -> str:
    if scenario == "projectile":
        return render_projectile_theater(
            sim, float(inp.get("v0", 20)), float(inp.get("angle_deg", 45)),
            caption=caption, dramatic=dramatic,
        )
    if scenario == "incline":
        return render_incline_theater(
            sim, float(inp.get("angle_deg", 30)), float(inp.get("mass", 2.0)),
            caption=caption, dramatic=dramatic,
        )
    if scenario == "rollercoaster":
        return render_rollercoaster_theater(sim, caption=caption, dramatic=dramatic)
    if scenario == "collision":
        return render_collision_theater(
            sim,
            float(inp.get("m1", 1.0)), float(inp.get("m2", 1.0)),
            float(inp.get("v1", 3.0)), float(inp.get("v2", -1.0)),
            caption=caption, dramatic=dramatic,
        )
    if scenario == "spring":
        return render_spring_theater(
            sim, float(inp.get("m", 1.0)), float(inp.get("k", 50.0)),
            caption=caption, dramatic=dramatic,
        )
    if scenario == "photoelectric":
        return render_photoelectric_theater(
            sim,
            float(inp.get("pe_freq_hz", 1e15)),
            float(inp.get("pe_intensity", 0.5)),
            float(inp.get("pe_phi", 2.3)),
            caption=caption, dramatic=dramatic,
        )
    if scenario == "de_broglie":
        return render_de_broglie_theater(
            sim,
            float(inp.get("db_mass_kg", 9.11e-31)),
            float(inp.get("db_v_mps", 1e6)),
            caption=caption, dramatic=dramatic,
            particle_name=str(inp.get("db_particle", "particle")),
        )
    # Fallback: empty scene with just the caption.
    return _frame(
        '<svg viewBox="0 0 520 200" width="100%" height="100%"><text x="260" y="100" '
        'text-anchor="middle" fill="#94a3b8" font-size="14">no theater for this scenario</text></svg>',
        caption=caption, dramatic=dramatic,
    )


# ---------------------------------------------------------------------------
# Shared CSS (one block emitted per render — small enough to be inert)
# ---------------------------------------------------------------------------

_THEATER_CSS = """
<style>
.phy-theater {
  background: radial-gradient(ellipse at top, #11182c 0%, #04060f 100%);
  border-radius: 14px;
  padding: 10px 12px 12px;
  color: #e5e7eb;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  display: flex; flex-direction: column; gap: 6px;
  overflow: hidden;
}
.phy-theater .phy-caption {
  align-self: center;
  background: rgba(252,211,77,0.12);
  border: 1px solid rgba(252,211,77,0.35);
  color: #fde68a;
  padding: 3px 12px;
  border-radius: 999px;
  font-size: 0.85rem;
  font-weight: 600;
}
.phy-theater .phy-moment {
  align-self: center;
  background: rgba(34,211,238,0.10);
  border: 1px solid rgba(34,211,238,0.35);
  color: #a5f3fc;
  padding: 4px 12px;
  border-radius: 8px;
  font-size: 0.85rem;
  max-width: 95%;
  text-align: center;
}
.phy-theater svg { display: block; }

/* Incline sliding block: uses precomputed --sdx / --sdy (CSS has no tan()) */
@keyframes phy-slide {
  0%   { transform: translate(0, 0); }
  100% { transform: translate(var(--sdx), var(--sdy)); }
}
.phy-incline-block.sliding rect,
.phy-incline-block.sliding text {
  /* rotation already applied on the parent <g> transform attribute */
}

/* Collision carts: x0 → meet (approach) → xe (recoil) */
@keyframes phy-cart1 {
  0%   { transform: translateX(var(--x0)); }
  45%  { transform: translateX(var(--xm)); }
  55%  { transform: translateX(var(--xm)); }
  100% { transform: translateX(var(--xe)); }
}
@keyframes phy-cart2 {
  0%   { transform: translateX(var(--x0)); }
  45%  { transform: translateX(var(--xm)); }
  55%  { transform: translateX(var(--xm)); }
  100% { transform: translateX(var(--xe)); }
}
.phy-cart1 { animation: phy-cart1 3.6s ease-in-out infinite; }
.phy-cart2 { animation: phy-cart2 3.6s ease-in-out infinite; }

/* Spring + block */
@keyframes phy-osc {
  0%   { transform: translateX(calc(var(--rest) - var(--amp))); }
  50%  { transform: translateX(calc(var(--rest) + var(--amp))); }
  100% { transform: translateX(calc(var(--rest) - var(--amp))); }
}
.phy-block {
  animation: phy-osc var(--period, 1s) ease-in-out infinite;
}
@keyframes phy-spring-stretch {
  0%   { transform: scaleX(0.7); }
  50%  { transform: scaleX(1.3); }
  100% { transform: scaleX(0.7); }
}
.phy-spring-group {
  animation: phy-spring-stretch var(--period, 1s) ease-in-out infinite;
}
.phy-block, .phy-spring-group {
  /* CSS variables come from inline style; provide a default period. */
  --period: 1s;
}

/* Photoelectric photons + electrons */
@keyframes phy-photon-fall {
  0%   { transform: translateY(0); opacity: 0; }
  10%  { opacity: 1; }
  85%  { transform: translateY(180px); opacity: 1; }
  100% { transform: translateY(180px); opacity: 0; }
}
.phy-photon { animation: phy-photon-fall 1.2s linear infinite; animation-delay: var(--delay, 0s); }

@keyframes phy-electron-fly {
  0%   { transform: translateY(0); opacity: 0; }
  20%  { opacity: 1; }
  90%  { transform: translateY(calc(var(--rise) * -1)); opacity: 1; }
  100% { transform: translateY(calc(var(--rise) * -1)); opacity: 0; }
}
.phy-electron { animation: phy-electron-fly 1.2s ease-out infinite; animation-delay: var(--delay, 0s); }

/* Wave shimmer */
@keyframes phy-wave-shimmer {
  from { stroke-dashoffset: 0; }
  to   { stroke-dashoffset: 60; }
}
.phy-wave {
  stroke-dasharray: 4 4;
  animation: phy-wave-shimmer 1.6s linear infinite;
}
</style>
"""
