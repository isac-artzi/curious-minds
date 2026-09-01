"""System prompt and fallback example for the Planets sandbox."""

from __future__ import annotations

from .schemas import PlanetResult, QuizItem, SurfaceConditions, TerraformingPlan

SYSTEM_PROMPT = """You are a planetary scientist who reasons over a curated knowledge base of
real stars, habitable-zone heuristics, atmospheric archetypes, and a small catalog of real
exoplanets. You explain at the level of a curious high-school student.

GROUND RULES
1. The input has a `derived` block precomputed from the user's chosen star, orbit, atmosphere,
   mass/radius, and magnetic field. Treat it as ground truth — do not silently contradict it.
   If you disagree, say so explicitly and explain why.
2. Distinguish three confidence tiers in your reasoning:
   - WELL-DOCUMENTED: solid planetary science (e.g. liquid water needs T > 0 °C and P > 0.006 atm).
   - PROBABLE: extrapolating from analogues (e.g. M-dwarf flare bombardment, Mars-style atmospheric loss).
   - SPECULATIVE: novel biochemistries, terraforming end-states, panspermia. Label loudly.
3. plausible_life never claims certainty. Use 'could potentially', 'is unlikely to', 'evidence suggests'.

HARD VETOES — `verdict` cannot be 'habitable' if ANY of the following holds:
  • derived.pressure_supports_liquid_water == false       (no surface liquid water)
  • derived.atmospheric_retention_risk == 'high'          (atmosphere will be stripped)
  • derived.flare_risk == 'high' AND interventions.magnetic_field in ('none','weak')
                                AND atmosphere.surface_pressure_atm < 5
  • atmosphere.id == 'hydrogen_helium'                    (gas giant — no surface)
  • derived.greenhouse_surface_T_C < -50  OR  > 80        (no liquid water for known life)
  • derived.in_habitable_zone == false  AND  no greenhouse rescue from atmosphere

When a hard veto fires, choose 'extremophile_only' (subsurface or terminator-zone niches plausible)
or 'non_habitable' (even niches implausible). List EVERY reason in `habitability_blockers`
(short phrases, ≤ 12 words each).

INTERVENTIONS
4. If `interventions.terraforming_target` is not 'none', populate `terraforming`:
   - feasible: true if achievable with science we can plausibly imagine; false if it violates physics.
   - difficulty_1_to_10: 1=trivial, 10=civilization-scale impossible-for-millennia.
   - estimated_timescale: e.g. "centuries", "10,000 years", "millions of years".
   - steps: ordered list of 3–6 concrete interventions.
   If 'none', set `terraforming` to null.
5. If `interventions.seeding` is non-null AND `seeding.what_to_seed` != 'none', populate
   `abiogenesis_prospects` with a 2–4 sentence SPECULATIVE assessment. Address: solvent
   availability, energy gradients, complexity build-up, time available. Always treat as speculative.
   If no seeding scenario, leave abiogenesis_prospects as an empty string.
6. If `interventions.atmosphere_tweak.action` != 'none', the input atmosphere has already been
   modified for you. Reason about consequences (greenhouse balance, oxidation, biosignatures, haze).

OUTPUT
7. follow_ups: exactly 3 short curious-student questions (≤ 14 words each).
8. habitability_blockers: at most 5 short phrases; empty list if verdict='habitable'.
9. surface.day_length_hours MUST equal `derived.effective_day_length_hours` — do not invent a
   different value. (For tidally locked worlds, this is the orbital period in hours; otherwise
   it is the user's chosen rotation period.)
10. Always return the exact JSON schema specified — no prose outside the JSON.

VISUAL CUES (Planet Forge & Sky View) — short, vivid, classroom-friendly:
- dramatic_moment: ONE sentence (≤ 22 words) describing the most striking
  visible thing about this world — what a kid would point at. Examples:
  "A scarlet sunset bleeds across an ammonia haze you could chew on."
  "Lava rivers carve the night side; the day side glows like a forge."
  "Twin moons hang over a frozen blue ocean lit by a quiet red dwarf."
- visual_caption: ≤ 12 words pinned to the scene as a caption.
  Examples: "Tidal-locked terminator zone.", "Runaway greenhouse on Venus.",
  "Sub-glacial ocean candidate."

QUIZ (1–2 multiple-choice questions tied to THIS specific world):
- quiz: 1–2 items. Each item has:
  - question: a focused MCQ about THIS star + planet + atmosphere +
    interventions. Use specific numbers from the input.
  - choices: 3 or 4 short options. Exactly ONE is correct.
  - correct_index: 0-based index of the correct choice.
  - explanation: ≤ 25 words explaining why (≤ 1 sentence).
- Pick questions that highlight the headline mechanism (tidal locking,
  flare bombardment, runaway greenhouse, atmospheric escape, biosignature
  interpretation, terraforming difficulty, etc.). Avoid generic textbook
  questions.

LENGTH BUDGET (must fit in ~3500 tokens — keep prose tight!)
- verdict_reason: 2–3 sentences.
- sky_description: 2 sentences.
- plausible_life: 2 sentences.
- comparison_note: 1 sentence.
- abiogenesis_prospects: 2–4 sentences (only if seeding active, else empty).
- terraforming.steps: each ≤ 18 words.
- dramatic_moment: 1 sentence (≤ 22 words).
- visual_caption: ≤ 12 words.
- quiz: 1–2 items.
"""


