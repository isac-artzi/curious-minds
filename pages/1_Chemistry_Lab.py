"""Chemistry What-If Lab — Curious Minds page."""

from __future__ import annotations

import html as _html

import streamlit as st
import streamlit.components.v1 as components

from curious_mind import llm, ui
from curious_mind.chemistry import data_loader, prompts
from curious_mind.chemistry.atom_3d import bohr_atom_figure, electron_config
from curious_mind.chemistry.mol_3d import (
    fetch_sdf_3d,
    mol_viewer_html,
    smiles_for_reactant,
)
from curious_mind.chemistry.periodic_table import render_picker, reset_picker_state
from curious_mind.chemistry.schemas import ReactionResult
from curious_mind.chemistry.atom_zoom import atom_zoom_height, atom_zoom_svg
from curious_mind.chemistry.theater import (
    heat_source_svg,
    render_theater,
    theater_height,
)
from curious_mind.chemistry.visuals import (
    energy_diagram_for,
    rate_vs_temperature_chart,
    reaction_flow_chart,
    reaction_flow_html,
    stoichiometry_chart,
)
from curious_mind.persistence import render_persistence_sidebar


ui.page_setup("Chemistry What-If Lab", "🧪")
ui.header("🧪 Chemistry What-If Lab", crumb="Curious Minds · Chemistry")

if not llm.have_api_key():
    ui.offline_banner()


PICKER_KEY = "chem"  # namespaces all picker state


def _default_inputs() -> dict:
    return {
        "selected": [],
        "quantities": {},
        "temperature_K": 298.0,
        "pressure_atm": 1.0,
        "catalyst": "spark",
        "mode": "realistic",
        "challenge_mode": False,
    }


def _apply_scenario(scenario: dict) -> None:
    """Load a Mad Scientist preset into session_state and force a fresh run."""
    sel: list[str] = []
    qty: dict[str, float] = {}
    for r in scenario.get("reagents", []):
        key = f"{r['kind']}:{r['key']}"
        sel.append(key)
        qty[key] = float(r.get("qty", 1.0))
    reset_picker_state(PICKER_KEY, sel, qty)
    cond_src = scenario.get("conditions", {})
    st.session_state.chem_conditions = {
        "temperature_K": float(cond_src.get("temperature_K", 298.0)),
        "pressure_atm":  float(cond_src.get("pressure_atm", 1.0)),
        "catalyst":      str(cond_src.get("catalyst", "spark")),
        "mode":          str(cond_src.get("mode", "realistic")),
    }
    st.session_state.pop("chem_last_result", None)
    st.session_state.pop("chem_last_signature", None)
    st.session_state.chem_active_scenario = scenario.get("id", "")
    # Reset any challenge-mode state so the new reaction starts fresh.
    st.session_state.pop("chem_challenge_revealed_sig", None)
    st.session_state.pop("chem_challenge_prediction", None)


# Seed picker state on first load only
if "chem_seeded" not in st.session_state:
    d = _default_inputs()
    reset_picker_state(PICKER_KEY, d["selected"], d["quantities"])
    st.session_state.chem_conditions = {
        "temperature_K": d["temperature_K"],
        "pressure_atm": d["pressure_atm"],
        "catalyst": d["catalyst"],
        "mode": d["mode"],
    }
    st.session_state.chem_seeded = True

