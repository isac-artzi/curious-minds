"""Star+orbit diagram, atmosphere donut, sky swatch."""

from __future__ import annotations

import math

import numpy as np
import plotly.graph_objects as go


def system_diagram(
    star_color_hex: str,
    hz_inner_AU: float,
    hz_outer_AU: float,
    planet_distance_AU: float,
) -> go.Figure:
    """Top-down 2D system view with shaded HZ and planet on its orbit."""
    # Pick a display scale that keeps the planet visible
    max_r = max(planet_distance_AU * 1.4, hz_outer_AU * 1.3, 0.3)

    theta = np.linspace(0, 2 * math.pi, 200)

    fig = go.Figure()

    # HZ ring (filled annulus via two circles)
    for r in np.linspace(hz_inner_AU, hz_outer_AU, 12):
        fig.add_trace(
            go.Scatter(
                x=r * np.cos(theta),
                y=r * np.sin(theta),
                mode="lines",
                line=dict(color="rgba(34,197,94,0.10)", width=8),
                hoverinfo="skip",
                showlegend=False,
            )
        )

    # Planet orbit
    fig.add_trace(
        go.Scatter(
            x=planet_distance_AU * np.cos(theta),
            y=planet_distance_AU * np.sin(theta),
            mode="lines",
            line=dict(color="#1F3864", width=1.5, dash="dot"),
            hoverinfo="skip",
            showlegend=False,
        )
    )

    # Star
    fig.add_trace(
        go.Scatter(
            x=[0], y=[0],
            mode="markers",
            marker=dict(size=28, color=star_color_hex, line=dict(color="#FFD27A", width=2)),
            name="Host star",
            hovertemplate="Host star<extra></extra>",
        )
    )

    # Planet at frame 0
    fig.add_trace(
        go.Scatter(
            x=[planet_distance_AU], y=[0],
            mode="markers",
            marker=dict(size=14, color="#2E5496", line=dict(color="white", width=1.5)),
            name="Planet",
            hovertemplate=f"Planet at {planet_distance_AU:.3f} AU<extra></extra>",
        )
    )

    # Animation: orbit the planet (frames patch only the planet trace)
    n_frames = 36
    frames = []
    for i in range(n_frames):
        ang = 2 * math.pi * i / n_frames
        frames.append(
            go.Frame(
                data=[
                    go.Scatter(
                        x=[planet_distance_AU * math.cos(ang)],
                        y=[planet_distance_AU * math.sin(ang)],
                        mode="markers",
                        marker=dict(size=14, color="#2E5496", line=dict(color="white", width=1.5)),
                    )
                ],
                traces=[len(fig.data) - 1],
                name=str(i),
            )
        )
    fig.frames = frames

    fig.update_layout(
        title="System diagram (HZ shaded green)",
        xaxis=dict(range=[-max_r, max_r], visible=False, scaleanchor="y"),
        yaxis=dict(range=[-max_r, max_r], visible=False),
        showlegend=False,
        height=380,
        margin=dict(l=10, r=10, t=50, b=10),
        plot_bgcolor="#0B1020",
        paper_bgcolor="#0B1020",
        font=dict(color="#E5E7EB"),
        updatemenus=[
            dict(
                type="buttons",
                direction="left",
                showactive=False,
                x=0.02, y=0.05,
                buttons=[
                    dict(
                        label="▶ Orbit",
                        method="animate",
                        args=[
                            None,
                            dict(
                                frame=dict(duration=180, redraw=True),
                                transition=dict(duration=80),
                                fromcurrent=True,
                                mode="immediate",
                            ),
                        ],
                    ),
                    dict(
                        label="⏸ Pause",
                        method="animate",
                        args=[[None], dict(frame=dict(duration=0, redraw=False),
                                           mode="immediate")],
                    ),
                    dict(
                        label="↺ Restart",
                        method="animate",
                        args=[["0"], dict(frame=dict(duration=0, redraw=True),
                                          mode="immediate")],
                    ),
                ],
            )
        ],
    )
    return fig


# Fixed color per gas so the same gas keeps its color as rank order shifts
# between runs (default Plotly colorway assigns by position, not identity).
_GAS_COLOR = {
    "N2": "#2E5496",
    "O2": "#16A34A",
    "CO2": "#D97706",
    "CH4": "#7C3AED",
    "H2O": "#0EA5E9",
    "H2": "#EC4899",
    "He": "#F59E0B",
    "Ar": "#6B7280",
    "NH3": "#14B8A6",
    "SO2": "#DC2626",
    "Ne": "#A78BFA",
}
_GAS_FALLBACK = ["#94A3B8", "#64748B", "#475569", "#334155"]


