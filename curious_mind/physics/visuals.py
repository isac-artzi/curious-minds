"""Plotly figure builders for the Physics Lab.

One function per scenario. Each consumes the dict returned by the matching
``simulators.py`` function plus a few input parameters needed for axes/labels.
"""

from __future__ import annotations

import math

import numpy as np
import plotly.graph_objects as go

NAVY = "#1F3864"
TEAL = "#2E5496"
AMBER = "#D97706"
GREEN = "#16A34A"
RED = "#DC2626"
PURPLE = "#7C3AED"
GRAY = "#5B6478"

# Per-disk palette for the multi-disk collision scenario (cycled by index).
DISK_COLORS = [TEAL, AMBER, "#16A34A", PURPLE, "#DB2777"]
SUB = "₁₂₃₄₅₆₇₈₉"  # subscript digits for m₁ … m₉ labels


# ---------------------------------------------------------------------------
# 1. Projectile
# ---------------------------------------------------------------------------
def projectile_figure(sim: dict, v0: float, angle_deg: float) -> go.Figure:
    """Trajectory + animated position marker."""
    xs = sim["trajectory_x"]
    ys = sim["trajectory_y"]
    rng = sim["range_m"]
    h_max = sim["max_height_m"]

    fig = go.Figure()
    # Static trajectory
    fig.add_trace(go.Scatter(
        x=xs, y=ys, mode="lines",
        line=dict(color=TEAL, width=3),
        name="Trajectory",
        hovertemplate="x = %{x:.1f} m<br>y = %{y:.1f} m<extra></extra>",
    ))
    # Apex marker
    if ys:
        i_max = int(np.argmax(ys))
        fig.add_trace(go.Scatter(
            x=[xs[i_max]], y=[ys[i_max]],
            mode="markers+text",
            marker=dict(size=10, color=AMBER, line=dict(color="white", width=2)),
            text=[f"  apex: {h_max:.1f} m"], textposition="top right",
            textfont=dict(size=11, color=NAVY),
            showlegend=False, hoverinfo="skip",
        ))
    # Landing marker
    fig.add_trace(go.Scatter(
        x=[rng], y=[0.0], mode="markers+text",
        marker=dict(size=10, color=RED, line=dict(color="white", width=2)),
        text=[f"  range: {rng:.1f} m"], textposition="top right",
        textfont=dict(size=11, color=NAVY),
        showlegend=False, hoverinfo="skip",
    ))

    # Animated frames — a moving ball along the path
    n = len(xs)
    stride = max(1, n // 40)
    indices = list(range(0, n, stride))
    if indices[-1] != n - 1:
        indices.append(n - 1)
    frames = []
    for i in indices:
        frames.append(go.Frame(
            data=[
                go.Scatter(x=xs, y=ys, mode="lines",
                           line=dict(color=TEAL, width=3)),
                go.Scatter(x=[xs[i]], y=[ys[i]], mode="markers",
                           marker=dict(size=14, color=NAVY,
                                       line=dict(color="white", width=2))),
            ],
            name=f"f{i}",
        ))
    # Insert ball trace into base data so frame[1] aligns with it
    fig.add_trace(go.Scatter(
        x=[xs[0]], y=[ys[0]], mode="markers",
        marker=dict(size=14, color=NAVY, line=dict(color="white", width=2)),
        name="Projectile", hoverinfo="skip",
    ))
    fig.frames = frames

    x_max = max(rng * 1.1, 1.0)
    y_max = max(h_max * 1.3, 1.0)
    fig.update_layout(
        title=dict(
            text=f"<b>Projectile trajectory</b><br>"
                 f"<span style='font-size:0.78rem;color:#6B7280;'>"
                 f"v₀ = {v0:.1f} m/s · θ = {angle_deg:.0f}°</span>",
            x=0.02, xanchor="left", y=0.97, yanchor="top",
            font=dict(size=15),
        ),
        xaxis=dict(title="Horizontal distance x (m)", range=[0, x_max]),
        yaxis=dict(title="Height y (m)", range=[0, y_max], scaleanchor=None),
        height=460,
        margin=dict(l=60, r=20, t=110, b=120),
        plot_bgcolor="#FAFBFC",
        showlegend=False,
        updatemenus=[dict(
            type="buttons", direction="left",
            x=0.0, xanchor="left", y=-0.22, yanchor="top",
            pad=dict(t=2, r=4), showactive=False,
            buttons=[
                dict(label="▶ Play", method="animate",
                     args=[None, dict(frame=dict(duration=60, redraw=True),
                                      fromcurrent=True, mode="immediate")]),
                dict(label="⏸ Pause", method="animate",
                     args=[[None], dict(frame=dict(duration=0, redraw=False),
                                        mode="immediate")]),
                dict(label="↺ Restart", method="animate",
                     args=[[frames[0].name], dict(frame=dict(duration=0, redraw=True),
                                                  mode="immediate")]),
            ],
        )],
    )
    return fig


# ---------------------------------------------------------------------------
# 2. Inclined plane
# ---------------------------------------------------------------------------
def incline_figure(sim: dict, angle_deg: float) -> go.Figure:
    """Free-body diagram on the slope (gravity, normal, friction, applied)."""
    theta = math.radians(angle_deg)
    # Right-triangle slope, length L on the hypotenuse, vertex at origin.
    # Vertices: bottom-left (0,0), bottom-right (base_x,0), top-left (0,base_y).
    # The hypotenuse goes from (0, base_y) DOWN to (base_x, 0) — block slides
    # along it to the lower-right.
    L = 6.0
    base_x = L * math.cos(theta)
    base_y = L * math.sin(theta)

    fig = go.Figure()
    # Filled triangle (close back to origin so the polygon is non-degenerate).
    fig.add_trace(go.Scatter(
        x=[0, base_x, 0, 0], y=[0, 0, base_y, 0],
        mode="lines", fill="toself",
        fillcolor="rgba(150,150,160,0.18)",
        line=dict(color=GRAY, width=2),
        showlegend=False, hoverinfo="skip",
    ))
    # Block sits partway along the hypotenuse. The hypotenuse direction (top → bottom)
    # is (sin θ, −cos θ); the outward normal is (cos θ, sin θ).
    # Parameterise the block's foot position by fraction `frac` along the hypotenuse.
    frac = 0.45
    foot_x = frac * base_x
    foot_y = base_y - frac * base_y
    nx, ny = math.sin(theta), math.cos(theta)   # outward normal (up-and-right)
    block = 0.4
    cx = foot_x + nx * block
    cy = foot_y + ny * block
    fig.add_trace(go.Scatter(
        x=[cx], y=[cy], mode="markers",
        marker=dict(size=26, color=NAVY, symbol="square",
                    line=dict(color="white", width=2)),
        showlegend=False, hoverinfo="skip",
    ))

    # Slope runs from (0, base_y) down to (base_x, 0), so the unit vector
    # pointing DOWN the slope is (base_x, -base_y) / L = (cos θ, -sin θ).
    down_x, down_y = math.cos(theta), -math.sin(theta)
    up_x, up_y = -down_x, -down_y

    f_friction = sim["friction_N"]
    f_applied = sim["f_applied_N"]

    # Each spec: (short_label, long_label, dx, dy, color, magnitude)
    # short_label is what's drawn near the block; long_label is shown via legend.
    arrow_specs = [
        ("W", "Weight (mg)", 0.0, -1.0, RED, sim["weight_N"]),
        ("N", "Normal", nx, ny, GREEN, sim["f_normal_N"]),
        ("f", "Friction",
         up_x if f_friction >= 0 else down_x,
         up_y if f_friction >= 0 else down_y,
         AMBER, abs(f_friction)),
        ("F", "Applied",
         up_x if f_applied >= 0 else down_x,
         up_y if f_applied >= 0 else down_y,
         PURPLE, abs(f_applied)),
    ]
    max_mag = max((m for _, _, _, _, _, m in arrow_specs), default=1.0) or 1.0
    arrow_len = 1.8   # plot units, for the largest force
    min_len = 1.0     # ensures small forces are still clearly visible

    annotations = []
    # Legend lines (top-right) so labels don't crowd the diagram.
    legend_lines = []
    for short_label, long_label, dx, dy, color, mag in arrow_specs:
        if mag <= 1e-9:
            continue
        # Square-root scaling compresses the dynamic range so a small force
        # next to a much larger one is still legible. Floor at min_len.
        scale = max(min_len, arrow_len * math.sqrt(mag / max_mag))
        tip_x = cx + dx * scale
        tip_y = cy + dy * scale
        # Arrow only — no inline text (text is in the legend box).
        annotations.append(dict(
            ax=cx, ay=cy, axref="x", ayref="y",
            x=tip_x, y=tip_y, xref="x", yref="y",
            showarrow=True, arrowhead=3, arrowsize=1.4,
            arrowwidth=2.4, arrowcolor=color,
        ))
        # Tiny label at the arrow tip, slightly past it.
        annotations.append(dict(
            x=tip_x + dx * 0.18, y=tip_y + dy * 0.18,
            xref="x", yref="y",
            text=f"<b>{short_label}</b>",
            showarrow=False,
            font=dict(size=12, color=color),
        ))
        legend_lines.append(
            f"<span style='color:{color}'><b>{short_label}</b> "
            f"{long_label}: {mag:.1f} N</span>"
        )

    # Compose a single legend annotation in the top-right corner.
    legend_text = "<br>".join(legend_lines)

    # Plot bounds — a bit of padding around the triangle and arrows.
    pad = arrow_len + 0.6
    x_lo = -pad
    x_hi = base_x + pad
    y_lo = -pad
    y_hi = base_y + pad

    fig.update_layout(
        title=dict(
            text=f"<b>Free-body diagram</b><br>"
                 f"<span style='font-size:0.78rem;color:#6B7280;'>"
                 f"Angle θ = {angle_deg:.0f}° · verdict: "
                 f"<b>{sim['verdict'].replace('_', ' ')}</b> · "
                 f"a = {sim['accel_m_s2']:+.2f} m/s²</span>",
            x=0.02, xanchor="left", y=0.97, yanchor="top",
            font=dict(size=15),
        ),
        xaxis=dict(visible=False, range=[x_lo, x_hi],
                   scaleanchor="y", scaleratio=1),
        yaxis=dict(visible=False, range=[y_lo, y_hi]),
        annotations=annotations + [dict(
            xref="paper", yref="paper",
            x=0.99, y=0.99, xanchor="right", yanchor="top",
            text=legend_text,
            showarrow=False,
            align="left",
            font=dict(size=11),
            bgcolor="rgba(255,255,255,0.92)",
            bordercolor=GRAY, borderwidth=1, borderpad=6,
        )],
        height=460,
        margin=dict(l=20, r=20, t=110, b=20),
        plot_bgcolor="#FAFBFC",
        showlegend=False,
    )
    return fig


# ---------------------------------------------------------------------------
# 3. Rollercoaster (energy conservation)
# ---------------------------------------------------------------------------
def rollercoaster_figure(sim: dict) -> go.Figure:
    """Track silhouette plus stacked PE / KE bars at each waypoint."""
    labels = sim["labels"]
    heights = sim["heights_m"]
    pe = sim["pe_J"]
    ke = sim["ke_J"]
    reachable = sim["reachable"]

    # Two-row subplot via single figure with two y-axes
    fig = go.Figure()
    # Track silhouette (smooth-ish line through hilltops)
    xs = list(range(len(heights)))
    fig.add_trace(go.Scatter(
        x=xs, y=heights, mode="lines+markers",
        line=dict(color=GRAY, width=3, shape="spline", smoothing=0.6),
        marker=dict(size=14,
                    color=[GREEN if r else RED for r in reachable],
                    line=dict(color="white", width=2)),
        name="Track height (m)",
        hovertemplate="<b>%{text}</b><br>h = %{y:.1f} m<extra></extra>",
        text=labels,
        yaxis="y",
    ))
    # PE bars
    fig.add_trace(go.Bar(
        x=labels, y=pe, name="Potential energy (J)",
        marker=dict(color=TEAL, opacity=0.55),
        yaxis="y2", offsetgroup="energy",
        hovertemplate="PE = %{y:.1f} J<extra></extra>",
    ))
    # KE bars (stacked alongside PE)
    fig.add_trace(go.Bar(
        x=labels, y=ke, name="Kinetic energy (J)",
        marker=dict(color=AMBER, opacity=0.85),
        yaxis="y2", offsetgroup="energy", base=pe,
        hovertemplate="KE = %{y:.1f} J<extra></extra>",
    ))

    fig.update_layout(
        title=dict(
            text="<b>Rollercoaster energy balance</b><br>"
                 "<span style='font-size:0.78rem;color:#6B7280;'>"
                 "Green dot = reachable, red dot = not enough energy. "
                 "PE + KE shrinks segment-by-segment from friction.</span>",
            x=0.02, xanchor="left", y=0.97, yanchor="top",
            font=dict(size=15),
        ),
        xaxis=dict(title="Waypoint"),
        yaxis=dict(title="Height (m)", side="left"),
        yaxis2=dict(title="Energy (J)", side="right", overlaying="y", showgrid=False),
        barmode="stack",
        height=480,
        margin=dict(l=60, r=60, t=110, b=60),
        plot_bgcolor="#FAFBFC",
        legend=dict(orientation="h", yanchor="bottom", y=1.005,
                    xanchor="left", x=0.0, font=dict(size=11)),
    )
    return fig


# ---------------------------------------------------------------------------
# 4. 2D collision (animated, true-radius disks, no pass-through)
# ---------------------------------------------------------------------------
def _circle_xy(cx: float, cy: float, r: float, n: int = 48) -> tuple[list[float], list[float]]:
    """Polygon points tracing a circle in DATA units (so the visual radius
    matches the physics radius, regardless of plot zoom)."""
    th = np.linspace(0.0, 2 * math.pi, n + 1)
    return (cx + r * np.cos(th)).tolist(), (cy + r * np.sin(th)).tolist()


def collision_2d_figure(sim: dict) -> go.Figure:
    """Top-view animation of N disks colliding inside a square plane.

    Consumes the dict returned by ``simulators.collision_multi``. The plane
    border is drawn as a bordered rectangle. Each disk is a real polygon
    circle (so visual size matches the collision radius) coloured from the
    ``DISK_COLORS`` palette, with a subscript m₁/m₂/… inside it. A red ★
    flashes at every disk-disk contact for ~6 frames. The legend below the
    chart lists the masses; axes are labelled x/z to make it clear this is
    a top view (gravity points into the page).
    """
    xs = sim["xs"]
    zs = sim["zs"]
    r = sim["r"]
    m = sim["m"]
    n = sim["n"]
    Lx = sim["plane_half_x"]
    Lz = sim["plane_half_z"]
    n_frames_total = len(xs[0])
    coll_events = sim.get("collision_events", [])
    flash_window = 6  # frames during which the contact flash is visible

    colors = [DISK_COLORS[i % len(DISK_COLORS)] for i in range(n)]

    pad = 0.4
    bound_x = Lx + pad
    bound_z = Lz + pad

    # Show up to ~240 frames so the animation stays smooth without bloating
    # the figure payload. Playback duration is matched to simulated time so
    # 20 s of physics plays back over ~20 s of wall-clock time.
    max_disp = 240
    stride = max(1, n_frames_total // max_disp)
    frame_idx = list(range(0, n_frames_total, stride))
    if frame_idx[-1] != n_frames_total - 1:
        frame_idx.append(n_frames_total - 1)
    sim_time_s = sim.get("dt", 0.04) * n_frames_total
    frame_duration_ms = max(20, min(200,
                                    int(sim_time_s * 1000 / max(1, len(frame_idx)))))

    def _flash_points(fi: int) -> tuple[list[float], list[float]]:
        """Midpoints of every collision pair active inside the flash window."""
        pxs, pys = [], []
        for fc, i, j in coll_events:
            if fc <= fi <= fc + flash_window:
                f = r[i] / (r[i] + r[j])
                pxs.append(xs[i][fi] + f * (xs[j][fi] - xs[i][fi]))
                pys.append(zs[i][fi] + f * (zs[j][fi] - zs[i][fi]))
        return pxs, pys

    def _mass_label_anns(fi: int) -> list[dict]:
        return [
            dict(x=xs[i][fi], y=zs[i][fi], xref="x", yref="y",
                 text=f"<b>m{SUB[i]}</b>", showarrow=False,
                 font=dict(size=16, color="white"))
            for i in range(n)
        ]

    # ------------- base traces (initial frame; legend lives here) ----------
    border_x = [-Lx, Lx, Lx, -Lx, -Lx]
    border_y = [-Lz, -Lz, Lz, Lz, -Lz]
    base_data: list[go.Scatter] = [
        go.Scatter(x=border_x, y=border_y, mode="lines",
                   line=dict(color="#374151", width=2),
                   fill="toself", fillcolor="rgba(241,245,249,0.65)",
                   hoverinfo="skip", showlegend=False, name="plane"),
    ]
    # Trails (one per disk).
    for i in range(n):
        base_data.append(go.Scatter(
            x=[xs[i][0]], y=[zs[i][0]], mode="lines",
            line=dict(color=colors[i], width=1.4, dash="dot"),
            hoverinfo="skip", showlegend=False,
        ))
    # Disks (filled polygons) — these are the legend entries.
    for i in range(n):
        cx, cy = _circle_xy(xs[i][0], zs[i][0], r[i])
        base_data.append(go.Scatter(
            x=cx, y=cy, mode="lines", fill="toself",
            fillcolor=colors[i], line=dict(color="white", width=2),
            name=f"m{SUB[i]} = {m[i]:.1f} kg",
            hoverinfo="skip", showlegend=True,
        ))
    fxs0, fys0 = _flash_points(0)
    base_data.append(go.Scatter(
        x=fxs0, y=fys0, mode="markers",
        marker=dict(size=20, color=RED, symbol="star",
                    line=dict(color="white", width=2)),
        hoverinfo="skip", showlegend=False,
    ))

    # ------------- animation frames ----------------------------------------
    frames = []
    for fi in frame_idx:
        data_list = [
            go.Scatter(x=border_x, y=border_y, mode="lines",
                       line=dict(color="#374151", width=2),
                       fill="toself", fillcolor="rgba(241,245,249,0.65)"),
        ]
        for i in range(n):
            data_list.append(go.Scatter(
                x=xs[i][: fi + 1], y=zs[i][: fi + 1], mode="lines",
                line=dict(color=colors[i], width=1.4, dash="dot"),
            ))
        for i in range(n):
            cx, cy = _circle_xy(xs[i][fi], zs[i][fi], r[i])
            data_list.append(go.Scatter(
                x=cx, y=cy, mode="lines", fill="toself",
                fillcolor=colors[i], line=dict(color="white", width=2),
            ))
        flxs, flys = _flash_points(fi)
        data_list.append(go.Scatter(
            x=flxs, y=flys, mode="markers",
            marker=dict(size=20, color=RED, symbol="star",
                        line=dict(color="white", width=2)),
        ))
        frames.append(go.Frame(
            data=data_list,
            layout=go.Layout(annotations=_mass_label_anns(fi)),
            name=f"f{fi}",
        ))

    fig = go.Figure(data=base_data, frames=frames)

    n_coll = sim.get("n_collisions", 0)
    n_wall = sim.get("n_wall_hits", 0)
    sub = (
        f"Top view (gravity points into the page) · {n} disks · "
        f"{n_coll} disk-disk collisions · {n_wall} wall hits"
    )
    if sim.get("plastic"):
        sub += " · plastic — pairs stick on contact"
    elif sim.get("restitution") is not None:
        sub += f" · restitution e = {sim['restitution']:.2f}"
    if sim.get("mu_k", 0.0) > 0:
        sub += f" · μₖ = {sim['mu_k']:.2f}"

    fig.update_layout(
        title=dict(
            text="<b>2-D collisions on a bounded plane</b><br>"
                 f"<span style='font-size:0.78rem;color:#6B7280;'>{sub}</span>",
            x=0.02, xanchor="left", y=0.97, yanchor="top",
            font=dict(size=15),
        ),
        annotations=_mass_label_anns(0),
        xaxis=dict(title="x (m)", range=[-bound_x, bound_x], zeroline=False,
                   scaleanchor="y", scaleratio=1, showgrid=False),
        yaxis=dict(title="z (m)", range=[-bound_z, bound_z], zeroline=False,
                   showgrid=False),
        height=540,
        margin=dict(l=60, r=20, t=110, b=140),
        plot_bgcolor="#FAFBFC",
        showlegend=True,
        legend=dict(
            orientation="h", yanchor="top", y=-0.16,
            xanchor="center", x=0.5,
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="#CBD5E1", borderwidth=1,
            font=dict(size=11),
            itemsizing="constant",
        ),
        updatemenus=[dict(
            type="buttons", direction="left",
            x=0.0, xanchor="left", y=-0.30, yanchor="top",
            pad=dict(t=2, r=4), showactive=False,
            buttons=[
                dict(label="▶ Play", method="animate",
                     args=[None, dict(frame=dict(duration=frame_duration_ms, redraw=True),
                                      fromcurrent=True, mode="immediate")]),
                dict(label="⏸ Pause", method="animate",
                     args=[[None], dict(frame=dict(duration=0, redraw=False),
                                        mode="immediate")]),
                dict(label="↺ Restart", method="animate",
                     args=[[frames[0].name], dict(frame=dict(duration=0, redraw=True),
                                                  mode="immediate")]),
            ],
        )],
    )
    return fig


def collision_momentum_figure(sim: dict) -> go.Figure:
    """BEFORE / AFTER head-to-tail momentum diagrams for N disks.

    Each panel chains the per-disk momentum vectors p_i = m_i · v_i tip-to-tail
    (colour-matched to the disk in the 2-D plot). The NAVY arrow drawn from
    the origin to the chain's end is the total momentum p = Σ p_i.

    With no friction and no wall hits the navy arrow is identical in both
    panels — momentum is conserved. With walls or friction the navy arrow
    can change; the page caller adds an explainer when that happens.
    """
    n = sim["n"]
    m = sim["m"]
    v_before = sim["v_before"]
    v_after = sim["v_after"]

    p_before = [(m[i] * v_before[i][0], m[i] * v_before[i][1]) for i in range(n)]
    p_after  = [(m[i] * v_after[i][0],  m[i] * v_after[i][1])  for i in range(n)]
    p_tot_b = (sum(p[0] for p in p_before), sum(p[1] for p in p_before))
    p_tot_a = sim["p_after"]

    colors = [DISK_COLORS[i % len(DISK_COLORS)] for i in range(n)]

    def _chain_pts(plist):
        pts = [(0.0, 0.0)]
        cx, cy = 0.0, 0.0
        for p in plist:
            cx += p[0]
            cy += p[1]
            pts.append((cx, cy))
        return pts
    all_pts = (_chain_pts(p_before) + _chain_pts(p_after) +
               [p_tot_b, p_tot_a])
    max_abs = max((abs(c) for pt in all_pts for c in pt), default=1.0) or 1.0
    lim = max_abs * 1.18

    def _build_panel(plist, ptot, axis_id, yaxis_id, panel_x_paper):
        traces = [go.Scatter(
            x=[0], y=[0], mode="markers",
            marker=dict(size=7, color=GRAY),
            xaxis=axis_id, yaxis=yaxis_id,
            showlegend=False, hoverinfo="skip",
        )]
        anns: list[dict] = []

        # Total arrow underneath as the wide base.
        if math.hypot(*ptot) > 1e-9:
            anns.append(dict(
                ax=0, ay=0, x=ptot[0], y=ptot[1],
                xref=axis_id, yref=yaxis_id,
                axref=axis_id, ayref=yaxis_id,
                showarrow=True, arrowhead=2,
                arrowsize=0.9, arrowwidth=3.4,
                arrowcolor=NAVY, opacity=1.0,
            ))

        # Head-to-tail per-disk arrows.
        cur = (0.0, 0.0)
        for i, p in enumerate(plist):
            end = (cur[0] + p[0], cur[1] + p[1])
            if math.hypot(p[0], p[1]) > 1e-9:
                anns.append(dict(
                    ax=cur[0], ay=cur[1], x=end[0], y=end[1],
                    xref=axis_id, yref=yaxis_id,
                    axref=axis_id, ayref=yaxis_id,
                    showarrow=True, arrowhead=2,
                    arrowsize=0.9, arrowwidth=2.0,
                    arrowcolor=colors[i], opacity=0.95,
                ))
            cur = end

        # Numeric legend (compact monospace block in panel's bottom-left).
        rows = []
        for i, p in enumerate(plist):
            rows.append(
                f"<span style='color:{colors[i]}'><b>p{SUB[i]}</b></span> "
                f"({p[0]:+.2f}, {p[1]:+.2f})  |p{SUB[i]}| = {math.hypot(*p):.2f}"
            )
        rows.append(
            f"<span style='color:{NAVY}'><b>p_tot</b></span> "
            f"({ptot[0]:+.2f}, {ptot[1]:+.2f})  |p| = {math.hypot(*ptot):.2f}"
        )
        anns.append(dict(
            xref="paper", yref="paper",
            x=panel_x_paper, y=0.02,
            xanchor="left", yanchor="bottom",
            text="<br>".join(rows), showarrow=False,
            align="left",
            font=dict(size=10, family="JetBrains Mono, monospace"),
            bgcolor="rgba(255,255,255,0.92)",
            bordercolor=GRAY, borderwidth=1, borderpad=5,
        ))
        return traces, anns

    traces_b, anns_b = _build_panel(p_before, p_tot_b, "x",  "y",  0.01)
    traces_a, anns_a = _build_panel(p_after,  p_tot_a, "x2", "y2", 0.55)

    cons_msg = (
        "The navy arrow is <b>identical</b> in both panels — momentum is conserved."
        if sim.get("momentum_conserved", False)
        else "The navy arrow <b>changes</b> because walls and/or friction "
             "exert outside forces on the system."
    )

    fig = go.Figure(data=traces_b + traces_a)
    fig.update_layout(
        title=dict(
            text="<b>Conservation of momentum — before vs after</b><br>"
                 f"<span style='font-size:0.78rem;color:#6B7280;'>"
                 f"Coloured arrows are each disk's momentum p_i = m_i · v_i, "
                 f"chained head-to-tail. Navy = total. {cons_msg}</span>",
            x=0.02, xanchor="left", y=0.97, yanchor="top",
            font=dict(size=15),
        ),
        xaxis=dict(domain=[0.0, 0.46], range=[-lim, lim],
                   title="pₓ (kg·m/s)", zeroline=True, zerolinecolor="#94A3B8",
                   zerolinewidth=1, gridcolor="#E5E7EB"),
        yaxis=dict(range=[-lim, lim], title="p_z (kg·m/s)",
                   scaleanchor="x", scaleratio=1,
                   zeroline=True, zerolinecolor="#94A3B8",
                   zerolinewidth=1, gridcolor="#E5E7EB"),
        xaxis2=dict(domain=[0.54, 1.0], range=[-lim, lim],
                    title="pₓ (kg·m/s)", zeroline=True, zerolinecolor="#94A3B8",
                    zerolinewidth=1, gridcolor="#E5E7EB",
                    anchor="y2"),
        yaxis2=dict(range=[-lim, lim], title="p_z (kg·m/s)",
                    scaleanchor="x2", scaleratio=1,
                    zeroline=True, zerolinecolor="#94A3B8",
                    zerolinewidth=1, gridcolor="#E5E7EB",
                    anchor="x2"),
        annotations=anns_b + anns_a + [
            dict(text="<b>BEFORE</b>", xref="paper", yref="paper",
                 x=0.23, y=1.04, xanchor="center", showarrow=False,
                 font=dict(size=12, color=NAVY)),
            dict(text="<b>AFTER</b>", xref="paper", yref="paper",
                 x=0.77, y=1.04, xanchor="center", showarrow=False,
                 font=dict(size=12, color=NAVY)),
        ],
        height=540,
        margin=dict(l=60, r=20, t=140, b=60),
        plot_bgcolor="#FAFBFC",
        showlegend=False,
    )
    return fig


def collision_energy_figure(sim: dict) -> go.Figure:
    """Stacked KE bars (per-disk) BEFORE vs AFTER, plus the amber 'lost' wedge.

    Each colour shows one disk's share of the kinetic energy. The amber
    pattern on the AFTER bar is energy that left kinetic motion — to disk-
    deformation heat in inelastic collisions, plus friction with the plane.
    The two bars have identical total height only when energy is conserved
    (elastic collisions + frictionless plane).
    """
    n = sim["n"]
    m = sim["m"]
    v_before = sim["v_before"]
    v_after = sim["v_after"]
    ke_i_b = [0.5 * m[i] * (v_before[i][0] ** 2 + v_before[i][1] ** 2) for i in range(n)]
    ke_i_a = [0.5 * m[i] * (v_after[i][0]  ** 2 + v_after[i][1]  ** 2) for i in range(n)]
    colors = [DISK_COLORS[i % len(DISK_COLORS)] for i in range(n)]
    ke_total_b = sum(ke_i_b)
    ke_total_a = sum(ke_i_a)
    ke_lost = max(0.0, ke_total_b - ke_total_a)

    fig = go.Figure()
    for i in range(n):
        fig.add_trace(go.Bar(
            x=["Before", "After"], y=[ke_i_b[i], ke_i_a[i]],
            name=f"KE m{SUB[i]}",
            marker=dict(color=colors[i]),
            text=[f"{ke_i_b[i]:.1f}",
                  f"{ke_i_a[i]:.1f}" if ke_i_a[i] > 1e-2 else ""],
            textposition="inside",
            textfont=dict(color="white", size=11),
            hovertemplate=f"m{SUB[i]} KE = " + "%{y:.2f} J<extra></extra>",
        ))
    fig.add_trace(go.Bar(
        x=["Before", "After"], y=[0.0, ke_lost],
        name="Lost (heat / sound / friction)",
        marker=dict(color=AMBER, pattern=dict(shape="/", size=6, solidity=0.4)),
        text=["", f"{ke_lost:.2f}" if ke_lost > 1e-6 else ""],
        textposition="inside",
        textfont=dict(color="white", size=11),
        hovertemplate="Lost = %{y:.2f} J<extra></extra>",
    ))

    fig.update_layout(
        title=dict(
            text="<b>Kinetic energy budget</b><br>"
                 "<span style='font-size:0.78rem;color:#6B7280;'>"
                 "Each colour = that disk's KE share. The amber portion is "
                 "energy that left the kinetic account (deformation, sound, "
                 "friction with the plane).</span>",
            x=0.02, xanchor="left", y=0.97, yanchor="top",
            font=dict(size=15),
        ),
        barmode="stack",
        yaxis=dict(title="Kinetic energy (J)"),
        height=380,
        margin=dict(l=60, r=20, t=110, b=40),
        plot_bgcolor="#FAFBFC",
        legend=dict(orientation="h", yanchor="bottom", y=1.005,
                    xanchor="left", x=0.0, font=dict(size=10)),
    )
    return fig


# ---------------------------------------------------------------------------
# 5. Spring SHM
# ---------------------------------------------------------------------------
def _spring_zigzag(x_left: float, x_right: float,
                   n_coils: int = 12, amp: float = 0.10) -> tuple[list, list]:
    """Return (xs, ys) for a zigzag polyline that looks like a coil spring."""
    n = n_coils * 2 + 2  # 2 endpoints + interior zigzag
    xs = np.linspace(x_left, x_right, n)
    ys = np.zeros(n)
    for i in range(1, n - 1):
        ys[i] = amp if i % 2 == 0 else -amp
    return xs.tolist(), ys.tolist()


def _block_polygon(cx: float, w: float, h: float) -> tuple[list, list]:
    hw, hh = w / 2.0, h / 2.0
    return ([cx - hw, cx + hw, cx + hw, cx - hw, cx - hw],
            [-hh, -hh, hh, hh, -hh])


def spring_figure(sim: dict, m: float, k: float) -> go.Figure:
    """Combined animated SHM scene: sliding mass + synced x/v/a curves +
    KE/PE bars. Play / Pause / Restart + frame slider."""
    from plotly.subplots import make_subplots

    t_full = np.asarray(sim["t"], dtype=float)
    x_full = np.asarray(sim["x"], dtype=float)
    v_full = np.asarray(sim["v"], dtype=float)
    a_full = np.asarray(sim["a"], dtype=float)
    ke_full = np.asarray(sim["ke"], dtype=float)
    pe_full = np.asarray(sim["pe"], dtype=float)
    period = float(sim["period_s"])
    amp = float(sim["amplitude_m"])
    omega = float(sim["omega"])
    total_E = float(ke_full[0] + pe_full[0]) if len(ke_full) else 0.0

    # Degenerate case (k or m = 0)
    if not np.isfinite(period) or period <= 0 or not np.isfinite(amp):
        fig = go.Figure()
        fig.add_annotation(
            text="Invalid SHM parameters (k or m = 0). Period would be infinite.",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=14, color=RED),
        )
        fig.update_layout(height=420, plot_bgcolor="#FAFBFC")
        return fig

    # Animate over ~2 periods (or whole sim if shorter)
    t_anim_max = float(min(2.0 * period, t_full[-1]))
    n_frames = 120
    frame_times = np.linspace(0.0, t_anim_max, n_frames)
    x_f = np.interp(frame_times, t_full, x_full)
    v_f = np.interp(frame_times, t_full, v_full)
    ke_f = 0.5 * m * v_f * v_f
    pe_f = 0.5 * k * x_f * x_f

    # Real-time playback (≈ wall-clock = simulated time, capped 20–80 ms/frame)
    frame_duration_ms = max(20, min(80, int(t_anim_max * 1000 / max(1, n_frames))))

    # --- Geometry for the spring scene ---
    A_disp = max(amp, 0.05)
    wall_x = -A_disp - 0.6
    block_w = max(0.18, 0.18 * (2 * A_disp + 0.6))
    block_h = 0.6
    scene_x_min = wall_x - 0.1
    scene_x_max = A_disp + 0.6
    scene_y_min, scene_y_max = -0.55, 0.55

    fig = make_subplots(
        rows=2, cols=2,
        specs=[[{"type": "xy"}, {"type": "xy"}],
               [{"type": "xy", "colspan": 2}, None]],
        column_widths=[0.46, 0.54],
        row_heights=[0.62, 0.38],
        horizontal_spacing=0.09, vertical_spacing=0.20,
        subplot_titles=(
            "Mass-on-spring (top view)",
            "x(t), v(t), a(t)  —  red line = current time",
            "Energy partition  —  KE + PE = total (constant, no friction)",
        ),
    )

    # ---- Subplot 1: spring scene ----
    # 0: amplitude band (static)
    fig.add_trace(go.Scatter(
        x=[-amp, amp, amp, -amp, -amp],
        y=[scene_y_min * 0.55, scene_y_min * 0.55,
           scene_y_max * 0.55, scene_y_max * 0.55, scene_y_min * 0.55],
        mode="lines", fill="toself",
        line=dict(color="rgba(46,84,150,0)"),
        fillcolor="rgba(46,84,150,0.08)",
        hoverinfo="skip", showlegend=False, name="amplitude",
    ), row=1, col=1)
    # 1: equilibrium dashed line (static)
    fig.add_trace(go.Scatter(
        x=[0, 0], y=[scene_y_min, scene_y_max],
        mode="lines", line=dict(color=GRAY, dash="dot", width=1.4),
        hoverinfo="skip", showlegend=False, name="equilibrium",
    ), row=1, col=1)
    # 2: wall (static)
    fig.add_trace(go.Scatter(
        x=[wall_x, wall_x], y=[scene_y_min, scene_y_max],
        mode="lines", line=dict(color=NAVY, width=5),
        hoverinfo="skip", showlegend=False, name="wall",
    ), row=1, col=1)
    # 3: spring (animated)
    sx0, sy0 = _spring_zigzag(wall_x, x_f[0] - block_w / 2)
    fig.add_trace(go.Scatter(
        x=sx0, y=sy0, mode="lines",
        line=dict(color=AMBER, width=2.2),
        hoverinfo="skip", showlegend=False, name="spring",
    ), row=1, col=1)
    # 4: block (animated)
    bx0, by0 = _block_polygon(x_f[0], block_w, block_h)
    fig.add_trace(go.Scatter(
        x=bx0, y=by0, mode="lines", fill="toself",
        line=dict(color=NAVY, width=2),
        fillcolor=TEAL,
        hoverinfo="skip", showlegend=False, name="block",
    ), row=1, col=1)

    # ---- Subplot 2: x/v/a curves ----
    mask = t_full <= t_anim_max + 1e-9
    t_disp = t_full[mask]
    x_disp = x_full[mask]
    v_disp = v_full[mask]
    a_disp = a_full[mask]
    # 5: x(t)
    fig.add_trace(go.Scatter(
        x=t_disp, y=x_disp, mode="lines",
        name="x (m)", line=dict(color=NAVY, width=2.4),
    ), row=1, col=2)
    # 6: v(t)
    fig.add_trace(go.Scatter(
        x=t_disp, y=v_disp, mode="lines",
        name="v (m/s)", line=dict(color=TEAL, width=2.0, dash="dash"),
    ), row=1, col=2)
    # 7: a(t)
    fig.add_trace(go.Scatter(
        x=t_disp, y=a_disp, mode="lines",
        name="a (m/s²)", line=dict(color=AMBER, width=2.0, dash="dot"),
    ), row=1, col=2)
    # 8: time cursor (animated)
    cy_min = float(min(x_disp.min(), v_disp.min(), a_disp.min()))
    cy_max = float(max(x_disp.max(), v_disp.max(), a_disp.max()))
    pad = 0.06 * (cy_max - cy_min + 1e-9)
    cursor_y = [cy_min - pad, cy_max + pad]
    fig.add_trace(go.Scatter(
        x=[0, 0], y=cursor_y, mode="lines",
        line=dict(color=RED, width=1.8),
        hoverinfo="skip", showlegend=False, name="t-cursor",
    ), row=1, col=2)

    # ---- Subplot 3: KE/PE bars (animated) ----
    bar_labels = ["Kinetic (½ m v²)", "Potential (½ k x²)", "Total"]
    # 9: bars
    fig.add_trace(go.Bar(
        x=bar_labels,
        y=[ke_f[0], pe_f[0], total_E],
        marker=dict(color=[AMBER, TEAL, NAVY]),
        text=[f"{ke_f[0]:.3f} J", f"{pe_f[0]:.3f} J", f"{total_E:.3f} J"],
        textposition="outside",
        showlegend=False, name="energy",
    ), row=2, col=1)

    # ---- Frames ----
    frames = []
    for i, t_i in enumerate(frame_times):
        sx, sy = _spring_zigzag(wall_x, x_f[i] - block_w / 2)
        bx_i, by_i = _block_polygon(x_f[i], block_w, block_h)
        frames.append(go.Frame(
            name=f"f{i}",
            data=[
                go.Scatter(x=sx, y=sy),                       # → trace 3
                go.Scatter(x=bx_i, y=by_i),                   # → trace 4
                go.Scatter(x=[t_i, t_i], y=cursor_y),         # → trace 8
                go.Bar(
                    x=bar_labels,
                    y=[ke_f[i], pe_f[i], total_E],
                    text=[f"{ke_f[i]:.3f} J",
                          f"{pe_f[i]:.3f} J",
                          f"{total_E:.3f} J"],
                ),                                            # → trace 9
            ],
            traces=[3, 4, 8, 9],
        ))
    fig.frames = frames

    # ---- Axes ----
    fig.update_xaxes(range=[scene_x_min, scene_x_max],
                     title_text="x (m)", row=1, col=1, zeroline=False)
    fig.update_yaxes(range=[scene_y_min, scene_y_max],
                     showticklabels=False, row=1, col=1, zeroline=False)
    fig.update_xaxes(range=[0, t_anim_max], title_text="time (s)", row=1, col=2)
    fig.update_yaxes(title_text="x / v / a", row=1, col=2)
    fig.update_yaxes(title_text="Energy (J)",
                     range=[0, total_E * 1.30 + 0.001], row=2, col=1)

    # ---- Slider steps ----
    slider_steps = []
    for i, t_i in enumerate(frame_times):
        slider_steps.append(dict(
            method="animate",
            label=f"{t_i:.2f}",
            args=[[f"f{i}"], dict(mode="immediate",
                                  frame=dict(duration=0, redraw=True),
                                  transition=dict(duration=0))],
        ))

    fig.update_layout(
        height=640,
        margin=dict(l=60, r=20, t=90, b=90),
        plot_bgcolor="#FAFBFC",
        title=dict(
            text=f"<b>Simple harmonic motion — animated</b><br>"
                 f"<span style='font-size:0.78rem;color:#6B7280;'>"
                 f"T = {period:.3f} s · ω = {omega:.2f} rad/s · "
                 f"amplitude = {amp:.3f} m · total E = {total_E:.3f} J · "
                 f"playing {t_anim_max:.2f} s ≈ "
                 f"{t_anim_max / period:.1f} periods</span>",
            x=0.02, xanchor="left", y=0.985, yanchor="top",
            font=dict(size=15),
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1.0, font=dict(size=11)),
        bargap=0.45,
        updatemenus=[dict(
            type="buttons", direction="left",
            x=0.02, y=-0.04, xanchor="left", yanchor="top",
            pad=dict(t=8, r=8), showactive=False,
            buttons=[
                dict(label="▶ Play", method="animate",
                     args=[None, dict(frame=dict(duration=frame_duration_ms,
                                                 redraw=True),
                                      fromcurrent=True, mode="immediate",
                                      transition=dict(duration=0))]),
                dict(label="⏸ Pause", method="animate",
                     args=[[None], dict(frame=dict(duration=0, redraw=False),
                                        mode="immediate",
                                        transition=dict(duration=0))]),
                dict(label="⏮ Restart", method="animate",
                     args=[["f0"], dict(frame=dict(duration=0, redraw=True),
                                        mode="immediate",
                                        transition=dict(duration=0))]),
            ],
        )],
        sliders=[dict(
            active=0, x=0.16, y=-0.02, len=0.80,
            xanchor="left", yanchor="top",
            currentvalue=dict(prefix="t = ", suffix=" s",
                              font=dict(size=12, color=NAVY)),
            steps=slider_steps,
            pad=dict(t=8, b=10),
        )],
    )
    return fig


# ---------------------------------------------------------------------------
# 6. Photoelectric effect
# ---------------------------------------------------------------------------
def _freq_to_visible_color(f_Hz: float) -> str:
    """Approximate hex color for a given light frequency (visible / UV range)."""
    if f_Hz < 4.05e14:
        return "#7F1D1D"  # IR / deep red
    if f_Hz < 4.80e14:
        return "#DC2626"  # red
    if f_Hz < 5.10e14:
        return "#F59E0B"  # orange / yellow
    if f_Hz < 5.70e14:
        return "#16A34A"  # green
    if f_Hz < 6.40e14:
        return "#2563EB"  # blue
    if f_Hz < 7.50e14:
        return "#7C3AED"  # violet
    return "#4C1D95"      # UV (deep violet)


def photoelectric_animation(sim: dict, freq_hz: float, phi_eV: float,
                            intensity_rel: float) -> go.Figure:
    """Animated photoelectric scene: photons stream into a metal slab; if
    hf ≥ φ, electrons fly out the other side. Includes status banner and a
    photon-energy / φ / KE_max bar comparison."""
    from plotly.subplots import make_subplots

    metal_x_left, metal_x_right = 2.0, 5.0
    metal_y_bot, metal_y_top = -1.4, 1.4
    scene_x_min, scene_x_max = -6.0, 5.0
    scene_y_min, scene_y_max = -2.0, 2.2

    n_frames = 120
    photon_color = _freq_to_visible_color(freq_hz)
    photon_eV = float(sim["photon_eV"])
    ke_max_eV = float(sim["ke_max_eV"])
    emits = bool(sim["emits_electrons"])

    # Number of photons in flight ≈ intensity (cap at 8 lanes)
    if intensity_rel <= 0.0:
        n_photons = 0
    else:
        n_photons = max(1, min(8, int(round(intensity_rel * 3))))

    # Photon kinematics
    photon_speed = 0.20  # plot-units per frame
    photon_distance = metal_x_left - scene_x_min  # 8.0 units
    photon_period = max(1, int(round(photon_distance / photon_speed)))  # ≈ 40

    # Lane y-positions (vertical fan-out)
    if n_photons > 0:
        lanes = np.linspace(metal_y_bot * 0.75, metal_y_top * 0.75, n_photons)
    else:
        lanes = np.array([])

    # Photon positions per frame + arrival events
    photon_xs_per_frame: list[list] = []
    photon_ys_per_frame: list[list] = []
    arrival_events: list[tuple[int, float]] = []  # (frame, lane_y)
    for f_idx in range(n_frames):
        xs, ys = [], []
        for i in range(n_photons):
            phase = (i * photon_period // max(n_photons, 1) + f_idx) % photon_period
            x = scene_x_min + phase * photon_speed
            xs.append(x)
            ys.append(float(lanes[i]))
            if phase == photon_period - 1:
                arrival_events.append((f_idx + 1, float(lanes[i])))
        photon_xs_per_frame.append(xs)
        photon_ys_per_frame.append(ys)

    # Electron speed scales with √KE_max (visual only, capped)
    e_speed = max(0.08, min(0.35, math.sqrt(max(ke_max_eV, 0.01)) * 0.20))

    electron_events = arrival_events if emits else []

    electron_xs_per_frame: list[list] = []
    electron_ys_per_frame: list[list] = []
    for f_idx in range(n_frames):
        xs, ys = [], []
        for (start_f, lane_y) in electron_events:
            if f_idx < start_f:
                continue
            x = metal_x_left - (f_idx - start_f) * e_speed
            if x < scene_x_min - 0.4:
                continue
            xs.append(x)
            ys.append(lane_y)
        electron_xs_per_frame.append(xs)
        electron_ys_per_frame.append(ys)

    # Status banner
    if intensity_rel <= 0.0:
        status_txt = "INTENSITY = 0  —  no light, no photons"
        status_color = GRAY
    elif not emits:
        status_txt = (f"BELOW THRESHOLD  —  hf = {photon_eV:.2f} eV "
                      f"&lt; φ = {phi_eV:.2f} eV  —  no electrons emitted "
                      f"(intensity does not help)")
        status_color = RED
    else:
        status_txt = (f"EMITTING  —  KE_max = {ke_max_eV:.2f} eV per electron  "
                      f"·  current ∝ intensity")
        status_color = GREEN

    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[0.66, 0.34],
        vertical_spacing=0.20,
        subplot_titles=(
            "",
            "Energy bookkeeping  —  hf, φ, and KE_max = hf − φ",
        ),
    )

    # ---- Row 1: scene ----
    # 0: metal slab (filled rectangle)
    fig.add_trace(go.Scatter(
        x=[metal_x_left, metal_x_right, metal_x_right, metal_x_left, metal_x_left],
        y=[metal_y_bot, metal_y_bot, metal_y_top, metal_y_top, metal_y_bot],
        mode="lines", fill="toself",
        fillcolor="rgba(91,100,120,0.35)",
        line=dict(color=NAVY, width=2),
        hoverinfo="skip", showlegend=False, name="metal target",
    ), row=1, col=1)

    # 1: bound electrons (lattice inside slab)
    bx, by = [], []
    for r in np.linspace(metal_y_bot + 0.35, metal_y_top - 0.35, 4):
        for c in np.linspace(metal_x_left + 0.4, metal_x_right - 0.4, 5):
            bx.append(float(c))
            by.append(float(r))
    fig.add_trace(go.Scatter(
        x=bx, y=by, mode="markers",
        marker=dict(size=8, color=NAVY, line=dict(color="white", width=1)),
        hoverinfo="skip", showlegend=False, name="bound electrons",
    ), row=1, col=1)

    # 2: photons (animated)
    fig.add_trace(go.Scatter(
        x=photon_xs_per_frame[0] if n_frames else [],
        y=photon_ys_per_frame[0] if n_frames else [],
        mode="markers",
        marker=dict(size=14, color=photon_color, symbol="diamond",
                    line=dict(color="white", width=1.5)),
        name=f"photon  ·  hf = {photon_eV:.2f} eV",
        showlegend=True,
    ), row=1, col=1)

    # 3: ejected electrons (animated)
    fig.add_trace(go.Scatter(
        x=electron_xs_per_frame[0] if n_frames else [],
        y=electron_ys_per_frame[0] if n_frames else [],
        mode="markers",
        marker=dict(size=11, color=AMBER, symbol="circle",
                    line=dict(color="white", width=1.5)),
        name=(f"ejected electron  ·  KE_max = {ke_max_eV:.2f} eV"
              if emits else "ejected electron (none)"),
        showlegend=True,
    ), row=1, col=1)

    # Slab annotation
    fig.add_annotation(
        text="Metal target", xref="x1", yref="y1",
        x=(metal_x_left + metal_x_right) / 2, y=metal_y_top + 0.30,
        showarrow=False, font=dict(size=12, color=NAVY),
    )
    # Status banner
    fig.add_annotation(
        text=f"<b>{status_txt}</b>",
        xref="x domain", yref="y domain",
        x=0.5, y=1.02, xanchor="center", yanchor="bottom",
        showarrow=False, font=dict(size=12, color=status_color),
        bgcolor="white", bordercolor=status_color, borderwidth=1, borderpad=4,
    )

    # ---- Row 2: energy bars ----
    bar_color_ke = GREEN if emits else RED
    fig.add_trace(go.Bar(
        x=["Photon energy (hf)", "Work function (φ)", "KE_max (hf − φ)"],
        y=[photon_eV, phi_eV, max(0.0, photon_eV - phi_eV)],
        marker=dict(color=[photon_color, GRAY, bar_color_ke]),
        text=[f"{photon_eV:.2f} eV",
              f"{phi_eV:.2f} eV",
              f"{max(0.0, photon_eV - phi_eV):.2f} eV"],
        textposition="outside",
        showlegend=False, name="energy",
    ), row=2, col=1)

    # ---- Frames ----
    frames = []
    for i in range(n_frames):
        frames.append(go.Frame(
            name=f"f{i}",
            data=[
                go.Scatter(x=photon_xs_per_frame[i], y=photon_ys_per_frame[i]),
                go.Scatter(x=electron_xs_per_frame[i], y=electron_ys_per_frame[i]),
            ],
            traces=[2, 3],
        ))
    fig.frames = frames

    # ---- Axes ----
    fig.update_xaxes(range=[scene_x_min, scene_x_max], visible=False, row=1, col=1)
    fig.update_yaxes(range=[scene_y_min, scene_y_max], visible=False, row=1, col=1)
    bar_max = max(photon_eV, phi_eV, max(0.0, photon_eV - phi_eV)) * 1.30 + 0.05
    fig.update_yaxes(title_text="Energy (eV)", range=[0, bar_max], row=2, col=1)

    # ---- Slider ----
    slider_steps = []
    for i in range(n_frames):
        slider_steps.append(dict(
            method="animate", label=str(i),
            args=[[f"f{i}"], dict(mode="immediate",
                                  frame=dict(duration=0, redraw=True),
                                  transition=dict(duration=0))],
        ))

    fig.update_layout(
        height=620,
        margin=dict(l=40, r=20, t=90, b=90),
        plot_bgcolor="#FAFBFC",
        title=dict(
            text=f"<b>Photoelectric effect — animated</b><br>"
                 f"<span style='font-size:0.78rem;color:#6B7280;'>"
                 f"f = {freq_hz:.2e} Hz  ·  φ = {phi_eV:.2f} eV  ·  "
                 f"intensity = {intensity_rel:.1f} (rel)  ·  "
                 f"photons in flight: {n_photons}</span>",
            x=0.02, xanchor="left", y=0.985, yanchor="top",
            font=dict(size=15),
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.13,
                    xanchor="right", x=1.0, font=dict(size=11)),
        bargap=0.45,
        updatemenus=[dict(
            type="buttons", direction="left",
            x=0.02, y=-0.04, xanchor="left", yanchor="top",
            showactive=False, pad=dict(t=8, r=8),
            buttons=[
                dict(label="▶ Play", method="animate",
                     args=[None, dict(frame=dict(duration=60, redraw=True),
                                      fromcurrent=True, mode="immediate",
                                      transition=dict(duration=0))]),
                dict(label="⏸ Pause", method="animate",
                     args=[[None], dict(frame=dict(duration=0, redraw=False),
                                        mode="immediate",
                                        transition=dict(duration=0))]),
                dict(label="⏮ Restart", method="animate",
                     args=[["f0"], dict(frame=dict(duration=0, redraw=True),
                                        mode="immediate",
                                        transition=dict(duration=0))]),
            ],
        )],
        sliders=[dict(
            active=0, x=0.32, y=-0.04, len=0.66,
            xanchor="left", yanchor="top",
            currentvalue=dict(prefix="frame ", font=dict(size=12, color=NAVY)),
            steps=slider_steps,
            pad=dict(t=8, b=10),
        )],
    )
    return fig


def photoelectric_figure(sim: dict, freq_hz: float, phi_eV: float) -> go.Figure:
    """KE_max vs frequency with threshold marker."""
    f_th = sim["threshold_freq_Hz"]
    f_max = max(freq_hz * 1.4, f_th * 1.6)
    f_grid = np.linspace(0, f_max, 200)
    # KE_max in eV: hf in J / eV→J − φ; clipped at 0.
    h = 6.62607015e-34
    eV = 1.602176634e-19
    ke_grid = np.maximum(0.0, (h * f_grid) / eV - phi_eV)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=f_grid, y=ke_grid, mode="lines",
        line=dict(color=NAVY, width=2.4),
        name="KE_max (eV)",
        hovertemplate="f = %{x:.2e} Hz<br>KE_max = %{y:.2f} eV<extra></extra>",
    ))
    # Threshold marker
    fig.add_vline(x=f_th, line=dict(color=AMBER, dash="dash"),
                  annotation_text=f"threshold f₀ = {f_th:.2e} Hz",
                  annotation_position="top right")
    # Current setting marker
    cur_ke = sim["ke_max_eV"]
    fig.add_trace(go.Scatter(
        x=[freq_hz], y=[cur_ke], mode="markers+text",
        marker=dict(size=14, color=RED if cur_ke == 0 else GREEN,
                    line=dict(color="white", width=2)),
        text=[f"  current: {cur_ke:.2f} eV"], textposition="top right",
        textfont=dict(size=11, color=NAVY),
        showlegend=False, hoverinfo="skip",
    ))
    fig.update_layout(
        title=dict(
            text=f"<b>Photoelectric effect</b><br>"
                 f"<span style='font-size:0.78rem;color:#6B7280;'>"
                 f"KE_max = h·f − φ · work function φ = {phi_eV:.2f} eV</span>",
            x=0.02, xanchor="left", y=0.97, yanchor="top",
            font=dict(size=15),
        ),
        xaxis=dict(title="Light frequency f (Hz)"),
        yaxis=dict(title="Max electron KE (eV)", rangemode="tozero"),
        height=380,
        margin=dict(l=60, r=20, t=110, b=60),
        plot_bgcolor="#FAFBFC",
        showlegend=False,
    )
    return fig


