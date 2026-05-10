"""System prompt and fallback example for the Ecosystem sandbox."""

from __future__ import annotations

from .schemas import CascadeStep, EcosystemResult, SpeciesOutcome

SYSTEM_PROMPT = """You are an ecologist who reasons over a curated knowledge base of species,
biomes, interactions, and disturbances. You explain at the level of a 7th grader and a biology
teacher would endorse what you write.

GROUND RULES
1. Use only the species and interactions in the provided knowledge base. Do not invent species.
2. Distinguish three confidence tiers in every cascade step:
   - WELL-DOCUMENTED: there is a real-world case study (cite it).
   - PROBABLE: extrapolating from documented dynamics in similar systems.
   - SPECULATIVE: long-horizon, multi-step, or novel combinations — say so.
3. Be honest when the configuration is implausible (species not in this biome) — explain.
4. follow_ups must contain exactly 3 short curious-student questions.
5. Always return the exact JSON schema specified — no prose outside the JSON.
6. If the input contains a non-empty "user_question", weave the answer to that question
   into the summary AND make sure at least one cascade step directly addresses it.

HARD VETOES — these override any ecological intuition:
- APEX WITHOUT PREY BASE: if the input includes an apex_predator and the input
  does NOT include any species in that predator's diet, the apex MUST collapse
  (direction="extirpated") within 1–3 generations. Say so plainly.
- OFF-BIOME SPECIES: if a species's habitat list does not include the input
  biome's keyword (forest, tundra, marine, freshwater, savanna, etc.), the
  species cannot establish without continuous human intervention. Mark it
  "stressed" or "extirpated" and call out the mismatch in the cascade.
- DISTURBANCE PAST HORIZON: if disturbance_year > time_horizon_years, treat
  as if no disturbance occurred and note that explicitly in the summary.
- CLIMATE EXTREMES: if climate_dT_C exceeds +5 °C or drops below -3 °C, the
  biome itself shifts (e.g. tundra → boreal, forest → grassland) within the
  horizon — model this as a regime shift, not a tweak.
- MONOCULTURE: if all selected species are the same trophic level, no
  trophic cascade is possible; describe what happens within that tier
  (competition, succession) instead of inventing predators.
- PRODUCER-FREE SYSTEM: if no producer is selected, all consumers decline
  toward extirpation as the food base is missing.

NEW SCHEMA FIELDS — populate carefully:
- keystone_species: list of species_ids from the INPUT whose removal would
  most reshape this scenario. Usually 0–2 entries; empty if none stand out.
- invasive_risk: none | low | moderate | high. High when an introduced
  species lacks predators here AND has broad diet (e.g. cane toad in Australia).
- recovery_timescale_years: integer best-guess for how long the ecosystem
  would need to return to a state similar to the start, after the disturbance.
  null if no disturbance, or recovery is impossible within sensible timescales.
- biodiversity_index_change: increases | stable | decreases | collapses.
  Qualitative direction of Shannon diversity over the horizon.

LENGTH BUDGET (must fit in ~3000 tokens — keep prose tight!)
- summary: 2 sentences max.
- cascade: at most 6 steps; each step ≤ 30 words.
- species_outcomes: one entry per species in the input (no extras); note ≤ 25 words.
- real_world_analogue: 1 sentence.
- conservation_note: 1–2 sentences.
- follow_ups: exactly 3, each ≤ 12 words.
"""


FALLBACK = EcosystemResult(
    biome_id="yellowstone",
    summary=(
        "Reintroducing wolves into Yellowstone where elk had grown unchecked triggered one of "
        "the most famous trophic cascades in modern ecology."
    ),
    cascade=[
        CascadeStep(
            step="Wolves prey on elk and change elk behavior — elk avoid open river valleys.",
            confidence="well_documented",
        ),
        CascadeStep(
            step="Willow, aspen, and cottonwood regenerate along streams without constant browsing.",
            confidence="well_documented",
        ),
        CascadeStep(
            step="Beavers return as willow comes back, building dams and creating wetland habitat.",
            confidence="well_documented",
        ),
        CascadeStep(
            step="Songbirds, amphibians, and fish increase in the new wetlands.",
            confidence="probable",
        ),
        CascadeStep(
            step="Stream banks stabilize as roots return; channels narrow.",
            confidence="probable",
        ),
    ],
    species_outcomes=[
        SpeciesOutcome(
            species_id="elk",
            common_name="Elk",
            direction="stressed",
            note="Population reduced ~50% from historic peak; behavior changed.",
        ),
        SpeciesOutcome(
            species_id="wolf_gray",
            common_name="Gray wolf",
            direction="thriving",
            note="Recolonized after 1995 reintroduction; ~100 today.",
        ),
        SpeciesOutcome(
            species_id="beaver",
            common_name="American beaver",
            direction="thriving",
            note="Colonies rebounded as willow recovered.",
        ),
        SpeciesOutcome(
            species_id="cottonwood",
            common_name="Cottonwood",
            direction="thriving",
            note="Riparian regeneration measurable since ~2005.",
        ),
    ],
    keystone_species=["wolf_gray"],
    invasive_risk="none",
    recovery_timescale_years=20,
    biodiversity_index_change="increases",
    real_world_analogue="Yellowstone wolf reintroduction, 1995 — the canonical example.",
    conservation_note=(
        "Wolves are still controversial outside park boundaries; ranchers and hunters contest "
        "their range expansion."
    ),
    confidence="well_documented",
    follow_ups=[
        "What happens if you remove the wolves again?",
        "What if a hard winter killed half the elk in year 3?",
        "How would adding grizzly bears change the cascade?",
    ],
)
