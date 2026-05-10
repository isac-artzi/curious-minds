"""Smoke tests for the knowledge bases and module imports."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def test_chemistry_kb_loads():
    elements = json.loads((DATA / "chemistry/elements.json").read_text())
    compounds = json.loads((DATA / "chemistry/compounds.json").read_text())
    reactions = json.loads((DATA / "chemistry/reactions.json").read_text())
    assert len(elements) >= 25
    assert len(compounds) >= 15
    assert len(reactions) >= 10
    # All compounds reference known element symbols
    symbols = {e["symbol"] for e in elements}
    for c in compounds:
        for comp in c["components"]:
            assert comp in symbols, f"{c['formula']} references unknown {comp}"


def test_ecosystem_kb_loads():
    species = json.loads((DATA / "ecosystem/species.json").read_text())
    biomes = json.loads((DATA / "ecosystem/biomes.json").read_text())
    interactions = json.loads((DATA / "ecosystem/interactions.json").read_text())
    disturbances = json.loads((DATA / "ecosystem/disturbances.json").read_text())
    ids = {s["id"] for s in species}
    assert len(species) >= 25
    assert len(biomes) >= 10
    assert len(interactions) >= 8
    assert len(disturbances) >= 5
    for ix in interactions:
        for k in ("predator", "prey", "actor", "species_a", "species_b"):
            v = ix.get(k)
            if v is not None and ix["type"] in {"predation", "competition"}:
                # Allow predation prey to be a generic descriptor not in KB
                if k in {"predator", "actor", "species_a", "species_b"} and v not in ids:
                    raise AssertionError(f"{ix} references unknown species id {v!r}")


def test_planets_kb_loads():
    stars = json.loads((DATA / "planets/stars.json").read_text())
    atms = json.loads((DATA / "planets/atmospheres.json").read_text())
    exos = json.loads((DATA / "planets/exoplanets.json").read_text())
    assert len(stars) == 7
    assert len(atms) >= 5
    assert len(exos) >= 15


def test_modules_import():
    # Import every page-side module to catch syntax errors.
    import importlib

    for mod in [
        "curious_mind",
        "curious_mind.llm",
        "curious_mind.ui",
        "curious_mind.persistence",
        "curious_mind.animations",
        "curious_mind.chemistry.data_loader",
        "curious_mind.chemistry.schemas",
        "curious_mind.chemistry.prompts",
        "curious_mind.chemistry.visuals",
        "curious_mind.ecosystem.data_loader",
        "curious_mind.ecosystem.schemas",
        "curious_mind.ecosystem.prompts",
        "curious_mind.ecosystem.visuals",
        "curious_mind.planets.data_loader",
        "curious_mind.planets.schemas",
        "curious_mind.planets.prompts",
        "curious_mind.planets.visuals",
    ]:
        importlib.import_module(mod)


def test_starter_examples_load():
    for app in ("chemistry", "ecosystem", "planet"):
        files = list((ROOT / "examples" / app).glob("*.curious"))
        assert files, f"no starter examples for {app}"
        for p in files:
            obj = json.loads(p.read_text())
            assert obj["schema"] == "curious-minds.experiment"
            assert obj["app"] == app
            assert "inputs" in obj
