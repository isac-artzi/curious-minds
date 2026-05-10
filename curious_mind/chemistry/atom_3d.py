"""3D Bohr-model atom rendering using Plotly scatter3d.

This is intentionally a simplified, K-12-friendly representation:
- Nucleus at origin as a single sphere (not resolved into protons/neutrons).
- Electron shells as concentric rings on alternating planes.
- Shell capacities use the simple K=2, L=8, M=8/18, N=8/18/32, O=8/18/32, P=8/18, Q=8
  pattern; we do NOT model Aufbau exceptions (Cr, Cu, etc.).
"""

from __future__ import annotations

import math

import numpy as np
import plotly.graph_objects as go

from .visuals import CATEGORY_COLOR

# Conventional electron-shell capacities (K, L, M, N, O, P, Q).
# These are the *historical Bohr* capacities, fine for K-12 visualization.
SHELL_CAPACITY = [2, 8, 8, 18, 18, 32, 32]

# Three orthogonal ring planes, cycled per shell for visual depth.
# Each tuple is (axis-1 unit, axis-2 unit) — ring lies in the plane spanned by them.
_PLANES = [
    ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),   # XY
    ((1.0, 0.0, 0.0), (0.0, 0.0, 1.0)),   # XZ
    ((0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),   # YZ
]


def electron_config(atomic_number: int) -> list[int]:
    """Distribute Z electrons across simple Bohr shells, low-to-high capacity."""
    z = max(int(atomic_number), 0)
    config: list[int] = []
    for cap in SHELL_CAPACITY:
        if z <= 0:
            break
        n = min(cap, z)
        config.append(n)
        z -= n
    return config


def _ring_points(radius: float, plane_idx: int, n_points: int = 96) -> tuple[list[float], list[float], list[float]]:
    u, v = _PLANES[plane_idx % len(_PLANES)]
    ts = np.linspace(0, 2 * math.pi, n_points)
    xs = [radius * (math.cos(t) * u[0] + math.sin(t) * v[0]) for t in ts]
    ys = [radius * (math.cos(t) * u[1] + math.sin(t) * v[1]) for t in ts]
    zs = [radius * (math.cos(t) * u[2] + math.sin(t) * v[2]) for t in ts]
    return xs, ys, zs


def _electron_positions(radius: float, plane_idx: int, n_electrons: int) -> tuple[list[float], list[float], list[float]]:
    if n_electrons <= 0:
        return [], [], []
    u, v = _PLANES[plane_idx % len(_PLANES)]
    # Phase offset per shell so electrons in adjacent shells aren't aligned
    phase = 0.31 * plane_idx
    ts = [phase + 2 * math.pi * i / n_electrons for i in range(n_electrons)]
    xs = [radius * (math.cos(t) * u[0] + math.sin(t) * v[0]) for t in ts]
    ys = [radius * (math.cos(t) * u[1] + math.sin(t) * v[1]) for t in ts]
    zs = [radius * (math.cos(t) * u[2] + math.sin(t) * v[2]) for t in ts]
    return xs, ys, zs


def bohr_atom_figure(
    symbol: str,
    atomic_number: int,
    *,
    category: str = "",
    name: str = "",
    height: int = 360,
) -> go.Figure:
    """Return a Plotly scatter3d Bohr-model atom for the given element."""
    config = electron_config(atomic_number)
    nucleus_color = CATEGORY_COLOR.get(category, "#94A3B8")

    fig = go.Figure()

    # --- Nucleus (single sphere; size grows mildly with Z) ----------------
    nucleus_size = 18 + min(atomic_number, 100) * 0.25
    fig.add_trace(go.Scatter3d(
        x=[0], y=[0], z=[0],
        mode="markers+text",
        marker=dict(
            size=nucleus_size, color=nucleus_color,
            line=dict(color="#1F2937", width=2), opacity=0.95,
        ),
        text=[symbol], textposition="middle center",
        textfont=dict(size=14, color="#1F2937", family="Arial Black"),
        hovertemplate=(
            f"<b>{symbol}</b> ({name})<br>"
            f"Z = {atomic_number}<br>"
            f"Electrons: {sum(config)}<extra></extra>"
        ),
        name="nucleus",
        showlegend=False,
    ))

    # --- Shells: faint ring + electron points -----------------------------
    for shell_idx, n_electrons in enumerate(config):
        radius = 1.0 + 0.9 * shell_idx
        # Ring outline
        rx, ry, rz = _ring_points(radius, shell_idx)
        fig.add_trace(go.Scatter3d(
            x=rx, y=ry, z=rz, mode="lines",
            line=dict(color="rgba(31,56,100,0.25)", width=2),
            hoverinfo="skip", showlegend=False,
        ))
        # Electrons
        ex, ey, ez = _electron_positions(radius, shell_idx, n_electrons)
        fig.add_trace(go.Scatter3d(
            x=ex, y=ey, z=ez, mode="markers",
            marker=dict(
                size=7, color="#2E5496",
                line=dict(color="white", width=1), opacity=0.95,
            ),
            hovertemplate=(
                f"Shell n={shell_idx + 1}<br>"
                f"{n_electrons} electron{'s' if n_electrons != 1 else ''}<extra></extra>"
            ),
            showlegend=False,
        ))

    config_str = ", ".join(str(n) for n in config) if config else "0"
    title = f"<b>{symbol}</b> &nbsp; Z = {atomic_number} &nbsp; · &nbsp; shells: {config_str}"

    # Square-ish 3D scene with hidden axes for a clean look
    extent = 1.2 + 0.9 * max(len(config), 1)
    axis_kw = dict(
        showbackground=False, showgrid=False, zeroline=False,
        showticklabels=False, title="",
        range=[-extent, extent],
    )
    fig.update_layout(
        height=height,
        margin=dict(l=0, r=0, t=40, b=0),
        scene=dict(
            xaxis=axis_kw, yaxis=axis_kw, zaxis=axis_kw,
            aspectmode="cube",
            camera=dict(eye=dict(x=1.6, y=1.4, z=1.1)),
        ),
        title=dict(text=title, x=0.02, xanchor="left", font=dict(size=13)),
        paper_bgcolor="#F8FAFC",
    )
    return fig
