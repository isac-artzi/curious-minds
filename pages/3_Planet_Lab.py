"""Planet / Exoplanet Builder — Curious Minds page."""

from __future__ import annotations

import html as _html
import json as _json

import streamlit as st
import streamlit.components.v1 as components

from curious_mind import llm, ui
from curious_mind.planets import data_loader, prompts
from curious_mind.planets.schemas import PlanetResult
from curious_mind.planets.theater import planet_theater_height, render_planet_theater
from curious_mind.planets.visuals import (
    atmosphere_donut,
    injection_evolution_figure,
    sky_swatch_html,
    system_diagram,
    transmission_spectrum_figure,
)
from curious_mind.persistence import render_persistence_sidebar


ui.page_setup("Planet Builder", "🪐")
ui.header("🪐 Planet / Exoplanet Builder", crumb="Curious Minds · Planets")

if not llm.have_api_key():
    ui.offline_banner()


# ---- defaults --------------------------------------------------------------
def _default_inputs() -> dict:
    return {
        "star_name": "Sun",
        "distance_AU": 1.0,
        "mass_earth": 1.0,
        "radius_earth": 1.0,
        "rotation_period_hours": 24.0,
        "atmosphere_id": "earth_like",
        "water_pct": 50,
        "moons": 1,
        # Interventions
        "magnetic_field": "strong",
        "atmosphere_tweak": {"action": "none", "gas": "CO2", "amount_pct": 5.0},
        "terraforming_target": "none",
        "seeding_what": "none",
        "seeding_where": "ocean",
        "seeding_horizon": "1M_yr",
    }


if "planet_inputs" not in st.session_state:
    st.session_state.planet_inputs = _default_inputs()

# Load knowledge base
named_stars = data_loader.load_named_stars()
star_class_records = data_loader.load_stars()
atmospheres = data_loader.load_atmospheres()
star_lookup = {s["name"]: s for s in named_stars}
star_class_lookup = {s["spectral_class"]: s for s in star_class_records}
atm_lookup = {a["id"]: a for a in atmospheres}

# Group named stars by spectral class for picker order (G/K/M up top — most relevant)
_CLASS_ORDER = ["G", "K", "M", "F", "A", "B", "O"]
stars_by_class: dict[str, list[dict]] = {}
for s in named_stars:
    stars_by_class.setdefault(s["spectral_class"], []).append(s)

# Backwards-compat: older saved presets use spectral_class instead of star_name
if "star_name" not in st.session_state.planet_inputs:
    spc = st.session_state.planet_inputs.pop("spectral_class", "G")
    cands = stars_by_class.get(spc, [])
    st.session_state.planet_inputs["star_name"] = cands[0]["name"] if cands else "Sun"

# Apply defaults for any missing intervention keys (older saved presets)
for k, v in _default_inputs().items():
    st.session_state.planet_inputs.setdefault(k, v)


def _apply_planet_scenario(scn: dict) -> None:
    """Overwrite planet_inputs with the scenario's preset values and bust cache."""
    base = _default_inputs()
    base.update(scn.get("inputs", {}))
    st.session_state.planet_inputs = base
    st.session_state.pop("planet_last_result", None)
    st.session_state.pop("planet_last_signature", None)
    st.session_state.pop("planet_user_question", None)
    st.session_state.pop("planet_challenge_revealed_sig", None)
    st.session_state.pop("planet_challenge_score", None)
    st.session_state["planet_active_scenario"] = scn["id"]


def _planet_temp_bucket(T_C: float) -> str:
    if T_C < -50:
        return "frozen (<−50 °C)"
    if T_C < 0:
        return "chilly (−50 to 0 °C)"
    if T_C < 35:
        return "temperate (0–35 °C)"
    if T_C < 200:
        return "hot (35–200 °C)"
    return "inferno (>200 °C)"


def _planet_challenge_questions(derived: dict, result: "PlanetResult", inputs: dict) -> list[dict]:
    T_C = (
        result.surface.avg_temperature_C
        if result.surface.avg_temperature_C
        else derived["greenhouse_surface_T_C"]
    )
    return [
        {
            "key": "verdict",
            "prompt": "Will Claude rate this world as…?",
            "choices": ["🟢 Habitable", "🟡 Extremophiles only", "🔴 Non-habitable"],
            "answer": {
                "habitable": "🟢 Habitable",
                "extremophile_only": "🟡 Extremophiles only",
                "non_habitable": "🔴 Non-habitable",
            }.get(result.verdict, "🟡 Extremophiles only"),
        },
        {
            "key": "temp",
            "prompt": "What temperature bucket fits the surface?",
            "choices": [
                "frozen (<−50 °C)",
                "chilly (−50 to 0 °C)",
                "temperate (0–35 °C)",
                "hot (35–200 °C)",
                "inferno (>200 °C)",
            ],
            "answer": _planet_temp_bucket(T_C),
        },
        {
            "key": "tidal",
            "prompt": "Is this planet likely tidally locked to its star?",
            "choices": ["🔒 Yes — tidally locked", "🔓 No — free rotation"],
            "answer": (
                "🔒 Yes — tidally locked"
                if derived["tidal_locking_likely"]
                else "🔓 No — free rotation"
            ),
        },
    ]


