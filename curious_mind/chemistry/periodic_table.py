"""Clickable periodic-table reagent picker for the Chemistry sandbox.

Renders the standard 18-column periodic table as a grid of `st.button` widgets
(one per element). Buttons are styled per chemical category via CSS that targets
Streamlit's `.st-key-{key}` container class. Click handling goes through
Streamlit's normal callback mechanism so `st.session_state` is preserved across
clicks (anchor-link / query-param toggling caused full-page reloads that wiped
session state).

State for the picker lives in `st.session_state` keyed by `state_key`:
    {state_key}_selected:   list[str]  e.g. ["element:H", "compound:H2O"]
    {state_key}_quantities: dict[str, float]
"""

from __future__ import annotations

import streamlit as st

from .data_loader import load_compounds, load_elements

# (period, group) for every element 1..118. Lanthanides/actinides display in
# rows 8 (La–Lu) and 9 (Ac–Lr), columns 4–18 (15 elements per row).
PT_POSITION: dict[str, tuple[int, int]] = {
    "H": (1, 1), "He": (1, 18),
    "Li": (2, 1), "Be": (2, 2),
    "B": (2, 13), "C": (2, 14), "N": (2, 15), "O": (2, 16), "F": (2, 17), "Ne": (2, 18),
    "Na": (3, 1), "Mg": (3, 2),
    "Al": (3, 13), "Si": (3, 14), "P": (3, 15), "S": (3, 16), "Cl": (3, 17), "Ar": (3, 18),
    "K": (4, 1), "Ca": (4, 2),
    "Sc": (4, 3), "Ti": (4, 4), "V": (4, 5), "Cr": (4, 6), "Mn": (4, 7),
    "Fe": (4, 8), "Co": (4, 9), "Ni": (4, 10), "Cu": (4, 11), "Zn": (4, 12),
    "Ga": (4, 13), "Ge": (4, 14), "As": (4, 15), "Se": (4, 16), "Br": (4, 17), "Kr": (4, 18),
    "Rb": (5, 1), "Sr": (5, 2),
    "Y": (5, 3), "Zr": (5, 4), "Nb": (5, 5), "Mo": (5, 6), "Tc": (5, 7),
    "Ru": (5, 8), "Rh": (5, 9), "Pd": (5, 10), "Ag": (5, 11), "Cd": (5, 12),
    "In": (5, 13), "Sn": (5, 14), "Sb": (5, 15), "Te": (5, 16), "I": (5, 17), "Xe": (5, 18),
    "Cs": (6, 1), "Ba": (6, 2),
    # Lanthanides: La..Lu in display row 8, columns 4..18
    "La": (8, 4), "Ce": (8, 5), "Pr": (8, 6), "Nd": (8, 7), "Pm": (8, 8),
    "Sm": (8, 9), "Eu": (8, 10), "Gd": (8, 11), "Tb": (8, 12), "Dy": (8, 13),
    "Ho": (8, 14), "Er": (8, 15), "Tm": (8, 16), "Yb": (8, 17), "Lu": (8, 18),
    "Hf": (6, 4), "Ta": (6, 5), "W": (6, 6), "Re": (6, 7),
    "Os": (6, 8), "Ir": (6, 9), "Pt": (6, 10), "Au": (6, 11), "Hg": (6, 12),
    "Tl": (6, 13), "Pb": (6, 14), "Bi": (6, 15), "Po": (6, 16), "At": (6, 17), "Rn": (6, 18),
    "Fr": (7, 1), "Ra": (7, 2),
    # Actinides: Ac..Lr in display row 9, columns 4..18
    "Ac": (9, 4), "Th": (9, 5), "Pa": (9, 6), "U": (9, 7), "Np": (9, 8),
    "Pu": (9, 9), "Am": (9, 10), "Cm": (9, 11), "Bk": (9, 12), "Cf": (9, 13),
    "Es": (9, 14), "Fm": (9, 15), "Md": (9, 16), "No": (9, 17), "Lr": (9, 18),
    "Rf": (7, 4), "Db": (7, 5), "Sg": (7, 6), "Bh": (7, 7),
    "Hs": (7, 8), "Mt": (7, 9), "Ds": (7, 10), "Rg": (7, 11), "Cn": (7, 12),
    "Nh": (7, 13), "Fl": (7, 14), "Mc": (7, 15), "Lv": (7, 16), "Ts": (7, 17), "Og": (7, 18),
}

CATEGORY_LABEL = {
    "alkali_metal": "Alkali Metal",
    "alkaline_earth": "Alkaline Earth",
    "transition_metal": "Transition Metal",
    "post_transition_metal": "Post-Transition",
    "metalloid": "Metalloid",
    "nonmetal": "Nonmetal",
    "halogen": "Halogen",
    "noble_gas": "Noble Gas",
    "lanthanide": "Lanthanide",
    "actinide": "Actinide",
    "unknown": "",
}