# ============================================================================
# Sidebar — conditions only (picker is in main pane so user has room)
# ============================================================================
with st.sidebar:
    # -------- Mad Scientist preset menu ------------------------------------
    with st.expander("🧙 Mad Scientist Picks", expanded=False):
        st.caption("One-click curated experiments. Each loads reagents + conditions and runs.")
        _scenarios = data_loader.load_scenarios()
        for s in _scenarios:
            if st.button(s["label"], key=f"scn_{s['id']}", width="stretch"):
                _apply_scenario(s)
                st.toast(f"Loaded: {s['label']}")
                st.rerun()
            st.caption(s.get("blurb", ""))
        if not _scenarios:
            st.caption("_(No scenarios.json found.)_")

    st.markdown("### Conditions")
    cond = st.session_state.chem_conditions
    cond["temperature_K"] = float(
        st.slider(
            "Temperature (K)", min_value=10, max_value=10000,
            value=int(cond["temperature_K"]), step=10,
            help="From cryogenic (10 K) to plasma (10000 K).",
        )
    )
    # Live heat-source preview — updates instantly as the slider moves.
    st.markdown(
        f"<div style='display:flex;justify-content:center;margin:-4px 0 6px;'>"
        f"{heat_source_svg(cond['temperature_K'], width=90, height=90)}</div>",
        unsafe_allow_html=True,
    )
    cond["pressure_atm"] = float(
        st.select_slider(
            "Pressure (atm)",
            options=[0.001, 0.01, 0.1, 1, 10, 100, 1000, 10000, 100000, 1000000],
            value=float(cond["pressure_atm"]),
        )
    )
    cond["catalyst"] = st.text_input(
        "Catalyst / initiator",
        value=cond["catalyst"],
        help="e.g. 'spark', 'platinum', 'UV light', 'enzyme'.",
    )
    cond["mode"] = st.radio(
        "Mode",
        options=["realistic", "speculative"],
        index=0 if cond["mode"] == "realistic" else 1,
        horizontal=True,
        help="Realistic sticks to documented chemistry. Speculative lets Claude reason about exotic combinations and labels its speculation.",
    )

    # -------- Challenge mode toggle ----------------------------------------
    st.session_state.setdefault("chem_challenge_mode", False)
    st.session_state.chem_challenge_mode = st.toggle(
        "🎯 Challenge mode",
        value=st.session_state.chem_challenge_mode,
        help="Hides the answer until you commit a prediction. Great for classroom 'guess first' moments.",
    )

    st.divider()

    inputs_for_save = {
        "selected": st.session_state[f"{PICKER_KEY}_selected"],
        "quantities": st.session_state[f"{PICKER_KEY}_quantities"],
        "challenge_mode": st.session_state.chem_challenge_mode,
        **cond,
    }
    loaded = render_persistence_sidebar(
        "chemistry", inputs_for_save,
        title_default=" + ".join(
            k.split(":", 1)[1] for k in inputs_for_save["selected"][:3]
        ) or "Experiment",
    )
    if loaded:
        merged = {**_default_inputs(), **loaded}
        reset_picker_state(PICKER_KEY, merged["selected"], merged["quantities"])
        st.session_state.chem_conditions = {
            "temperature_K": merged["temperature_K"],
            "pressure_atm": merged["pressure_atm"],
            "catalyst": merged["catalyst"],
            "mode": merged["mode"],
        }
        st.session_state.chem_challenge_mode = bool(merged.get("challenge_mode", False))
        st.session_state.pop("chem_last_result", None)
        st.rerun()

    run_btn = st.button("⚗️ Run reaction", type="primary", width="stretch")
    st.caption("Tip: any change to reagents or conditions auto-runs on next page render.")
    cc1, cc2 = st.columns(2)
    with cc1:
        if st.button("♻️ Reset reagents", width="stretch",
                     help="Clear all selected elements and compounds."):
            reset_picker_state(PICKER_KEY, [], {})
            st.session_state.pop("chem_last_result", None)
            st.session_state.pop("chem_last_signature", None)
            st.rerun()
    with cc2:
        if st.button("🗑 Clear cache", width="stretch",
                     help="Forces a fresh call to Claude on the next reaction."):
            st.cache_data.clear()
            st.session_state.pop("chem_last_result", None)
            st.session_state.pop("chem_last_signature", None)
            st.toast("Cache cleared.")
            st.rerun()

# ============================================================================
# Main — periodic-table picker
# ============================================================================
selected_keys, quantities = render_picker(PICKER_KEY)

if not selected_keys:
    ui.info_panel(
        "👆 Click an element in the periodic table above (or expand <b>Add a compound</b>) "
        "to start building a reaction."
    )
    st.stop()

st.divider()

# ============================================================================
# Run + render
# ============================================================================
inputs = {
    "selected": selected_keys,
    "quantities": quantities,
    **st.session_state.chem_conditions,
}

# Cheap heuristic warnings for unrealistic setups (does NOT gate the LLM call).
_warnings = data_loader.sanity_warnings(selected_keys, st.session_state.chem_conditions)
for _w in _warnings:
    ui.warn_panel(f"⚠️ {_w}")

