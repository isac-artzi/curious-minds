"""Chemistry-specific visuals (energy diagram + reaction flow + stoichiometry + Arrhenius)."""

from __future__ import annotations

import math
import re

import numpy as np
import plotly.graph_objects as go

from ..animations import energy_diagram
from .data_loader import compound_by_formula, element_by_symbol

ENTHALPY_TO_ENERGY = {
    "strongly_exothermic": (-300.0, 60.0),
    "exothermic": (-100.0, 50.0),
    "thermoneutral": (0.0, 40.0),
    "endothermic": (100.0, 60.0),
    "strongly_endothermic": (300.0, 100.0),
}

CATEGORY_COLOR = {
    "alkali_metal": "#FCA5A5",
    "alkaline_earth": "#FDBA74",
    "transition_metal": "#FCD34D",
    "post_transition_metal": "#A7F3D0",
    "metalloid": "#86EFAC",
    "nonmetal": "#7DD3FC",
    "halogen": "#A5B4FC",
    "noble_gas": "#C4B5FD",
    "actinide": "#F0ABFC",
    "lanthanide": "#FBCFE8",
    "compound": "#E5E7EB",
    "product": "#BFDBFE",
}

PHASE_GLYPH = {
    "gas": "≋",
    "liquid": "💧",
    "solid": "■",
    "plasma": "✦",
    "aqueous": "≈",
    "unknown": "·",
}


def _reagent_card_html(label: str, sublabel: str, qty: float | None, color: str) -> str:
    qty_html = (
        f'<div style="font-size:0.7rem; color:#6B7280;">{qty:g} mol</div>' if qty else ""
    )
    return f"""
    <div style="
      display:inline-block; width:140px;
      padding:0.55rem 0.5rem; margin:0.15rem;
      background:{color}; border-radius:8px;
      border:1px solid rgba(31,56,100,0.2);
      text-align:center; vertical-align:middle;
      box-shadow: 0 1px 2px rgba(0,0,0,0.06);
      white-space: normal;
      word-break: break-word;
      overflow-wrap: break-word;
    ">
      <div style="font-size:1.05rem; font-weight:700; color:#1F2937;
                  word-break: break-word; overflow-wrap: break-word;">{label}</div>
      <div style="font-size:0.72rem; color:#374151; line-height:1.2;
                  word-break: break-word; overflow-wrap: break-word;">{sublabel}</div>
      {qty_html}
    </div>
    """


