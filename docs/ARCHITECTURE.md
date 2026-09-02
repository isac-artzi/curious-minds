# How Curious Minds Works

*The "how did they do that?" answer, in prose.*

Curious Minds is not a science simulator. It runs no physics engine, solves no
differential equations, and contains no chemistry solver. It is a **retrieval +
reasoning + rendering** pipeline, and understanding that distinction is the
whole pedagogical point of the project.

---

## The four-layer pattern

Every one of the four labs is the same four layers. Learn it once, and you can
read — or extend — any of them.

```
   1. KNOWLEDGE BASE        data/<domain>/*.json
      hand-curated JSON, version-controlled, human-readable
                 |
                 v
   2. PROMPT ASSEMBLY       curious_mind/<domain>/prompts.py
      SYSTEM_PROMPT + only the KB rows relevant to this question
                 |
                 v
   3. STRUCTURED REASONING  curious_mind/llm.py -> Claude Haiku 4.5
      response validated against a Pydantic schema, not free text
                 |
                 v
   4. SCIENTIFIC RENDERING  curious_mind/<domain>/visuals.py + theater.py
      Plotly figures, animated SVG, confidence badges
```

### Layer 1 — The knowledge base

Plain JSON. No database, no API, no scraping. Anyone can read it, and anyone
can edit it in a text editor.

| Domain | Files | Contents |
|---|---|---|
| Chemistry | `elements.json`, `compounds.json`, `reactions.json` | 118 elements, 20 compounds, 10 reference reactions |
| Ecosystem | `species.json`, `biomes.json`, `disturbances.json`, `interactions.json` | 81 species with IUCN status, 12 biomes, 8 disturbances |
| Planets | `named_stars.json`, `exoplanets.json`, `atmospheres.json`, `stars.json` | 21 named stars, 20 real exoplanets, atmosphere presets |
| Physics | `scenarios.json`, `particles.json` | 15 worked scenarios across 7 scenario types, 6 particles |

This is the layer that makes the output trustworthy. The model is not recalling
that a gray wolf eats elk — it is **reading that from a file you can inspect and
correct**. That is the difference between a tool a teacher can stand behind and
a chatbot.

### Layer 2 — Prompt assembly

Each domain's `prompts.py` holds a `SYSTEM_PROMPT` that establishes the
scientific register, the grade level, and — critically — the requirement to
label confidence. The lab then selects **only the relevant KB rows** and passes
them in. Ecosystem's `relevant_kb_subset()` in `data_loader.py` is the clearest
example: it ships the chosen biome, the selected species, and the disturbance,
and nothing else.

Two reasons this matters. It keeps token cost near zero, and it keeps the model
anchored: a small, precise context produces far less drift than a large vague one.

### Layer 3 — Structured reasoning

`llm.call_structured()` is the single choke point through which all four labs
talk to Claude. It returns a tuple:

```python
result, source = llm.call_structured(
    domain="ecosystem",
    system_prompt=prompts.SYSTEM_PROMPT,
    user_payload=payload,
    schema=schemas.EcosystemResult,
    fallback=prompts.FALLBACK,
)
```

`source` is one of `"live"`, `"cached"`, or `"fallback"`, and the UI always
shows which one you got. Three things happen inside that are worth knowing:

- **Schema validation.** The response must satisfy a Pydantic v2 model. If it
  does not, the call retries once with the validator's own error text appended
  to the system prompt — the model is told exactly how it failed.
- **Truncation repair.** `_repair_truncated_json()` walks the bracket stack of a
  response cut short by `max_tokens` and closes it cleanly, rather than throwing
  away a nearly-complete answer.
- **Graceful degradation.** No API key, network failure, or two failed
  validation attempts all land in the same place: a real, hand-written
  `FALLBACK` object. **The app never shows an error to a classroom.** It shows
  a cached example, clearly labeled.

### Layer 4 — Rendering

Plotly for data (population curves, energy diagrams, orbital plots, trajectory
traces), plus hand-written animated SVG "theaters" rendered in an iframe via
`st.components.v1.html` to avoid CSS collisions with Streamlit.

---

## The three ideas worth stealing

If you take nothing else from this codebase, take these.

**1. Ground the model in a file you control.** The knowledge base is the
difference between "the AI said so" and "the AI reasoned over this specific,
inspectable data." When a student asks *how do you know?*, you open the JSON.

**2. Demand structure, not prose.** Asking for free text gets you something you
must read and trust. Asking for a schema-validated object gets you something you
can **render, chart, validate, and reject**. Every visual in this app exists
because the data arrived in a known shape.

**3. Label your confidence.** Every claim carries `well_documented`, `probable`,
or `speculative`, shown as a colored pill. This turns the model's uncertainty
from a hidden liability into the actual lesson: students learn to see the
boundary between established science and extrapolation. This is the single most
valuable pedagogical feature in the project, and it costs about twelve lines.

---

## Shared infrastructure

| Module | Role |
|---|---|
| `curious_mind/llm.py` | Claude client, structured calls, JSON repair, caching |
| `curious_mind/ui.py` | `page_setup`, headers, info panels, confidence badges |
| `curious_mind/persistence.py` | `.curious` file save/load, starter gallery |
| `curious_mind/animations.py` | Shared animation helpers |

Four labs share three modules. That is deliberately the *right* amount of
abstraction — enough to avoid copy-paste drift, not so much that adding a fifth
lab means fighting a framework.

## The `.curious` file

A saved experiment is small, readable JSON:

```json
{
  "schema": "curious-minds.experiment",
  "version": "1.0",
  "app": "ecosystem",
  "created_at": "2026-09-03T15:04:05Z",
  "title": "Yellowstone without wolves",
  "inputs": { "...": "every slider and selection" },
  "notes": "For 7th period."
}
```

It stores **inputs, not outputs** — so re-opening it re-runs the reasoning. Hand
one to a student and they get your setup, then discover the result themselves.

## Challenge mode

Every lab has a `🎯 Challenge mode` toggle that **hides the result until the
student commits a prediction**. Predict-then-check is the highest-leverage
switch in the app for classroom use. Turn it on before you turn anything else on.

---

## What this is not

Honest limits, so you can answer them when a colleague asks:

- **Not a numerical simulator.** Physics Lab plots real closed-form kinematics,
  but the *explanation* is model-generated. Ecosystem population curves are
  reasoned, not integrated from Lotka–Volterra.
- **Not research-grade.** It is calibrated to a good K-12 textbook. It is not
  a source for a paper.
- **Not deterministic.** The same inputs can yield differently-worded output.
  The `.curious` file preserves the setup, not the exact prose.
- **Not free to run live.** Reasoning requires an Anthropic API key. Without
  one, everything still renders in fallback mode. See `FORK_AND_DEPLOY.md`.
