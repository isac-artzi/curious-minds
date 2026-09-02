---
layout: default
title: "📐 NGSS & CSTA Alignment"
nav_order: 5
---

# NGSS & CSTA Alignment

**How to use this:** the alignments below are drafted from what each lab
actually does — not aspirational mappings. They're strong enough to drop into a
lesson plan or an administrator conversation.

> ⚠️ **Verify codes before formal use.** These performance expectations were
> written to match the labs' real content, but standards get revised and states
> adopt modified versions. Check each code against your state's current
> framework before putting it in a submitted plan, an evaluation document, or a
> grant application. The *descriptions* are reliable; treat the *codes* as a
> strong starting point that takes five minutes to confirm.

---

## What every lab does, regardless of content

These cut across all four labs and are the honest core of the alignment.

**Science & Engineering Practices**
- **SEP 2 — Developing and Using Models.** Every lab *is* a model. The confidence
  tiers make its limits explicit, which is the part usually left implicit.
- **SEP 4 — Analyzing and Interpreting Data.** Students read population curves,
  energy diagrams, trajectories, and orbital plots.
- **SEP 6 — Constructing Explanations.** Challenge mode forces a student
  explanation *before* the model offers one.
- **SEP 7 — Engaging in Argument from Evidence.** The confidence badges give
  students something concrete to argue with.

**Crosscutting Concepts**
- **Cause and Effect** — the central mechanic of all four labs.
- **Systems and System Models** — every lab defines a system boundary and shows
  what crossing it does.
- **Stability and Change** — disturbances, phase changes, orbital limits.

---

## 🧪 Chemistry What-If Lab

| Code | Performance expectation | How the lab addresses it |
|---|---|---|
| **MS-PS1-2** | Analyze data on properties before/after substances interact to determine whether a chemical reaction occurred | Products panel shows properties of reactants vs. products; salt from sodium + chlorine is the canonical case |
| **MS-PS1-5** | Model how the number of atoms doesn't change in a reaction, so mass is conserved | Balanced equations are typeset for every reaction; students verify atom counts |
| **MS-PS1-4** | Model changes in particle motion/temperature/state on adding or removing thermal energy | The 10 K–10,000 K temperature slider with live phase feedback |
| **HS-PS1-2** | Explain reaction outcomes using outermost electron states and periodic trends | The atom-zoom view shows electron shells; the periodic table picker makes trends visible |
| **HS-PS1-5** | Explain effects of temperature/concentration on reaction rate | Temperature and quantity controls; rate discussion in the output |
| **HS-PS1-6** | Refine a chemical system to increase product at equilibrium | The Haber–Bosch pressure exploration (card C5) |

**CSTA:** `2-DA-09` (refine computational models based on generated data) ·
`3A-DA-12` (create computational models representing relationships in data)

---

## 🌿 Ecosystem / Biome Lab

| Code | Performance expectation | How the lab addresses it |
|---|---|---|
| **MS-LS2-1** | Analyze data for effects of resource availability on populations | Population sliders plus climate/precipitation controls over a 25-year horizon |
| **MS-LS2-2** | Explain patterns of interactions among organisms across ecosystems | Food-web graph built from the `diet` relationships in the KB |
| **MS-LS2-3** | Model cycling of matter and energy flow among living and nonliving parts | Trophic tiers including decomposers — the tier students usually skip |
| **MS-LS2-4** | Argue from evidence that changes to an ecosystem affect populations | The disturbance system: 8 disturbances, each producing a traced cascade |
| **MS-ESS3-5** | Ask questions about factors causing rising global temperatures | The climate ΔT control, run comparatively at +2 °C and +4 °C |
| **HS-LS2-2** | Use mathematical representations to explain factors affecting biodiversity and populations | Population dynamics charts across scenarios |
| **HS-LS2-6** | Evaluate claims about ecosystem stability under modest vs. extreme disturbance | Directly: run the same biome under increasing disturbance severity |
| **HS-LS2-7** | Design and refine a solution reducing human impact on biodiversity | Students propose interventions and test them against the cascade |