def atmosphere_donut(composition: dict[str, float]) -> go.Figure:
    items = [(k, v) for k, v in composition.items() if v > 0]
    items.sort(key=lambda kv: -kv[1])
    labels = [k for k, _ in items]
    values = [v for _, v in items]
    colors = [
        _GAS_COLOR.get(k, _GAS_FALLBACK[i % len(_GAS_FALLBACK)])
        for i, k in enumerate(labels)
    ]
    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.55,
            sort=False,  # preserve our largest-first order
            textinfo="label+percent",
            textposition="auto",                # inside big slices, outside tiny ones
            insidetextorientation="horizontal",
            outsidetextfont=dict(size=11),
            insidetextfont=dict(size=12, color="white"),
            marker=dict(colors=colors, line=dict(color="white", width=2)),
        )
    )
    # Generous margins so the outside-label leader lines don't clip at the
    # plot boundary (e.g. small "Ar 1.61%" callouts at the top of the donut).
    fig.update_layout(
        title="Atmosphere composition",
        height=400,
        margin=dict(l=80, r=80, t=60, b=40),
        showlegend=False,
    )
    return fig


# ---------------------------------------------------------------------------
# Transmission spectrum — what JWST would see
# ---------------------------------------------------------------------------

# Major absorption bands per gas: list of (wavelength_um, relative_strength).
# Strength is qualitative (0–1) — used to scale the depth of the dip.
_ABSORPTION_BANDS: dict[str, list[tuple[float, float]]] = {
    "O2":  [(0.69, 0.3), (0.76, 0.7), (1.27, 0.5)],
    "O3":  [(0.6, 0.6), (9.6, 1.0)],
    "H2O": [(0.94, 0.4), (1.13, 0.6), (1.4, 0.8), (1.9, 0.9), (2.7, 0.9), (6.3, 1.0)],
    "CO2": [(1.6, 0.5), (2.0, 0.7), (2.7, 0.6), (4.3, 1.0), (15.0, 0.95)],
    "CH4": [(1.7, 0.5), (2.3, 0.7), (3.3, 1.0), (7.6, 0.85)],
    "NH3": [(2.0, 0.4), (6.0, 0.7), (10.5, 0.8)],
    "N2O": [(4.5, 0.5), (7.8, 0.5)],
    "SO2": [(4.0, 0.5), (7.3, 0.7), (8.7, 0.6)],
    "H2":  [(2.4, 0.2)],
    "N2":  [],  # essentially transparent in vis/IR
    "He":  [],
    "Ar":  [],
}

NAVY = "#1F3864"