# ---- sidebar ---------------------------------------------------------------
with st.sidebar:
    with st.expander("🧙 Showcase worlds", expanded=False):
        st.caption("One-click curated planets — handy for demos.")
        scenarios = data_loader.load_scenarios()
        for scn in scenarios:
            cols = st.columns([1, 0.001])
            if cols[0].button(
                scn.get("label", scn["id"]),
                key=f"planet_preset_{scn['id']}",
                use_container_width=True,
                help=scn.get("blurb", ""),
            ):
                _apply_planet_scenario(scn)
                st.toast(f"Loaded: {scn.get('label', scn['id'])}")
                st.rerun()

    challenge_mode = st.toggle(
        "🎯 Challenge mode",
        value=bool(st.session_state.get("planet_challenge_mode", False)),
        help=(
            "Predict-then-reveal: guess the verdict, surface temperature bucket, "
            "and tidal-locking status before seeing Claude's answer."
        ),
    )
    st.session_state["planet_challenge_mode"] = challenge_mode

    st.markdown("### Star")
    star_options: list[str] = []
    for cls in _CLASS_ORDER:
        for s in stars_by_class.get(cls, []):
            star_options.append(s["name"])

    cur_name = st.session_state.planet_inputs.get("star_name", "Sun")
    if cur_name not in star_options:
        cur_name = "Sun"

    star_name = st.selectbox(
        "Pick a star",
        options=star_options,
        index=star_options.index(cur_name),
        format_func=lambda n: (
            f"{n}  ·  {star_lookup[n]['spectral_class']}-class  ·  "
            f"L={star_lookup[n]['luminosity_solar']:g} L☉"
        ),
    )
    star = star_lookup[star_name]
    spectral = star["spectral_class"]
    star_class_data = star_class_lookup[spectral]
    st.caption(
        f"Mass {star['mass_solar']:g} M☉ · Age {star['age_Gyr']:g} Gyr"
        f"{' · ⚡ flare-active' if star.get('flare_active') else ''}"
    )
    st.caption(star.get("notes", ""))

    st.markdown("### Orbit")
    distance_AU = st.select_slider(
        "Orbital distance (AU)",
        options=[0.01, 0.03, 0.05, 0.1, 0.3, 0.5, 1.0, 1.5, 3.0, 5.0, 10.0, 30.0, 100.0],
        value=st.session_state.planet_inputs.get("distance_AU", 1.0),
        help=(
            "Average distance from the host star, in Astronomical Units. "
            "1 AU = Earth–Sun distance ≈ 150 million km."
        ),
    )

    st.markdown("### Planet")
    mass_earth = st.slider(
        "Mass (Earth masses)", min_value=0.1, max_value=20.0,
        value=float(st.session_state.planet_inputs["mass_earth"]), step=0.1,
        help="Planet mass relative to Earth (1 M⊕ = 5.97 × 10²⁴ kg).",
    )
    radius_earth = st.slider(
        "Radius (Earth radii)", min_value=0.3, max_value=5.0,
        value=float(st.session_state.planet_inputs["radius_earth"]), step=0.1,
        help="Planet radius relative to Earth (1 R⊕ = 6,371 km).",
    )
    rotation_period_hours = st.select_slider(
        "Rotation period (hours)",
        options=[1, 6, 10, 12, 24, 48, 100, 240, 720, 1408, 2000, 5832],
        value=int(st.session_state.planet_inputs.get("rotation_period_hours", 24)),
        format_func=lambda h: {
            10: "10 h (Jupiter)", 24: "24 h (Earth)", 1408: "1408 h (Mercury)",
            5832: "5832 h (Venus, retrograde)",
        }.get(int(h), f"{h} h"),
        help=(
            "How long the planet takes to spin once on its axis. "
            "If we detect tidal locking (orbit close to the star), the effective "
            "day equals the year and this slider is overridden."
        ),
    )
    density_g_per_cm3 = (mass_earth / (radius_earth ** 3)) * 5.51
    st.caption(f"→ Density ≈ {density_g_per_cm3:.2f} g/cm³ (Earth = 5.51)")

    st.markdown("### Atmosphere")
    atm_id = st.selectbox(
        "Composition archetype",
        options=[a["id"] for a in atmospheres],
        index=[a["id"] for a in atmospheres].index(st.session_state.planet_inputs["atmosphere_id"]),
        format_func=lambda i: atm_lookup[i]["name"],
        help=(
            "Pre-built atmosphere templates. Each carries a fixed composition AND "
            "a surface pressure (Mars=0.006 atm, Earth=1 atm, Venus=92 atm)."
        ),
    )

    water_pct = st.slider(
        "Water budget (%)", min_value=0, max_value=100,
        value=int(st.session_state.planet_inputs["water_pct"]),
        help="0% = desert world; 100% = ocean world. Affects available solvent for life.",
    )

    moons = st.radio(
        "Moons", options=[0, 1, 2, 5], horizontal=True,
        index=[0, 1, 2, 5].index(st.session_state.planet_inputs["moons"])
        if st.session_state.planet_inputs["moons"] in [0, 1, 2, 5] else 1,
        help="A large moon stabilizes axial tilt — relevant for long-term climate stability.",
    )

    # ---- INTERVENTIONS (the fun part) --------------------------------
    with st.expander("🛠 Interventions", expanded=False):
        st.markdown("**Planetary magnetic field**")
        mf_options = ["none", "weak", "strong", "artificial_shield"]
        mf_labels = {
            "none": "None (Mars-like)",
            "weak": "Weak",
            "strong": "Strong (Earth-like)",
            "artificial_shield": "Artificial L1 magnetic shield 🛰",
        }
        cur_mf = st.session_state.planet_inputs.get("magnetic_field", "strong")
        if cur_mf not in mf_options:
            cur_mf = "strong"
        magnetic_field = st.radio(
            "Strength",
            options=mf_options,
            index=mf_options.index(cur_mf),
            format_func=lambda v: mf_labels[v],
        )

        st.divider()
        st.markdown("**Atmosphere tweak** — perturb the chosen archetype with one gas.")
        cur_tweak = st.session_state.planet_inputs.get("atmosphere_tweak") or {}
        tweak_actions = ["none", "add", "remove", "replace"]
        tweak_action = st.selectbox(
            "Action",
            options=tweak_actions,
            index=tweak_actions.index(cur_tweak.get("action", "none")),
            format_func=lambda a: {
                "none": "— no tweak —",
                "add": "Add gas",
                "remove": "Remove gas",
                "replace": "Set gas to %",
            }[a],
        )
        gas_options = ["CO2", "O2", "N2", "CH4", "NH3", "H2O", "H2", "He", "Ar", "SO2"]
        tweak_gas = st.selectbox(
            "Gas",
            options=gas_options,
            index=gas_options.index(cur_tweak.get("gas", "CO2"))
            if cur_tweak.get("gas", "CO2") in gas_options else 0,
            disabled=(tweak_action == "none"),
        )
        tweak_amount = st.slider(
            "Amount (% by volume)",
            min_value=0.0, max_value=99.0,
            value=float(cur_tweak.get("amount_pct", 5.0)),
            step=1.0,
            disabled=(tweak_action == "none"),
        )
        atmosphere_tweak = {
            "action": tweak_action,
            "gas": tweak_gas,
            "amount_pct": tweak_amount,
        }

        st.divider()
        st.markdown("**Terraforming goal** — what would it take?")
        terraforming_options = [
            "none", "warm_it_up", "cool_it_down",
            "thicken_atmosphere", "add_ocean", "oxygenate", "magnetize",
        ]
        terraforming_labels = {
            "none": "— none —",
            "warm_it_up": "Warm it up",
            "cool_it_down": "Cool it down",
            "thicken_atmosphere": "Thicken the atmosphere",
            "add_ocean": "Add a liquid ocean",
            "oxygenate": "Oxygenate the air",
            "magnetize": "Give it a magnetosphere",
        }
        cur_tt = st.session_state.planet_inputs.get("terraforming_target", "none")
        if cur_tt not in terraforming_options:
            cur_tt = "none"
        terraforming_target = st.selectbox(
            "Target",
            options=terraforming_options,
            index=terraforming_options.index(cur_tt),
            format_func=lambda v: terraforming_labels[v],
        )

        st.divider()
        st.markdown("**Seeding scenario** ⚠️ speculative thought experiment")
        seeding_options = [
            "none", "prebiotic_organics", "amino_acids",
            "rna_precursors", "extremophile_microbes",
        ]
        seeding_labels = {
            "none": "— none —",
            "prebiotic_organics": "Prebiotic organics (formaldehyde, HCN)",
            "amino_acids": "Amino acids",
            "rna_precursors": "RNA precursors (nucleotides)",
            "extremophile_microbes": "Earth extremophile microbes",
        }
        cur_sw = st.session_state.planet_inputs.get("seeding_what", "none")
        if cur_sw not in seeding_options:
            cur_sw = "none"
        seeding_what = st.selectbox(
            "What to seed",
            options=seeding_options,
            index=seeding_options.index(cur_sw),
            format_func=lambda v: seeding_labels[v],
        )
        seeding_where_options = ["ocean", "subsurface", "atmosphere"]
        cur_sw_where = st.session_state.planet_inputs.get("seeding_where", "ocean")
        if cur_sw_where not in seeding_where_options:
            cur_sw_where = "ocean"
        seeding_where = st.radio(
            "Where",
            options=seeding_where_options,
            index=seeding_where_options.index(cur_sw_where),
            horizontal=True,
            disabled=(seeding_what == "none"),
        )
        seeding_horizon_options = ["1k_yr", "1M_yr", "1Gyr"]
        cur_sw_h = st.session_state.planet_inputs.get("seeding_horizon", "1M_yr")
        if cur_sw_h not in seeding_horizon_options:
            cur_sw_h = "1M_yr"
        seeding_horizon = st.radio(
            "Time horizon",
            options=seeding_horizon_options,
            index=seeding_horizon_options.index(cur_sw_h),
            format_func=lambda v: {"1k_yr": "1,000 yr", "1M_yr": "1 Myr", "1Gyr": "1 Gyr"}[v],
            horizontal=True,
            disabled=(seeding_what == "none"),
        )

    # commit input snapshot
    st.session_state.planet_inputs = {
        "star_name": star_name,
        "distance_AU": float(distance_AU),
        "mass_earth": float(mass_earth),
        "radius_earth": float(radius_earth),
        "rotation_period_hours": float(rotation_period_hours),
        "atmosphere_id": atm_id,
        "water_pct": int(water_pct),
        "moons": int(moons),
        "magnetic_field": magnetic_field,
        "atmosphere_tweak": atmosphere_tweak,
        "terraforming_target": terraforming_target,
        "seeding_what": seeding_what,
        "seeding_where": seeding_where,
        "seeding_horizon": seeding_horizon,
    }

    st.divider()
    _inputs_for_save = {
        **st.session_state.planet_inputs,
        "challenge_mode": bool(st.session_state.get("planet_challenge_mode", False)),
    }
    loaded = render_persistence_sidebar(
        "planet", _inputs_for_save,
        title_default=f"{star_name} @ {distance_AU} AU",
    )
    if loaded:
        st.session_state["planet_challenge_mode"] = bool(loaded.pop("challenge_mode", False))
        st.session_state.planet_inputs = {**_default_inputs(), **loaded}
        st.rerun()

    run_btn = st.button("🪐 Build planet", type="primary", use_container_width=True)


