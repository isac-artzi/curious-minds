"""Food-web graph + population dynamics charts."""

from __future__ import annotations

import math

import networkx as nx
import numpy as np
import plotly.graph_objects as go

TROPHIC_Y = {
    "producer": 0,
    "primary_consumer": 1,
    "secondary_consumer": 2,
    "apex_predator": 3,
}

TROPHIC_LABEL = {
    "producer": "Producers",
    "primary_consumer": "Herbivores",
    "secondary_consumer": "Carnivores",
    "apex_predator": "Apex predators",
}

TROPHIC_COLOR = {
    "producer": "#16A34A",
    "primary_consumer": "#0EA5E9",
    "secondary_consumer": "#7C3AED",
    "apex_predator": "#DC2626",
}


def food_web_figure(
    species_records: list[dict],
    interactions: list[dict],
) -> go.Figure:
    """Tier-stacked food web with explicit prey→predator arrows and a legend.

    Layout:
      • Y-axis is trophic level (Producers at bottom, Apex on top).
      • Within each tier, species are spaced evenly on a fixed grid (no jitter),
        sorted alphabetically for stable layout.
      • Edges run from prey up to predator with an arrowhead at the predator.
    """
    G = nx.DiGraph()
    for s in species_records:
        G.add_node(s["id"], **s)

    # Pull predator → prey edges from BOTH sources so we don't miss any:
    #   1. interactions.json (curated predation records w/ notes & strength)
    #   2. each species' "diet" field (a fast way to declare prey lists
    #      without writing a full interaction record).
    edges_seen: set[tuple[str, str]] = set()
    for ix in interactions:
        if ix.get("type") == "predation":
            pred = ix.get("predator")
            prey = ix.get("prey")
            if pred in G.nodes and prey in G.nodes and pred != prey:
                G.add_edge(prey, pred, kind="eats")
                edges_seen.add((pred, prey))
    for s in species_records:
        pred = s["id"]
        for prey in s.get("diet", []) or []:
            if prey in G.nodes and pred != prey and (pred, prey) not in edges_seen:
                G.add_edge(prey, pred, kind="eats")
                edges_seen.add((pred, prey))

    # Group nodes by trophic level, sort within each level for stable layout
    by_level: dict[int, list[str]] = {}
    for nid, ndata in G.nodes(data=True):
        level = TROPHIC_Y.get(ndata.get("trophic_level", "producer"), 1)
        by_level.setdefault(level, []).append(nid)
    for lvl in by_level:
        by_level[lvl].sort(
            key=lambda nid: G.nodes[nid].get("common_name", nid).lower()
        )

    # Width of widest tier defines the x-grid; thinner tiers get centered
    max_width = max((len(v) for v in by_level.values()), default=1)
    pos: dict[str, tuple[float, float]] = {}
    for level, nodes in by_level.items():
        n = len(nodes)
        # center this tier within max_width slots
        offset = (max_width - n) / 2.0
        for i, nid in enumerate(nodes):
            pos[nid] = (offset + i + 0.5, float(level))

    # ---- edges as line segments (no arrow) for the hover layer ------------
    edge_x: list[float | None] = []
    edge_y: list[float | None] = []
    for u, v in G.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y, mode="lines",
        line=dict(color="rgba(91,100,120,0.45)", width=1.4),
        hoverinfo="none", showlegend=False,
    )

    # ---- arrowheads at predator end (annotation per edge) -----------------
    annotations = []
    for u, v in G.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        annotations.append(dict(
            ax=x0, ay=y0, axref="x", ayref="y",
            x=x1, y=y1, xref="x", yref="y",
            showarrow=True, arrowhead=3, arrowsize=1.2,
            arrowwidth=1.4, arrowcolor="rgba(31,56,100,0.55)",
            standoff=14,
        ))

    # ---- one node trace per trophic level so we get a real legend ---------
    fig = go.Figure(data=[edge_trace])
    legend_seen: set[str] = set()
    # Iterate in trophic order so the legend reads bottom-up
    level_order = sorted(by_level.keys())
    inverse_level: dict[int, str] = {v: k for k, v in TROPHIC_Y.items()}
    for lvl in level_order:
        cat = inverse_level.get(lvl, "primary_consumer")
        color = TROPHIC_COLOR.get(cat, "#777")
        label = TROPHIC_LABEL.get(cat, cat.replace("_", " ").title())
        xs, ys, labels, hovers = [], [], [], []
        for nid in by_level[lvl]:
            d = G.nodes[nid]
            emoji = d.get("emoji", "•")
            xs.append(pos[nid][0])
            ys.append(pos[nid][1])
            labels.append(f"{emoji} {d.get('common_name', nid)}")
            hovers.append(
                f"<b>{d.get('common_name', nid)}</b><br>"
                f"<i>{d.get('binomial', '')}</i><br>"
                f"Trophic level: {d.get('trophic_level', '?')}<br>"
                f"IUCN: {d.get('iucn_status', '?')}"
            )
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="markers+text",
            marker=dict(
                size=28, color=color,
                line=dict(color="white", width=2),
            ),
            text=labels, textposition="bottom center",
            textfont=dict(size=12),
            hovertext=hovers, hoverinfo="text",
            name=label, legendgroup=cat,
            showlegend=label not in legend_seen,
        ))
        legend_seen.add(label)

    # Tier guidelines for visual separation
    for lvl in range(0, 4):
        fig.add_hline(
            y=lvl, line=dict(color="rgba(150,150,160,0.18)", width=1, dash="dot"),
            layer="below",
        )

    fig.update_layout(
        title=dict(
            text="<b>Food web</b><br><span style='font-size:0.78rem;color:#6B7280;'>"
                 "Arrows point from prey → predator. Colour = trophic level. "
                 "Hover for details.</span>",
            x=0.02, xanchor="left", y=0.97, yanchor="top",
            font=dict(size=15),
        ),
        annotations=annotations,
        xaxis=dict(
            visible=False,
            range=[-0.5, max_width + 0.5],
        ),
        yaxis=dict(
            tickmode="array",
            tickvals=[0, 1, 2, 3],
            ticktext=["Producers", "Herbivores", "Carnivores", "Apex"],
            range=[-0.6, 3.7],
            gridcolor="rgba(0,0,0,0)",
        ),
        height=520,
        # Generous top margin so the legend (placed below the title) doesn't
        # overlap the title text.
        margin=dict(l=70, r=20, t=110, b=40),
        plot_bgcolor="#FAFBFC",
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.005, xanchor="left", x=0.0,
            bgcolor="rgba(255,255,255,0)",
            font=dict(size=11),
        ),
    )
    return fig


