"""Load and validate the chemistry knowledge base."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "chemistry"


@lru_cache(maxsize=1)
def load_elements() -> list[dict]:
    return json.loads((DATA_DIR / "elements.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_compounds() -> list[dict]:
    return json.loads((DATA_DIR / "compounds.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_reactions() -> list[dict]:
    return json.loads((DATA_DIR / "reactions.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_scenarios() -> list[dict]:
    """Mad Scientist preset experiments — see data/chemistry/scenarios.json."""
    path = DATA_DIR / "scenarios.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def scenario_by_id(scenario_id: str) -> dict | None:
    for s in load_scenarios():
        if s.get("id") == scenario_id:
            return s
    return None


def element_by_symbol(symbol: str) -> dict | None:
    for e in load_elements():
        if e["symbol"] == symbol:
            return e
    return None


def compound_by_formula(formula: str) -> dict | None:
    for c in load_compounds():
        if c["formula"] == formula:
            return c
    return None


def picker_options() -> list[tuple[str, str]]:
    """Return (label, key) tuples for the unified element/compound picker."""
    options = []
    for e in load_elements():
        options.append((f"{e['symbol']} — {e['name']}", f"element:{e['symbol']}"))
    for c in load_compounds():
        options.append((f"{c['formula']} — {c['name']}", f"compound:{c['formula']}"))
    return options


_NOBLE_GASES = {"He", "Ne", "Ar", "Kr", "Xe", "Rn"}
_HIGH_ENERGY_CUES = (
    "spark", "flame", "uv", "plasma", "arc", "laser", "radiation",
    "gamma", "x-ray", "electron beam", "ignition", "fusion", "combustion",
)
_AUTO_REACTIVE_PAIRS = (
    {"alkali_metal", "halogen"},
    {"alkali_metal", "nonmetal"},   # Na + O, Li + N etc.
    {"alkaline_earth", "halogen"},
)


def _split_key(key: str) -> tuple[str, str]:
    """Split a 'kind:ident' picker key; tolerate malformed keys from
    hand-edited .curious files instead of crashing the page."""
    if ":" in key:
        kind, ident = key.split(":", 1)
        return kind, ident
    return "", key


def _melting_point_K(key: str) -> float | None:
    kind, ident = _split_key(key)
    if kind == "element":
        rec = element_by_symbol(ident) or {}
    else:
        rec = compound_by_formula(ident) or {}
    mp = rec.get("melting_point_K")
    return float(mp) if mp is not None else None


def _categories(selected_keys: list[str]) -> list[str]:
    cats: list[str] = []
    for k in selected_keys:
        kind, ident = _split_key(k)
        if kind == "element":
            rec = element_by_symbol(ident) or {}
            cat = rec.get("category")
            if cat:
                cats.append(cat)
    return cats


def sanity_warnings(selected_keys: list[str], conditions: dict) -> list[str]:
    """Cheap heuristics to flag unrealistic setups before the LLM call.

    Returns a list of plain-text warning strings (may be empty).
    """
    if not selected_keys:
        return []

    warnings: list[str] = []
    try:
        T = float(conditions.get("temperature_K", 298.0))
        P = float(conditions.get("pressure_atm", 1.0))
    except (TypeError, ValueError):
        T, P = 298.0, 1.0
    catalyst = str(conditions.get("catalyst", "")).strip().lower()
    near_stp = 200.0 <= T <= 400.0 and 0.5 <= P <= 5.0

    # 1. Noble-gas inertness
    element_syms = [k.split(":", 1)[1] for k in selected_keys if k.startswith("element:")]
    only_elements = len(element_syms) == len(selected_keys)
    if (
        only_elements and element_syms
        and all(sym in _NOBLE_GASES for sym in element_syms)
        and near_stp
    ):
        warnings.append(
            "All selected species are noble gases at near-STP conditions. "
            "Expect no reaction — these are essentially inert."
        )

    # 2. Frozen everything
    mps = [m for m in (_melting_point_K(k) for k in selected_keys) if m is not None]
    if mps and T < min(mps) - 5:
        warnings.append(
            f"Temperature ({T:.0f} K) is below the melting point of every reactant. "
            "Kinetics are effectively zero — the system is frozen."
        )

    # 3. Extreme pressure
    if P >= 1e4:
        warnings.append(
            f"Pressure ({P:g} atm) is in the diamond-anvil / planetary-core regime. "
            "Real chemistry at these pressures is poorly characterized; treat results as speculative."
        )

    # 4. Plasma temperature
    if T > 10000:
        warnings.append(
            f"Temperature ({T:.0f} K) is plasma-regime — species exist as ions, "
            "not molecules. Expect plasma chemistry, not familiar reactions."
        )

    # 5. Inert mix with no activation cue
    if (
        len(selected_keys) >= 2
        and near_stp
        and not any(cue in catalyst for cue in _HIGH_ENERGY_CUES)
    ):
        cats = set(_categories(selected_keys))
        auto_reactive = any(pair.issubset(cats) for pair in _AUTO_REACTIVE_PAIRS)
        # Acid + base / oxide + acid pairs handled implicitly via compound names
        if not auto_reactive and "noble_gas" in cats and len(cats) > 1:
            warnings.append(
                "Mix includes a noble gas and another species at near-STP with no high-energy "
                "initiator. The noble gas will not participate."
            )

    return warnings


def relevant_kb_subset(selected_keys: list[str]) -> dict:
    """Return only the KB records the user selected, plus a few anchor reactions."""
    elements = []
    compounds = []
    for k in selected_keys:
        kind, ident = _split_key(k)
        if kind == "element":
            rec = element_by_symbol(ident)
            if rec:
                elements.append(rec)
        elif kind == "compound":
            rec = compound_by_formula(ident)
            if rec:
                compounds.append(rec)
    return {
        "elements": elements,
        "compounds": compounds,
        "anchor_reactions": load_reactions(),
    }
