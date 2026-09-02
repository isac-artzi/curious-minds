"""Ecosystem / Biome Lab — Curious Minds page."""

from __future__ import annotations

import html as _html

import streamlit as st
import streamlit.components.v1 as components

from curious_mind import llm, ui
from curious_mind.ecosystem import data_loader, prompts
from curious_mind.ecosystem.schemas import EcosystemResult
from curious_mind.ecosystem.theater import biome_theater_height, render_biome_theater
from curious_mind.ecosystem.visuals import (
    climate_comparison_figure,
    food_web_figure,
    keystone_impact_figure,
    population_dynamics_figure,
    shannon_diversity_figure,
    simulate_populations,
    trophic_pyramid_figure,
)
from curious_mind.persistence import render_persistence_sidebar


ui.page_setup("Ecosystem Lab", "🌿")
ui.header("🌿 Ecosystem / Biome Lab", crumb="Curious Minds · Ecosystem")

# Hide Streamlit's per-chart "View fullscreen" button. It clones the chart
# DOM into a modal, which breaks Plotly's animation state binding — after
# exiting fullscreen, the Play / Restart buttons silently no-op because they
# point at a div that no longer exists. The chart is already 560 px tall and
# fully interactive, so this is a clean tradeoff.
st.markdown(
    "<style>button[title='View fullscreen']{display:none;}</style>",
    unsafe_allow_html=True,
)

if not llm.have_api_key():
    ui.offline_banner()


HORIZON_OPTIONS = [1, 5, 20, 25, 30, 50, 100]


def _default_inputs() -> dict:
    return {
        "biome_id": "yellowstone",
        "species_ids": ["wolf_gray", "elk", "beaver", "cottonwood", "willow", "grizzly_bear"],
        "populations": {
            "wolf_gray": 30,
            "elk": 800,
            "beaver": 50,
            "cottonwood": 500,
            "willow": 600,
            "grizzly_bear": 20,
        },
        "disturbance_id": None,
        "disturbance_year": None,
        "horizon_years": 25,
        "climate_dT_C": 0.0,
        "climate_dP_pct": 0.0,
        "protect": {},   # species_id -> intrinsic-rate multiplier
        "hunt": {},      # species_id -> annual mortality fraction
    }


if "eco_inputs" not in st.session_state:
    st.session_state.eco_inputs = _default_inputs()
else:
    # Backfill new keys for sessions that pre-date the climate/intervention sliders.
    for k, v in _default_inputs().items():
        st.session_state.eco_inputs.setdefault(k, v)


def _apply_eco_scenario(scn: dict) -> None:
    """Load a Showcase preset into session_state.eco_inputs and force a rerun."""
    base = _default_inputs()
    sc_inputs = scn.get("inputs", {}) or {}
    new = {**base, **sc_inputs}
    # Make sure populations + dicts are proper types after JSON roundtrip.
    new["populations"] = {str(k): float(v) for k, v in (new.get("populations") or {}).items()}
    new["protect"] = {str(k): float(v) for k, v in (new.get("protect") or {}).items()}
    new["hunt"] = {str(k): float(v) for k, v in (new.get("hunt") or {}).items()}
    st.session_state.eco_inputs = new
    # Reset widget keys so the new biome/species selection takes effect.
    for s in data_loader.load_species():
        st.session_state[f"chk_{s['id']}"] = (s["id"] in new["species_ids"])
    for key in list(st.session_state.keys()):
        if key.startswith(("pop_", "protect_", "hunt_")):
            del st.session_state[key]
    st.session_state.pop("eco_last_result", None)
    st.session_state.pop("eco_last_signature", None)
    st.session_state.pop("eco_challenge_revealed_sig", None)
    st.session_state.pop("eco_challenge_prediction", None)
    st.session_state["eco_active_scenario_preset"] = scn.get("id", "")
    st.session_state["eco_active_preset_callout"] = scn.get("callout", "")


biomes = data_loader.load_biomes()
species_all = data_loader.load_species()
disturbances = data_loader.load_disturbances()
biome_lookup = {b["id"]: b for b in biomes}
species_lookup = {s["id"]: s for s in species_all}


def _default_pop_for(species: dict) -> int:
    """Sensible starting population by trophic level."""
    return {
        "decomposer": 400,
        "producer": 600,
        "primary_consumer": 300,
        "secondary_consumer": 60,
        "apex_predator": 20,
    }.get(species.get("trophic_level", "primary_consumer"), 100)