def transmission_spectrum_figure(composition: dict[str, float]) -> "go.Figure":
    """Simulated transmission spectrum across 0.3–15 μm.

    For each gas with non-trivial abundance, draws Gaussian dips at its
    known absorption bands. Background includes a weak Rayleigh rise toward
    the blue. Output mimics what a transmission spectrum from JWST would look like.
    """
    wavelengths = np.linspace(0.3, 15.0, 700)
    # Baseline = 100% transmission with a tiny Rayleigh rise toward blue.
    rayleigh = np.minimum(0.001 * (1.0 / np.maximum(wavelengths, 0.3)) ** 4 * 5, 4)
    transmission = 100.0 - rayleigh

    for gas, pct in composition.items():
        if pct < 0.01:
            continue
        bands = _ABSORPTION_BANDS.get(gas, [])
        # Depth scales as sqrt(abundance) — a common rough approximation,
        # since optical depth saturates for the strongest bands.
        scale = math.sqrt(min(pct, 100.0) / 100.0)
        for center, strength in bands:
            sigma = 0.04 * center  # ~ resolving power R ~ 25
            depth = strength * 35.0 * scale
            transmission -= depth * np.exp(-((wavelengths - center) / sigma) ** 2)

    transmission = np.clip(transmission, 0, 100)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=wavelengths, y=transmission, mode="lines",
            line=dict(color="#2E5496", width=2),
            fill="tozeroy", fillcolor="rgba(46,84,150,0.12)",
            hovertemplate="λ = %{x:.2f} μm · transmission = %{y:.0f}%<extra></extra>",
            name="Transmission",
        )
    )

    # Wavelength region shading
    fig.add_vrect(x0=0.4, x1=0.7, fillcolor="rgba(255,255,200,0.25)",
                  line_width=0, layer="below")
    fig.add_vrect(x0=0.7, x1=2.5, fillcolor="rgba(255,210,160,0.18)",
                  line_width=0, layer="below")
    fig.add_vrect(x0=2.5, x1=15, fillcolor="rgba(220,180,180,0.15)",
                  line_width=0, layer="below")

    # Annotate the strongest gas bands actually present
    annotations = []
    seen: set[tuple[str, float]] = set()
    sorted_gases = sorted(composition.items(), key=lambda kv: -kv[1])
    for gas, pct in sorted_gases:
        if pct < 0.5 or gas not in _ABSORPTION_BANDS:
            continue
        bands = sorted(_ABSORPTION_BANDS[gas], key=lambda b: -b[1])
        for center, strength in bands:
            if strength < 0.6 or center > 14.0:
                continue
            key = (gas, round(center, 1))
            if key in seen:
                continue
            seen.add(key)
            idx = int(np.argmin(np.abs(wavelengths - center)))
            annotations.append(
                dict(
                    x=center, y=transmission[idx],
                    text=f"<b>{gas}</b>",
                    showarrow=True, arrowhead=2, arrowwidth=1, arrowcolor="#5B6478",
                    ax=0, ay=-30,
                    font=dict(size=11, color=NAVY),
                )
            )
            break  # one annotation per gas keeps things readable
        if len(annotations) >= 7:
            break

    # Region labels along the top
    annotations.extend([
        dict(x=0.55, y=104, text="Visible", showarrow=False,
             font=dict(size=10, color="#5B6478"), xref="x", yref="y"),
        dict(x=1.6, y=104, text="Near-IR", showarrow=False,
             font=dict(size=10, color="#5B6478"), xref="x", yref="y"),
        dict(x=8, y=104, text="Mid-IR", showarrow=False,
             font=dict(size=10, color="#5B6478"), xref="x", yref="y"),
    ])

    fig.update_layout(
        title="Simulated transmission spectrum (what JWST would observe)",
        xaxis=dict(
            title="Wavelength (μm)", type="log",
            tickvals=[0.5, 1, 2, 3, 5, 10, 15],
            ticktext=["0.5", "1", "2", "3", "5", "10", "15"],
        ),
        yaxis=dict(title="Transmission (%)", range=[0, 110]),
        annotations=annotations,
        height=340,
        margin=dict(l=60, r=20, t=50, b=50),
        showlegend=False,
    )
    return fig


# ---------------------------------------------------------------------------
# Injection time evolution — animated 2-panel chart
# ---------------------------------------------------------------------------