# ---------------------------------------------------------------------------
# 7. de Broglie wavelength
# ---------------------------------------------------------------------------
_REFERENCE_LENGTHS = [
    ("Atomic nucleus (~1 fm)", 1e-15),
    ("Atom (~0.1 nm)", 1e-10),
    ("Visible light (~500 nm)", 5e-7),
    ("Human hair (~0.1 mm)", 1e-4),
    ("1 metre", 1.0),
]


def de_broglie_figure(sim: dict, mass_kg: float, v_mps: float,
                      particle_name: str) -> go.Figure:
    """Log-log λ vs p with reference markers and current point."""
    p_now = sim["momentum_kg_m_s"]
    lam_now = sim["wavelength_m"]
    h = 6.62607015e-34

    # Sweep p over many decades around the current value.
    p_min = max(p_now / 1e6, 1e-30)
    p_max = max(p_now * 1e6, 1e-15)
    p_grid = np.logspace(math.log10(p_min), math.log10(p_max), 200)
    lam_grid = h / p_grid

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=p_grid, y=lam_grid, mode="lines",
        line=dict(color=NAVY, width=2.4),
        name="λ = h/p",
        hovertemplate="p = %{x:.2e} kg·m/s<br>λ = %{y:.2e} m<extra></extra>",
    ))
    # Reference horizontal markers — labels anchored individually on the LEFT
    # edge so they never stack on top of each other or the current-point box.
    label_x = p_grid[3]  # just inside the left edge
    for label, lam_ref in _REFERENCE_LENGTHS:
        if lam_ref < lam_grid.min() or lam_ref > lam_grid.max():
            continue
        fig.add_hline(
            y=lam_ref,
            line=dict(color=GRAY, dash="dot", width=1),
        )
        fig.add_annotation(
            x=label_x, y=lam_ref,
            xref="x", yref="y",
            text=label,
            xanchor="left", yanchor="bottom",
            showarrow=False,
            font=dict(size=10, color=GRAY),
            bgcolor="rgba(255,255,255,0.75)",
            borderpad=2,
        )
    # Current point — marker only; values are shown in the metrics row below
    # the chart, so no in-chart text box is needed (avoids overlap with
    # reference labels).
    if p_now > 0 and lam_now > 0 and not math.isinf(lam_now):
        fig.add_trace(go.Scatter(
            x=[p_now], y=[lam_now], mode="markers",
            marker=dict(size=15, color=AMBER,
                        line=dict(color="white", width=2)),
            name=particle_name,
            hovertemplate=(f"<b>{particle_name}</b><br>"
                           "p = %{x:.2e} kg·m/s<br>"
                           "λ = %{y:.2e} m<extra></extra>"),
            showlegend=False,
        ))
    fig.update_layout(
        title=dict(
            text=f"<b>de Broglie wavelength</b><br>"
                 f"<span style='font-size:0.78rem;color:#6B7280;'>"
                 f"{particle_name} at v = {v_mps:.2e} m/s · "
                 f"p = {p_now:.2e} kg·m/s</span>",
            x=0.02, xanchor="left", y=0.97, yanchor="top",
            font=dict(size=15),
        ),
        xaxis=dict(title="Momentum p (kg·m/s)", type="log"),
        yaxis=dict(title="Wavelength λ (m)", type="log"),
        height=440,
        margin=dict(l=60, r=20, t=110, b=60),
        plot_bgcolor="#FAFBFC",
        showlegend=False,
    )
    return fig