_INTRINSIC = {
    "producer": 0.20,
    "primary_consumer": 0.05,
    "secondary_consumer": -0.02,
    "apex_predator": -0.05,
}
_K_FOR = {
    "producer": 1000.0,
    "primary_consumer": 400.0,
    "secondary_consumer": 100.0,
    "apex_predator": 80.0,
}


def simulate_populations(
    species_records: list[dict],
    initial_populations: dict[str, float],
    years: int,
    *,
    disturbance_year: int | None = None,
    disturbance_strength: float = 0.4,   # fraction killed at the disturbance step
    climate_dT_C: float = 0.0,
    climate_dP_pct: float = 0.0,
    protect: dict[str, float] | None = None,   # multiplier on intrinsic growth, e.g. 1.5
    hunt: dict[str, float] | None = None,      # mortality rate per year, e.g. 0.1
    seed: int = 42,
) -> tuple[np.ndarray, dict[str, list[float]]]:
    """Toy Lotka–Volterra-style sim with climate, intervention and disturbance levers.

    Returns ``(t_vector, pops_dict)``. Pure function — used by every dynamics chart.
    """
    protect = protect or {}
    hunt = hunt or {}
    rng = np.random.default_rng(seed)
    # Resolution scales with horizon so 100-yr runs stay smooth without exploding step count.
    timesteps = max(min(years * 4, 240), 12)
    t = np.linspace(0, years, timesteps)

    species_ids = [s["id"] for s in species_records]
    pops: dict[str, list[float]] = {sid: [float(initial_populations.get(sid, 100.0))] for sid in species_ids}

    prey_of: dict[str, list[str]] = {
        s["id"]: [d for d in s.get("diet", []) if d in species_ids]
        for s in species_records
    }

    # Climate modifiers (gentle — meant for pedagogical signal, not realism).
    # Producers benefit from mild warming + more rain, suffer from extremes.
    warmth_factor = 1.0 + 0.05 * climate_dT_C - 0.01 * (climate_dT_C ** 2) / 4.0
    rain_factor = 1.0 + 0.006 * climate_dP_pct - 0.00003 * (climate_dP_pct ** 2)
    producer_climate = max(0.05, warmth_factor * rain_factor)
    # Animals get a milder version (heat stress at high ΔT, cold stress at very negative ΔT)
    animal_climate = max(0.1, 1.0 - 0.02 * abs(climate_dT_C) - 0.001 * abs(climate_dP_pct))

    for step in range(1, timesteps):
        dt = t[step] - t[step - 1]
        for s in species_records:
            sid = s["id"]
            level = s.get("trophic_level", "primary_consumer")
            r = _INTRINSIC.get(level, 0.0) * float(protect.get(sid, 1.0))
            if level == "producer":
                r *= producer_climate
            else:
                r *= animal_climate
            pop = pops[sid][-1]
            K = _K_FOR.get(level, 200.0)
            growth = r * pop * (1 - pop / K)
            interaction = 0.0
            for prey_id in prey_of[sid]:
                interaction += 0.0008 * pop * pops[prey_id][-1]
            for p in species_records:
                if sid in prey_of.get(p["id"], []):
                    interaction -= 0.0010 * pop * pops[p["id"]][-1]
            noise = rng.normal(0, pop * 0.02)
            mortality = float(hunt.get(sid, 0.0)) * pop
            new_pop = pop + (growth + interaction + noise - mortality) * dt
            if disturbance_year is not None and abs(t[step] - disturbance_year) < dt:
                new_pop *= max(0.0, 1.0 - disturbance_strength)
            new_pop = max(0.0, min(new_pop, K * 2.0))
            pops[sid].append(new_pop)

    return t, pops