def injection_evolution_figure(sim: dict) -> "go.Figure":
    """Animated atmospheric response over time after a one-shot injection.

    Top panel: composition (%) of the top gases vs log(time).
    Bottom panel: greenhouse ΔT (°C) vs log(time).
    A vertical guide line scrubs across both panels via Play / slider.
    """
    from plotly.subplots import make_subplots

    t = sim["t_years"]
    series: dict[str, list[float]] = sim["composition_series"]
    dT = sim["temperature_offset_C"]

    # Pick top 6 gases by peak abundance to keep the chart readable
    sorted_gases = sorted(series.keys(), key=lambda g: -max(series[g]))
    top_gases = sorted_gases[:6]

    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.15,
        subplot_titles=(
            "Atmospheric composition over time",
            "Greenhouse temperature offset (vs. baseline atmosphere)",
        ),
        row_heights=[0.62, 0.38],
    )

    palette = ["#2E5496", "#16A34A", "#D97706", "#7C3AED", "#DB2777", "#0891B2"]
    for i, g in enumerate(top_gases):
        fig.add_trace(
            go.Scatter(
                x=t, y=series[g], name=g, mode="lines",
                line=dict(color=palette[i % len(palette)], width=2.2),
                hovertemplate=f"<b>{g}</b><br>t = %{{x:.0f}} yr<br>%{{y:.2f}}%<extra></extra>",
            ),
            row=1, col=1,
        )

    fig.add_trace(
        go.Scatter(
            x=t, y=dT, mode="lines", name="ΔT (°C)",
            line=dict(color="#DC2626", width=2.2),
            hovertemplate="t = %{x:.0f} yr<br>ΔT = %{y:+.1f} °C<extra></extra>",
            showlegend=False,
            fill="tozeroy", fillcolor="rgba(220,38,38,0.10)",
        ),
        row=2, col=1,
    )

    # Compute y-ranges so the moving line spans cleanly
    y1_max = max((max(series[g]) for g in top_gases), default=100.0) * 1.05
    y2_min = min(min(dT), -1.0) - 1.0
    y2_max = max(max(dT), 1.0) + 1.0

    # Vertical scrubber lines (one per subplot). Frames update both.
    init_x = t[0]
    fig.add_trace(
        go.Scatter(
            x=[init_x, init_x], y=[0, y1_max], mode="lines",
            line=dict(color="rgba(0,0,0,0.55)", width=1.5, dash="dash"),
            showlegend=False, hoverinfo="skip",
        ),
        row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=[init_x, init_x], y=[y2_min, y2_max], mode="lines",
            line=dict(color="rgba(0,0,0,0.55)", width=1.5, dash="dash"),
            showlegend=False, hoverinfo="skip",
        ),
        row=2, col=1,
    )

    # Frames: only update the two scrubber traces (the last two added).
    n_static = len(top_gases) + 1  # gas lines + dT line
    frames = []
    for i, ti in enumerate(t):
        frames.append(
            go.Frame(
                data=[
                    go.Scatter(x=[ti, ti], y=[0, y1_max]),
                    go.Scatter(x=[ti, ti], y=[y2_min, y2_max]),
                ],
                traces=[n_static, n_static + 1],
                name=str(i),
            )
        )
    fig.frames = frames

    # Slider with sparse labels
    step_indices = list(range(0, len(t), max(1, len(t) // 18)))
    if step_indices[-1] != len(t) - 1:
        step_indices.append(len(t) - 1)

    def _fmt_year(yr: float) -> str:
        if yr >= 1e6:
            return f"{yr/1e6:.0f} Myr"
        if yr >= 1e3:
            return f"{yr/1e3:.0f} kyr"
        return f"{yr:.0f} yr"

    sliders = [
        dict(
            active=0,
            x=0.05, y=-0.18, len=0.9, pad=dict(t=4, b=4),
            currentvalue=dict(prefix="t = ", font=dict(size=12, color=NAVY)),
            steps=[
                dict(
                    method="animate",
                    label=_fmt_year(t[i]),
                    args=[
                        [str(i)],
                        dict(
                            mode="immediate",
                            frame=dict(duration=0, redraw=True),
                            transition=dict(duration=0),
                        ),
                    ],
                )
                for i in step_indices
            ],
        )
    ]

    fig.update_layout(
        height=560,
        margin=dict(l=60, r=20, t=70, b=110),
        sliders=sliders,
        updatemenus=[
            dict(
                type="buttons", showactive=False,
                x=0.0, y=-0.32, xanchor="left",
                pad=dict(t=4, b=4),
                buttons=[
                    dict(
                        label="▶ Play", method="animate",
                        args=[
                            None,
                            dict(
                                frame=dict(duration=180, redraw=True),
                                fromcurrent=True, mode="immediate",
                            ),
                        ],
                    ),
                    dict(
                        label="⏸ Pause", method="animate",
                        args=[
                            [None],
                            dict(
                                frame=dict(duration=0, redraw=False),
                                mode="immediate",
                            ),
                        ],
                    ),
                    dict(
                        label="⏮ Restart", method="animate",
                        args=[
                            ["0"],
                            dict(
                                frame=dict(duration=0, redraw=True),
                                mode="immediate",
                            ),
                        ],
                    ),
                ],
            )
        ],
        legend=dict(orientation="h", y=1.10, x=0.5, xanchor="center"),
    )
    fig.update_xaxes(type="log", row=1, col=1)
    fig.update_xaxes(type="log", title_text="Time (years, log scale)", row=2, col=1)
    fig.update_yaxes(title_text="% of atmosphere", range=[0, y1_max], row=1, col=1)
    fig.update_yaxes(title_text="ΔT (°C)", range=[y2_min, y2_max], row=2, col=1)
    return fig


def sky_swatch_html(star_color_hex: str, atmosphere_id: str) -> str:
    """Returns HTML for a CSS-gradient sky swatch."""
    sky_top = {
        "earth_like": "#5B9BD5",
        "venus_like": "#E2B14A",
        "mars_like": "#C97B53",
        "titan_like": "#D9A56A",
        "hydrogen_helium": "#A6BBE8",
        "reducing_archean": "#D58B4A",
        "ice_world": "#A0C4E8",
    }.get(atmosphere_id, "#7AAFE0")
    return f"""
    <div style="
      width:100%; height:140px; border-radius:8px;
      background: linear-gradient(180deg, {sky_top} 0%, {star_color_hex} 100%);
      box-shadow: inset 0 -10px 30px rgba(0,0,0,0.15);
    ">
      <div style="
        position:relative; top:18px; left:50%;
        width:40px; height:40px; border-radius:50%;
        background:{star_color_hex};
        box-shadow: 0 0 30px {star_color_hex};
        transform: translateX(-50%);
      "></div>
    </div>
    """