# ---- main ------------------------------------------------------------------
inputs = st.session_state.planet_inputs
star = star_lookup[inputs["star_name"]]
spectral = star["spectral_class"]
star_class_data = star_class_lookup[spectral]
atm_base = atm_lookup[inputs["atmosphere_id"]]
atm = data_loader.apply_atmosphere_tweak(atm_base, inputs.get("atmosphere_tweak"))

# Use the SPECIFIC star's luminosity — no more mid-luminosity collapse
L = star["luminosity_solar"]
hz_inner, hz_outer = data_loader.habitable_zone(L)
T_eq = data_loader.equilibrium_temperature_K(L, inputs["distance_AU"])
T_surf_C = data_loader.greenhouse_surface_T_C(
    T_eq, inputs["atmosphere_id"], atm.get("surface_pressure_atm", 1.0),
)

_tidally_locked = data_loader.tidal_locking_likely(
    inputs["distance_AU"], star["mass_solar"], star["age_Gyr"],
)
_year_yr = data_loader.orbital_period_years(inputs["distance_AU"], star["mass_solar"])
_day_h = data_loader.effective_day_length_hours(
    inputs.get("rotation_period_hours", 24.0), _tidally_locked, _year_yr,
)

derived = {
    "habitable_zone_AU": [hz_inner, hz_outer],
    "in_habitable_zone": hz_inner <= inputs["distance_AU"] <= hz_outer,
    "equilibrium_temperature_K": T_eq,
    "equilibrium_temperature_C": T_eq - 273.15,
    "greenhouse_surface_T_C": T_surf_C,
    "orbital_period_years": _year_yr,
    "orbital_period_days": _year_yr * 365.25,
    "rotation_period_hours": inputs.get("rotation_period_hours", 24.0),
    "effective_day_length_hours": _day_h,
    "tidal_locking_likely": _tidally_locked,
    "flare_risk": data_loader.flare_risk(
        spectral, star["age_Gyr"], star.get("flare_active", False),
    ),
    "pressure_supports_liquid_water": data_loader.pressure_supports_liquid_water(
        atm.get("surface_pressure_atm", 1.0),
    ),
    "atmospheric_retention_risk": data_loader.atmospheric_retention(
        inputs["mass_earth"], inputs["radius_earth"], T_eq, inputs["magnetic_field"],
    ),
}