def population_dynamics_figure(
    species_records: list[dict],
    initial_populations: dict[str, float],
    years: int,
    disturbance_year: int | None = None,
    *,
    climate_dT_C: float = 0.0,
    climate_dP_pct: float = 0.0,
    protect: dict[str, float] | None = None,
    hunt: dict[str, float] | None = None,
    precomputed: tuple[np.ndarray, dict[str, list[float]]] | None = None,
) -> go.Figure:
    """Animated multi-species sim (toy Lotka–Volterra; pedagogical only).

    Uses Plotly frames so the user can press ▶ Play to watch the populations
    evolve year-by-year, or drag the slider to scrub. Pass ``precomputed``
    when the same simulation result is shared with other charts on the page.
    """
    if precomputed is not None:
        t, pops = precomputed
    else:
        t, pops = simulate_populations(
            species_records, initial_populations, years,
            disturbance_year=disturbance_year,
            climate_dT_C=climate_dT_C, climate_dP_pct=climate_dP_pct,
            protect=protect, hunt=hunt,
        )
    timesteps = len(t)

    # Per-species line trace + matching marker trace ("now" dot at frame end)
    trace_meta = []
    for s in species_records:
        sid = s["id"]
        color = TROPHIC_COLOR.get(s.get("trophic_level", "primary_consumer"), "#444")
        trace_meta.append((sid, s, color))

    # ---- initial frame: only the very first point ------------------------
    initial_data = []
    for sid, s, color in trace_meta:
        name = f"{s.get('emoji', '')} {s.get('common_name', sid)}"
        initial_data.append(go.Scatter(
            x=[t[0]], y=[pops[sid][0]],
            mode="lines",
            name=name,
            line=dict(width=2.4, color=color, shape="spline", smoothing=0.4),
            hovertemplate="%{x:.1f} yr<br>%{y:.0f}<extra>%{fullData.name}</extra>",
            legendgroup=sid,
            cliponaxis=True,
        ))
    # "Now" markers — separate traces, hidden from legend
    for sid, s, color in trace_meta:
        initial_data.append(go.Scatter(
            x=[t[0]], y=[pops[sid][0]],
            mode="markers",
            marker=dict(size=10, color=color, line=dict(color="white", width=1.5)),
            showlegend=False, hoverinfo="skip",
            legendgroup=sid,
        ))

    # ---- frames: progressively reveal the time series --------------------
    # Use ~40 frames max (every k-th step) to keep the slider light.
    stride = max(1, timesteps // 40)
    frame_indices = list(range(0, timesteps, stride))
    if frame_indices[-1] != timesteps - 1:
        frame_indices.append(timesteps - 1)

    frames = []
    for fi in frame_indices:
        fdata = []
        # Lines up to fi (inclusive)
        for sid, s, color in trace_meta:
            fdata.append(go.Scatter(
                x=t[: fi + 1].tolist(),
                y=pops[sid][: fi + 1],
                mode="lines",
                line=dict(width=2.4, color=color, shape="spline", smoothing=0.4),
                cliponaxis=True,
            ))
        # "Now" markers at fi
        for sid, s, color in trace_meta:
            fdata.append(go.Scatter(
                x=[t[fi]], y=[pops[sid][fi]],
                mode="markers",
                marker=dict(size=10, color=color, line=dict(color="white", width=1.5)),
            ))
        frames.append(go.Frame(
            data=fdata,
            name=f"{t[fi]:.1f}",
            layout=go.Layout(
                annotations=[dict(
                    text=f"Year {t[fi]:.1f}",
                    xref="paper", yref="paper",
                    x=0.99, y=0.97, xanchor="right", yanchor="top",
                    showarrow=False,
                    font=dict(size=13, color="#1F3864"),
                    bgcolor="rgba(255,255,255,0.8)",
                    borderpad=4,
                )]
            ),
        ))

    # Robust y-axis range, fixed across frames so lines don't jump:
    #   - upper = max of (90th-percentile of all values * 1.4, max initial pop * 1.5),
    #     so a single transient spike can't squash everyone else's variation;
    #   - lower = 0 (we already clamp populations to >= 0).
    all_values = np.concatenate([np.asarray(v) for v in pops.values()]) if pops else np.array([1.0])
    p90 = float(np.percentile(all_values, 90)) if all_values.size else 1.0
    init_max = max(initial_populations.values(), default=1.0)
    ymax = max(p90 * 1.4, init_max * 1.5, 10.0)

    fig = go.Figure(data=initial_data, frames=frames)

    if disturbance_year is not None:
        fig.add_vline(
            x=disturbance_year,
            line=dict(color="#D97706", dash="dash"),
            annotation_text="disturbance",
            annotation_position="top",
        )

    fig.update_layout(
        title=dict(
            text="<b>Population dynamics</b><br><span style='font-size:0.78rem;color:#6B7280;'>"
                 "Press ▶ Play to watch populations evolve. Toy Lotka–Volterra — "
                 "pedagogical, not predictive.</span>",
            x=0.02, xanchor="left", y=0.97, yanchor="top",
            font=dict(size=15),
        ),
        xaxis=dict(
            title="Years",
            range=[0, years],
        ),
        yaxis=dict(
            title="Population (relative units)",
            range=[0, ymax],
            fixedrange=True,
        ),
        height=560,
        # Extra bottom space so the controls (buttons row + slider row below it)
        # have room and don't crowd the x-axis.
        margin=dict(l=60, r=20, t=110, b=140),
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.005, xanchor="left", x=0.0,
            bgcolor="rgba(255,255,255,0)",
            font=dict(size=11),
        ),
        annotations=[dict(
            text=f"Year {t[0]:.1f}",
            xref="paper", yref="paper",
            x=0.99, y=0.97, xanchor="right", yanchor="top",
            showarrow=False,
            font=dict(size=13, color="#1F3864"),
            bgcolor="rgba(255,255,255,0.8)",
            borderpad=4,
        )],
        updatemenus=[dict(
            type="buttons",
            direction="left",
            # Buttons sit on their own row, just below the x-axis title.
            x=0.0, xanchor="left",
            y=-0.18, yanchor="top",
            pad=dict(t=2, r=4),
            showactive=False,
            buttons=[
                dict(
                    label="▶ Play",
                    method="animate",
                    args=[None, dict(
                        frame=dict(duration=140, redraw=True),
                        transition=dict(duration=60),
                        fromcurrent=True,
                        mode="immediate",
                    )],
                ),
                dict(
                    label="⏸ Pause",
                    method="animate",
                    args=[[None], dict(
                        frame=dict(duration=0, redraw=False),
                        transition=dict(duration=0),
                        mode="immediate",
                    )],
                ),
                dict(
                    label="↺ Restart",
                    method="animate",
                    args=[[frames[0].name], dict(
                        frame=dict(duration=0, redraw=True),
                        mode="immediate",
                    )],
                ),
            ],
        )],
        sliders=[dict(
            active=0,
            currentvalue=dict(prefix="Year: ", font=dict(size=12, color="#1F3864")),
            # Slider sits on its own row, well below the buttons row, so the
            # tick labels and the buttons never collide.
            x=0.0, xanchor="left",
            y=-0.36, yanchor="top",
            len=1.0,
            pad=dict(t=4, b=4),
            steps=[
                dict(
                    method="animate",
                    label=f"{t[fi]:.0f}",
                    args=[[f"{t[fi]:.1f}"], dict(
                        frame=dict(duration=0, redraw=True),
                        mode="immediate",
                        transition=dict(duration=0),
                    )],
                )
                for fi in frame_indices
            ],
        )],
    )
    return fig