**CSTA:** `1B-DA-07` (use data to propose cause-and-effect relationships) ·
`3A-DA-11` (interactive data visualizations of real-world phenomena)

---

## 🪐 Planet / Exoplanet Builder

| Code | Performance expectation | How the lab addresses it |
|---|---|---|
| **MS-ESS1-3** | Analyze data to determine scale properties of solar-system objects | Mass, radius, and orbital distance controls with real comparison bodies |
| **MS-ESS2-6** | Model how unequal heating and rotation drive atmospheric circulation | Rotation-period control and its effect on climate and winds |
| **HS-ESS1-4** | Use computational representations to predict orbiting-object motion | Orbital distance and stellar mass drive the habitable-zone calculation |
| **HS-ESS1-6** *(verify)* | Apply evidence to reason about planetary formation and history | Comparison against catalogued NASA Exoplanet Archive worlds |
| **HS-ESS2-4** | Use a model to describe factors changing planetary climate | The Venus runaway-greenhouse scenario (card P3) |

**CSTA:** `3A-DA-12` (computational models of relationships in data) ·
`2-IC-20` (tradeoffs of computing technologies — here, model vs. observation)

---

## 🔬 Physics Lab

| Code | Performance expectation | How the lab addresses it |
|---|---|---|
| **MS-PS2-2** | Investigate that change in motion depends on net force and mass | Incline scenarios with friction and mass controls |
| **MS-PS3-1** | Model the relationship of kinetic energy to mass and speed | Rollercoaster energy-bar visualization |
| **MS-PS3-5** | Argue that changing an object's motion transfers energy | The stall-vs-clear coaster comparison |
| **HS-PS2-1** | Analyze data supporting Newton's second law | Projectile and incline scenarios with variable `g` |
| **HS-PS2-2** | Show that total momentum is conserved in a closed system | Elastic vs. inelastic collision pair (card F4) |
| **HS-PS3-1** | Create a computational model of energy change in a system | Rollercoaster energy accounting |
| **HS-PS3-2** | Model energy as motion of particles plus relative position | Spring/oscillator scenarios trading KE and PE |
| **HS-PS4-3** | Evaluate wave vs. particle models of electromagnetic radiation | The photoelectric pair — the clearest case in K-12 physics |
| **HS-PS4-4** | Evaluate claims about effects of different EM frequencies on matter | Below-threshold vs. UV photoelectric scenarios |

**CSTA:** `3A-DA-12` (computational models) · `2-DA-08` (collect and transform
data using computational tools)

---

## The cross-cutting one: AI literacy

This is what makes Curious Minds different from a simulator, and it maps to CSTA
more cleanly than to NGSS.

| Code | Standard | How |
|---|---|---|
| **2-IC-21** | Discuss issues of bias and accessibility in existing technologies | Confidence tiers make model uncertainty visible and discussable |
| **3A-IC-24** | Evaluate how computing impacts social and cultural practices | "Where does this knowledge come from?" — the JSON knowledge base is openable |
| **3A-IC-25** *(verify)* | Evaluate computational artifacts for correctness and usability | Students audit `speculative` claims against outside sources |
| **2-IC-20** | Compare tradeoffs of computing technologies | Live reasoning vs. cached fallback; grounded AI vs. ungrounded chatbot |

**The move that makes this real:** open `data/ecosystem/species.json` on the
projector. Show students the exact line the model read to answer their question.
The distinction between *grounded* AI and a chatbot guessing from memory becomes
concrete in about fifteen seconds — and it is the most transferable thing in the
session.

---

*Source: `docs/NGSS_CSTA_ALIGNMENT.md`. Corrections welcome via GitHub Issues —
especially from anyone who teaches to these standards daily.*