def de_broglie_animation(sim: dict, mass_kg: float, v_mps: float,
                         particle_name: str) -> go.Figure:
    """Animated matter wave: a sinusoid travels rightward; its visible
    cycles-per-screen are a logarithmic mapping of the true wavelength so the
    user can compare regimes (electron vs baseball) on the same canvas."""
    lam = float(sim["wavelength_m"])
    p = float(sim["momentum_kg_m_s"])

    # Degenerate case: v = 0 → infinite λ
    if not math.isfinite(lam) or lam <= 0:
        fig = go.Figure()
        fig.add_annotation(
            text="v = 0  →  p = 0  →  λ = ∞ (no matter wave to draw)",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=14, color=RED),
        )
        fig.update_layout(height=320, plot_bgcolor="#FAFBFC")
        return fig

    # Map true log10(λ) to on-screen cycles across a 10-unit canvas.
    # log10(λ): -35 (baseball)  → 50 cycles (very dense → looks solid)
    # log10(λ):   0 (1 metre)   →  0.5 cycle (nearly flat)
    log_lam = math.log10(lam)
    log_lam_c = max(-35.0, min(5.0, log_lam))
    cycles_on_screen = max(0.5, 50.0 - (log_lam_c + 35.0) * (49.5 / 40.0))

    # Closest reference scale, for the caption
    refs = [
        ("atomic nucleus (~1 fm)", 1e-15),
        ("atom (~0.1 nm)", 1e-10),
        ("visible light (~500 nm)", 5e-7),
        ("human hair (~0.1 mm)", 1e-4),
        ("1 metre", 1.0),
    ]
    closest = min(refs, key=lambda r: abs(math.log10(r[1]) - log_lam))

    if lam < 1e-15:
        regime = "Far smaller than an atomic nucleus — quantum wave behaviour negligible."
    elif lam < 1e-10:
        regime = "Smaller than an atom — quantum effects subtle but present."
    elif lam < 1e-7:
        regime = ("Atomic-to-molecular scale — diffraction is measurable "
                  "(Davisson–Germer experiment, electron microscopes).")
    elif lam < 1e-3:
        regime = "Macroscopic-ish wavelength — quantum effects dominate at this scale."
    else:
        regime = "Wavelength comparable to or larger than everyday objects."

    n_frames = 80
    x = np.linspace(0, 10, 600)
    k = 2.0 * math.pi * cycles_on_screen / 10.0  # spatial wavenumber on canvas
    particle_x = 5.0  # fixed centre

    fig = go.Figure()
    # 0: matter wave (animated)
    y0 = np.sin(k * x)
    fig.add_trace(go.Scatter(
        x=x, y=y0, mode="lines",
        line=dict(color=PURPLE, width=1.8),
        showlegend=False, name="matter wave",
        hoverinfo="skip",
    ))
    # 1: particle marker (animated, bobs on the wave)
    fig.add_trace(go.Scatter(
        x=[particle_x], y=[math.sin(k * particle_x)],
        mode="markers",
        marker=dict(size=18, color=AMBER,
                    line=dict(color="white", width=2)),
        showlegend=False, name="particle",
        hoverinfo="skip",
    ))

    # Header annotation (line 1 + line 2 — all above the chart, never overlaps slider)
    fig.add_annotation(
        xref="paper", yref="paper",
        x=0.02, y=1.16, xanchor="left", yanchor="bottom",
        text=(f"<b>{particle_name}</b>  ·  v = {v_mps:.2e} m/s  ·  "
              f"p = {p:.2e} kg·m/s  ·  "
              f"<span style='color:{PURPLE};'>λ = {lam:.2e} m</span>"),
        showarrow=False, font=dict(size=12, color=NAVY),
    )
    fig.add_annotation(
        xref="paper", yref="paper",
        x=0.02, y=1.03, xanchor="left", yanchor="bottom",
        text=(f"<span style='color:{GRAY};'>wave shown at "
              f"<b>{cycles_on_screen:.1f}</b> cycles "
              f"(log-scaled — see caption below) · {regime}</span>"),
        showarrow=False, font=dict(size=10, color=GRAY),
    )
    # Closest-scale corner box (top-right)
    fig.add_annotation(
        xref="paper", yref="paper",
        x=0.985, y=0.97, xanchor="right", yanchor="top",
        text=f"closest scale:<br><b>{closest[0]}</b>",
        showarrow=False, align="right",
        font=dict(size=11, color=NAVY),
        bgcolor="rgba(255,255,255,0.92)",
        bordercolor=PURPLE, borderwidth=1, borderpad=6,
    )

    # Frames: phase shift only (no x-translation — wave just moves rightward)
    frames = []
    for i in range(n_frames):
        phase = -2.0 * math.pi * i / n_frames  # negative → wave travels rightward
        y_i = np.sin(k * x + phase)
        py = math.sin(k * particle_x + phase)
        frames.append(go.Frame(
            name=f"f{i}",
            data=[
                go.Scatter(x=x, y=y_i),
                go.Scatter(x=[particle_x], y=[py]),
            ],
            traces=[0, 1],
        ))
    fig.frames = frames

    fig.update_xaxes(visible=False, range=[0, 10])
    fig.update_yaxes(visible=False, range=[-1.6, 1.6])

    slider_steps = []
    for i in range(n_frames):
        slider_steps.append(dict(
            method="animate", label=str(i),
            args=[[f"f{i}"], dict(mode="immediate",
                                  frame=dict(duration=0, redraw=True),
                                  transition=dict(duration=0))],
        ))

    fig.update_layout(
        height=380,
        margin=dict(l=20, r=20, t=130, b=80),
        plot_bgcolor="#FAFBFC",
        title=dict(
            text="<b>Matter wave — animated</b>",
            x=0.02, xanchor="left", y=0.985, yanchor="top",
            font=dict(size=15),
        ),
        updatemenus=[dict(
            type="buttons", direction="left",
            x=0.02, y=-0.04, xanchor="left", yanchor="top",
            showactive=False, pad=dict(t=8, r=8),
            buttons=[
                dict(label="▶ Play", method="animate",
                     args=[None, dict(frame=dict(duration=50, redraw=True),
                                      fromcurrent=True, mode="immediate",
                                      transition=dict(duration=0))]),
                dict(label="⏸ Pause", method="animate",
                     args=[[None], dict(frame=dict(duration=0, redraw=False),
                                        mode="immediate",
                                        transition=dict(duration=0))]),
                dict(label="⏮ Restart", method="animate",
                     args=[["f0"], dict(frame=dict(duration=0, redraw=True),
                                        mode="immediate",
                                        transition=dict(duration=0))]),
            ],
        )],
        sliders=[dict(
            active=0, x=0.32, y=-0.04, len=0.66,
            xanchor="left", yanchor="top",
            currentvalue=dict(prefix="frame ", font=dict(size=12, color=NAVY)),
            steps=slider_steps,
            pad=dict(t=8, b=10),
        )],
    )
    return fig