# ----------------------------------------------------------------------
# Pedagogical extras: trophic pyramid, Shannon diversity, keystone &
# climate comparisons. All consume final populations from
# ``simulate_populations`` so they stay consistent with the dynamics chart.
# ----------------------------------------------------------------------


_TIER_ORDER = ["producer", "primary_consumer", "secondary_consumer", "apex_predator"]


def _aggregate_by_tier(
    species_records: list[dict],
    populations: dict[str, float],
) -> dict[str, float]:
    totals: dict[str, float] = {lvl: 0.0 for lvl in _TIER_ORDER}
    for s in species_records:
        lvl = s.get("trophic_level", "primary_consumer")
        totals[lvl] = totals.get(lvl, 0.0) + float(populations.get(s["id"], 0.0))
    return totals


def trophic_pyramid_figure(
    species_records: list[dict],
    populations: dict[str, float],
) -> go.Figure:
    """Funnel-style trophic pyramid showing biomass per tier.

    Pedagogical only: uses raw population sums per tier (Lindeman's 10% rule
    is mentioned in the title but not enforced — the simulation produces the
    actual numbers).
    """
    totals = _aggregate_by_tier(species_records, populations)
    # Funnel reads top-down; we want apex on top, producers at the base.
    labels_top_down = list(reversed(_TIER_ORDER))
    values = [totals.get(lvl, 0.0) for lvl in labels_top_down]
    text = [TROPHIC_LABEL.get(lvl, lvl) for lvl in labels_top_down]
    colors = [TROPHIC_COLOR.get(lvl, "#777") for lvl in labels_top_down]

    fig = go.Figure(go.Funnel(
        y=text,
        x=values,
        textinfo="value+percent total",
        marker=dict(color=colors, line=dict(color="white", width=2)),
        hovertemplate="<b>%{y}</b><br>Biomass units: %{x:.0f}<extra></extra>",
    ))
    fig.update_layout(
        title=dict(
            text="<b>Trophic pyramid</b><br>"
                 "<span style='font-size:0.78rem;color:#6B7280;'>Total population per tier "
                 "at end of horizon. Healthy systems taper toward the top (~10% rule).</span>",
            x=0.02, xanchor="left", y=0.97, yanchor="top",
            font=dict(size=15),
        ),
        height=360,
        margin=dict(l=20, r=20, t=110, b=30),
        plot_bgcolor="#FAFBFC",
    )
    return fig