kb_subset = data_loader.relevant_kb_subset(selected_keys)
user_payload = {
    "components": [
        {"key": k, "moles": quantities.get(k, 1.0)} for k in selected_keys
    ],
    "conditions": {
        "temperature_K": inputs["temperature_K"],
        "pressure_atm": inputs["pressure_atm"],
        "catalyst": inputs["catalyst"],
    },
    "mode": inputs["mode"],
    "knowledge_base": kb_subset,
    "user_question": st.session_state.get("chem_user_question"),
}

# Detect any meaningful input change so we re-run without the user clicking
import json as _json

# A follow-up question applies to the inputs it was asked about; when any
# OTHER input changes, drop it so later runs aren't answering an old question.
_base_signature = _json.dumps(
    {k: v for k, v in user_payload.items() if k != "user_question"},
    sort_keys=True, default=str,
)
if st.session_state.get("chem_base_signature") not in (None, _base_signature):
    st.session_state.pop("chem_user_question", None)
    user_payload["user_question"] = None
st.session_state["chem_base_signature"] = _base_signature

input_signature = _json.dumps(user_payload, sort_keys=True, default=str)
# Short unique id for widget keys: the first characters of the raw
# signature are identical across runs, so hash the whole thing.
import hashlib as _hashlib
_sig_hash = _hashlib.md5(input_signature.encode()).hexdigest()[:12]

should_run = (
    run_btn
    or "chem_last_result" not in st.session_state
    or st.session_state.get("chem_last_signature") != input_signature
)

if should_run:
    with st.spinner("Computing reaction enthalpy and balanced equation…"):
        result, source = llm.call_structured(
            domain="chemistry",
            system_prompt=prompts.SYSTEM_PROMPT,
            user_payload=user_payload,
            schema=ReactionResult,
            fallback=prompts.FALLBACK_REACTION,
            max_tokens=1800,
        )
    st.session_state.chem_last_result = result
    st.session_state.chem_last_source = source
    st.session_state.chem_last_signature = input_signature

result: ReactionResult = st.session_state.chem_last_result
source: str = st.session_state.chem_last_source

ui.source_indicator(source)
if result.confidence == "speculative":
    ui.speculation_banner()

# ============================================================================
# Challenge mode gate — predict-then-reveal
# ============================================================================
_RXN_TYPE_CHOICES = [
    "synthesis", "decomposition", "single_replacement", "double_replacement",
    "acid_base", "redox", "combustion", "no_reaction", "other",
]


def _exo_endo(enthalpy_class: str) -> str:
    s = (enthalpy_class or "").lower()
    if "exo" in s:
        return "releases energy (exothermic)"
    if "endo" in s:
        return "absorbs energy (endothermic)"
    return "roughly thermoneutral"


def _normalize_phase(phase: str) -> str:
    p = (phase or "").lower().strip()
    for opt in ("solid", "liquid", "gas", "aqueous", "plasma"):
        if opt in p:
            return opt
    return "gas"  # safe default for the predict form


def _rxn_type_options(correct: str, seed: str) -> list[str]:
    """4 stable-shuffled reaction-type options including the correct one."""
    import random as _r
    rng = _r.Random(hash(seed) & 0xFFFFFFFF)
    pool = [t for t in _RXN_TYPE_CHOICES if t != correct]
    rng.shuffle(pool)
    picks = [correct] + pool[:3]
    rng.shuffle(picks)
    return picks