def double_slit_animation(ds: dict, particle_name: str) -> go.Figure:
    """Young's double-slit, animated. Particles stream from a source through
    a barrier with two slits and accumulate as dots on a detector screen,
    revealing the interference fringes whose spacing is set by the de Broglie
    wavelength."""
    fringe = float(ds["fringe_spacing_m"])
    screen_half_m = float(ds["screen_half_m"])
    arrivals_m = np.asarray(ds["arrival_positions_m"], dtype=float)
    n_particles = int(len(arrivals_m))
    intensity = np.asarray(ds["intensity_norm"], dtype=float)
    y_grid_m = np.asarray(ds["y_grid_m"], dtype=float)

    if not math.isfinite(fringe) or n_particles == 0 or screen_half_m <= 0:
        fig = go.Figure()
        fig.add_annotation(
            text="Invalid double-slit parameters.",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=14, color=RED),
        )
        fig.update_layout(height=380, plot_bgcolor="#FAFBFC")
        return fig

    SOURCE_X = 0.5
    BARRIER_X = 4.5
    SCREEN_X = 9.3
    SLIT_Y = 0.6
    SLIT_VIS_W = 0.18
    PLOT_Y_SCALE = 2.4
    BARRIER_TOP = 2.7
    BARRIER_BOT = -2.7
    BARRIER_W = 0.30

    arrivals_plot_y = (arrivals_m / screen_half_m) * PLOT_Y_SCALE

    n_frames = 160
    T_flight = 24
    half_T = T_flight // 2

    in_x_pf: list[list] = []
    in_y_pf: list[list] = []
    acc_x_pf: list[list] = []
    acc_y_pf: list[list] = []

    for f_idx in range(n_frames):
        in_x, in_y = [], []
        acc_x, acc_y = [], []
        for i in range(min(n_particles, f_idx + 1)):
            tau = f_idx - i
            if tau < 0:
                continue
            if tau >= T_flight:
                acc_x.append(SCREEN_X)
                acc_y.append(float(arrivals_plot_y[i]))
                continue
            slit_y = SLIT_Y if (i % 2) == 0 else -SLIT_Y
            target_y = float(arrivals_plot_y[i])
            if tau < half_T:
                t = tau / max(1, half_T - 1)
                x = SOURCE_X + t * (BARRIER_X - SOURCE_X)
                y = t * slit_y
            else:
                t = (tau - half_T) / max(1, T_flight - half_T - 1)
                x = BARRIER_X + t * (SCREEN_X - BARRIER_X)
                y = slit_y + t * (target_y - slit_y)
            in_x.append(x)
            in_y.append(y)
        in_x_pf.append(in_x)
        in_y_pf.append(in_y)
        acc_x_pf.append(acc_x)
        acc_y_pf.append(acc_y)

    env_y_plot = (y_grid_m / screen_half_m) * PLOT_Y_SCALE
    env_x_plot = SCREEN_X + 0.10 + intensity * 0.55

    # Per-frame histogram of arrivals so far (matches theoretical envelope's
    # x-range; built up live as particles land on the screen).
    n_bins = 40
    bin_edges = np.linspace(-screen_half_m, screen_half_m, n_bins + 1)
    bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])
    hist_y_plot = (bin_centers / screen_half_m) * PLOT_Y_SCALE
    flat_x = [SCREEN_X + 0.10] * n_bins

    hist_x_pf: list[list] = []
    hist_y_pf: list[list] = []
    for f_idx in range(n_frames):
        n_arrived = max(0, min(n_particles, f_idx - T_flight + 1))
        if n_arrived == 0:
            hist_x_pf.append(flat_x)
            hist_y_pf.append(hist_y_plot.tolist())
            continue
        hist, _ = np.histogram(arrivals_m[:n_arrived], bins=bin_edges)
        hist_f = hist.astype(float)
        # 3-point moving average (smooth a bit)
        if len(hist_f) >= 3:
            sm = hist_f.copy()
            sm[1:-1] = (hist_f[:-2] + hist_f[1:-1] + hist_f[2:]) / 3.0
            hist_f = sm
        peak = float(hist_f.max()) if hist_f.size else 0.0
        hist_norm = hist_f / peak if peak > 0 else hist_f
        hist_x_pf.append((SCREEN_X + 0.10 + hist_norm * 0.55).tolist())
        hist_y_pf.append(hist_y_plot.tolist())

    fig = go.Figure()
    # 0: source
    fig.add_trace(go.Scatter(
        x=[SOURCE_X], y=[0.0], mode="markers",
        marker=dict(size=20, color=NAVY, symbol="square",
                    line=dict(color="white", width=2)),
        showlegend=False, hoverinfo="skip", name="source",
    ))
    # 1, 2, 3: barrier sections (top piece, between-slits piece, bottom piece)
    for (y_top, y_bot) in [
        (BARRIER_TOP, SLIT_Y + SLIT_VIS_W),
        (SLIT_Y - SLIT_VIS_W, -SLIT_Y + SLIT_VIS_W),
        (-SLIT_Y - SLIT_VIS_W, BARRIER_BOT),
    ]:
        fig.add_trace(go.Scatter(
            x=[BARRIER_X - BARRIER_W / 2, BARRIER_X + BARRIER_W / 2,
               BARRIER_X + BARRIER_W / 2, BARRIER_X - BARRIER_W / 2,
               BARRIER_X - BARRIER_W / 2],
            y=[y_bot, y_bot, y_top, y_top, y_bot],
            mode="lines", fill="toself",
            fillcolor="rgba(91,100,120,0.7)",
            line=dict(color=NAVY, width=1.5),
            showlegend=False, hoverinfo="skip",
        ))
    # 4: screen
    fig.add_trace(go.Scatter(
        x=[SCREEN_X, SCREEN_X], y=[-2.7, 2.7],
        mode="lines", line=dict(color=NAVY, width=3),
        showlegend=False, hoverinfo="skip", name="screen",
    ))
    # 5: theoretical intensity envelope (faint dotted reference)
    fig.add_trace(go.Scatter(
        x=env_x_plot, y=env_y_plot,
        mode="lines", line=dict(color=PURPLE, width=1, dash="dot"),
        opacity=0.45,
        showlegend=False, hoverinfo="skip", name="prediction I(y)",
    ))
    # 6: in-flight particles (animated)
    fig.add_trace(go.Scatter(
        x=in_x_pf[0], y=in_y_pf[0], mode="markers",
        marker=dict(size=8, color=AMBER, symbol="circle",
                    line=dict(color="white", width=1)),
        showlegend=False, hoverinfo="skip", name="in flight",
    ))
    # 7: accumulated dots (animated)
    fig.add_trace(go.Scatter(
        x=acc_x_pf[0], y=acc_y_pf[0], mode="markers",
        marker=dict(size=5, color=PURPLE, symbol="circle",
                    line=dict(color="white", width=0.4),
                    opacity=0.85),
        showlegend=False, hoverinfo="skip", name="accumulated",
    ))
    # 8: live histogram of arrivals (animated, builds up with particles)
    fig.add_trace(go.Scatter(
        x=hist_x_pf[0], y=hist_y_pf[0],
        mode="lines", line=dict(color=PURPLE, width=2.5, shape="spline"),
        showlegend=False, hoverinfo="skip", name="arrivals histogram",
    ))

    frames = []
    for i in range(n_frames):
        frames.append(go.Frame(
            name=f"f{i}",
            data=[
                go.Scatter(x=in_x_pf[i], y=in_y_pf[i]),
                go.Scatter(x=acc_x_pf[i], y=acc_y_pf[i]),
                go.Scatter(x=hist_x_pf[i], y=hist_y_pf[i]),
            ],
            traces=[6, 7, 8],
        ))
    fig.frames = frames

    fig.add_annotation(x=SOURCE_X, y=0.45, text="source",
                       showarrow=False, font=dict(size=10, color=NAVY))
    fig.add_annotation(x=BARRIER_X, y=SLIT_Y + 0.45, text="slit 1",
                       showarrow=False, font=dict(size=10, color=NAVY))
    fig.add_annotation(x=BARRIER_X, y=-SLIT_Y - 0.45, text="slit 2",
                       showarrow=False, font=dict(size=10, color=NAVY))
    fig.add_annotation(x=SCREEN_X, y=2.92, text="detector",
                       showarrow=False, font=dict(size=10, color=NAVY))
    fig.add_annotation(x=SCREEN_X + 0.7, y=-2.92,
                       text="↑ intensity I(y)",
                       showarrow=False, font=dict(size=9, color=PURPLE),
                       xanchor="left")

    fig.add_annotation(
        xref="paper", yref="paper",
        x=0.02, y=0.97, xanchor="left", yanchor="top",
        text=(f"<b>Δy = λL/d = {fringe:.2e} m</b><br>"
              f"d = {ds['slit_separation_m']:.2e} m  ·  "
              f"L = {ds['slit_to_screen_m']:.2f} m  ·  "
              f"λ = {ds['wavelength_m']:.2e} m"),
        showarrow=False, align="left",
        font=dict(size=11, color=NAVY),
        bgcolor="rgba(255,255,255,0.95)",
        bordercolor=PURPLE, borderwidth=1, borderpad=5,
    )

    regime = ds["regime"]
    if regime == "fringes_atomic_or_smaller":
        regime_text = (f"Δy = {fringe:.2e} m  &lt; atomic spacing  —  "
                       f"no observable interference in any real experiment")
        regime_color = RED
    elif regime == "fringes_microscopic":
        regime_text = (f"Δy = {fringe*1e6:.2f} μm  —  microscopic fringes, "
                       f"need a fine detector to resolve")
        regime_color = AMBER
    elif regime == "fringes_visible":
        regime_text = (f"Δy = {fringe*1e3:.2f} mm  —  fringes clearly visible "
                       f"on a real detector")
        regime_color = GREEN
    else:
        regime_text = (f"Δy = {fringe:.2f} m  —  fringes wider than the "
                       f"detector itself")
        regime_color = AMBER

    fig.add_annotation(
        xref="paper", yref="paper",
        x=0.5, y=1.10, xanchor="center", yanchor="bottom",
        text=f"<b>{regime_text}</b>",
        showarrow=False, font=dict(size=12, color=regime_color),
        bgcolor="white", bordercolor=regime_color, borderwidth=1, borderpad=4,
    )

    fig.update_xaxes(visible=False, range=[0, 10.5])
    fig.update_yaxes(visible=False, range=[-3.0, 3.0])

    slider_steps = []
    for i in range(n_frames):
        slider_steps.append(dict(
            method="animate", label=str(i),
            args=[[f"f{i}"], dict(mode="immediate",
                                  frame=dict(duration=0, redraw=True),
                                  transition=dict(duration=0))],
        ))

    fig.update_layout(
        height=510,
        margin=dict(l=20, r=20, t=150, b=80),
        plot_bgcolor="#FAFBFC",
        title=dict(
            text=(f"<b>Young's double-slit  —  {particle_name}</b><br>"
                  f"<span style='font-size:0.78rem;color:#6B7280;'>"
                  f"Each particle goes through the slits one at a time; "
                  f"the interference pattern emerges only after many arrive."
                  f"</span>"),
            x=0.02, xanchor="left", y=0.97, yanchor="top",
            font=dict(size=15),
        ),
        updatemenus=[dict(
            type="buttons", direction="left",
            x=0.02, y=-0.04, xanchor="left", yanchor="top",
            showactive=False, pad=dict(t=8, r=8),
            buttons=[
                dict(label="▶ Play", method="animate",
                     args=[None, dict(frame=dict(duration=80, redraw=True),
                                      fromcurrent=True, mode="immediate",
                                      transition=dict(duration=0))]),
                dict(label="⏸ Pause", method="animate",
                     args=[[None], dict(frame=dict(duration=0, redraw=False),
                                        mode="immediate",
                                        transition=dict(duration=0))]),
                dict(label="⏮ Restart", method="animate",
                     args=[["f0"], dict(frame=dict(duration=0, redraw=True),
                                        mode="immediate",
                                        transition=dict(duration=0))]),
            ],
        )],
        sliders=[dict(
            active=0, x=0.32, y=-0.04, len=0.66,
            xanchor="left", yanchor="top",
            currentvalue=dict(prefix="frame ", font=dict(size=12, color=NAVY)),
            steps=slider_steps,
            pad=dict(t=8, b=10),
        )],
    )
    return fig