density_g_per_cm3 = (inputs["mass_earth"] / (inputs["radius_earth"] ** 3)) * 5.51
esi = data_loader.earth_similarity_index(inputs["radius_earth"], density_g_per_cm3, T_surf_C)

# ---- LLM verdict (moved up so the theater can show Claude's caption) -------
closest = data_loader.closest_real_exoplanet(
    inputs["mass_earth"], inputs["radius_earth"], inputs["distance_AU"], spectral,
)

interventions = {
    "magnetic_field": inputs["magnetic_field"],
    "atmosphere_tweak": inputs["atmosphere_tweak"],
    "terraforming_target": inputs["terraforming_target"],
    "seeding": (
        {
            "what_to_seed": inputs["seeding_what"],
            "where": inputs["seeding_where"],
            "time_horizon": inputs["seeding_horizon"],
        }
        if inputs["seeding_what"] != "none"
        else None
    ),
}

payload = {
    "star": star,
    "orbit_AU": inputs["distance_AU"],
    "planet": {
        "mass_earth": inputs["mass_earth"],
        "radius_earth": inputs["radius_earth"],
        "density_g_per_cm3": density_g_per_cm3,
        "earth_similarity_index": esi,
    },
    "atmosphere": atm,
    "water_pct": inputs["water_pct"],
    "moons": inputs["moons"],
    "derived": derived,
    "interventions": interventions,
    "closest_real_exoplanet": closest,
    "user_question": st.session_state.get("planet_user_question"),
}

input_signature = _json.dumps(payload, sort_keys=True, default=str)
should_run = (
    run_btn
    or "planet_last_result" not in st.session_state
    or st.session_state.get("planet_last_signature") != input_signature
)

if should_run:
    with st.spinner("Computing habitability and sky conditions…"):
        result, source = llm.call_structured(
            domain="planets",
            system_prompt=prompts.SYSTEM_PROMPT,
            user_payload=payload,
            schema=PlanetResult,
            fallback=prompts.FALLBACK,
            max_tokens=3500,
        )
    st.session_state.planet_last_result = result
    st.session_state.planet_last_source = source
    st.session_state.planet_last_signature = input_signature

result: PlanetResult = st.session_state.planet_last_result
source: str = st.session_state.planet_last_source

# ---- Challenge gate state --------------------------------------------------
_challenge_on = bool(st.session_state.get("planet_challenge_mode", False))
_revealed = (not _challenge_on) or (
    st.session_state.get("planet_challenge_revealed_sig") == input_signature
)

# ---- Living Planet Theater (hero) ------------------------------------------
components.html(
    render_planet_theater(
        star=star,
        star_color_hex=star_class_data["color_hex"],
        distance_AU=inputs["distance_AU"],
        radius_earth=inputs["radius_earth"],
        atmosphere_id=inputs["atmosphere_id"],
        surface_T_C=result.surface.avg_temperature_C if result.surface.avg_temperature_C else T_surf_C,
        surface_pressure_atm=result.surface.surface_pressure_atm or atm.get("surface_pressure_atm", 1.0),
        water_pct=int(inputs["water_pct"]),
        moons=int(inputs["moons"]),
        tidally_locked=_tidally_locked,
        flare_risk=derived["flare_risk"],
        verdict=result.verdict if _revealed else None,
        dramatic=result.dramatic_moment if _revealed else "",
        caption=result.visual_caption if _revealed else "",
        seed=hash(input_signature) & 0xFFFFFF,
    ),
    height=planet_theater_height() + 8,
)