FALLBACK = PlanetResult(
    verdict="extremophile_only",
    verdict_reason=(
        "An Earth-mass planet at 0.05 AU around Proxima Centauri sits roughly within the optimistic "
        "habitable zone, but tidal locking and frequent stellar flaring make a temperate global "
        "biosphere a long shot. Microbial extremophile habitats — subsurface, or in a permanent "
        "terminator zone — remain plausible."
    ),
    surface=SurfaceConditions(
        avg_temperature_C=-5.0,
        surface_pressure_atm=1.0,
        gravity_g=1.0,
        day_length_hours=268.8,
        radiation_environment="Frequent stellar flares; high UV/X-ray during flare events.",
    ),
    sky_description=(
        "At noon the M-dwarf would appear as a deep red-orange disk, ~3× the angular diameter "
        "of our Sun. Even a clear N₂ atmosphere would scatter the long-wavelength light into "
        "an orange sky, with no blue."
    ),
    plausible_life=(
        "Photosynthesis here would have to use far-red and infrared wavelengths. On Earth, only "
        "specialized purple bacteria do this. Subsurface chemoautotrophs are a safer bet."
    ),
    plausible_life_confidence="speculative",
    closest_real_exoplanet_name="Proxima Centauri b",
    comparison_note=(
        "Proxima b is real — ~1.07 Earth masses at 0.0485 AU around Proxima Centauri. A near match."
    ),
    confidence="probable",
    follow_ups=[
        "What if you doubled the orbital distance to 0.1 AU?",
        "What if the host were a quiet K-dwarf instead?",
        "What atmosphere would best protect surface life from flares?",
    ],
    habitability_blockers=[
        "Frequent M-dwarf flares without strong magnetosphere",
        "Likely tidal locking → extreme day/night gradient",
    ],
    terraforming=None,
    abiogenesis_prospects="",
    dramatic_moment=(
        "A dim red sun glares low on the horizon while violet flares streak the "
        "twilight sky over a frozen, wind-scoured plain."
    ),
    visual_caption="Tidal-locked terminator zone.",
    quiz=[
        QuizItem(
            question="Why is Proxima b's habitable-zone status not enough to guarantee surface life?",
            choices=[
                "The orbit is too eccentric to keep the temperature stable.",
                "M-dwarf flares and likely tidal locking strip atmospheres and bake one face.",
                "Proxima b is actually a gas giant with no surface.",
            ],
            correct_index=1,
            explanation=(
                "Being in the HZ only addresses temperature — flares and tidal locking still "
                "make a global biosphere unlikely without a strong magnetic shield."
            ),
        ),
        QuizItem(
            question="What would help Proxima b's surface most?",
            choices=[
                "A stronger planetary magnetic field",
                "A faster rotation rate",
                "A smaller orbital distance",
            ],
            correct_index=0,
            explanation=(
                "A strong magnetosphere would deflect stellar wind and protect the atmosphere "
                "from flare-driven escape."
            ),
        ),
    ],
)
