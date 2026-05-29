"""System prompt and per-scenario fallbacks for the Physics Lab.

The deterministic numbers come from ``simulators.py``. Claude only writes the
narrative, so the same ``PhysicsResult`` schema and one shared system prompt
cover every scenario.
"""

from __future__ import annotations

from .schemas import PhysicsResult, QuizItem

SYSTEM_PROMPT = """You are a high-school physics teacher who explains scenarios in plain language.
The user picks one scenario at a time; the deterministic numbers (forces, trajectories,
energies, wavelengths, etc.) are computed for you and provided in the input under
``computed``. Your job is to write the narrative around those numbers.

GROUND RULES
1. Stay at high-school physics level: algebraic, non-calculus formulas (kinematics,
   Newton's 2nd law, work–energy theorem, conservation of momentum/energy, T = 2π√(m/k),
   KE_max = h·f − φ, λ = h/p). No derivatives, no integrals.
2. Trust the numbers in ``computed`` — do NOT recompute them. Cite them in the summary
   and intuition (e.g. "the cart reaches 4.2 m/s at the bottom").
3. Be honest about assumptions: no air resistance, point masses, ideal springs, etc.
   List the most relevant ones in ``limitations_or_assumptions``.
4. Confidence tiers:
   - well_documented: textbook-standard physics with no approximations beyond the
     listed assumptions (projectile w/o drag, elastic collision, ideal SHM, etc.)
   - probable: pedagogical model that captures the main physics but skips secondary
     effects (rollercoaster friction approximated per segment).
   - speculative: edge cases the model is not designed for (e.g. de Broglie at v > 0.1c
     where classical p = mv breaks down, photoelectric below threshold).
5. follow_ups must contain exactly 3 short curious-student questions, each ≤ 12 words.
6. If ``user_question`` is non-empty, address it in the summary AND make sure
   ``intuition`` directly speaks to it.

VISUAL CUES (for the Apparatus Theater animation above the narrative)
- dramatic_moment: ONE vivid sentence (≤ 25 words) about the cool thing students should
  watch for — e.g., "Notice how the ball spends almost all its time near the peak."
  Make it pop. Reference computed numbers when it lands well.
- visual_caption: a SHORT (≤ 12 words) banner that floats over the animation —
  e.g., "Peak: 12.4 m · Range: 47 m". Punchy, numeric when possible.

QUIZ (return 1–2 items in the ``quiz`` array; OK to return 0 if nothing tight fits)
- Each item: ``question`` (1 sentence), ``choices`` (2–4 short strings), ``correct_index``
  (0-based), and a one-sentence ``explanation``.
- Tie each question to THIS scenario's computed numbers or qualitative behavior
  (e.g., "What happens to the range if we double v₀?", "Will electrons eject if we
   drop the frequency by 30%?"). Avoid generic textbook questions.
- Keep choices short (≤ 8 words). Exactly ONE correct choice per item.

LENGTH BUDGET (must fit in ~2000 tokens — keep prose tight!)
- summary: 1–2 sentences citing the key computed numbers.
- intuition: 2–3 sentences of plain-language "why".
- key_concepts: 3–5 short labels (e.g. "Conservation of momentum", "Restitution").
- common_misconceptions: 1–3 short bullets.
- real_world_examples: 1–3 short bullets (sports, vehicles, lab demos, devices).
- limitations_or_assumptions: 1–3 short bullets.
- follow_ups: exactly 3, each ≤ 12 words.
- dramatic_moment: ≤ 25 words.
- visual_caption: ≤ 12 words.

Always return the exact JSON schema specified — no prose outside the JSON.
"""


# ---------------------------------------------------------------------------
# Per-scenario fallbacks (used when no API key, API error, or schema failure).
# Each is a real PhysicsResult instance keyed by scenario_id.
# ---------------------------------------------------------------------------