if st.session_state.chem_challenge_mode:
    _revealed = (
        st.session_state.get("chem_challenge_revealed_sig") == input_signature
    )
    if not _revealed:
        ui.info_panel(
            "🎯 <b>Challenge mode:</b> commit your predictions before the answer is revealed."
        )
        with st.form("chem_challenge_form", clear_on_submit=False):
            pred_energy = st.radio(
                "Will this reaction release or absorb energy?",
                options=["releases energy (exothermic)",
                         "absorbs energy (endothermic)",
                         "roughly thermoneutral"],
                index=0,
            )
            pred_phase = st.radio(
                "What phase will the main product be in at the given conditions?",
                options=["solid", "liquid", "gas", "aqueous", "plasma"],
                index=2, horizontal=True,
            )
            _rxn_options = _rxn_type_options(result.reaction_type, input_signature)
            pred_type = st.radio(
                "Which reaction type best describes what happens?",
                options=[t.replace("_", " ").title() for t in _rxn_options],
                index=0,
            )
            submit = st.form_submit_button("🔮 Reveal the answer", type="primary",
                                           width="stretch")
        if submit:
            st.session_state.chem_challenge_prediction = {
                "energy": pred_energy,
                "phase": pred_phase,
                "type": _rxn_options[
                    [t.replace("_", " ").title() for t in _rxn_options].index(pred_type)
                ],
            }
            st.session_state.chem_challenge_revealed_sig = input_signature
            st.rerun()
        st.stop()
    else:
        # Score chip
        pred = st.session_state.get("chem_challenge_prediction") or {}
        correct_energy = _exo_endo(result.enthalpy_class)
        correct_phase = _normalize_phase(result.primary_product.phase)
        correct_type = result.reaction_type
        rows = [
            ("Energy", pred.get("energy", ""), correct_energy),
            ("Product phase", pred.get("phase", ""), correct_phase),
            ("Reaction type",
             pred.get("type", "").replace("_", " ").title(),
             correct_type.replace("_", " ").title()),
        ]
        score = sum(1 for _, p, c in rows if p.strip().lower() == c.strip().lower())
        st.markdown(
            f"""<div style='background:linear-gradient(90deg,#10b981,#3b82f6);
            padding:12px 16px;border-radius:10px;color:white;margin-bottom:12px;'>
            <div style='font-size:1.3rem;font-weight:600;'>🎉 Score: {score} / 3</div>
            <div style='font-size:0.9rem;opacity:0.9;'>
            {"Perfect prediction!" if score == 3 else
             "Great instincts — see the reveal below." if score >= 2 else
             "Cool — let's see what really happens."}
            </div></div>""",
            unsafe_allow_html=True,
        )
        # Per-row table
        for label, p, c in rows:
            ok = p.strip().lower() == c.strip().lower()
            mark = "✅" if ok else "❌"
            st.markdown(
                f"- {mark} <b>{label}</b> · you said <code>{p or '—'}</code> · "
                f"answer: <code>{c}</code>",
                unsafe_allow_html=True,
            )

# ----- 1) Reaction Theater — the hero animated scene -----------------------
_theater_header_left, _theater_header_right = st.columns([3, 2])
with _theater_header_left:
    st.subheader("🎬 Reaction Theater")
with _theater_header_right:
    _zoom_on = st.toggle(
        "🔬 Zoom into atoms",
        key="chem_atom_zoom",
        help="Switch from the vessels view to an atom-level conservation scene.",
    )

reactant_records = [
    {"kind": k.split(":", 1)[0], "ident": k.split(":", 1)[1], "qty": quantities.get(k)}
    for k in selected_keys
]
if _zoom_on:
    components.html(
        atom_zoom_svg(result.balanced_equation),
        height=atom_zoom_height(),
    )
else:
    _theater_html = render_theater(
        reactants=reactant_records,
        product_phase=result.primary_product.phase,
        product_label=result.primary_product.formula or "?",
        byproduct_labels=[bp.formula for bp in result.byproducts if bp.formula],
        reactant_colors=result.reactant_colors,
        product_colors=result.product_colors,
        visual_effects=result.visual_effects,
        dramatic_moment=result.dramatic_moment,
        temperature_K=st.session_state.chem_conditions["temperature_K"],
    )
    components.html(_theater_html, height=theater_height())

with st.expander("📋 Reaction summary card", expanded=False):
    st.markdown(
        reaction_flow_html(
            reactants=reactant_records,
            primary_product={
                "formula": result.primary_product.formula,
                "name": result.primary_product.name,
                "phase": result.primary_product.phase,
            },
            byproducts=[
                {"formula": bp.formula, "name": bp.name, "phase": bp.phase}
                for bp in result.byproducts
            ],
            enthalpy_kJ_per_mol=result.enthalpy_kJ_per_mol,
            enthalpy_class=result.enthalpy_class,
            catalyst=inputs["catalyst"],
        ),
        unsafe_allow_html=True,
    )

