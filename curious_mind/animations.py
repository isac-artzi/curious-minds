"""Plotly animation factories shared across apps."""

from __future__ import annotations

import plotly.graph_objects as go


def energy_diagram(
    reactant_energy: float,
    product_energy: float,
    activation_energy: float | None = None,
    *,
    animate: bool = True,
) -> go.Figure:
    """Reaction-coordinate energy diagram with reactant → TS → product."""
    if activation_energy is None:
        # Pick a sensible TS height: above max(R, P) by 30% of |ΔH| or 50 kJ/mol
        delta = abs(reactant_energy - product_energy)
        activation_energy = max(reactant_energy, product_energy) + max(0.3 * delta, 50.0)

    xs = [0, 1, 2, 3, 4]
    ys = [
        reactant_energy,
        reactant_energy,
        activation_energy,
        product_energy,
        product_energy,
    ]
    labels = ["", "Reactants", "Transition state", "Products", ""]

    def _trace(k: int) -> go.Scatter:
        return go.Scatter(
            x=xs[:k],
            y=ys[:k],
            mode="lines+markers+text",
            line=dict(color="#1F3864", width=3, shape="spline"),
            marker=dict(size=[0, 10, 12, 10, 0][:k], color="#2E5496"),
            text=labels[:k],
            textposition="top center",
            hovertemplate="%{text}: %{y:.0f} kJ/mol<extra></extra>",
        )

    fig = go.Figure()
    fig.add_trace(_trace(len(xs)))
    # ΔH annotation
    fig.add_annotation(
        x=4, y=product_energy,
        ax=1, ay=reactant_energy,
        xref="x", yref="y", axref="x", ayref="y",
        showarrow=True, arrowhead=3, arrowcolor="#D97706",
        text=f"ΔH = {product_energy - reactant_energy:+.0f} kJ/mol",
        font=dict(color="#D97706", size=12),
        bgcolor="rgba(255,255,255,0.8)",
    )

    if animate:
        fig.frames = [
            go.Frame(data=[_trace(k)], name=str(k)) for k in range(2, len(xs) + 1)
        ]
        fig.update_layout(
            updatemenus=[
                dict(
                    type="buttons",
                    showactive=False,
                    buttons=[
                        dict(
                            label="▶ Play",
                            method="animate",
                            args=[
                                None,
                                dict(
                                    frame=dict(duration=350, redraw=True),
                                    transition=dict(duration=250),
                                    fromcurrent=True,
                                ),
                            ],
                        )
                    ],
                    x=0, y=1.15,
                )
            ],
        )

    fig.update_layout(
        title="Reaction energy profile",
        xaxis=dict(title="Reaction coordinate", showticklabels=False, range=[-0.3, 4.3]),
        yaxis=dict(title="Energy (kJ/mol)"),
        showlegend=False,
        height=360,
        margin=dict(l=40, r=20, t=60, b=40),
    )
    return fig
