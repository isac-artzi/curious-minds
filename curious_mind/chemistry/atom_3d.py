"""3D Bohr-model atom rendering using Plotly scatter3d.

This is intentionally a simplified, K-12-friendly representation:
- Nucleus at origin as a single sphere (not resolved into protons/neutrons).
- Electron shells as concentric rings on alternating planes.
- Shell occupancies come from Madelung-order subshell filling (2-8-8-2 for Ca,
  2-8-18-7 for Br, …); we do NOT model Aufbau exceptions (Cr, Cu, Ag, etc.).
"""

from __future__ import annotations

import math

import numpy as np
import plotly.graph_objects as go

from .visuals import CATEGORY_COLOR

# Subshells in Madelung (Aufbau) filling order as (principal n, capacity).
# Summing filled subshells per n gives the standard textbook shell
# occupancies (e.g. Ca = 2-8-8-2, Br = 2-8-18-7) — the naive "fill each
# shell to capacity" rule gets these wrong past Z = 20.
_MADELUNG_SUBSHELLS = [
    (1, 2),           # 1s
    (2, 2), (2, 6),   # 2s 2p
    (3, 2), (3, 6),   # 3s 3p
    (4, 2), (3, 10), (4, 6),    # 4s 3d 4p
    (5, 2), (4, 10), (5, 6),    # 5s 4d 5p
    (6, 2), (4, 14), (5, 10), (6, 6),   # 6s 4f 5d 6p
    (7, 2), (5, 14), (6, 10), (7, 6),   # 7s 5f 6d 7p
]

# Three orthogonal ring planes, cycled per shell for visual depth.
# Each tuple is (axis-1 unit, axis-2 unit) — ring lies in the plane spanned by them.
_PLANES = [
    ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),   # XY
    ((1.0, 0.0, 0.0), (0.0, 0.0, 1.0)),   # XZ
    ((0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),   # YZ
]


def electron_config(atomic_number: int) -> list[int]:
    """Electrons per shell (K, L, M, …) from Madelung-order subshell filling.

    Matches the standard textbook shell occupancies for all elements (we
    deliberately ignore the handful of Aufbau exceptions like Cr and Cu —
    they differ by one electron and don't change the K-12 story).
    """
    z = max(int(atomic_number), 0)
    shells: dict[int, int] = {}
    for n, cap in _MADELUNG_SUBSHELLS:
        if z <= 0:
            break
        take = min(cap, z)
        shells[n] = shells.get(n, 0) + take
        z -= take
    if not shells:
        return []
    return [shells.get(n, 0) for n in range(1, max(shells) + 1)]


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