# ----- 2) Balanced equation + headline metrics ----------------------------
left, right = st.columns([3, 2])
with left:
    st.subheader("Balanced equation")
    if result.balanced_equation:
        st.latex(result.balanced_equation)
    else:
        st.caption("No balanced equation returned.")
    st.markdown(
        f"**Primary product:** `{result.primary_product.formula}` — "
        f"{result.primary_product.name} ({result.primary_product.phase}) "
        f"· {result.primary_product.amount_estimation or '—'}"
    )
    if result.byproducts:
        st.markdown("**Byproducts:**")
        for bp in result.byproducts:
            st.markdown(f"- `{bp.formula}` — {bp.name} ({bp.phase})")

with right:
    st.markdown(
        "**Confidence** "
        "<span title='well_documented = textbook chemistry · probable = reasonable extrapolation · "
        "speculative = beyond established science'>ⓘ</span>",
        unsafe_allow_html=True,
    )
    st.markdown(ui.confidence_badge(result.confidence), unsafe_allow_html=True)
    st.markdown("**Reaction type**")
    st.caption(result.reaction_type.replace("_", " ").title())
    st.markdown("**Phase at conditions**")
    st.caption(result.phase_at_conditions or "—")
    mc1, mc2 = st.columns(2)
    with mc1:
        if result.enthalpy_kJ_per_mol is not None:
            st.metric(
                "ΔH (kJ/mol)", f"{result.enthalpy_kJ_per_mol:+.0f}",
                help="Energy released (negative) or absorbed (positive) per mole of primary product.",
            )
    with mc2:
        if result.activation_energy_kJ_per_mol is not None:
            st.metric(
                "Eₐ (kJ/mol)", f"{result.activation_energy_kJ_per_mol:.0f}",
                help="Activation energy — the kinetic barrier the system must climb before products can form.",
            )
if result.equilibrium_notes:
    ui.info_panel(f"⚖️ <b>Equilibrium:</b> {_html.escape(result.equilibrium_notes)}")

# ----- 3) Energy diagram + Sankey side by side -----------------------------
ec1, ec2 = st.columns([3, 2])
with ec1:
    st.plotly_chart(
        energy_diagram_for(result.enthalpy_class, result.enthalpy_kJ_per_mol),
        width="stretch",
    )
    with st.expander("ℹ️ How is this computed?"):
        st.markdown(
            "- **Reactants** are pinned at energy 0.\n"
            "- **Products** sit at +ΔH (so an exothermic reaction *drops*).\n"
            "- The **transition state** is placed at "
            "`max(reactant, product) + max(0.25·|ΔH|, 60)` kJ/mol — a stand-in for "
            "the activation barrier when an explicit Eₐ isn't returned. The dedicated "
            "**Arrhenius rate** chart below uses Claude's Eₐ estimate when available."
        )
with ec2:
    st.plotly_chart(
        reaction_flow_chart(
            reactants=reactant_records,
            primary_product={
                "formula": result.primary_product.formula,
                "name": result.primary_product.name,
                "phase": result.primary_product.phase,
            },
            byproducts=[
                {"formula": bp.formula, "name": bp.name, "phase": bp.phase}
                for bp in result.byproducts
            ],
            enthalpy_kJ_per_mol=result.enthalpy_kJ_per_mol,
        ),
        width="stretch",
    )
    st.caption("Sankey: node thickness = mole share, not mass.")

# ----- 3b) Stoichiometry + rate-vs-T --------------------------------------
sc1, sc2 = st.columns(2)
with sc1:
    st.markdown("**Stoichiometry (moles per balanced equation)**")
    products_for_chart = [{
        "formula": result.primary_product.formula,
        "name": result.primary_product.name,
        "amount": result.primary_product.amount_estimation,
    }] + [
        {"formula": bp.formula, "name": bp.name, "amount": bp.amount_estimation}
        for bp in result.byproducts
    ]
    st.plotly_chart(
        stoichiometry_chart(reactant_records, products_for_chart),
        width="stretch",
    )

with sc2:
    if result.activation_energy_kJ_per_mol is not None and result.activation_energy_kJ_per_mol > 0:
        st.markdown("**Reaction rate vs. temperature**")
        st.plotly_chart(
            rate_vs_temperature_chart(
                result.activation_energy_kJ_per_mol,
                st.session_state.chem_conditions["temperature_K"],
            ),
            width="stretch",
        )
        with st.expander("ℹ️ Arrhenius equation"):
            st.markdown(
                "Rate constant $k = A \\cdot e^{-E_a / (RT)}$, with $R = 8.314 \\times 10^{-3}$ kJ/(mol·K) "
                "and a fixed pre-factor $A = 10^{13}$ s⁻¹. Y-axis is **relative**; only the "
                "slope of the curve matters pedagogically. The curve climbs steeply once "
                "$RT \\sim E_a$."
            )
    else:
        st.markdown("**Reaction rate vs. temperature**")
        st.caption("No activation energy returned; rate curve hidden.")

