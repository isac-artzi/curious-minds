# Modifying Curious Minds

Three tiers, easiest first. **Tier 1 needs no coding at all** — and it is where
almost all the classroom value is.

---

# Tier 1 — Edit the knowledge base (no code)

Every scientific fact lives in `data/<domain>/*.json`. Edit these on GitHub in
your browser: open the file, click ✏️, edit, **Commit changes**. Streamlit
redeploys in about a minute.

> **One rule: valid JSON.** Every `{` needs a `}`, every entry but the last needs
> a trailing comma, and strings need `"double quotes"`. If the app won't start
> after an edit, you broke a comma. Paste the file into jsonlint.com to find it.

## Add a species to your local watershed

`data/ecosystem/species.json` — copy an existing entry and change it:

```json
{
  "id": "salmon_chinook",
  "common_name": "Chinook salmon",
  "binomial": "Oncorhynchus tshawytscha",
  "trophic_level": "secondary_consumer",
  "diet": ["zooplankton", "herring"],
  "habitat": ["river", "ocean", "coast"],
  "iucn_status": "Least Concern",
  "role": "Anadromous fish; carries marine nutrients upstream, feeding bears, eagles, and riparian forests when it spawns and dies.",
  "emoji": "🐟"
}
```

Field notes:
- **`id`** — lowercase, underscores, unique. Other species reference it in `diet`.
- **`trophic_level`** — one of `producer`, `primary_consumer`, `secondary_consumer`, `apex_predator`, `decomposer`. Drives food-web placement.
- **`diet`** — must use the **`id`s** of other species. Misspell one and the food web silently loses an edge.
- **`habitat`** — must match biome `id`s in `biomes.json` for the species to appear in that biome's picker.
- **`role`** — this text goes to Claude. **A specific, causal sentence produces a dramatically better cascade narrative than a vague one.** This is the single highest-leverage field in the whole project.

## Add a biome

`data/ecosystem/biomes.json`. Give it an `id`, a `name`, and
`characteristic_species` (a list of species `id`s). Any species whose `habitat`
includes your biome `id` becomes selectable there.

## Add a chemical reaction

`data/chemistry/reactions.json` — reference reactions that anchor Claude's
chemistry. Add the ones from your unit and student answers get noticeably sharper.

## Add a star or exoplanet

`data/planets/named_stars.json` and `exoplanets.json`. Use real values from the
[NASA Exoplanet Archive](https://exoplanetarchive.ipac.caltech.edu/) — the whole
credibility of the Planet Lab rests on these being accurate.

## Add a physics scenario

`data/physics/scenarios.json`. Note that `scenario` must be one of the seven
existing engines — `projectile`, `incline`, `rollercoaster`, `collision`,
`spring`, `photoelectric`, `de_broglie` — because each has matching plotting code:

```json
{
  "id": "moon_basketball",
  "label": "🏀 Free throw on the Moon",
  "scenario": "projectile",
  "blurb": "The same shooting motion, one-sixth the gravity.",
  "inputs": { "v0": 7.5, "angle_deg": 52.0, "g": 1.62, "y0": 2.0 },
  "callout": "Hang time scales as 1/g — about six times longer than on Earth."
}
```

## Add a starter experiment

Easiest of all: **run the setup you want in the app, click 💾 Save experiment**,
then commit the downloaded `.curious` file into `examples/<app>/`. It appears in
everyone's Starter gallery on the next deploy.

---

# Tier 2 — Change the voice and the science bar (light code)

## Retune the prompts

`curious_mind/<domain>/prompts.py` holds each lab's `SYSTEM_PROMPT`. This is
where reading level, tone, and scientific strictness live. Edit the English.

Genuinely useful edits:
- **Change the grade band.** "Explain for a 5th grader" vs. "for an AP student"
  transforms every output in the lab.
- **Add a local frame.** "Where possible, use examples from the North American
  Great Plains."
- **Demand a misconception check.** "Name one common student misconception this
  scenario exposes." — a strong addition for a teacher-facing deployment.
- **Tighten speculation.** Make the model more conservative about labeling
  things `well_documented`.

## Retheme it

`curious_mind/ui.py` — the constants `NAVY`, `TEAL`, `AMBER`, `GRAY` and the
`page_setup()` CSS. `.streamlit/config.toml` sets the Streamlit base theme. Put
your school's colors in and it becomes your school's tool.

## Response length

If long answers get cut off, raise `max_tokens` in the lab's `call_structured()`
call. Current values were tuned against observed truncation: chemistry 1200,
planets 2400, ecosystem 3000. Higher costs slightly more.

---

# Tier 3 — Add a whole new lab (real code)

The four labs are deliberately parallel. Copy the smallest one and follow the
shape. **Do not try to abstract them into a shared base class** — the duplication
is intentional and keeps each lab independently editable.

To add, say, a Geology Lab:

1. **`data/geology/*.json`** — your knowledge base. Start with 20 solid entries,
   not 200 thin ones.
2. **`curious_mind/geology/data_loader.py`** — `@lru_cache` loaders plus a
   `relevant_kb_subset()` that returns only what a given question needs.
3. **`curious_mind/geology/schemas.py`** — a Pydantic v2 model of your output.
   **Design this before you write the prompt**; the schema *is* the spec. Use
   lenient `field_validator(mode="before")` coercions so a slightly-off model
   response is repaired rather than rejected.
4. **`curious_mind/geology/prompts.py`** — `SYSTEM_PROMPT` plus a `FALLBACK` that
   is a real, fully-populated instance of your schema. The fallback is what
   every key-less user sees, so write it as carefully as you'd write a textbook
   sidebar.
5. **`curious_mind/geology/visuals.py`** — Plotly figures.
6. **`pages/5_Geology_Lab.py`** — the UI. Copy `pages/4_Physics_Lab.py` and
   follow its order: inputs → signature → `call_structured` → render.
7. Add `"geology"` to the `App` literal in `curious_mind/persistence.py`.
8. Add a card to `streamlit_app.py`.

## Three patterns you must not break

These are load-bearing and non-obvious. Violating them causes bugs that look
like Streamlit being haunted.

**1. Widget state is sticky.** `del st.session_state[key]` is unreliable. To flip
a widget programmatically, write the key *before* the widget renders:
```python
st.session_state[f"chk_{item_id}"] = True   # BEFORE st.checkbox(...)
```

**2. Cache keys must include everything that should trigger a re-run.**
`_cached_call` keys on the full payload. If you add a follow-up question, inject
it into the payload **and** into `input_signature`, or you'll get a stale
cached answer and conclude the model is ignoring you.

**3. Always ship a real `FALLBACK`.** Never `None`, never a stub. It is the
difference between a graceful classroom and a traceback on a projector.

---

## Testing your changes

```bash
pip install -r requirements.txt
python -m pytest -q          # validates every knowledge-base JSON file
streamlit run streamlit_app.py
```

`tests/test_kb_validators.py` catches malformed JSON, bad trophic levels, and
dangling species references. **Run it after every knowledge-base edit** — it
takes under a second and will save you a broken deploy.

## Contributing back

Corrections to the science are the most welcome contribution there is. Open a
pull request against the upstream repo, or an Issue if you'd rather just report
it. If you build a lab for your discipline, say so in Discussions — other
teachers want it.