def _shannon_index(values: list[float]) -> float:
    nums = [v for v in values if v > 0]
    total = sum(nums)
    if total <= 0:
        return 0.0
    return -sum((v / total) * math.log(v / total) for v in nums)


def shannon_diversity_figure(populations: dict[str, float]) -> go.Figure:
    """Gauge indicator for the Shannon diversity index H'.

    Range 0..~3 covers most realistic K-12 scenarios; we clip the gauge max
    at 3.5 so a small system doesn't look broken.
    """
    h = _shannon_index(list(populations.values()))
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=h,
        number=dict(font=dict(size=34, color="#1F3864"), valueformat=".2f"),
        title=dict(
            text="Shannon diversity (H′)",
            font=dict(size=14, color="#1F3864"),
        ),
        gauge=dict(
            axis=dict(range=[0, 3.5], tickwidth=1, tickcolor="#94A3B8"),
            bar=dict(color="#0EA5E9"),
            steps=[
                dict(range=[0, 1.0], color="#FEE2E2"),
                dict(range=[1.0, 2.0], color="#FEF3C7"),
                dict(range=[2.0, 3.5], color="#DCFCE7"),
            ],
            threshold=dict(line=dict(color="#1F3864", width=3), thickness=0.8, value=h),
        ),
    ))
    fig.update_layout(
        height=260,
        margin=dict(l=20, r=20, t=20, b=10),
    )
    return fig


