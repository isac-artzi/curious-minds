"""Load physics constants and small reference tables."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "physics"


@lru_cache(maxsize=1)
def load_constants() -> dict[str, dict]:
    return json.loads((DATA_DIR / "constants.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_particles() -> list[dict]:
    return json.loads((DATA_DIR / "particles.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_metals() -> list[dict]:
    return json.loads((DATA_DIR / "photoelectric_metals.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_materials() -> list[dict]:
    return json.loads((DATA_DIR / "materials.json").read_text(encoding="utf-8"))


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


def constant(name: str) -> float:
    """Return the numeric value of a named constant."""
    return float(load_constants()[name]["value"])


def particle_by_id(pid: str) -> dict | None:
    for p in load_particles():
        if p["id"] == pid:
            return p
    return None


def metal_by_id(mid: str) -> dict | None:
    for m in load_metals():
        if m["id"] == mid:
            return m
    return None


def material_by_id(mid: str) -> dict | None:
    for m in load_materials():
        if m["id"] == mid:
            return m
    return None