# ---- Active scenario callout (from Showcase preset) ------------------------
_active_id = st.session_state.get("planet_active_scenario")
if _active_id:
    _scn = data_loader.scenario_by_id(_active_id)
    if _scn and _scn.get("callout"):
        ui.info_panel(
            f"🧙 <b>{_html.escape(_scn.get('label', _scn['id']))}</b> — "
            f"{_html.escape(_scn['callout'])}"
        )

# ---- Predict-then-Reveal form (Challenge mode) -----------------------------
if not _revealed:
    _q_list = _planet_challenge_questions(derived, result, inputs)
    with st.form("planet_challenge_form"):
        st.subheader("🎯 Predict before reveal")
        st.caption(
            "Make a guess for each. Submit to unlock Claude's verdict, the metrics, "
            "and the sky description."
        )
        _predictions: dict[str, str] = {}
        for q in _q_list:
            _predictions[q["key"]] = st.radio(
                q["prompt"], q["choices"], key=f"planet_pp_{q['key']}",
            )
        _submitted = st.form_submit_button("🔬 Reveal", type="primary")
    if _submitted:
        _score = 0
        _rows = []
        for q in _q_list:
            ok = _predictions.get(q["key"]) == q["answer"]
            if ok:
                _score += 1
            _rows.append({
                "prompt": q["prompt"],
                "user": _predictions.get(q["key"], ""),
                "answer": q["answer"],
                "ok": ok,
            })
        st.session_state["planet_challenge_revealed_sig"] = input_signature
        st.session_state["planet_challenge_score"] = {
            "sig": input_signature,
            "score": _score,
            "total": len(_q_list),
            "rows": _rows,
        }
        st.rerun()
    st.stop()

# Score chip — only shown right after a reveal for the current signature
_score_data = st.session_state.get("planet_challenge_score") or {}
if _score_data.get("sig") == input_signature:
    _s = _score_data["score"]
    _t = _score_data["total"]
    if _s == _t:
        st.success(f"🎯 Perfect — {_s} / {_t}")
    elif _s >= _t / 2:
        st.info(f"🎯 Nice — {_s} / {_t}")
    else:
        st.warning(f"🎯 Tough one — {_s} / {_t}")
    for row in _score_data["rows"]:
        mark = "✅" if row["ok"] else "❌"
        st.markdown(
            f"- {mark} **{row['prompt']}**  \n"
            f"  You guessed: `{row['user']}` · Truth: `{row['answer']}`"
        )

c1, c2 = st.columns([1, 1])
with c1:
    st.subheader(
        "🌌 Orbit & vital signs",
        help="Top-down view of the star (centre), the green habitable-zone ring, "
             "and your planet's orbit. The numbers below summarize temperature, "
             "year length, day length, and Earth Similarity Index.",
    )
    st.plotly_chart(
        system_diagram(star_class_data["color_hex"], hz_inner, hz_outer, inputs["distance_AU"]),
        use_container_width=True,
    )
    in_hz = derived["in_habitable_zone"]
    # Year — pretty format depending on magnitude
    if _year_yr >= 1.0:
        year_str = f"{_year_yr:.2f} Earth years"
    else:
        year_str = f"{_year_yr * 365.25:.1f} Earth days"
    # Day — call out tidal locking
    if _tidally_locked:
        day_str = f"⚠️ tidally locked → day = year ({year_str})"
    else:
        day_str = f"{_day_h:.0f} h"
    st.markdown(
        f"**T_eq (bare rock)** {T_eq - 273.15:+.0f} °C &nbsp;·&nbsp; "
        f"**T_surf (w/ greenhouse)** {T_surf_C:+.0f} °C  \n"
        f"**HZ** {hz_inner:.3f}–{hz_outer:.3f} AU &nbsp;·&nbsp; "
        f"{'✅ inside HZ' if in_hz else '⚠️ outside HZ'}  \n"
        f"**Year** {year_str} &nbsp;·&nbsp; **Day** {day_str}  \n"
        f"**ESI** {esi:.2f} (Earth = 1.00)"
    )

with c2:
    st.subheader(
        "🌫 Atmosphere & sky",
        help="Donut chart of atmospheric composition by volume, plus a colour swatch "
             "showing what the sky would look like at noon — combination of stellar "
             "colour and Rayleigh scattering through this atmosphere.",
    )
    st.plotly_chart(atmosphere_donut(atm["composition"]), use_container_width=True)
    if inputs["atmosphere_tweak"].get("action") not in (None, "none"):
        t = inputs["atmosphere_tweak"]
        ui.info_panel(
            f"🧪 Atmosphere tweak applied: <b>{t['action']} {t['amount_pct']:g}% {t['gas']}</b>. "
            "Composition was renormalized."
        )
    st.markdown("**Sky preview at noon**")
    st.markdown(sky_swatch_html(star_class_data["color_hex"], atm["id"]), unsafe_allow_html=True)