def reaction_flow_html(
    reactants: list[dict],     # [{kind, ident, qty}]
    primary_product: dict,     # {formula, name, phase}
    byproducts: list[dict],    # [{formula, name, phase}, ...]
    enthalpy_kJ_per_mol: float | None,
    enthalpy_class: str,
    catalyst: str = "",
) -> str:
    """A 'reactants → arrow → products' visual flow card."""
    # Build reactant cards
    r_html = ""
    for i, r in enumerate(reactants):
        if i > 0:
            r_html += '<span style="font-size:1.4rem; color:#6B7280; margin:0 0.2rem;">+</span>'
        kind = r["kind"]
        ident = r["ident"]
        qty = r.get("qty")
        if kind == "element":
            rec = element_by_symbol(ident) or {}
            color = CATEGORY_COLOR.get(rec.get("category", ""), "#E5E7EB")
            r_html += _reagent_card_html(ident, rec.get("name", ""), qty, color)
        else:
            rec = compound_by_formula(ident) or {}
            r_html += _reagent_card_html(
                ident, rec.get("name", ""), qty, CATEGORY_COLOR["compound"]
            )

    # Arrow + condition labels
    arrow_top = catalyst[:40] if catalyst else ""
    arrow_bot = ""
    if enthalpy_kJ_per_mol is not None:
        sign = "release" if enthalpy_kJ_per_mol < 0 else "absorb"
        arrow_bot = f"{abs(enthalpy_kJ_per_mol):.0f} kJ/mol ({sign})"
    elif enthalpy_class:
        arrow_bot = enthalpy_class.replace("_", " ")

    arrow_html = f"""
    <div style="
      display:inline-block; vertical-align:middle;
      text-align:center; margin: 0 0.6rem; min-width:140px;
    ">
      <div style="font-size:0.78rem; color:#6B7280; margin-bottom:-0.1rem;">{arrow_top}</div>
      <div style="font-size:2.1rem; line-height:1; color:#1F3864; font-weight:300;">⟶</div>
      <div style="font-size:0.78rem; color:#D97706;">{arrow_bot}</div>
    </div>
    """

    # Product cards
    p_html = ""
    glyph = PHASE_GLYPH.get(primary_product.get("phase", "unknown"), "·")
    p_html += _reagent_card_html(
        primary_product.get("formula", "?"),
        f"{glyph} {primary_product.get('name', '')}",
        None,
        CATEGORY_COLOR["product"],
    )
    for bp in byproducts:
        p_html += '<span style="font-size:1.4rem; color:#6B7280; margin:0 0.2rem;">+</span>'
        bglyph = PHASE_GLYPH.get(bp.get("phase", "unknown"), "·")
        p_html += _reagent_card_html(
            bp.get("formula", "?"),
            f"{bglyph} {bp.get('name', '')}",
            None,
            CATEGORY_COLOR["product"],
        )

    return f"""
    <div style="
      padding: 1rem 0.8rem;
      background: linear-gradient(180deg, #F8FAFC 0%, #F1F5F9 100%);
      border-radius: 10px;
      border: 1px solid rgba(31,56,100,0.12);
      overflow-x: auto; white-space: nowrap;
      text-align: center;
    ">
      <div style="display:inline-block; vertical-align:middle;">{r_html}</div>
      {arrow_html}
      <div style="display:inline-block; vertical-align:middle;">{p_html}</div>
    </div>
    """


def reaction_flow_chart(
    reactants: list[dict],
    primary_product: dict,
    byproducts: list[dict],
    enthalpy_kJ_per_mol: float | None,
) -> go.Figure:
    """Plotly Sankey alternative — useful when product names are long."""
    labels = []
    sources = []
    targets = []
    values = []
    colors = []

    for r in reactants:
        ident = r["ident"]
        labels.append(ident)
        colors.append("#7DD3FC")

    arrow_idx = len(labels)
    labels.append("⟶")
    colors.append("#1F3864")

    product_start = len(labels)
    labels.append(primary_product.get("formula", "?"))
    colors.append("#BFDBFE")
    for bp in byproducts:
        labels.append(bp.get("formula", "?"))
        colors.append("#BFDBFE")

    for i, r in enumerate(reactants):
        sources.append(i)
        targets.append(arrow_idx)
        values.append(max(r.get("qty") or 1.0, 0.5))
    n_products = 1 + len(byproducts)
    for j in range(n_products):
        sources.append(arrow_idx)
        targets.append(product_start + j)
        values.append(1.0)

    fig = go.Figure(
        go.Sankey(
            arrangement="snap",
            node=dict(
                pad=18, thickness=18,
                line=dict(color="rgba(31,56,100,0.3)", width=0.5),
                label=labels, color=colors,
            ),
            link=dict(source=sources, target=targets, value=values),
        )
    )
    fig.update_layout(
        height=260,
        margin=dict(l=10, r=10, t=20, b=10),
        font=dict(size=13),
    )
    return fig


_LEAD_NUM = re.compile(r"^\s*~?\s*([0-9]*\.?[0-9]+)")


def _parse_amount(text: str | None, default: float = 1.0) -> float:
    if not text:
        return default
    m = _LEAD_NUM.match(str(text))
    if not m:
        return default
    try:
        v = float(m.group(1))
        return v if v > 0 else default
    except ValueError:
        return default