# PubChem-inspired palette: light fills, slightly darker borders.
CATEGORY_COLOR = {
    "alkali_metal":          "#FFD3D3",
    "alkaline_earth":        "#FFE2BE",
    "transition_metal":      "#CFE2FF",
    "post_transition_metal": "#CDF6D5",
    "metalloid":             "#D8F0BD",
    "nonmetal":              "#FFF6B5",
    "halogen":               "#FFE49C",
    "noble_gas":             "#F4D0EE",
    "lanthanide":            "#C8F0E8",
    "actinide":              "#BCEFD0",
    "unknown":               "#E5E7EB",
}
CATEGORY_BORDER = {
    "alkali_metal":          "#E08484",
    "alkaline_earth":        "#D69556",
    "transition_metal":      "#7AA8DD",
    "post_transition_metal": "#5BB873",
    "metalloid":             "#7BB957",
    "nonmetal":              "#D8B83A",
    "halogen":               "#C99025",
    "noble_gas":             "#B673AB",
    "lanthanide":            "#4FBBA9",
    "actinide":              "#43AE7C",
    "unknown":               "#9CA3AF",
}


# The ~120-rule CSS block is deterministic per state_key (the element KB is
# static), so build it once per session instead of on every rerun.
_CSS_CACHE: dict[str, str] = {}


def _inject_css(state_key: str, elements: list[dict]) -> None:
    """Style every periodic-table button by category via st-key-{key} class.

    The button label is just the element symbol — atomic number (top-left) and
    element name (bottom-center) are added via per-element ::before / ::after
    pseudo-elements so the cell stays a clean fixed-size rectangle.
    """
    cached = _CSS_CACHE.get(state_key)
    if cached is not None:
        st.markdown(cached, unsafe_allow_html=True)
        return
    rules = [
        f"""
        div[class*="st-key-{state_key}_pt_"] {{
            margin: 0 !important;
        }}
        div[class*="st-key-{state_key}_pt_"] button {{
            position: relative !important;
            padding: 16px 2px 12px 2px !important;
            min-height: 70px !important;
            height: 70px !important;
            font-size: 1.05rem !important;
            font-weight: 800 !important;
            line-height: 1 !important;
            color: #111827 !important;
            border-width: 1.5px !important;
            border-style: solid !important;
            border-radius: 6px !important;
            overflow: hidden !important;
            transition: transform 0.08s ease, box-shadow 0.08s ease;
        }}
        div[class*="st-key-{state_key}_pt_"] button p {{
            margin: 0 !important;
            font-size: 1.05rem !important;
            font-weight: 800 !important;
            line-height: 1 !important;
        }}
        div[class*="st-key-{state_key}_pt_"] button:hover {{
            transform: translateY(-1px);
            box-shadow: 0 4px 10px rgba(0,0,0,0.18);
            z-index: 2;
        }}
        .pt-empty {{ min-height: 70px; height: 70px; }}
        .pt-rowlabel {{
            font-size: 0.7rem; color: #6B7280;
            display: flex; align-items: center; justify-content: flex-end;
            height: 70px; padding-right: 4px;
        }}
        .pt-fblock-note {{
            font-size: 0.72rem; color: #6B7280; margin: 0.4rem 0 0.1rem 0;
        }}
        .pt-legend {{
            display: flex; flex-wrap: wrap; gap: 0.35rem 0.9rem;
            font-size: 0.72rem; color: #374151;
            padding: 0.5rem 0.2rem 0.6rem 0.2rem;
        }}
        .pt-leg-sw {{
            display: inline-block; width: 12px; height: 12px;
            border-radius: 3px; margin-right: 5px; vertical-align: -2px;
            border: 1px solid rgba(0,0,0,0.18);
        }}
        .pt-selected-chip {{
            display: inline-block;
            padding: 0.18rem 0.6rem;
            margin: 0.15rem 0.25rem 0.15rem 0;
            border-radius: 999px;
            background: #1F3864;
            color: white;
            font-size: 0.82rem;
            font-weight: 500;
        }}
        """
    ]
    # Per-category background + border + selected-state styling
    for cat, color in CATEGORY_COLOR.items():
        border = CATEGORY_BORDER[cat]
        rules.append(f"""
        div[class*="st-key-{state_key}_pt_{cat}_"] button {{
            background: {color} !important;
            border-color: {border} !important;
        }}
        div[class*="st-key-{state_key}_pt_{cat}_"] button[kind="primary"],
        div[class*="st-key-{state_key}_pt_{cat}_"] button[data-testid="baseButton-primary"] {{
            background: {color} !important;
            color: #111827 !important;
            outline: 3px solid #1F3864 !important;
            outline-offset: -1px !important;
            box-shadow: 0 0 0 1px #fff inset, 0 4px 12px rgba(31,56,100,0.35) !important;
        }}
        """)
    # Per-element pseudo-elements for atomic number (top-left) and name (bottom)
    for elem in elements:
        sym = elem["symbol"]
        cat = elem.get("category") or "unknown"
        z = elem.get("atomic_number", "")
        name = (elem.get("name") or "")[:10].replace('"', '\\"')
        rules.append(f"""
        div[class*="st-key-{state_key}_pt_{cat}_{sym}"] button::before {{
            content: "{z}";
            position: absolute; top: 3px; left: 5px;
            font-size: 0.6rem; font-weight: 600; line-height: 1;
            color: #374151;
        }}
        div[class*="st-key-{state_key}_pt_{cat}_{sym}"] button::after {{
            content: "{name}";
            position: absolute; left: 0; right: 0; bottom: 4px;
            font-size: 0.6rem; font-weight: 500; line-height: 1;
            color: #1F2937; text-align: center;
            white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
            padding: 0 2px;
        }}
        """)
    css = f"<style>{''.join(rules)}</style>"
    _CSS_CACHE[state_key] = css
    st.markdown(css, unsafe_allow_html=True)