# Pre-flight diagnostics — show the user our derived signals BEFORE Claude
with st.expander("🔬 Pre-flight diagnostics (derived signals fed to Claude)", expanded=False):
    st.caption(
        "These are computed deterministically from your inputs — no AI involved. "
        "Claude is required to honor the hard vetoes among them."
    )
    diag_l, diag_r = st.columns(2)
    with diag_l:
        st.markdown(
            f"- **In HZ:** {'✅ yes' if derived['in_habitable_zone'] else '❌ no'}  \n"
            "  &nbsp;&nbsp;_Whether the planet's orbit lies within the conservative habitable zone "
            "for this star._"
        )
        st.markdown(
            "- **Pressure supports liquid water:** "
            f"{'✅ yes' if derived['pressure_supports_liquid_water'] else '❌ no'}  \n"
            "  &nbsp;&nbsp;_Surface pressure ≥ 0.01 atm. Below this, water boils to vapor or "
            "sublimates to ice regardless of temperature (water's triple point)._"
        )
        st.markdown(
            f"- **Atmospheric retention risk:** `{derived['atmospheric_retention_risk']}`  \n"
            "  &nbsp;&nbsp;_How likely the planet keeps its atmosphere over Gyr timescales — "
            "function of escape velocity, surface temperature, and magnetic shielding._"
        )
    with diag_r:
        st.markdown(
            "- **Tidal locking likely:** "
            f"{'⚠️ yes' if derived['tidal_locking_likely'] else 'no'}  \n"
            "  &nbsp;&nbsp;_When close to its star, a planet's rotation slows until one face "
            "always points at the star — like the Moon to Earth._"
        )
        st.markdown(
            f"- **Flare risk:** `{derived['flare_risk']}`  \n"
            "  &nbsp;&nbsp;_How often the star throws sterilizing UV/X-ray flares. M-dwarfs "
            "and hot O/B/A stars are the worst._"
        )
        st.markdown(
            f"- **Magnetic field:** `{inputs['magnetic_field']}`  \n"
            "  &nbsp;&nbsp;_Earth's magnetosphere deflects solar wind. Mars lost its field "
            "~4 Gyr ago and lost most of its atmosphere as a result._"
        )

# ---- Transmission spectrum (deterministic) ---------------------------------
st.subheader("🔭 Transmission spectrum")
st.caption(
    "Simulated absorption spectrum across visible & infrared wavelengths — the "
    "same kind of measurement JWST makes when an exoplanet transits its star. "
    "Dips show wavelengths where the atmosphere absorbs starlight; each gas has "
    "a fingerprint pattern."
)
st.plotly_chart(transmission_spectrum_figure(atm["composition"]), use_container_width=True)

# ---- Biosignatures (deterministic) -----------------------------------------
biosignatures = data_loader.detect_biosignatures(
    atm["composition"], has_water=inputs["water_pct"] > 0,
)
st.subheader("🧪 Biosignature analysis")
if not biosignatures:
    ui.info_panel(
        "No biosignature gases detected in this atmosphere. Doesn't mean no life — "
        "just no smoking gun. (Earth in the Archean had abundant life but no oxygen.)"
    )
else:
    _BIOSIG_COLORS = {"strong": "#16A34A", "moderate": "#D97706", "weak": "#6B7280"}
    _BIOSIG_LABELS = {"strong": "STRONG", "moderate": "MODERATE", "weak": "WEAK"}
    for b in biosignatures:
        color = _BIOSIG_COLORS.get(b["level"], "#6B7280")
        label = _BIOSIG_LABELS.get(b["level"], b["level"].upper())
        st.markdown(
            f'<div class="cm-info" style="border-left-color:{color};">'
            f'<span class="cm-badge" style="background:{color}; margin-right:0.6rem;">'
            f'{label}</span><b>{b["name"]}</b><br>'
            f'<span style="color:#374151;">{b["why"]}</span></div>',
            unsafe_allow_html=True,
        )

# ---- Injection time evolution (only if a tweak is active) -------------------
if inputs["atmosphere_tweak"].get("action") not in (None, "none"):
    sim = data_loader.simulate_injection(
        base_composition=atm_base["composition"],
        tweak=inputs["atmosphere_tweak"],
        T_eq_K=T_eq,
        mass_earth=inputs["mass_earth"],
        flare_risk=derived["flare_risk"],
    )
    if sim:
        st.subheader("🌪 Injection time evolution")
        tw = inputs["atmosphere_tweak"]
        action_word = {"add": "Adding", "remove": "Removing", "replace": "Setting"}.get(
            tw["action"], tw["action"].title()
        )
        tau = sim["tau_years"].get(tw["gas"], 1e6)
        if tau >= 1e6:
            tau_str = f"~{tau/1e6:.1f} Myr"
        elif tau >= 1e3:
            tau_str = f"~{tau/1e3:.1f} kyr"
        elif tau >= 1:
            tau_str = f"~{tau:.0f} yr"
        else:
            tau_str = f"~{tau*365:.0f} days"
        st.caption(
            f"<b>{action_word} {tw['amount_pct']:g}% {tw['gas']}</b>. "
            f"Atmospheric lifetime of {tw['gas']} on this world: <b>{tau_str}</b>. "
            "Press ▶ Play to watch the atmosphere relax back toward baseline. "
            "Each gas decays at a different rate based on UV destruction, atmospheric "
            "escape, and condensation. The greenhouse temperature panel below shows "
            "how the climate responds in real time.",
            unsafe_allow_html=True,
        )
        st.plotly_chart(injection_evolution_figure(sim), use_container_width=True)
        with st.expander("ℹ️ How is this computed?"):
            st.markdown(
                """
This is a **simplified compartment model** — not a full atmospheric chemistry simulation.

For each gas, we use a textbook **atmospheric residence time** (e.g. CH₄ ≈ 12 years on Earth,
CO₂ ≈ 100,000 years, O₂ ≈ 5 million years), then adjust it for this planet:

- **High flare risk** → photochemically-destroyed gases (CH₄, NH₃, H₂O, H₂) decay 2-3× faster.
- **Low gravity** → light gases (H₂, He) escape to space much faster.
- **Cold (T < 273 K)** → water vapor freezes out; lifetime drops sharply.
- **Hot (T > 350 K)** → volatiles (H₂O, NH₃) desiccate faster.

Each gas relaxes exponentially toward the baseline composition. The greenhouse ΔT
panel uses textbook **forcing-per-doubling** values: CO₂ ≈ +3.7 °C, CH₄ ≈ +0.5 °C,
H₂O ≈ +3 °C per doubling.

This **does not model**: atmospheric chemistry coupling, ocean–atmosphere exchange,
biological feedbacks, or weathering. Real Earth-system models include all of these.
"""
            )