def keystone_impact_figure(
    species_records: list[dict],
    initial_populations: dict[str, float],
    years: int,
    keystone_id: str,
    *,
    disturbance_year: int | None = None,
    climate_dT_C: float = 0.0,
    climate_dP_pct: float = 0.0,
    protect: dict[str, float] | None = None,
    hunt: dict[str, float] | None = None,
) -> go.Figure | None:
    """Side-by-side: scenario WITH the keystone vs scenario WITHOUT it.

    Returns None if the keystone isn't actually in the selection (caller
    should check and skip rendering).
    """
    if keystone_id not in initial_populations:
        return None

    t_with, pops_with = simulate_populations(
        species_records, initial_populations, years,
        disturbance_year=disturbance_year,
        climate_dT_C=climate_dT_C, climate_dP_pct=climate_dP_pct,
        protect=protect, hunt=hunt, seed=42,
    )
    without_records = [s for s in species_records if s["id"] != keystone_id]
    without_init = {k: v for k, v in initial_populations.items() if k != keystone_id}
    t_wo, pops_wo = simulate_populations(
        without_records, without_init, years,
        disturbance_year=disturbance_year,
        climate_dT_C=climate_dT_C, climate_dP_pct=climate_dP_pct,
        protect=protect, hunt=hunt, seed=42,
    )

    keystone_name = next(
        (s.get("common_name", keystone_id) for s in species_records if s["id"] == keystone_id),
        keystone_id,
    )

    fig = go.Figure()
    for s in species_records:
        sid = s["id"]
        color = TROPHIC_COLOR.get(s.get("trophic_level", "primary_consumer"), "#444")
        name = f"{s.get('emoji', '')} {s.get('common_name', sid)}"
        fig.add_trace(go.Scatter(
            x=t_with, y=pops_with[sid],
            mode="lines",
            name=f"{name} (with)",
            line=dict(width=2.2, color=color, shape="spline", smoothing=0.4),
            legendgroup=sid,
            xaxis="x", yaxis="y",
        ))
    for s in without_records:
        sid = s["id"]
        color = TROPHIC_COLOR.get(s.get("trophic_level", "primary_consumer"), "#444")
        name = f"{s.get('emoji', '')} {s.get('common_name', sid)}"
        fig.add_trace(go.Scatter(
            x=t_wo, y=pops_wo[sid],
            mode="lines",
            name=f"{name} (without)",
            line=dict(width=2.2, color=color, dash="dash", shape="spline", smoothing=0.4),
            legendgroup=sid, showlegend=False,
            xaxis="x2", yaxis="y2",
        ))

    fig.update_layout(
        title=dict(
            text=f"<b>Keystone impact:</b> with vs without <i>{keystone_name}</i>"
                 "<br><span style='font-size:0.78rem;color:#6B7280;'>"
                 "Left: full ecosystem · Right: same scenario, keystone removed.</span>",
            x=0.02, xanchor="left", y=0.97, yanchor="top",
            font=dict(size=15),
        ),
        xaxis=dict(domain=[0.0, 0.46], title="Years (with)"),
        yaxis=dict(title="Population", anchor="x"),
        xaxis2=dict(domain=[0.54, 1.0], title="Years (without)"),
        yaxis2=dict(anchor="x2", showticklabels=False),
        height=420,
        margin=dict(l=60, r=20, t=110, b=60),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.005, xanchor="left", x=0.0,
            font=dict(size=10),
        ),
        plot_bgcolor="#FAFBFC",
    )
    return fig