# ----- 4) Mechanism + real-world ------------------------------------------
if result.mechanism:
    st.subheader("What's happening")
    st.write(result.mechanism)
if result.real_world_connection:
    st.subheader("Why it matters")
    st.write(result.real_world_connection)

if result.safety_notes:
    st.subheader("Safety & honesty")
    for note in result.safety_notes:
        ui.warn_panel(f"⚠️ {note}")

# ----- 4b) Quiz me panel --------------------------------------------------
if result.quiz:
    with st.expander("🧠 Quiz me on this reaction", expanded=False):
        st.caption("Pick an answer, then click *Reveal* to check yourself.")
        for qi, q in enumerate(result.quiz):
            st.markdown(f"**Q{qi + 1}. {q.question}**")
            ans_key = f"chem_quiz_{_sig_hash}_{qi}_ans"
            rev_key = f"chem_quiz_{_sig_hash}_{qi}_rev"
            choice = st.radio(
                "Your answer:",
                options=q.choices,
                key=ans_key,
                label_visibility="collapsed",
                index=None,
            )
            cols = st.columns([1, 5])
            with cols[0]:
                if st.button("Reveal", key=f"btn_{rev_key}"):
                    st.session_state[rev_key] = True
            if st.session_state.get(rev_key):
                correct = q.choices[q.correct_index]
                if choice == correct:
                    st.success(f"✅ Correct — {q.explanation}")
                else:
                    st.error(
                        f"❌ Answer: **{correct}**" +
                        (f" — {q.explanation}" if q.explanation else "")
                    )
            st.markdown("---")

# ----- 5) 3D atomic structure (Bohr model) --------------------------------
_selected_elements = [
    k.split(":", 1)[1] for k in selected_keys if k.startswith("element:")
]
if _selected_elements:
    with st.expander("🔬 Atomic structure (3D Bohr model)", expanded=False):
        st.caption(
            "Simplified Bohr-model view: nucleus at center, electrons in concentric shells. "
            "Drag to rotate. Shell capacities use the K=2, L=8, M=8/18, N=8/18/32 pattern; "
            "Aufbau exceptions (Cr, Cu, etc.) are not modeled."
        )
        cols_per_row = 3
        for row_start in range(0, len(_selected_elements), cols_per_row):
            row_syms = _selected_elements[row_start:row_start + cols_per_row]
            cols = st.columns(len(row_syms))
            for col, sym in zip(cols, row_syms):
                rec = data_loader.element_by_symbol(sym) or {}
                with col:
                    st.plotly_chart(
                        bohr_atom_figure(
                            symbol=sym,
                            atomic_number=int(rec.get("atomic_number", 0)),
                            category=rec.get("category", ""),
                            name=rec.get("name", ""),
                        ),
                        width="stretch",
                    )
                    cfg = electron_config(int(rec.get("atomic_number", 0)))
                    st.caption(
                        f"Electron config (Bohr): {', '.join(str(n) for n in cfg) or '0'}"
                    )