ui.source_indicator(source)
if result.confidence == "speculative":
    ui.speculation_banner()

verdict_emoji = {"habitable": "🟢", "extremophile_only": "🟡", "non_habitable": "🔴"}
st.subheader(
    f"{verdict_emoji.get(result.verdict, '⚪')} Habitability: "
    f"{result.verdict.replace('_', ' ').title()}",
    help="Claude's overall verdict in three tiers: 🟢 habitable (Earth life could "
         "survive on the surface), 🟡 extremophile-only (only hardy microbes), "
         "🔴 non-habitable (none of Earth's biochemistry would work).",
)
st.write(result.verdict_reason)

if result.habitability_blockers:
    st.markdown("**Habitability blockers Claude identified:**")
    for b in result.habitability_blockers:
        st.markdown(f"- 🚫 {b}")

# Format year compactly
if _year_yr >= 1.0:
    _year_metric = f"{_year_yr:.2f} yr"
else:
    _year_metric = f"{_year_yr * 365.25:.1f} d"
# Format day — flag tidal lock instead of showing the huge number
if _tidally_locked:
    _day_metric = "locked"
elif _day_h >= 240:
    _day_metric = f"{_day_h / 24:.1f} d"
else:
    _day_metric = f"{_day_h:.0f} h"

m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric(
    "Avg surface T", f"{result.surface.avg_temperature_C:+.0f} °C",
    help="Claude's estimate of mean surface temperature, accounting for atmosphere and greenhouse.",
)
m2.metric(
    "Pressure", f"{result.surface.surface_pressure_atm:g} atm",
    help="Surface atmospheric pressure. Earth = 1 atm; Mars = 0.006 atm; Venus = 92 atm.",
)
m3.metric(
    "Gravity", f"{result.surface.gravity_g:.2f} g",
    help="Surface gravity in Earth g (9.81 m/s²). Derived from mass and radius.",
)
m4.metric(
    "Year", _year_metric,
    help=(
        "Orbital period — time to circle the host star once. "
        f"Computed via Kepler's 3rd law: T = √(a³/M_star). Here a={inputs['distance_AU']} AU, "
        f"M_star={star['mass_solar']:g} M☉."
    ),
)
m5.metric(
    "Day", _day_metric,
    help=(
        "Effective day length. If the planet is tidally locked, one face always faces the "
        "star — there is no solar day cycle, so we mark it 'locked'. Otherwise this is the "
        "rotation period you set."
    ),
)
m6.metric(
    "ESI", f"{esi:.2f}",
    help=(
        "Earth Similarity Index (Schulze-Makuch et al. 2011), 3-axis simplified version. "
        "Combines radius, density, and surface temperature. Earth = 1.00; values > 0.8 are "
        "considered very Earth-like."
    ),
)

st.subheader(
    "Sky at noon",
    help="What an observer on the surface would see overhead during the day. "
         "Combines the star's spectral colour with Rayleigh scattering through "
         "this atmosphere — Earth's blue, Mars' butterscotch, Titan's orange.",
)
st.write(result.sky_description)

st.subheader(
    "Plausible life",
    help="Claude's best guess at what kind of biology — if any — could plausibly "
         "exist here, with a confidence badge. Always speculative when extrapolating "
         "beyond known Earth chemistry.",
)
st.markdown(
    ui.confidence_badge(result.plausible_life_confidence) + " &nbsp; " + result.plausible_life,
    unsafe_allow_html=True,
)

st.subheader(
    "Radiation environment",
    help="Surface UV / X-ray / cosmic-ray exposure given the host star's flare "
         "activity, the planet's magnetic field, and atmospheric shielding. "
         "Drives whether complex molecules can survive on the surface.",
)
st.caption(result.surface.radiation_environment)

# Terraforming output
if result.terraforming and inputs["terraforming_target"] != "none":
    st.subheader(
        f"🛠 Terraforming plan: {inputs['terraforming_target'].replace('_', ' ').title()}"
    )
    tcols = st.columns([1, 1])
    with tcols[0]:
        st.metric("Difficulty (1–10)", result.terraforming.difficulty_1_to_10)
    with tcols[1]:
        st.metric("Timescale", result.terraforming.estimated_timescale or "—")
    if not result.terraforming.feasible:
        ui.warn_panel(
            "Claude flagged this terraforming target as <b>infeasible</b> within known physics."
        )
    if result.terraforming.steps:
        for i, step in enumerate(result.terraforming.steps, start=1):
            st.markdown(f"**{i}.** {step}")

# Abiogenesis / seeding output
if result.abiogenesis_prospects and inputs["seeding_what"] != "none":
    st.subheader("🧬 Abiogenesis prospects")
    ui.speculation_banner()
    st.write(result.abiogenesis_prospects)

st.subheader("Closest real exoplanet")
ui.info_panel(
    f"<b>{result.closest_real_exoplanet_name}</b> — {result.comparison_note}"
)
if closest:
    with st.expander("KB record for the closest match"):
        st.json(closest)