FALLBACK: dict[str, PhysicsResult] = {
    "projectile": PhysicsResult(
        scenario_id="projectile",
        summary=(
            "A projectile launched at an angle follows a parabolic arc — "
            "horizontal speed stays constant while gravity reshapes the vertical motion."
        ),
        intuition=(
            "Break the launch velocity into horizontal and vertical pieces. The "
            "horizontal piece never changes (no air resistance), so range = vₓ · t. "
            "The vertical piece slows, reverses, and returns under constant "
            "gravitational acceleration g."
        ),
        key_concepts=[
            "Independence of x- and y-motion",
            "Constant horizontal velocity",
            "Uniform vertical acceleration",
            "Parabolic trajectory",
        ],
        common_misconceptions=[
            "Heavier objects do NOT fall faster (in vacuum).",
            "Maximum range is at 45° only when launch and landing heights are equal.",
        ],
        real_world_examples=[
            "Basketball free throw arc",
            "Cannonballs and artillery range tables",
            "Water from a garden hose",
        ],
        limitations_or_assumptions=[
            "No air resistance — real range is shorter at high speeds.",
            "Constant g (flat-Earth approximation).",
        ],
        follow_ups=[
            "What angle gives the longest range from a cliff?",
            "How would air drag change the trajectory?",
            "What if gravity were half as strong?",
        ],
        confidence="well_documented",
        dramatic_moment=(
            "Watch the ball linger near its peak — that's why catches look easy at the top of the arc."
        ),
        visual_caption="Apex hangtime · gravity bends the y-motion",
        quiz=[
            QuizItem(
                question="If you double v₀ while keeping the launch angle, the range…",
                choices=["doubles", "quadruples", "stays the same", "halves"],
                correct_index=1,
                explanation="Range scales with v₀² for level ground (R = v₀² sin(2θ)/g).",
            ),
            QuizItem(
                question="From level ground, which angle gives the LONGEST range?",
                choices=["30°", "45°", "60°", "75°"],
                correct_index=1,
                explanation="sin(2θ) is maxed at θ = 45°.",
            ),
        ],
    ),

    "incline": PhysicsResult(
        scenario_id="incline",
        summary=(
            "On an inclined plane, gravity splits into a component pulling the block "
            "down the slope and a component pressing it into the surface."
        ),
        intuition=(
            "The 'down-the-slope' force is m·g·sin(θ); the 'into-the-surface' force "
            "is m·g·cos(θ). Friction can resist motion up to μₛ·N. If the net push "
            "exceeds that limit, the block slides and kinetic friction (μₖ·N) takes "
            "over."
        ),
        key_concepts=[
            "Resolving forces along/perpendicular to the slope",
            "Static vs kinetic friction",
            "Free-body diagram",
            "Newton's 2nd law",
        ],
        common_misconceptions=[
            "Friction does not depend on contact area (Amontons' law).",
            "A block at rest on an incline isn't 'stuck' — friction only matches what's needed.",
        ],
        real_world_examples=[
            "Cars on a banked turn",
            "Ramps for loading trucks",
            "Skiing down a slope",
        ],
        limitations_or_assumptions=[
            "Rigid block, single contact patch.",
            "Constant μ — real friction varies with speed and temperature.",
        ],
        follow_ups=[
            "At what angle does the block always slip?",
            "How much push is needed to drag it up?",
            "What changes with a heavier block?",
        ],
        confidence="well_documented",
        dramatic_moment=(
            "Tilt past the critical angle and friction snaps — the block goes from glued to gliding in an instant."
        ),
        visual_caption="Static friction holds · then kinetic takes over",
    ),

    "rollercoaster": PhysicsResult(
        scenario_id="rollercoaster",
        summary=(
            "Energy converts between gravitational PE and KE along the track; friction "
            "skims a little off each segment, sometimes leaving a hill unreachable."
        ),
        intuition=(
            "The cart starts with potential energy m·g·h₀. As it descends, that "
            "becomes kinetic energy ½·m·v². Going up the next hill, KE turns back "
            "into PE — but friction has stolen some, so each hill must be lower than "
            "the last unless the cart had energy to spare."
        ),
        key_concepts=[
            "Conservation of energy",
            "Gravitational potential energy",
            "Kinetic energy",
            "Work done by friction",
        ],
        common_misconceptions=[
            "A cart can never reach a hill higher than its starting point.",
            "Speed depends on height drop, not on the path taken (without friction).",
        ],
        real_world_examples=[
            "Rollercoaster design (first hill must be tallest)",
            "Skateboard half-pipes",
            "Pendulum clocks slowing without rewinding",
        ],
        limitations_or_assumptions=[
            "Friction loss approximated as μ·m·g·L per segment.",
            "Treats the cart as a point mass; ignores curves and rotation.",
        ],
        follow_ups=[
            "What if the second hill were taller than the first?",
            "How does mass change the result?",
            "Why do real coasters use chain lifts?",
        ],
        confidence="probable",
        dramatic_moment=(
            "Every meter of hill drop becomes kinetic energy at the bottom — minus whatever friction steals along the way."
        ),
        visual_caption="PE ↔ KE swap · friction skims the total",
    ),

    "collision": PhysicsResult(
        scenario_id="collision",
        summary=(
            "Momentum is always conserved in a 1-D collision; kinetic energy is "
            "conserved only when e = 1 (perfectly elastic)."
        ),
        intuition=(
            "Total momentum before = total momentum after, no matter how squishy the "
            "collision. The coefficient of restitution e tells you how 'bouncy' it "
            "is: e = 1 means objects rebound at the same relative speed, e = 0 means "
            "they stick together."
        ),
        key_concepts=[
            "Conservation of momentum",
            "Coefficient of restitution",
            "Elastic vs inelastic collisions",
            "Centre-of-mass velocity",
        ],
        common_misconceptions=[
            "Energy 'lost' in inelastic collisions becomes heat, sound, deformation.",
            "Heavier object doesn't always 'win' — it depends on velocities too.",
        ],
        real_world_examples=[
            "Newton's cradle (near-elastic)",
            "Car crashes (highly inelastic — crumple zones)",
            "Billiard balls (nearly elastic)",
        ],
        limitations_or_assumptions=[
            "1-D motion only (no glancing blows).",
            "No external forces during the brief collision.",
        ],
        follow_ups=[
            "What if one mass were infinite (a wall)?",
            "How does restitution relate to crumple zones?",
            "Where does the lost energy actually go?",
        ],
        confidence="well_documented",
        dramatic_moment=(
            "Total momentum survives the smash even when kinetic energy gets shredded into heat and sound."
        ),
        visual_caption="Σp before = Σp after · energy may vanish",
    ),

    "spring": PhysicsResult(
        scenario_id="spring",
        summary=(
            "A mass on an ideal spring oscillates sinusoidally with period "
            "T = 2π√(m/k); KE and PE swap continuously while total energy stays put."
        ),
        intuition=(
            "Hooke's law gives a restoring force F = −k·x. A larger mass swings "
            "more slowly; a stiffer spring swings faster. At the extremes all energy "
            "is potential; at the centre all of it is kinetic."
        ),
        key_concepts=[
            "Simple harmonic motion (SHM)",
            "Hooke's law",
            "Period and angular frequency",
            "Energy partition",
        ],
        common_misconceptions=[
            "Period does NOT depend on amplitude (small-oscillation approximation).",
            "Velocity is maximum at the centre, not the extremes.",
        ],
        real_world_examples=[
            "Car suspensions",
            "Tuning-fork vibrations",
            "Atomic bonds modelled as tiny springs",
        ],
        limitations_or_assumptions=[
            "Linear spring (Hooke's law) — fails for large stretches.",
            "No friction or damping.",
        ],
        follow_ups=[
            "What if the spring had damping?",
            "How does period change on the Moon?",
            "What's the energy at half-amplitude?",
        ],
        confidence="well_documented",
        dramatic_moment=(
            "Energy bounces between stretched spring and moving block, but never disappears — total stays constant."
        ),
        visual_caption="T = 2π√(m/k) · period is mass+stiffness only",
    ),

    "photoelectric": PhysicsResult(
        scenario_id="photoelectric",
        summary=(
            "Einstein's photoelectric equation KE_max = h·f − φ explains why no "
            "electrons fly out below the threshold frequency, no matter how bright the light."
        ),
        intuition=(
            "Light comes in discrete photons of energy h·f. One photon kicks out at "
            "most one electron, and only if its energy exceeds the metal's work "
            "function φ. Brighter light = more photons = more electrons, but their "
            "max energy depends on frequency, not intensity."
        ),
        key_concepts=[
            "Photon energy E = h·f",
            "Work function φ",
            "Threshold frequency",
            "Particle nature of light",
        ],
        common_misconceptions=[
            "Brighter light doesn't give faster electrons — only higher frequency does.",
            "Electrons aren't 'shaken loose' continuously; it's one-photon-per-electron.",
        ],
        real_world_examples=[
            "Solar cells",
            "Night-vision photomultiplier tubes",
            "Garage-door safety sensors",
        ],
        limitations_or_assumptions=[
            "Ignores tunnelling and multi-photon absorption (high-intensity lasers).",
            "Treats the metal surface as uniform with one work function.",
        ],
        follow_ups=[
            "Why doesn't this work with red light on most metals?",
            "What if you used a UV lamp instead?",
            "How is this used in solar panels?",
        ],
        confidence="well_documented",
        dramatic_moment=(
            "Below the threshold frequency NO electrons eject — turn the lamp brighter and still nothing happens."
        ),
        visual_caption="KE_max = h·f − φ · color matters, not brightness",
    ),

    "de_broglie": PhysicsResult(
        scenario_id="de_broglie",
        summary=(
            "Every particle has a matter-wave with wavelength λ = h/p — vanishingly "
            "small for everyday objects, but measurable for electrons and atoms."
        ),
        intuition=(
            "A baseball's wavelength is ~10⁻³⁴ m — far smaller than an atom — so wave "
            "behaviour is invisible. An electron at ~1% of light speed has λ ≈ 0.24 "
            "nm, comparable to atomic spacing, which is why electron diffraction works."
        ),
        key_concepts=[
            "Wave–particle duality",
            "Momentum p = m·v",
            "de Broglie wavelength λ = h/p",
            "Quantum scale vs classical scale",
        ],
        common_misconceptions=[
            "It's NOT just for light — every particle has a matter wave.",
            "Wavelength shrinks with speed (more momentum = smaller λ).",
        ],
        real_world_examples=[
            "Electron microscopes",
            "Neutron diffraction in materials science",
            "Atom interferometers",
        ],
        limitations_or_assumptions=[
            "Classical p = m·v breaks above ~0.1c — use relativistic momentum.",
            "Doesn't predict the spread of the wavepacket itself.",
        ],
        follow_ups=[
            "Why don't we see baseballs diffract?",
            "What's the wavelength of a thrown ball?",
            "How does this enable electron microscopes?",
        ],
        confidence="well_documented",
        dramatic_moment=(
            "Every object has a matter-wave — but a baseball's wavelength is smaller than a proton, so we never see it ripple."
        ),
        visual_caption="λ = h/p · waves of matter shrink with mass",
    ),
}
