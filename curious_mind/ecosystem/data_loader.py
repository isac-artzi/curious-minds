"""Load and validate the ecosystem knowledge base."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "ecosystem"


@lru_cache(maxsize=1)
def load_species() -> list[dict]:
    return json.loads((DATA_DIR / "species.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_biomes() -> list[dict]:
    return json.loads((DATA_DIR / "biomes.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_interactions() -> list[dict]:
    return json.loads((DATA_DIR / "interactions.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_disturbances() -> list[dict]:
    return json.loads((DATA_DIR / "disturbances.json").read_text(encoding="utf-8"))


def species_by_id(sid: str) -> dict | None:
    for s in load_species():
        if s["id"] == sid:
            return s
    return None


def biome_by_id(bid: str) -> dict | None:
    for b in load_biomes():
        if b["id"] == bid:
            return b
    return None


def sanity_warnings(
    biome_id: str,
    species_ids: list[str],
    populations: dict[str, float],
    *,
    disturbance_id: str | None = None,
    disturbance_year: int | None = None,
    horizon_years: int = 25,
    climate_dT: float = 0.0,
    climate_dP_pct: float = 0.0,
) -> list[str]:
    """Cheap heuristics flagging unrealistic configurations before the LLM call.

    Returns plain-text warning strings (may be empty).
    """
    if not species_ids:
        return []

    species = [species_by_id(sid) for sid in species_ids]
    species = [s for s in species if s]
    levels = {s["id"]: s.get("trophic_level", "primary_consumer") for s in species}
    diets = {s["id"]: set(s.get("diet", []) or []) for s in species}

    warnings: list[str] = []
    selected_set = set(species_ids)

    # 1. Apex without prey base in the selection.
    for s in species:
        if levels.get(s["id"]) == "apex_predator":
            if not (diets.get(s["id"], set()) & selected_set):
                warnings.append(
                    f"{s.get('emoji', '•')} {s.get('common_name', s['id'])} is an apex "
                    "predator, but none of its diet species are in your selection — "
                    "expect collapse within a few generations."
                )

    # 2. No producers => collapse base.
    if not any(lvl == "producer" for lvl in levels.values()):
        warnings.append(
            "No producers selected. Without a plant/algae base, every consumer "
            "tier loses its food source."
        )

    # 3. Monoculture (all one trophic level).
    distinct_levels = set(levels.values())
    if len(distinct_levels) == 1 and len(species) > 1:
        warnings.append(
            f"All selected species are at the same trophic level "
            f"({list(distinct_levels)[0].replace('_', ' ')}). No cross-tier cascade is possible."
        )

    # 4. Disturbance year past horizon.
    if disturbance_id and disturbance_year is not None and disturbance_year > horizon_years:
        warnings.append(
            f"Disturbance scheduled for year {disturbance_year}, beyond the "
            f"{horizon_years}-year horizon — it will not occur in this run."
        )

    # 5. Climate extremes.
    if climate_dT >= 5.0:
        warnings.append(
            f"Climate ΔT = +{climate_dT:.1f} °C is large enough to shift biomes "
            "(e.g. tundra → boreal forest) within decades."
        )
    if climate_dT <= -3.0:
        warnings.append(
            f"Climate ΔT = {climate_dT:.1f} °C pushes the system toward a colder "
            "regime (potential glaciation if sustained)."
        )
    if abs(climate_dP_pct) >= 40.0:
        direction = "drought" if climate_dP_pct < 0 else "flooding"
        warnings.append(
            f"Precipitation change of {climate_dP_pct:+.0f}% implies sustained "
            f"{direction}, which is itself a regime-shifting disturbance."
        )

    # 6. Off-biome species (informational; existing UI also calls this out).
    biome = biome_by_id(biome_id) or {}
    char_set = set(biome.get("characteristic_species", []))
    off = [s for s in species if s["id"] not in char_set]
    if off and len(off) == len(species):
        warnings.append(
            "None of the selected species are native to this biome. The whole "
            "system is essentially a thought experiment."
        )

    return warnings


def relevant_kb_subset(biome_id: str, species_ids: list[str], disturbance_id: str | None) -> dict:
    relevant_interactions = []
    for ix in load_interactions():
        members = {ix.get("predator"), ix.get("prey"), ix.get("actor"),
                   ix.get("species_a"), ix.get("species_b")} - {None}
        if members & set(species_ids):
            relevant_interactions.append(ix)
    return {
        "biome": biome_by_id(biome_id),
        "species": [species_by_id(s) for s in species_ids if species_by_id(s)],
        "interactions": relevant_interactions,
        "disturbance": next(
            (d for d in load_disturbances() if d["id"] == disturbance_id), None
        ),
    }