with st.expander("📖 Concepts (what do these terms mean?)", expanded=False):
    st.markdown(
        """
**AU (Astronomical Unit)** — the average Earth–Sun distance, ≈ 150 million km.
A planet at 0.05 AU is ~20× closer to its star than Earth is to the Sun.

**Habitable Zone (HZ)** — the orbital ring around a star where a rocky planet
*could* hold liquid water on its surface (with a sensible atmosphere). Inner
edge: too hot, oceans evaporate. Outer edge: too cold, oceans freeze.
Computed here as `0.95·√L` to `1.67·√L` AU, where `L` is the star's luminosity
relative to the Sun (Kasting heuristic).

**T_eq (equilibrium temperature, bare-rock)** — the temperature a perfectly
black ball would settle at given just stellar flux and 30% reflectivity. It
*ignores* greenhouse warming. Earth's T_eq is **−18 °C**; with our atmosphere
we sit at **+15 °C**.

**T_surf (greenhouse-corrected surface temperature)** — T_eq plus a per-archetype
greenhouse delta, scaled by atmospheric pressure. This is closer to what a
thermometer would read on the surface.

**Year (orbital period)** — time to circle the star once, from Kepler's third
law: **T_years = √(a³ / M_star)** with `a` in AU and `M_star` in solar masses.
A planet at 0.05 AU around a 0.1 M☉ red dwarf has a year of just ~11 days.

**Day (rotation period)** — how long the planet takes to spin once on its axis.
Independent of the year — *unless* the planet is tidally locked, in which case
day = year and one face permanently faces the star.

**Tidal locking** — close-in planets get their rotation gradually braked by the
star's gravity until they spin once per orbit. Time to lock scales as ~d⁶, so
a planet at 0.05 AU locks in <1 Gyr while Earth at 1 AU would take ~64 Gyr.

**Flare risk** — small red dwarfs (M-class) emit huge UV and X-ray flares,
sometimes doubling their brightness for minutes. Without a magnetic shield,
this strips atmospheres and damages biology on the surface.

**Atmospheric retention** — whether the planet can hold onto its gases over
billions of years. Depends on escape velocity (more mass → harder to escape),
surface temperature (hotter → faster gas molecules), and magnetic field
(deflects the solar wind that erodes atmospheres).

**ESI (Earth Similarity Index)** — a 0-to-1 score combining radius, density,
and surface temperature similarity to Earth. Earth = 1.00. Most known
exoplanets are well below 0.5; the highest, like Teegarden's Star b, sit
around 0.95.

**Greenhouse effect** — gases like CO₂, H₂O, and CH₄ absorb infrared light
the planet emits, sending heat back down. Without it, Earth would freeze.
Too much (Venus) and the surface hits 462 °C.

**Triple point of water** — the unique pressure & temperature where ice,
liquid water, and water vapor coexist. **0.006 atm and 0.01 °C.** Below
0.006 atm, water *cannot* be liquid at any temperature.

**Magnetosphere / L1 shield** — Earth's molten iron core generates a magnetic
field that deflects the solar wind. Mars lacks one, so its atmosphere has been
slowly stripped away. The "artificial L1 shield" is a real proposal: park a
giant magnetic dipole between the planet and its star at the L1 Lagrange
point.

**Transmission spectrum** — when a planet passes in front of its star, a
fraction of the starlight passes *through* the planet's atmosphere on its way
to us. Each gas absorbs at characteristic wavelengths, leaving dark dips in
the spectrum — its molecular fingerprint. This is how JWST detected CO₂ in
the atmosphere of WASP-39b in 2022.

**Biosignature** — a gas (or combination) whose presence is hard to explain
*without* life. The gold standard is **redox disequilibrium**: e.g. O₂ and
CH₄ together. They react with each other in years, so finding both means
something is constantly making them. On Earth, that's photosynthesis (O₂)
and methanogens (CH₄).

**Atmospheric residence time** — average time a molecule of a given gas spends
in the atmosphere before being destroyed (UV photochemistry), removed (rainout,
weathering, biological uptake), or escaping to space. CH₄ ≈ 12 years; CO₂ ≈
100,000 years; O₂ ≈ 5 million years (without continuous bio replenishment).
This is why O₂ is such a striking biosignature.

**Greenhouse forcing per doubling** — climatology shorthand for how much
surface temperature rises if you double a greenhouse gas's concentration.
Standard values: CO₂ ≈ +3.7 °C per doubling; CH₄ ≈ +0.5 °C; H₂O ≈ +3 °C.
The injection animation uses these to estimate the temperature response.
"""
    )

clicked = ui.follow_up_buttons(result.follow_ups, "planet")
if clicked:
    # Mirror the Ecosystem pattern: inject the question so the cache key
    # changes AND Claude sees it on the next render.
    st.session_state.planet_user_question = clicked
    st.session_state.pop("planet_last_result", None)
    st.session_state.pop("planet_last_signature", None)
    st.toast(f"Exploring: {clicked}")
    st.rerun()

# ---- Quiz panel (1–2 MCQs Claude generated about THIS world) ---------------
if result.quiz:
    st.divider()
    st.subheader("🧠 Quiz me on this world")
    _qkey_prefix = f"planet_quiz_{(input_signature or '')[:12]}"
    for idx, q in enumerate(result.quiz):
        with st.expander(f"Question {idx + 1}: {q.question}", expanded=False):
            picked = st.radio(
                "Pick an answer:",
                options=list(range(len(q.choices))),
                format_func=lambda i, _q=q: _q.choices[i],
                key=f"{_qkey_prefix}_q{idx}",
                index=None,
            )
            if picked is not None:
                if picked == q.correct_index:
                    st.success(f"✅ Correct — {q.explanation}")
                else:
                    correct_text = q.choices[q.correct_index]
                    st.error(
                        f"❌ Not quite. Correct answer: **{correct_text}**.  \n"
                        f"{q.explanation}"
                    )