def stoichiometry_chart(
    reactants: list[dict],     # [{ident, qty}]
    products: list[dict],      # [{formula, name, amount}]
) -> go.Figure:
    """Horizontal grouped bars: reactant moles (left) vs product moles (right)."""
    r_labels = [r["ident"] for r in reactants]
    r_values = [float(r.get("qty") or 1.0) for r in reactants]

    p_labels = [p.get("formula", "?") for p in products]
    p_values = [_parse_amount(p.get("amount"), default=1.0) for p in products]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=r_labels, x=r_values, name="Reactants (mol)",
        orientation="h", marker_color="#7DD3FC",
        text=[f"{v:g}" for v in r_values], textposition="outside",
        hovertemplate="%{y}: %{x:g} mol<extra>Reactant</extra>",
    ))
    fig.add_trace(go.Bar(
        y=p_labels, x=p_values, name="Products (mol)",
        orientation="h", marker_color="#86EFAC",
        text=[f"{v:g}" for v in p_values], textposition="outside",
        hovertemplate="%{y}: %{x:g} mol<extra>Product</extra>",
    ))
    fig.update_layout(
        height=max(220, 60 + 32 * (len(r_labels) + len(p_labels))),
        margin=dict(l=10, r=10, t=30, b=20),
        barmode="group",
        xaxis_title="Moles (per balanced equation)",
        yaxis=dict(autorange="reversed"),
        legend=dict(orientation="h", y=1.12, x=0),
        font=dict(size=12),
        plot_bgcolor="#F8FAFC",
    )
    return fig


def rate_vs_temperature_chart(
    activation_energy_kJ_per_mol: float,
    current_T_K: float,
    *,
    T_min: float = 100.0,
    T_max: float = 2000.0,
    A: float = 1e13,
) -> go.Figure:
    """Arrhenius rate constant k = A·exp(-Ea/RT) as a function of T (log-y).

    Marks the user's current temperature with a vertical line.
    """
    R = 8.314e-3  # kJ / (mol · K)
    Ea = float(activation_energy_kJ_per_mol)
    Ts = np.linspace(T_min, T_max, 240)
    ks = A * np.exp(-Ea / (R * Ts))
    # Mask (don't floor) values below the log-plot range: a floored flat
    # shelf reads as "the rate stops changing", which is teachably wrong.
    ks = np.where(ks < 1e-30, np.nan, ks)

    k_now = A * math.exp(-Ea / (R * max(current_T_K, 1.0)))
    k_now = max(k_now, 1e-30)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=Ts, y=ks, mode="lines",
        line=dict(color="#1F3864", width=3),
        name="k(T)",
        hovertemplate="T = %{x:.0f} K<br>k = %{y:.2e}<extra></extra>",
    ))
    fig.add_vline(
        x=current_T_K, line=dict(color="#D97706", width=2, dash="dash"),
        annotation_text=f"current T = {current_T_K:.0f} K",
        annotation_position="top right",
    )
    fig.add_trace(go.Scatter(
        x=[current_T_K], y=[k_now], mode="markers",
        marker=dict(color="#D97706", size=11, line=dict(color="white", width=2)),
        showlegend=False,
        hovertemplate=f"At {current_T_K:.0f} K, k ≈ %{{y:.2e}}<extra></extra>",
    ))
    fig.update_layout(
        height=300,
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis_title="Temperature (K)",
        yaxis_title="Relative rate k  (log scale)",
        yaxis_type="log",
        plot_bgcolor="#F8FAFC",
        font=dict(size=12),
        title=dict(
            text=f"Arrhenius rate, Eₐ ≈ {Ea:.0f} kJ/mol",
            font=dict(size=13), x=0, xanchor="left",
        ),
        showlegend=False,
    )
    return fig


def energy_diagram_for(enthalpy_class: str, enthalpy_value: float | None):
    """Render an energy diagram. Use the explicit value if provided, else class defaults."""
    if enthalpy_value is not None:
        # Reactants at 0; products at +ΔH (so exothermic = negative drop)
        reactant = 0.0
        product = float(enthalpy_value)
        # Activation: above the higher of the two by 25% of |ΔH| or 60 kJ/mol
        delta = abs(product - reactant)
        activation = max(reactant, product) + max(0.25 * delta, 60.0)
    else:
        product, bump = ENTHALPY_TO_ENERGY.get(
            enthalpy_class, ENTHALPY_TO_ENERGY["thermoneutral"]
        )
        reactant = 0.0
        activation = max(reactant, product) + bump
    return energy_diagram(reactant, product, activation, animate=True)