def _ensure_state(state_key: str, defaults: dict) -> None:
    if f"{state_key}_selected" not in st.session_state:
        st.session_state[f"{state_key}_selected"] = list(defaults.get("selected", []))
    if f"{state_key}_quantities" not in st.session_state:
        st.session_state[f"{state_key}_quantities"] = dict(defaults.get("quantities", {}))


def _toggle(state_key: str, item_key: str) -> None:
    sel = st.session_state[f"{state_key}_selected"]
    qty = st.session_state[f"{state_key}_quantities"]
    if item_key in sel:
        sel.remove(item_key)
        qty.pop(item_key, None)
    else:
        sel.append(item_key)
        qty.setdefault(item_key, 1.0)


def _format_mass(m) -> str:
    if m is None or m == "":
        return ""
    try:
        f = float(m)
    except (TypeError, ValueError):
        return str(m)
    if f >= 100:
        return f"{f:.1f}"
    if f >= 10:
        return f"{f:.2f}"
    return f"{f:.3f}"


def _button_for_element(state_key: str, elem: dict) -> None:
    sym = elem["symbol"]
    cat = elem.get("category") or "unknown"
    item_key = f"element:{sym}"
    selected = item_key in st.session_state[f"{state_key}_selected"]
    mass_str = _format_mass(elem.get("atomic_mass"))
    cat_label = CATEGORY_LABEL.get(cat, "")
    name = elem.get("name", "")

    # Label is just the symbol — atomic number and name are positioned via
    # CSS ::before / ::after pseudo-elements (see _inject_css).
    label = f"**{sym}**"

    tooltip_bits = [f"{name} ({sym})", f"Z = {elem.get('atomic_number', '?')}"]
    if mass_str:
        tooltip_bits.append(f"mass {mass_str} u")
    if cat_label:
        tooltip_bits.append(cat_label)
    phase = elem.get("phase_at_stp")
    if phase:
        tooltip_bits.append(f"{phase} at STP")
    en = elem.get("electronegativity")
    if en is not None:
        tooltip_bits.append(f"χ {en}")
    mp = elem.get("melting_point_K")
    bp = elem.get("boiling_point_K")
    if mp:
        tooltip_bits.append(f"mp {mp} K")
    if bp:
        tooltip_bits.append(f"bp {bp} K")
    fact = elem.get("fun_fact")
    if fact:
        tooltip_bits.append(fact)

    st.button(
        label,
        key=f"{state_key}_pt_{cat}_{sym}",
        help=" · ".join(tooltip_bits),
        width="stretch",
        type="primary" if selected else "secondary",
        on_click=_toggle,
        args=(state_key, item_key),
    )


def _row(state_key: str, period: int, by_pos: dict, col_range=range(1, 19)) -> None:
    cols = st.columns(18, gap="small")
    for grp in col_range:
        with cols[grp - 1]:
            elem = by_pos.get((period, grp))
            if elem is None:
                st.markdown('<div class="pt-empty"></div>', unsafe_allow_html=True)
                continue
            _button_for_element(state_key, elem)


def _fblock_row(state_key: str, period: int, by_pos: dict, label: str) -> None:
    cols = st.columns(18, gap="small")
    # column 3 holds a small "57–71" / "89–103" label
    with cols[2]:
        st.markdown(f'<div class="pt-rowlabel">{label}</div>', unsafe_allow_html=True)
    for grp in range(4, 19):
        with cols[grp - 1]:
            elem = by_pos.get((period, grp))
            if elem is None:
                st.markdown('<div class="pt-empty"></div>', unsafe_allow_html=True)
                continue
            _button_for_element(state_key, elem)


