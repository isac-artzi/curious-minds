"""Load the planets knowledge base + derived habitability signals."""

from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "planets"


@lru_cache(maxsize=1)
def load_stars() -> list[dict]:
    """Generic spectral-class records (kept for color, sky_appearance lookup)."""
    return json.loads((DATA_DIR / "stars.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_named_stars() -> list[dict]:
    """Specific real stars with concrete luminosity, mass, age, and flare flag."""
    return json.loads((DATA_DIR / "named_stars.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_atmospheres() -> list[dict]:
    return json.loads((DATA_DIR / "atmospheres.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_exoplanets() -> list[dict]:
    return json.loads((DATA_DIR / "exoplanets.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_scenarios() -> list[dict]:
    path = DATA_DIR / "scenarios.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def scenario_by_id(scenario_id: str) -> dict | None:
    for s in load_scenarios():
        if s.get("id") == scenario_id:
            return s
    return None


def star_by_class(spc: str) -> dict | None:
    for s in load_stars():
        if s["spectral_class"] == spc:
            return s
    return None


def star_by_name(name: str) -> dict | None:
    for s in load_named_stars():
        if s["name"] == name:
            return s
    return None


# ---------------------------------------------------------------------------
# Heuristics — habitable zone, equilibrium temperature
# ---------------------------------------------------------------------------

def habitable_zone(luminosity_solar: float) -> tuple[float, float]:
    """Conservative HZ via simple L^0.5 scaling (Kasting heuristic)."""
    inner = 0.95 * math.sqrt(luminosity_solar)
    outer = 1.67 * math.sqrt(luminosity_solar)
    return inner, outer


def equilibrium_temperature_K(
    luminosity_solar: float,
    distance_AU: float,
    albedo: float = 0.30,
) -> float:
    """Stefan–Boltzmann equilibrium temperature, no greenhouse."""
    L_sun = 3.828e26  # W
    sigma = 5.670374419e-8
    AU = 1.495978707e11
    L = luminosity_solar * L_sun
    d = distance_AU * AU
    flux = L / (4 * math.pi * d * d)
    T = (((1 - albedo) * flux) / (4 * sigma)) ** 0.25
    return T


def orbital_period_years(distance_AU: float, star_mass_solar: float) -> float:
    """Kepler's third law: T_years = sqrt(a^3 / M_star) with a in AU, M in M☉."""
    if distance_AU <= 0 or star_mass_solar <= 0:
        return 0.0
    return math.sqrt((distance_AU ** 3) / star_mass_solar)


def effective_day_length_hours(
    rotation_period_hours: float,
    is_tidally_locked: bool,
    orbital_period_years_value: float,
) -> float:
    """Day length seen by an observer on the planet.

    If tidally locked, one face always points at the star → no solar day cycle;
    we report the orbital period as the relevant 'day' (one full circuit).
    Otherwise, return the rotation period itself (close enough to a solar day
    when the year is much longer than the rotation, which is the usual case).
    """
    if is_tidally_locked:
        return orbital_period_years_value * 365.25 * 24.0
    return max(rotation_period_hours, 0.01)


# ---------------------------------------------------------------------------
# Derived signals — fed to Claude as the `derived` block
# ---------------------------------------------------------------------------

def tidal_locking_likely(distance_AU: float, star_mass_solar: float, age_Gyr: float) -> bool:
    """Cheap tidal-lock check: lock timescale ~ d^6 / M_star.

    Calibrated against the known case Proxima Centauri b (0.0485 AU, ~0.12 M☉,
    ~5 Gyr) which IS tidally locked, and Earth at 1 AU which is NOT.
    """
    if star_mass_solar <= 0 or distance_AU <= 0 or age_Gyr <= 0:
        return False
    # 1 Gyr at d=0.05 AU around a 1 M☉ star — order-of-magnitude only
    timescale_Gyr = (distance_AU / 0.05) ** 6 * (1.0 / star_mass_solar)
    return timescale_Gyr < age_Gyr


def flare_risk(spectral_class: str, age_Gyr: float, is_known_flare_active: bool = False) -> str:
    """Return 'low' / 'moderate' / 'high' / 'very_high_uv'."""
    if is_known_flare_active:
        return "high"
    if spectral_class == "M":
        return "high" if age_Gyr < 6 else "moderate"
    if spectral_class == "K":
        return "moderate" if age_Gyr < 1 else "low"
    if spectral_class in ("F", "G"):
        return "low"
    if spectral_class in ("O", "B", "A"):
        return "very_high_uv"  # hot stars: sterilizing UV/XUV continuum
    return "low"


def pressure_supports_liquid_water(pressure_atm: float) -> bool:
    """Triple-point pressure of water is 0.006 atm. Use 0.01 as the floor."""
    return pressure_atm >= 0.01


def atmospheric_retention(
    mass_earth: float,
    radius_earth: float,
    T_eq_K: float,
    mag_field: str,
) -> str:
    """Return 'low' / 'moderate' / 'high' retention risk.

    Proxy: escape velocity vs. thermal energy, with a magnetic-field bonus.
    """
    # v_esc(Earth) = 11.2 km/s; scales as sqrt(M/R) in Earth units.
    v_esc = 11.2 * math.sqrt(max(mass_earth, 0.01) / max(radius_earth, 0.1))
    score = (v_esc / 11.2) * (255.0 / max(T_eq_K, 50.0))
    bonus = {"none": 0.6, "weak": 0.85, "strong": 1.3, "artificial_shield": 1.5}.get(mag_field, 1.0)
    score *= bonus
    if score >= 1.0:
        return "low"
    if score >= 0.55:
        return "moderate"
    return "high"


_GREENHOUSE_DELTA_K: dict[str, float] = {
    "earth_like": 33.0,        # +33 K on Earth
    "venus_like": 510.0,       # runaway
    "mars_like": 5.0,          # very thin → little
    "titan_like": 12.0,        # methane greenhouse + anti-greenhouse haze
    "hydrogen_helium": 0.0,    # no surface
    "reducing_archean": 25.0,  # CH4 + CO2 mix
    "ice_world": 2.0,
}


def greenhouse_surface_T_C(
    T_eq_K: float,
    atmosphere_id: str,
    pressure_atm: float,
) -> float:
    """Greenhouse-corrected surface temperature in °C, scaled by pressure.

    `T_eq` is bare-rock equilibrium; the chosen atmosphere adds a per-archetype
    delta scaled by log10(pressure). Mars-like at 0.006 atm gets ~0; Earth at
    1 atm gets the full delta; Venus at 92 atm clips at ~1.5× delta.
    """
    delta = _GREENHOUSE_DELTA_K.get(atmosphere_id, 15.0)
    if pressure_atm <= 0:
        scale = 0.0
    else:
        scale = max(0.0, min(1.5, math.log10(pressure_atm * 100.0) / 2.0))
    return T_eq_K + delta * scale - 273.15


def earth_similarity_index(
    radius_earth: float,
    density_g_per_cm3: float,
    surface_T_C: float,
) -> float:
    """Simplified ESI (Schulze-Makuch et al. 2011), 3 axes. Earth = 1.0."""
    def weighted(x: float, x_ref: float, w: float) -> float:
        if x <= 0 or x_ref <= 0:
            return 0.0
        return (1 - abs((x - x_ref) / (x + x_ref))) ** w
    r = weighted(radius_earth, 1.0, 0.57)
    d = weighted(density_g_per_cm3, 5.51, 1.07)
    t = weighted(surface_T_C + 273.15, 288.0, 5.58)
    return r * d * t


# ---------------------------------------------------------------------------
# Atmosphere tweaks (single-gas perturbation)
# ---------------------------------------------------------------------------

def apply_atmosphere_tweak(atm: dict, tweak: dict | None) -> dict:
    """Return a NEW atmosphere dict with one-gas perturbation applied.

    `tweak` keys:
      action: 'none' | 'add' | 'remove' | 'replace'
      gas:    one of 'CO2', 'O2', 'N2', 'CH4', 'NH3', 'H2O', 'H2', 'He', 'Ar', 'SO2'
      amount_pct: float, percent of atmosphere by volume

    Composition is renormalized to sum to 100. The original atmosphere is
    not mutated. Surface_pressure_atm is left unchanged (composition tweak
    only — pressure is its own knob).
    """
    if not tweak or tweak.get("action") in (None, "none", ""):
        return atm
    comp: dict[str, float] = {k: float(v) for k, v in atm.get("composition", {}).items()}
    gas = tweak.get("gas")
    amount = float(tweak.get("amount_pct", 0))
    action = tweak["action"]
    if action == "add":
        comp[gas] = comp.get(gas, 0.0) + amount
    elif action == "remove":
        comp[gas] = max(0.0, comp.get(gas, 0.0) - amount)
    elif action == "replace":
        comp[gas] = amount
    # Drop near-zero entries
    comp = {k: v for k, v in comp.items() if v > 1e-4}
    total = sum(comp.values())
    if total > 0:
        comp = {k: round(v * 100.0 / total, 3) for k, v in comp.items()}
    return {**atm, "composition": comp, "_tweak": tweak}


# ---------------------------------------------------------------------------
# Biosignatures — what compounds, if detected, would suggest life?
# ---------------------------------------------------------------------------

def detect_biosignatures(composition: dict[str, float], has_water: bool = True) -> list[dict]:
    """Return a list of biosignature findings, each with name/level/why.

    Levels: 'strong', 'moderate', 'weak'. Order: strongest first.
    Logic is deterministic — pure rules, no LLM.
    """
    o2 = composition.get("O2", 0.0)
    o3 = composition.get("O3", 0.0)
    ch4 = composition.get("CH4", 0.0)
    nh3 = composition.get("NH3", 0.0)
    n2o = composition.get("N2O", 0.0)
    co2 = composition.get("CO2", 0.0)
    h2o = composition.get("H2O", 0.0)

    findings: list[dict] = []

    # Strongest: O2 + CH4 simultaneously — they react quickly. Both being present
    # implies a continuous biological source for at least one.
    if o2 >= 0.5 and ch4 >= 0.0001:
        findings.append({
            "name": "O₂ + CH₄ disequilibrium",
            "level": "strong",
            "why": (
                "These two gases react with each other — together, they shouldn't both persist. "
                "Their coexistence implies BOTH are being continuously produced, almost certainly "
                "by life. This is the textbook 'redox disequilibrium' biosignature."
            ),
        })

    # Free oxygen — abiotically unstable
    if o2 >= 1.0:
        findings.append({
            "name": "Free O₂ (≥ 1%)",
            "level": "strong",
            "why": (
                "Free oxygen reacts away (rusts iron, oxidizes minerals) within geological time. "
                "On Earth, EVERY molecule of atmospheric O₂ traces back to photosynthesis. "
                "Hard to explain without a biosphere."
            ),
        })
    elif o2 >= 0.1:
        findings.append({
            "name": "Trace O₂",
            "level": "moderate",
            "why": (
                "Some O₂ can come from photodissociation of water vapor by UV. "
                "Trace amounts are interesting but not conclusive."
            ),
        })

    # Ozone is derived from O2 — same basic logic
    if o3 >= 0.0001:
        findings.append({
            "name": "Ozone (O₃)",
            "level": "moderate",
            "why": (
                "Ozone forms when UV breaks O₂ apart. A persistent ozone layer implies "
                "a steady O₂ source, again pointing toward photosynthesis."
            ),
        })

    # Methane alone — could be biological (methanogens) OR geological (serpentinization)
    if ch4 >= 1.0 and o2 < 0.5:
        findings.append({
            "name": "CH₄ in a reducing atmosphere",
            "level": "weak",
            "why": (
                "Methane can be biological (methanogen archaea) OR purely geological "
                "(hot water + olivine rocks releases CH₄). On its own, it's an interesting "
                "but ambiguous signal — early Archean Earth looked like this."
            ),
        })

    # Nitrous oxide — almost entirely bio on Earth
    if n2o >= 0.0001:
        findings.append({
            "name": "Nitrous oxide (N₂O)",
            "level": "weak",
            "why": (
                "On Earth, ~70% of atmospheric N₂O comes from soil microbes. Some abiotic "
                "production is possible (lightning), so trace amounts are weakly suggestive."
            ),
        })

    # Ammonia is unstable but bio-produced on Earth in small amounts
    if nh3 >= 0.01:
        findings.append({
            "name": "Ammonia (NH₃)",
            "level": "weak",
            "why": (
                "NH₃ is destroyed by UV in days to years. Persistent NH₃ implies a continuous "
                "source — could be biological nitrogen fixation, or a hydrogen-rich primordial "
                "atmosphere."
            ),
        })

    # Reducing-Archean-like signature (CO2 + N2 + traces of CH4) with surface water
    if has_water and co2 >= 5 and ch4 >= 0.1 and o2 < 0.1:
        findings.append({
            "name": "Archean-Earth analogue",
            "level": "moderate",
            "why": (
                "This composition mimics Earth ~3 billion years ago, when life had emerged "
                "but oxygenic photosynthesis hadn't yet spread. The CH₄ here is most plausibly "
                "biological."
            ),
        })

    return findings


# ---------------------------------------------------------------------------
# Atmosphere injection simulator (compartment model)
# ---------------------------------------------------------------------------

# Approximate atmospheric residence times (years) at Earth-like conditions.
# Order-of-magnitude only — these vary with planet, biology, geology.
_ATMOSPHERIC_LIFETIMES_YR: dict[str, float] = {
    "CO2": 1.0e5,   # very long without weathering or bio uptake
    "O2":  5.0e6,   # very long without bio replenishment
    "CH4": 12.0,    # short — UV oxidation
    "NH3": 50.0,    # short — UV destruction
    "H2O": 0.025,   # ~10 days in troposphere (rains out)
    "N2":  1.0e9,   # essentially permanent
    "H2":  4.0,     # escapes to space quickly (low mass)
    "He":  1.0e6,   # also escapes, but slowly
    "Ar":  1.0e10,  # noble — basically permanent
    "SO2": 0.5,     # rains out as sulfuric acid
    "N2O": 120.0,
    "O3":  0.1,     # very reactive
}


def _adjust_lifetime(
    gas: str, base_tau: float, T_K: float, mass_earth: float, flare_risk: str,
) -> float:
    """Adjust the textbook lifetime for the actual planet's conditions."""
    tau = base_tau
    # UV destruction by stellar radiation
    if gas in ("CH4", "NH3", "H2O", "H2"):
        if flare_risk in ("high", "very_high_uv"):
            tau *= 0.3
        elif flare_risk == "moderate":
            tau *= 0.7
    # Escape of light gases — a low-mass planet leaks H/He fast
    if gas in ("H2", "He"):
        if mass_earth < 0.3:
            tau *= 0.2
        elif mass_earth < 1.0:
            tau *= 0.6
    # Water freezes/condenses out below 273 K — effectively no atmospheric water
    if gas == "H2O" and T_K < 273:
        tau *= 0.1
    # Hot worlds (T > 350 K) lose volatiles faster
    if T_K > 350 and gas in ("H2O", "NH3"):
        tau *= 0.3
    return max(tau, 1e-3)


def simulate_injection(
    base_composition: dict[str, float],
    tweak: dict | None,
    T_eq_K: float,
    mass_earth: float,
    flare_risk: str,
    n_steps: int = 80,
    duration_years: float = 1.0e7,
) -> dict | None:
    """Simulate the atmospheric response to a one-time gas injection.

    Returns dict with time series of composition (% per gas) and greenhouse ΔT.
    Returns None if no tweak active.
    """
    if not tweak or tweak.get("action") in (None, "none", ""):
        return None

    # Numpy is heavy but already a Streamlit dep
    import numpy as np

    baseline = {k: float(v) for k, v in base_composition.items() if v > 1e-4}
    initial = dict(baseline)
    gas = tweak["gas"]
    amount = float(tweak.get("amount_pct", 0))
    action = tweak["action"]

    if action == "add":
        initial[gas] = initial.get(gas, 0.0) + amount
    elif action == "remove":
        initial[gas] = max(0.0, initial.get(gas, 0.0) - amount)
    elif action == "replace":
        initial[gas] = amount

    def _norm(d: dict[str, float]) -> dict[str, float]:
        s = sum(d.values())
        if s <= 0:
            return d
        return {k: v * 100 / s for k, v in d.items() if v > 1e-4}

    initial = _norm(initial)
    baseline = _norm(baseline)

    # Log-spaced time grid: 1 yr → duration_years
    t = np.logspace(0, math.log10(max(duration_years, 10)), n_steps)

    # Per-gas exponential relaxation toward baseline
    all_gases = sorted(set(initial) | set(baseline))
    raw_series: dict[str, list[float]] = {}
    tau_used: dict[str, float] = {}
    for g in all_gases:
        c0 = initial.get(g, 0.0)
        cinf = baseline.get(g, 0.0)
        base_tau = _ATMOSPHERIC_LIFETIMES_YR.get(g, 1.0e6)
        tau = _adjust_lifetime(g, base_tau, T_eq_K, mass_earth, flare_risk)
        tau_used[g] = tau
        traj = cinf + (c0 - cinf) * np.exp(-t / tau)
        raw_series[g] = traj.tolist()

    # Renormalize each timestep so the atmosphere always sums to 100%
    matrix = np.array([raw_series[g] for g in all_gases])
    totals = matrix.sum(axis=0)
    matrix = matrix * 100.0 / np.where(totals > 0, totals, 1.0)
    series = {g: matrix[i].tolist() for i, g in enumerate(all_gases)}

    # Greenhouse temperature offset relative to baseline composition.
    # Effect-per-doubling values (rough): CO2 +3.7 °C, CH4 +0.5 °C, H2O +3 °C.
    def _log2_ratio(c: float, c_ref: float) -> float:
        c_safe = max(c, 1e-3)
        c_ref_safe = max(c_ref, 1e-3)
        return math.log2(c_safe / c_ref_safe)

    dT = []
    factors = {"CO2": 3.7, "CH4": 0.5, "H2O": 3.0}
    for i in range(len(t)):
        delta = 0.0
        for g, factor in factors.items():
            if g in series:
                ref = baseline.get(g, series[g][-1])
                delta += factor * _log2_ratio(series[g][i], ref)
        dT.append(delta)

    return {
        "t_years": t.tolist(),
        "composition_series": series,
        "temperature_offset_C": dT,
        "tau_years": tau_used,
        "tweak": tweak,
    }


# ---------------------------------------------------------------------------
# Closest real exoplanet (host_class match now strongly preferred)
# ---------------------------------------------------------------------------

def closest_real_exoplanet(
    mass_earth: float,
    radius_earth: float,
    distance_AU: float,
    host_class: str,
) -> dict:
    """Find the nearest real exoplanet by simple normalized log-space distance."""
    best = None
    best_score = float("inf")
    for ex in load_exoplanets():
        dm = math.log10(max(mass_earth, 0.01) / max(ex["mass_earth"], 0.01))
        dr = math.log10(max(radius_earth, 0.1) / max(ex["radius_earth"], 0.1))
        dd = math.log10(max(distance_AU, 0.001) / max(ex["orbital_distance_AU"], 0.001))
        host_penalty = 0.0 if ex["host_class"] == host_class else 1.5
        score = dm * dm + dr * dr + dd * dd + host_penalty
        if score < best_score:
            best_score = score
            best = ex
    return best