# ----- 6) 3D molecule view (PubChem + 3Dmol.js) ---------------------------
with st.expander("🧬 3D molecule view", expanded=False):
    st.caption(
        "Live 3D structures fetched from PubChem; rendered with 3Dmol.js. "
        "Not all species (especially ionic salts and exotic intermediates) have "
        "published 3D conformers — those show a placeholder."
    )

    def _render_one(label: str, smiles: str | None, formula: str | None, height: int = 280) -> None:
        st.markdown(f"**{label}**")
        sdf = fetch_sdf_3d(smiles=smiles, formula=formula)
        if not sdf:
            st.caption("_(No 3D structure available from PubChem.)_")
            return
        components.html(mol_viewer_html(sdf, height=height), height=height + 10)
        if not smiles and formula:
            # Formula → CID lookup is ambiguous (C₂H₆O could be ethanol OR
            # dimethyl ether) — be honest about what's shown.
            st.caption(f"_A molecule with formula {formula} (isomer not guaranteed)._")

    # Build reactant + product lists once
    _reactant_panels = [
        (r["ident"], *smiles_for_reactant(r["kind"], r["ident"]))
        for r in reactant_records[:3]
    ]
    _product_panels: list[tuple[str, str | None, str | None]] = [(
        result.primary_product.formula or "?",
        result.primary_product.smiles or None,
        result.primary_product.formula or None,
    )]
    for bp in result.byproducts[:2]:
        _product_panels.append((
            bp.formula or "?",
            bp.smiles or None,
            bp.formula or None,
        ))

    tab_react, tab_prod, tab_side = st.tabs(["Reactants", "Products", "Side-by-side"])

    with tab_react:
        cols = st.columns(max(len(_reactant_panels), 1))
        for col, (label, smi, fml) in zip(cols, _reactant_panels):
            with col:
                _render_one(label, smi, fml)

    with tab_prod:
        cols = st.columns(max(len(_product_panels), 1))
        for col, (label, smi, fml) in zip(cols, _product_panels):
            with col:
                _render_one(label, smi, fml)

    with tab_side:
        left_col, arrow_col, right_col = st.columns([5, 1, 5])
        with left_col:
            st.markdown("##### Reactants")
            for label, smi, fml in _reactant_panels:
                _render_one(label, smi, fml, height=220)
        with arrow_col:
            st.markdown(
                "<div style='text-align:center; font-size:3rem; color:#1F3864; "
                "padding-top:4rem;'>⟶</div>",
                unsafe_allow_html=True,
            )
        with right_col:
            st.markdown("##### Products")
            for label, smi, fml in _product_panels:
                _render_one(label, smi, fml, height=220)

# ----- 7) Concepts glossary -----------------------------------------------
with st.expander("📖 Concepts (chemistry refresher)"):
    st.markdown(
        """
- **Balanced equation** — reactants and products written so every atom on the left
  also appears on the right. Coefficients are *moles*, not masses.
- **Mole** — a count: 6.022 × 10²³ particles. Lets us go between counts and
  weighable masses.
- **Stoichiometry** — the bookkeeping of how many moles react with how many
  to make how many. Driven by the balanced equation's coefficients.
- **ΔH (enthalpy change, kJ/mol)** — energy released (negative) or absorbed
  (positive) per mole of primary product, at constant pressure.
- **Exothermic / endothermic** — releases / absorbs heat. *Strongly* means roughly
  > |200| kJ/mol.
- **Activation energy (Eₐ)** — the kinetic hill the reactants must climb
  before products can form. Catalysts lower this hill.
- **Transition state** — the high-energy, fleeting structure at the top of the hill.
- **Catalyst vs. initiator** — a catalyst speeds the reaction without being
  consumed; an initiator (spark, UV) just *starts* a reaction that's already
  thermodynamically favorable.
- **Phase** — solid, liquid, gas, aqueous, plasma. Depends on T and P.
- **STP (Standard Temperature & Pressure)** — 273.15 K (0°C) and 1 atm. Many
  textbook reactions are tabulated here.
- **Oxidation state** — the bookkeeping charge an atom would have if all its
  bonds were ionic. Changes during redox reactions.
- **Equilibrium** — when forward and reverse reactions balance and net
  composition stops changing. Le Chatelier's principle predicts how T or P
  shifts shift the equilibrium.
- **Reaction types** — synthesis (A+B→C), decomposition (C→A+B),
  single/double replacement, acid–base (proton transfer), redox
  (electron transfer), combustion (fast oxidation by O₂).
- **Confidence tiers** —
  *well_documented* (textbook), *probable* (defensible extrapolation),
  *speculative* (beyond established science).
"""
    )

# ----- 8) Follow-ups -------------------------------------------------------
clicked = ui.follow_up_buttons(result.follow_ups, "chem")
if clicked:
    # Inject the question into the payload (same pattern as the other labs);
    # the payload change also busts the cache so a fresh call runs.
    st.session_state.chem_user_question = clicked
    st.session_state.pop("chem_last_result", None)
    st.session_state.pop("chem_last_signature", None)
    st.toast(f"Exploring: {clicked}")
    st.rerun()