def _legend_html() -> str:
    items = []
    for cat, label in CATEGORY_LABEL.items():
        if not label:
            continue
        color = CATEGORY_COLOR.get(cat, "#E5E7EB")
        border = CATEGORY_BORDER.get(cat, "#9CA3AF")
        items.append(
            f'<span><span class="pt-leg-sw" style="background:{color};border-color:{border};"></span>{label}</span>'
        )
    return f'<div class="pt-legend">{"".join(items)}</div>'


def render_picker(state_key: str, defaults: dict | None = None) -> tuple[list[str], dict[str, float]]:
    """
    Render the periodic-table picker + compounds expander + selected-chips bar.
    Returns (selected_keys, quantities).
    """
    _ensure_state(state_key, defaults or {})

    elements = load_elements()
    _inject_css(state_key, elements)
    by_sym = {e["symbol"]: e for e in elements}
    by_pos: dict[tuple[int, int], dict] = {}
    for e in elements:
        pos = PT_POSITION.get(e["symbol"])
        if pos:
            by_pos[pos] = e

    st.markdown("**Periodic table** — click any element to add or remove it from the reaction.")
    for period in range(1, 8):
        _row(state_key, period, by_pos)

    if any(p in (8, 9) for p, _ in by_pos.keys()):
        st.markdown('<div class="pt-fblock-note">Lanthanides / Actinides</div>', unsafe_allow_html=True)
        _fblock_row(state_key, 8, by_pos, "57–71")
        _fblock_row(state_key, 9, by_pos, "89–103")

    st.markdown(_legend_html(), unsafe_allow_html=True)

    # Compounds picker
    compounds = load_compounds()
    with st.expander("➕ Add a compound", expanded=False):
        compound_labels = [f"{c['formula']} — {c['name']}" for c in compounds]
        compound_keys = [f"compound:{c['formula']}" for c in compounds]
        already = set(st.session_state[f"{state_key}_selected"])
        choice = st.selectbox(
            "Compound",
            options=["—"] + [
                lbl for lbl, k in zip(compound_labels, compound_keys) if k not in already
            ],
            key=f"{state_key}_compound_choice",
        )
        if choice != "—":
            idx = compound_labels.index(choice)
            ck = compound_keys[idx]
            if st.button("Add to reaction", key=f"{state_key}_add_compound", type="primary"):
                _toggle(state_key, ck)
                st.rerun()

    selected = st.session_state[f"{state_key}_selected"]
    quantities = st.session_state[f"{state_key}_quantities"]

    # Selected chips + quantity sliders
    st.markdown("**Selected reagents**")
    if not selected:
        st.caption("No reagents yet — click an element above to add one.")
    else:
        chips_html = ""
        for k in selected:
            kind, ident = k.split(":", 1)
            if kind == "element":
                e = by_sym.get(ident, {})
                label = f"{ident} {e.get('name', '')}".strip()
            else:
                label = ident
            chips_html += f'<span class="pt-selected-chip">{label}</span>'
        st.markdown(chips_html, unsafe_allow_html=True)

        for k in list(selected):
            kind, ident = k.split(":", 1)
            if kind == "element":
                e = by_sym.get(ident, {})
                title = f"{ident} — {e.get('name', '')}"
            else:
                title = ident
            qcol, rcol = st.columns([5, 1])
            with qcol:
                quantities[k] = st.slider(
                    f"{title}  (mol)",
                    min_value=0.1, max_value=10.0,
                    value=float(quantities.get(k, 1.0)),
                    step=0.1,
                    key=f"{state_key}_qty_{k}",
                )
            with rcol:
                st.write("")
                st.button(
                    "✕",
                    key=f"{state_key}_rm_{k}",
                    help="Remove",
                    on_click=_toggle,
                    args=(state_key, k),
                )

    return list(selected), dict(quantities)


def reset_picker_state(state_key: str, selected: list[str], quantities: dict[str, float]) -> None:
    """Force-replace picker state. Call before render_picker on starter load."""
    st.session_state[f"{state_key}_selected"] = list(selected)
    st.session_state[f"{state_key}_quantities"] = dict(quantities)
    # Streamlit widget state is sticky: the per-reagent quantity sliders keep
    # their old values unless their widget keys are rewritten BEFORE they
    # render. Without this, a preset that says "2 mol" silently runs with
    # whatever the slider last showed.
    prefix = f"{state_key}_qty_"
    for wkey in [k for k in st.session_state.keys() if str(k).startswith(prefix)]:
        del st.session_state[wkey]
    for k, q in quantities.items():
        st.session_state[f"{prefix}{k}"] = float(q)