def climate_comparison_figure(
    species_records: list[dict],
    initial_populations: dict[str, float],
    years: int,
    *,
    climate_dT_C: float,
    climate_dP_pct: float,
    disturbance_year: int | None = None,
    protect: dict[str, float] | None = None,
    hunt: dict[str, float] | None = None,
) -> go.Figure:
    """Side-by-side: baseline climate (0,0) vs the user's chosen ΔT/ΔP."""
    t_base, pops_base = simulate_populations(
        species_records, initial_populations, years,
        disturbance_year=disturbance_year,
        climate_dT_C=0.0, climate_dP_pct=0.0,
        protect=protect, hunt=hunt, seed=42,
    )
    t_alt, pops_alt = simulate_populations(
        species_records, initial_populations, years,
        disturbance_year=disturbance_year,
        climate_dT_C=climate_dT_C, climate_dP_pct=climate_dP_pct,
        protect=protect, hunt=hunt, seed=42,
    )

    fig = go.Figure()
    for s in species_records:
        sid = s["id"]
        color = TROPHIC_COLOR.get(s.get("trophic_level", "primary_consumer"), "#444")
        name = f"{s.get('emoji', '')} {s.get('common_name', sid)}"
        fig.add_trace(go.Scatter(
            x=t_base, y=pops_base[sid], mode="lines",
            name=name,
            line=dict(width=2.0, color=color, shape="spline", smoothing=0.4),
            legendgroup=sid, xaxis="x", yaxis="y",
        ))
        fig.add_trace(go.Scatter(
            x=t_alt, y=pops_alt[sid], mode="lines",
            line=dict(width=2.0, color=color, dash="dot", shape="spline", smoothing=0.4),
            legendgroup=sid, showlegend=False,
            xaxis="x2", yaxis="y2",
        ))

    delta = f"ΔT = {climate_dT_C:+.1f} °C, Δprecip = {climate_dP_pct:+.0f}%"
    fig.update_layout(
        title=dict(
            text=f"<b>Climate comparison</b><br>"
                 "<span style='font-size:0.78rem;color:#6B7280;'>"
                 f"Left: present-day climate · Right: {delta}.</span>",
            x=0.02, xanchor="left", y=0.97, yanchor="top",
            font=dict(size=15),
        ),
        xaxis=dict(domain=[0.0, 0.46], title="Years (baseline)"),
        yaxis=dict(title="Population", anchor="x"),
        xaxis2=dict(domain=[0.54, 1.0], title="Years (adjusted)"),
        yaxis2=dict(anchor="x2", showticklabels=False),
        height=420,
        margin=dict(l=60, r=20, t=110, b=60),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.005, xanchor="left", x=0.0,
            font=dict(size=10),
        ),
        plot_bgcolor="#FAFBFC",
    )
    return fig