with st.sidebar:
    # -------- Showcase preset menu ----------------------------------------
    with st.expander("🧙 Showcase experiments", expanded=False):
        st.caption("One-click curated biomes + species + disturbance.")
        _scenarios = data_loader.load_scenarios()
        for s in _scenarios:
            if st.button(s["label"], key=f"eco_scn_{s['id']}", width="stretch"):
                _apply_eco_scenario(s)
                st.toast(f"Loaded: {s['label']}")
                st.rerun()
            if s.get("blurb"):
                st.caption(s["blurb"])
        if not _scenarios:
            st.caption("_(No scenarios.json found.)_")

    st.markdown("### Biome")
    biome_id = st.selectbox(
        "Pick a biome",
        options=[b["id"] for b in biomes],
        index=[b["id"] for b in biomes].index(st.session_state.eco_inputs["biome_id"]),
        format_func=lambda b: biome_lookup[b]["name"],
    )

    # Auto-load characteristic species when the biome changes — otherwise
    # picking a new biome would have no visible effect on the picker.
    if st.session_state.eco_inputs.get("biome_id") != biome_id:
        chars = [
            sid for sid in biome_lookup[biome_id].get("characteristic_species", [])
            if sid in species_lookup
        ]
        chars_set = set(chars)
        st.session_state.eco_inputs["biome_id"] = biome_id
        st.session_state.eco_inputs["species_ids"] = chars
        st.session_state.eco_inputs["populations"] = {
            sid: _default_pop_for(species_lookup[sid]) for sid in chars
        }
        st.session_state.eco_inputs["protect"] = {}
        st.session_state.eco_inputs["hunt"] = {}
        # Explicitly set every checkbox key to its new value. Just deleting
        # the keys is unreliable in Streamlit — the widget framework can
        # repopulate stale state on the next rerun. Writing the key directly
        # before the widget renders forces it to honor the new value.
        for s in species_all:
            st.session_state[f"chk_{s['id']}"] = (s["id"] in chars_set)
        for key in list(st.session_state.keys()):
            if key.startswith(("pop_", "protect_", "hunt_")):
                del st.session_state[key]
        st.session_state.pop("eco_last_result", None)
        st.session_state.pop("eco_last_signature", None)
        st.rerun()

    biome = biome_lookup[biome_id]
    st.caption(f"🌍 {biome.get('real_world', '')}")
    st.caption(f"☁️ {biome.get('climate', '')}")

    st.markdown("### Species")
    char_set = set(biome.get("characteristic_species", []))
    default_species = set(st.session_state.eco_inputs["species_ids"])

    # Group species by trophic level so the picker reads top→bottom of the web
    _TROPHIC_ORDER = [
        ("apex_predator", "🦁 Apex predators"),
        ("secondary_consumer", "🦊 Carnivores"),
        ("primary_consumer", "🦌 Herbivores"),
        ("producer", "🌱 Producers"),
        ("decomposer", "🍄 Decomposers"),
    ]
    species_by_level: dict[str, list[dict]] = {k: [] for k, _ in _TROPHIC_ORDER}
    for s in species_all:
        lvl = s.get("trophic_level", "primary_consumer")
        species_by_level.setdefault(lvl, []).append(s)
    for lvl in species_by_level:
        species_by_level[lvl].sort(key=lambda s: s.get("common_name", "").lower())

    species_ids: list[str] = []
    for lvl, label in _TROPHIC_ORDER:
        items = species_by_level.get(lvl, [])
        if not items:
            continue
        with st.expander(label, expanded=any(s["id"] in default_species for s in items)):
            for s in items:
                native_marker = " 🏡" if s["id"] in char_set else ""
                checked = st.checkbox(
                    f"{s.get('emoji', '•')} {s['common_name']}{native_marker}",
                    value=s["id"] in default_species,
                    key=f"chk_{s['id']}",
                    help=(s.get("binomial", "") + ("  ·  native to this biome" if s["id"] in char_set else "")),
                )
                if checked:
                    species_ids.append(s["id"])
    st.caption("🏡 = native to selected biome")

    populations: dict[str, int] = {}
    if species_ids:
        st.markdown("### Starting populations")
        for sid in species_ids:
            prev = st.session_state.eco_inputs["populations"].get(sid, 100)
            populations[sid] = st.slider(
                f"{species_lookup[sid].get('emoji', '•')} {species_lookup[sid]['common_name']}",
                min_value=0,
                max_value=2000,
                value=int(prev),
                step=10,
                key=f"pop_{sid}",
                help="Initial relative population at year 0. Toy units, not real headcounts.",
            )

    st.markdown("### Climate")
    climate_dT_C = st.slider(
        "ΔTemperature (°C vs. present)", min_value=-5.0, max_value=8.0,
        value=float(st.session_state.eco_inputs.get("climate_dT_C", 0.0)),
        step=0.5,
        help="Sustained shift from today's average. ±5 °C is enough to push biomes "
             "(e.g. tundra → boreal). Affects producer growth most.",
    )
    climate_dP_pct = st.slider(
        "ΔPrecipitation (% vs. present)", min_value=-60, max_value=60,
        value=int(st.session_state.eco_inputs.get("climate_dP_pct", 0.0)),
        step=5,
        help="Sustained change in annual rainfall. <-40% implies sustained drought; "
             ">+40% implies sustained flooding.",
    )

    st.markdown("### Human intervention (optional)")
    with st.expander("Protect / hunt species", expanded=False):
        protect: dict[str, float] = {}
        hunt: dict[str, float] = {}
        if not species_ids:
            st.caption("Pick species first to see intervention sliders.")
        for sid in species_ids:
            sp = species_lookup[sid]
            label = f"{sp.get('emoji', '•')} {sp['common_name']}"
            st.markdown(f"**{label}**")
            cols = st.columns(2)
            with cols[0]:
                p = st.slider(
                    "Protect ×", 1.0, 2.0,
                    value=float(st.session_state.eco_inputs.get("protect", {}).get(sid, 1.0)),
                    step=0.1, key=f"protect_{sid}",
                    help="Multiplier on intrinsic growth (e.g. anti-poaching, habitat restoration).",
                )
            with cols[1]:
                h = st.slider(
                    "Hunt /yr", 0.0, 0.5,
                    value=float(st.session_state.eco_inputs.get("hunt", {}).get(sid, 0.0)),
                    step=0.05, key=f"hunt_{sid}",
                    help="Annual mortality fraction added by humans (hunt, fishing, culling).",
                )
            if p != 1.0:
                protect[sid] = p
            if h > 0.0:
                hunt[sid] = h

    st.markdown("### Event")
    distur_options = [None] + [d["id"] for d in disturbances]
    distur_id = st.selectbox(
        "Inject a disturbance (optional)",
        options=distur_options,
        index=distur_options.index(st.session_state.eco_inputs["disturbance_id"])
        if st.session_state.eco_inputs["disturbance_id"] in distur_options
        else 0,
        format_func=lambda d: "— none —" if d is None else next(x["name"] for x in disturbances if x["id"] == d),
        help="A one-off shock applied at a specific year (fire, drought, disease, etc.).",
    )

    horizon = st.radio(
        "Time horizon (years)", options=HORIZON_OPTIONS, horizontal=True,
        index=HORIZON_OPTIONS.index(st.session_state.eco_inputs["horizon_years"])
        if st.session_state.eco_inputs["horizon_years"] in HORIZON_OPTIONS else 2,
        help="How far the simulation runs. Long horizons amplify climate and "
             "human-intervention signals.",
    )
    distur_year = None
    if distur_id is not None:
        distur_year = st.slider(
            "Disturbance year", min_value=0, max_value=horizon,
            value=min(st.session_state.eco_inputs.get("disturbance_year") or max(1, horizon // 4), horizon),
        )

    st.session_state.eco_inputs = {
        "biome_id": biome_id,
        "species_ids": species_ids,
        "populations": populations,
        "disturbance_id": distur_id,
        "disturbance_year": distur_year,
        "horizon_years": horizon,
        "climate_dT_C": climate_dT_C,
        "climate_dP_pct": climate_dP_pct,
        "protect": protect,
        "hunt": hunt,
    }

    # -------- Challenge mode toggle ---------------------------------------
    st.session_state.setdefault("eco_challenge_mode", False)
    st.session_state.eco_challenge_mode = st.toggle(
        "🎯 Challenge mode",
        value=st.session_state.eco_challenge_mode,
        help="Hides the answer until you commit a prediction. Great for "
             "classroom 'guess first' moments.",
    )

    st.divider()
    inputs_for_save = {
        **st.session_state.eco_inputs,
        "challenge_mode": st.session_state.eco_challenge_mode,
    }
    loaded = render_persistence_sidebar(
        "ecosystem", inputs_for_save,
        title_default=biome_lookup[biome_id]["name"],
    )
    if loaded:
        st.session_state.eco_challenge_mode = bool(loaded.pop("challenge_mode", False))
        st.session_state.eco_inputs = {**_default_inputs(), **loaded}
        st.session_state.pop("eco_last_result", None)
        st.session_state.pop("eco_last_signature", None)
        st.session_state.pop("eco_challenge_revealed_sig", None)
        st.session_state.pop("eco_challenge_prediction", None)
        st.rerun()

    run_btn = st.button("🌱 Run scenario", type="primary", width="stretch")

# ---- main ------------------------------------------------------------
inputs = st.session_state.eco_inputs

if not inputs["species_ids"]:
    ui.info_panel(
        "👈 Pick a biome, populate it with species, optionally inject a disturbance, "
        "then press <b>Run scenario</b>."
    )
    st.stop()

species_records = [species_lookup[s] for s in inputs["species_ids"]]

# Off-biome banner — call out species the user added that don't belong here.
biome_chars = set(biome_lookup[inputs["biome_id"]].get("characteristic_species", []))
off_biome = [species_lookup[sid] for sid in inputs["species_ids"] if sid not in biome_chars]
if off_biome:
    names = ", ".join(f"<b>{s.get('emoji', '•')} {s['common_name']}</b>" for s in off_biome)
    biome_name = biome_lookup[inputs["biome_id"]]["name"]
    ui.warn_panel(
        f"🤔 Unlikely for {names} to live in <b>{biome_name}</b>, but let's run the "
        "thought experiment and see what might happen. Claude will flag this in the "
        "scenario summary."
    )

# Cheap heuristic warnings — surfaced before any LLM call.
warnings = data_loader.sanity_warnings(
    inputs["biome_id"], inputs["species_ids"], inputs["populations"],
    disturbance_id=inputs["disturbance_id"],
    disturbance_year=inputs["disturbance_year"],
    horizon_years=inputs["horizon_years"],
    climate_dT=inputs["climate_dT_C"],
    climate_dP_pct=inputs["climate_dP_pct"],
)
for w in warnings:
    ui.warn_panel(w)

# Shared simulation — every dynamics chart on the page consumes this.
sim_t, sim_pops = simulate_populations(
    species_records, inputs["populations"], inputs["horizon_years"],
    disturbance_year=inputs["disturbance_year"],
    climate_dT_C=inputs["climate_dT_C"],
    climate_dP_pct=inputs["climate_dP_pct"],
    protect=inputs["protect"],
    hunt=inputs["hunt"],
)
final_pops = {sid: vals[-1] for sid, vals in sim_pops.items()}

# ---- LLM cascade narrative ------------------------------------------
# Run BEFORE charts so the theater hero can use Claude's caption + moment.
import json as _json

kb = data_loader.relevant_kb_subset(
    inputs["biome_id"], inputs["species_ids"], inputs["disturbance_id"]
)
payload = {
    "biome_id": inputs["biome_id"],
    "species_with_populations": [
        {**species_lookup[sid], "initial_population": inputs["populations"].get(sid, 100)}
        for sid in inputs["species_ids"]
    ],
    "disturbance": kb["disturbance"],
    "disturbance_year": inputs["disturbance_year"],
    "time_horizon_years": inputs["horizon_years"],
    "climate_dT_C": inputs["climate_dT_C"],
    "climate_dP_pct": inputs["climate_dP_pct"],
    "protect": inputs["protect"],
    "hunt": inputs["hunt"],
    "knowledge_base": kb,
    # If the user clicked a follow-up, fold it into the payload so it both
    # reaches Claude AND changes the cache key (otherwise we'd hit the cache
    # and show the same answer again).
    "user_question": st.session_state.get("eco_user_question"),
}
# Drop a stale follow-up question as soon as any other input changes.
_base_signature = _json.dumps(
    {k: v for k, v in payload.items() if k != "user_question"},
    sort_keys=True, default=str,
)
if st.session_state.get("eco_base_signature") not in (None, _base_signature):
    st.session_state.pop("eco_user_question", None)
    payload["user_question"] = None
st.session_state["eco_base_signature"] = _base_signature

input_signature = _json.dumps(payload, sort_keys=True, default=str)
# Short unique id for widget keys: the first characters of the raw
# signature are identical across runs, so hash the whole thing.
import hashlib as _hashlib
_sig_hash = _hashlib.md5(input_signature.encode()).hexdigest()[:12]

# The Showcase-preset callout describes a specific curated setup; once the
# user edits any input away from it, retire the banner.
if st.session_state.get("eco_active_scenario_preset"):
    _preset_sig = st.session_state.get("eco_active_preset_sig")
    if _preset_sig is None:
        st.session_state["eco_active_preset_sig"] = input_signature
    elif _preset_sig != input_signature:
        st.session_state.pop("eco_active_scenario_preset", None)
        st.session_state.pop("eco_active_preset_callout", None)
        st.session_state.pop("eco_active_preset_sig", None)

should_run = (
    run_btn
    or "eco_last_result" not in st.session_state
    or st.session_state.get("eco_last_signature") != input_signature
)
if should_run:
    with st.spinner("Reasoning over the food web…"):
        result, source = llm.call_structured(
            domain="ecosystem",
            system_prompt=prompts.SYSTEM_PROMPT,
            user_payload=payload,
            schema=EcosystemResult,
            fallback=prompts.FALLBACK,
            max_tokens=3500,
        )
    st.session_state.eco_last_result = result
    st.session_state.eco_last_source = source
    st.session_state.eco_last_signature = input_signature

result: EcosystemResult = st.session_state.eco_last_result
source: str = st.session_state.eco_last_source

ui.source_indicator(source)
if result.confidence == "speculative":
    ui.speculation_banner()

# Showcase preset callout banner (one-line "what to notice").
if (
    st.session_state.get("eco_active_scenario_preset")
    and st.session_state.get("eco_active_preset_callout")
):
    ui.info_panel(f"💡 {st.session_state['eco_active_preset_callout']}")


# ===========================================================================
# Challenge mode gate — predict-then-reveal
# ===========================================================================
def _eco_recovery_bucket(years: int | None, has_disturbance: bool) -> int:
    """0 = none/no disturbance, 1 = <5 yr, 2 = 5–25 yr, 3 = >25 yr."""
    if not has_disturbance or years is None:
        return 0
    if years < 5:
        return 1
    if years <= 25:
        return 2
    return 3


def _eco_challenge_questions(
    res: EcosystemResult,
    inp: dict,
    final_pops_: dict[str, float],
) -> list[dict]:
    """Return predict-then-reveal MCQs derived from sim + Claude's result."""
    out: list[dict] = []

    # Q1: biodiversity trend ------------------------------------------------
    biodiv_opts = [
        "Biodiversity goes UP", "Stays the same",
        "Goes DOWN", "Collapses",
    ]
    biodiv_idx = {
        "increases": 0, "stable": 1, "decreases": 2, "collapses": 3,
    }.get(res.biodiversity_index_change, 1)
    out.append({
        "question": "What happens to overall biodiversity over the horizon?",
        "options": biodiv_opts,
        "correct_index": biodiv_idx,
    })

    # Q2: does any species go locally extinct in the simulator? ------------
    init = inp.get("populations") or {}
    extirpated_sim = any(
        float(final_pops_.get(sid, 0.0)) < 1.0 and float(init.get(sid, 0.0)) > 0
        for sid in inp.get("species_ids", [])
    )
    out.append({
        "question": "Does any species locally go extinct?",
        "options": ["Yes — at least one species vanishes", "No — they all survive"],
        "correct_index": 0 if extirpated_sim else 1,
    })

    # Q3: recovery timescale (only if there's a disturbance) ---------------
    has_dist = bool(inp.get("disturbance_id"))
    if has_dist:
        rec_opts = [
            "Doesn't recover within horizon",
            "Under 5 years",
            "5–25 years",
            "Over 25 years",
        ]
        rb = _eco_recovery_bucket(res.recovery_timescale_years, True)
        out.append({
            "question": "How long until the system looks like it did before the disturbance?",
            "options": rec_opts,
            "correct_index": rb,
        })

    return out


if st.session_state.eco_challenge_mode:
    _ch_q = _eco_challenge_questions(result, inputs, final_pops)
    _revealed = (
        st.session_state.get("eco_challenge_revealed_sig") == input_signature
    )
    if _ch_q and not _revealed:
        ui.info_panel(
            "🎯 <b>Challenge mode:</b> commit your predictions before the answer is revealed."
        )
        with st.form("eco_challenge_form", clear_on_submit=False):
            picks: list[int] = []
            for qi, q in enumerate(_ch_q):
                choice = st.radio(
                    f"**Q{qi + 1}. {q['question']}**",
                    options=list(range(len(q["options"]))),
                    format_func=lambda i, opts=q["options"]: opts[i],
                    index=0,
                    key=f"eco_pred_{_sig_hash}_{qi}",
                )
                picks.append(int(choice))
            submit_pred = st.form_submit_button(
                "🔮 Reveal the answer", type="primary",
                width="stretch",
            )
        if submit_pred:
            st.session_state.eco_challenge_prediction = picks
            st.session_state.eco_challenge_revealed_sig = input_signature
            st.rerun()
        st.stop()
    elif _ch_q and _revealed:
        picks = st.session_state.get("eco_challenge_prediction") or []
        score = 0
        rows: list[tuple[str, str, str, bool]] = []
        for qi, q in enumerate(_ch_q):
            user_idx = picks[qi] if qi < len(picks) else -1
            correct_idx = int(q["correct_index"])
            ok = user_idx == correct_idx
            score += int(ok)
            rows.append((
                q["question"],
                q["options"][user_idx] if 0 <= user_idx < len(q["options"]) else "—",
                q["options"][correct_idx],
                ok,
            ))
        total = len(_ch_q)
        celebrate = (
            "Perfect prediction!" if score == total else
            "Great instincts — see the reveal below." if score >= max(1, total // 2 + 1)
            else "Cool — let's see what really happens."
        )
        st.markdown(
            f"""<div style='background:linear-gradient(90deg,#10b981,#3b82f6);
            padding:12px 16px;border-radius:10px;color:white;margin-bottom:12px;'>
            <div style='font-size:1.3rem;font-weight:600;'>🎉 Score: {score} / {total}</div>
            <div style='font-size:0.9rem;opacity:0.9;'>{celebrate}</div>
            </div>""",
            unsafe_allow_html=True,
        )
        for question, you, ans, ok in rows:
            mark = "✅" if ok else "❌"
            st.markdown(
                f"- {mark} <b>{question}</b> · you said <code>{you}</code> · "
                f"answer: <code>{ans}</code>",
                unsafe_allow_html=True,
            )

# ---- 🎬 Living Biome Theater hero ------------------------------------
st.subheader("🎬 Living Biome Theater")
components.html(
    render_biome_theater(
        inputs["biome_id"],
        species_records,
        final_pops,
        caption=result.visual_caption,
        dramatic=result.dramatic_moment,
        seed=hash(input_signature) & 0xFFFFFFFF,
    ),
    height=biome_theater_height(),
)

# Food web — always rendered, no LLM needed
left, right = st.columns([1, 1])
with left:
    st.subheader(
        "🕸️ Food web",
        help="Who eats whom in this scenario. Arrows point from prey to predator. "
             "Vertical position = trophic level (Producers at the bottom, Apex at the top). "
             "Built from each species' diet plus curated predation records.",
    )
    st.plotly_chart(
        food_web_figure(
            species_records,
            data_loader.load_interactions(),
        ),
        width="stretch",
    )

with right:
    st.subheader(
        "📈 Population dynamics",
        help="Toy Lotka–Volterra simulation over the chosen horizon. Each line is "
             "one species. Press ▶ Play to watch populations evolve, or drag the "
             "slider. See 'How is this computed?' below for the equations.",
    )
    st.plotly_chart(
        population_dynamics_figure(
            species_records,
            inputs["populations"],
            years=inputs["horizon_years"],
            disturbance_year=inputs["disturbance_year"],
            climate_dT_C=inputs["climate_dT_C"],
            climate_dP_pct=inputs["climate_dP_pct"],
            protect=inputs["protect"],
            hunt=inputs["hunt"],
            precomputed=(sim_t, sim_pops),
        ),
        width="stretch",
    )
    with st.expander("ℹ️ How is this computed?"):
        st.markdown(
            "Toy logistic + Lotka–Volterra-style sim:\n\n"
            "- Each species has an intrinsic growth rate (positive for producers, "
            "near-zero or negative for consumers) and a carrying capacity by tier.\n"
            "- Predators gain a small boost per unit of prey present; prey lose "
            "a slightly larger amount per predator (`+0.0008 · pred · prey`, `-0.0010 · pred · prey`).\n"
            "- Climate sliders rescale producer growth (warming + rain → more productive, "
            "extremes → penalty); animals get a milder climate-stress penalty.\n"
            "- 'Protect ×' multiplies intrinsic growth; 'Hunt /yr' adds annual mortality.\n"
            "- A disturbance, if scheduled, multiplies every population by `(1 - strength)` "
            "in the matching year.\n\n"
            "**Pedagogical only — not predictive.** Real food webs need calibrated "
            "parameters, age structure, spatial dynamics, and stochastic events."
        )

# ---- Trophic pyramid + diversity meter -------------------------------
st.subheader(
    "📊 System health",
    help="Two snapshots of the ecosystem at the END of the horizon: a trophic "
         "pyramid (biomass per tier) and a Shannon diversity gauge (how many "
         "species there are AND how evenly they're distributed).",
)
m1, m2 = st.columns([2, 1])
with m1:
    st.plotly_chart(
        trophic_pyramid_figure(species_records, final_pops),
        width="stretch",
    )
with m2:
    st.plotly_chart(
        shannon_diversity_figure(final_pops),
        width="stretch",
    )
    st.caption(
        "Shannon **H′** combines species count and evenness. "
        "0 = monoculture · 1–2 = simple system · 2+ = species-rich."
    )

# ---- Climate comparison panel ---------------------------------------
if abs(inputs["climate_dT_C"]) > 0.01 or abs(inputs["climate_dP_pct"]) > 0.01:
    st.subheader(
        "🌡️ Climate comparison",
        help="Same scenario rerun under two climates: present-day on the left, "
             "your ΔT / Δprecip choices on the right. Lets you see what climate "
             "alone is doing to the trajectory, separate from disturbances or "
             "human intervention.",
    )
    st.plotly_chart(
        climate_comparison_figure(
            species_records, inputs["populations"], inputs["horizon_years"],
            climate_dT_C=inputs["climate_dT_C"],
            climate_dP_pct=inputs["climate_dP_pct"],
            disturbance_year=inputs["disturbance_year"],
            protect=inputs["protect"], hunt=inputs["hunt"],
        ),
        width="stretch",
    )

st.subheader(
    "Scenario summary",
    help="Claude's two-sentence read on what this scenario is and where it's headed. "
         "Generated from the species, climate, and disturbance you chose plus a "
         "curated knowledge base of real interactions.",
)
st.write(result.summary)

# ---- High-level metrics from the new schema fields -------------------
metric_cols = st.columns(4)
with metric_cols[0]:
    risk_emoji = {"none": "✅", "low": "🟢", "moderate": "🟡", "high": "🔴"}
    st.metric(
        "Invasive risk",
        f"{risk_emoji.get(result.invasive_risk, '•')} {result.invasive_risk.title()}",
        help="How likely an introduced species in this scenario establishes "
             "and disrupts native dynamics.",
    )
with metric_cols[1]:
    biodiv_emoji = {
        "increases": "📈", "stable": "➡️", "decreases": "📉", "collapses": "💀",
    }
    st.metric(
        "Biodiversity trend",
        f"{biodiv_emoji.get(result.biodiversity_index_change, '•')} "
        f"{result.biodiversity_index_change.title()}",
        help="Qualitative direction of Shannon diversity over the horizon, "
             "as judged by Claude.",
    )
with metric_cols[2]:
    rec = result.recovery_timescale_years
    st.metric(
        "Recovery time",
        f"{rec} yr" if rec is not None else "—",
        help="Best-guess years to return to a state similar to the start, "
             "after the disturbance. Empty if no disturbance or recovery is implausible.",
    )
with metric_cols[3]:
    st.markdown("**Confidence**")
    st.markdown(ui.confidence_badge(result.confidence), unsafe_allow_html=True)

# ---- Keystone callout + comparison chart -----------------------------
if result.keystone_species:
    keystone_names = []
    for ksid in result.keystone_species:
        sp = species_lookup.get(ksid)
        keystone_names.append(
            f"{sp.get('emoji', '•')} {sp.get('common_name', ksid)}" if sp else ksid
        )
    ui.info_panel(
        "🗝️ <b>Keystone species:</b> " + ", ".join(keystone_names) +
        " — removal would most reshape this scenario."
    )
    # Render a comparison chart for the first keystone that's actually selected.
    primary_keystone = next(
        (k for k in result.keystone_species if k in inputs["populations"]),
        None,
    )
    if primary_keystone is not None and len(species_records) > 1:
        ki_fig = keystone_impact_figure(
            species_records, inputs["populations"], inputs["horizon_years"],
            primary_keystone,
            disturbance_year=inputs["disturbance_year"],
            climate_dT_C=inputs["climate_dT_C"],
            climate_dP_pct=inputs["climate_dP_pct"],
            protect=inputs["protect"], hunt=inputs["hunt"],
        )
        if ki_fig is not None:
            st.plotly_chart(ki_fig, width="stretch")

if result.cascade:
    st.subheader(
        "Cascade",
        help="Step-by-step ripple of effects through the food web. Each step has a "
             "confidence badge: well-documented (real case study), probable "
             "(extrapolated from similar systems), or speculative (long-horizon or novel).",
    )
    for i, step in enumerate(result.cascade, start=1):
        st.markdown(
            f"**{i}.** {step.step}  &nbsp; {ui.confidence_badge(step.confidence)}",
            unsafe_allow_html=True,
        )

if result.species_outcomes:
    st.subheader(
        "Species outcomes",
        help="Per-species verdict at the end of the horizon — thriving 📈, "
             "stable ➡️, stressed 📉, or extirpated 💀 (locally extinct).",
    )
    cols = st.columns(min(4, len(result.species_outcomes)))
    arrow = {"thriving": "📈", "stable": "➡️", "stressed": "📉", "extirpated": "💀"}
    for i, so in enumerate(result.species_outcomes):
        with cols[i % len(cols)]:
            st.markdown(f"**{arrow.get(so.direction, '•')} {so.common_name}**")
            st.caption(so.note)

if result.real_world_analogue:
    st.subheader(
        "Real-world analogue",
        help="A documented case from real ecology that most resembles this scenario "
             "— a sanity anchor so abstract dynamics map onto something concrete.",
    )
    ui.info_panel(_html.escape(result.real_world_analogue))

if result.conservation_note:
    st.subheader(
        "Conservation note",
        help="What this scenario implies for management: protected areas, hunting "
             "policy, invasive control, climate adaptation. Connects the simulation "
             "to actual decisions.",
    )
    st.write(result.conservation_note)

clicked = ui.follow_up_buttons(result.follow_ups, "eco")
if clicked:
    # Inject the question into the payload so the cache key changes AND
    # Claude sees the new question on the next render.
    st.session_state.eco_user_question = clicked
    st.session_state.pop("eco_last_result", None)
    st.session_state.pop("eco_last_signature", None)
    st.toast(f"Exploring: {clicked}")
    st.rerun()

# ---- 🧠 Quiz panel ---------------------------------------------------
if result.quiz:
    with st.expander("🧠 Quiz me on this ecosystem", expanded=False):
        st.caption("Pick an answer, then click *Reveal* to check yourself.")
        for qi, q in enumerate(result.quiz):
            st.markdown(f"**Q{qi + 1}. {q.question}**")
            ans_key = f"eco_quiz_{_sig_hash}_{qi}_ans"
            rev_key = f"eco_quiz_{_sig_hash}_{qi}_rev"
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

# ---- Concept glossary -----------------------------------------------
with st.expander("📖 Concepts"):
    st.markdown(
        "- **Trophic level** — position in the food web. "
        "Producers → herbivores (primary consumers) → carnivores (secondary) → apex predators.\n"
        "- **Food web** — directed graph of who eats whom. Arrows point from prey to predator.\n"
        "- **Keystone species** — a species whose removal disproportionately reshapes the system "
        "(e.g. wolves in Yellowstone, sea otters in kelp forests).\n"
        "- **Trophic cascade** — change at one level rippling up or down the web.\n"
        "- **10% rule** — only ~10% of the energy at one trophic level becomes biomass at the next, "
        "which is why pyramids taper.\n"
        "- **Shannon diversity (H′)** — `−Σ pᵢ · ln pᵢ` where `pᵢ` is each species' share of total "
        "population. Higher = more even mix.\n"
        "- **Invasive risk** — chance an introduced species establishes and disrupts native dynamics.\n"
        "- **Disturbance** — a one-off shock (fire, flood, disease, hunting pulse).\n"
        "- **Recovery timescale** — how long the system needs to look like its pre-disturbance state.\n"
        "- **Climate ΔT / Δprecip** — sustained shifts vs. today's average. ±5 °C is enough to "
        "shift biomes (e.g. tundra → boreal forest).\n"
        "- **Confidence tiers** — `well_documented` (real case studies), `probable` (extrapolated "
        "from similar systems), `speculative` (long-horizon or novel combinations)."
    )

ui.footer()
