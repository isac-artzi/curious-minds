# Curious Minds — Product Requirements Document

*The planning document this project was built from. Reproduced here as a
**worked example of how to specify an app like this** — the section that follows
the header is the original v1.1 text.*

| | |
|---|---|
| **Document version** | 1.1 (May 2026) |
| **Author** | Isac Artzi, SenSym LLC |
| **Repository** | [github.com/isac-artzi/curious-minds](https://github.com/isac-artzi/curious-minds) (public, MIT) |
| **Hosting** | Streamlit Community Cloud (free tier) |
| **LLM** | Claude Haiku 4.5 (`claude-haiku-4-5-20251001`) |
| **Conference target** | National Rural STEM Learning Summit, Sept 3–4 2026 — Glendale, AZ |
| **Status** | ✅ **Shipped.** All planned scope delivered, plus a fourth lab. |

---

## Read this first: what changed between plan and product

The PRD below says **three** sandboxes. The app ships **four** — a Physics Lab
was added in August 2026, after the document was written. Everything else in the
spec survived largely intact.

That gap is the most useful thing about publishing this document. A PRD is not a
contract; it is a **hypothesis about what to build**, written when you know the
least. Reading it next to the finished app shows you which decisions held and
which moved.

**What held, and why it mattered:**

- **The four-layer pattern** — curated JSON → prompt assembly → schema-validated
  reasoning → scientific rendering. Specified before a line was written, and
  never revised. Getting this right up front is what made a fourth lab a
  weekend's work instead of a rewrite.
- **Confidence tiers.** Named in the PRD as a requirement, not an enhancement.
  It became the project's most distinctive pedagogical feature.
- **Fallback objects.** The rule that every lab ships a real, fully-populated
  `FALLBACK` was written down early. It's why the app degrades into a usable
  classroom tool with no API key at all.
- **Hard constraints as design inputs.** "Runs on a Chromebook," "free tier,"
  "under $5 for a 50-person session" ruled out whole categories of design before
  any code existed. Constraints stated early save more time than features
  specified late.

**What moved:**

- **A fourth lab.** The architecture absorbed it without structural change.
- **Species count.** The PRD's ambition exceeded what could be curated to a
  defensible standard. The KB ships **81 species** — each with a real IUCN status
  and a specific causal `role` sentence. Fewer, better entries produce better
  reasoning than more, thinner ones. This is the single most transferable lesson
  in the document.
- **Persistence.** The planned `localStorage` layer was dropped; file-based
  `.curious` export/import carried the full load and is more portable anyway.
- **Challenge mode.** Not in the PRD at all. Emerged from classroom thinking
  during the build, and is now arguably the highest-value feature in the app.

**If you're writing your own:** specify the *architecture* and the *constraints*
precisely, and hold the *feature list* loosely. That's the ratio that worked here.

---

## 1.  Overview

### 1.1  Vision
Curious Minds is a suite of three browser-accessible science sandboxes that let teachers, students, and the genuinely curious explore three corners of natural science by combining real, curated facts in unexpected ways. Drop hydrogen and oxygen onto a workbench and watch water condense. Place a wolf into a Yellowstone biome with no elk and watch the ecosystem reason its way through the cascade. Build a planet at 0.3 AU around an M-dwarf star and learn whether life could exist on it, why, and what kind.
The intellectual hook is a question every visitor will ask within thirty seconds: “How did they do that?” The answer — a small, hand-curated knowledge base, plus Claude reasoning over it, plus careful scientific framing — is the educational lesson. Students learn that AI is leverage on real knowledge, not a magician’s hat.

### 1.2  Audience
- Primary: K–12 STEM teachers in rural and under-resourced districts who need free, no-install, Chromebook-friendly classroom tools.
- Secondary: middle and high school students using the apps directly, individually or in small groups.
- Tertiary: science-curious adults, librarians running STEM programs, informal educators, and homeschool parents.
- Deliberately not a target: chemistry / ecology / astronomy researchers. The apps are pedagogical, not research-grade.

### 1.3  Success criteria
- A first-time visitor reaches a satisfying scientific insight in under 90 seconds with no instruction.
- A STEM teacher recognizes the output as scientifically accurate and would feel comfortable using it in front of their class.
- Three apps share one repository, one Streamlit deployment, one Anthropic API key, and one design language.
- A teacher can fork the repo and deploy their own copy with their own knowledge base modifications in under 15 minutes.
- The trio survives a 55-minute conference session as the centerpiece of a hands-on showcase: 50 attendees on Chromebooks, all running combinations simultaneously, total Anthropic spend < $5.

## 2.  Goals and Non-Goals

### 2.1  Goals
- Build a polished, scientifically credible feel — every output should look like it could appear in a quality STEM textbook.
- Make every interaction returnable to a teacher’s daily lesson plan: NGSS-aligned, classroom-printable, talking-point-friendly.
- Keep the UI elegant, intuitive, and confidence-inspiring. No gimmicks. No drag-and-drop friction. Inputs are obvious; outputs are revelatory.
- Animate where animation aids understanding — reaction energy diagrams, orbital paths, population dynamics — never as decoration.
- Treat the knowledge base as the primary creative asset. The JSON files are version-controlled, hand-curated, and hold up to a chemistry teacher’s scrutiny.
- Provide graceful fallbacks: cached example outputs, offline JSON-only mode if the Anthropic API is unreachable.

### 2.2  Non-Goals
- Drag-and-drop interfaces, simulation game-loops, or real-time multi-user collaboration.
- Authentication, user accounts, saved projects across sessions (browser localStorage is fine for current-session memory).
- Replicating professional simulation tools (PyMOL, NetLogo, Universe Sandbox). Curious Minds is curiosity-first; depth-second.
- Mobile-first design. Designed for laptop and Chromebook screens (≥ 1024 px). Responsive scaling is a stretch goal.
- Localization to non-English languages in v1. The architecture supports it; the v1 strings are English-only.
- Support for older or unusual browsers. Modern Chromium, Firefox, Safari only.

## 3.  The Three Apps

### 3.1  Chemistry What-If Lab
Premise. Combine elements and simple compounds, dial in conditions (temperature, pressure, catalyst), and watch a real reaction unfold. The app reasons over a curated dataset of all 118 elements plus a library of common compounds.

#### Inputs
- Element / compound picker: searchable multi-select with periodic-table-style filtering. Each item carries a quantity slider in moles or grams.
- Conditions panel: temperature (0–10,000 K log scale), pressure (10⁻³ – 10⁶ atm log scale), catalyst (free-text suggestion box with autocomplete).
- Mode toggle: realistic mode (only chemistry the curated KB supports) vs. speculative mode (Claude reasons about exotic / extreme combinations and labels speculation explicitly).

#### Outputs
- Predicted products with formulas and IUPAC names, rendered with proper subscripts and stoichiometry.
- Balanced reaction equation typeset in LaTeX (rendered via Streamlit’s native st.latex).
- Energy diagram: animated Plotly chart showing reactants → transition state → products with ΔH labeled.
- Phase diagram annotation: the resulting product positioned on a P-T phase diagram for the system.
- 2D molecular structures via RDKit, rendered as inline SVG.
- Real-world connection: where this reaction matters (industry, biology, geology, daily life).
- Safety & honesty panel: explicit hazards, where Claude is speculating, what a chemist would actually do next to verify.
- Three follow-up questions, one-click to explore (e.g., “What if the temperature were 1000 K higher?”).

#### Animation moments
- Reaction equation typesets character-by-character (Streamlit st.write with rerender, ~600 ms total).
- Energy diagram animates: reactants line draws from left, climbs to transition state, drops to product line. Plotly frame animation, ~1.5 s.
- Molecular structures fade in once the LLM call returns.

#### Knowledge base anchor data
- All 118 elements, sourced from NIST: atomic number, mass, symbol, name, electron configuration, electronegativity, melting and boiling points, density, phase at STP, common oxidation states, abundance in universe / Earth crust, hazards, top three uses, fun fact.
- ~150 common compounds (water, CO₂, NaCl, glucose, ammonia, etc.) with formula, IUPAC name, components, phase at STP, molar mass, melting / boiling points, common uses.
- ~40 common reactions for grounding (combustion, neutralization, photosynthesis, Haber-Bosch, etc.) so Claude has anchors when reasoning about novel combinations.

### 3.2  Ecosystem / Biome Lab
Premise. Pick a biome, populate it with species, introduce events (drought, fire, invasive species, climate change), and watch the food web reorganize. The app explains every cascade in plain language a 7th grader can understand and a biology teacher can endorse.

#### Inputs
- Biome selector: 12 major biomes — temperate forest, tundra, savanna, kelp forest, coral reef, etc.
- Species picker: searchable multi-select drawn from a 200-species dataset, with quantity sliders (rough population sizes).
- Event injector: drop-down of disturbances — drought, wildfire, hard winter, invasive arrival, removal of apex predator, climate +2°C, plastic pollution, habitat loss N%.
- Time horizon: 1 year, 5 years, 25 years.

#### Outputs
- Food web graph: NetworkX-built, Plotly-rendered, color-coded by trophic level. Edges thickened by interaction strength.
- Population dynamics chart: animated Lotka-Volterra-style line plot showing each species over the time horizon. Plotly frames.
- Cascade explanation: ordered list of consequences, each tagged by confidence (well-documented / probable / speculative). Real-world analogue cited where it exists (e.g., “similar to Yellowstone wolf reintroduction, 1995”).
- Conservation note: which species are now stressed, which are thriving, and the IUCN status implications.
- Three follow-up scenarios.

#### Animation moments
- Food web nodes appear in trophic order: plants first, herbivores next, carnivores last, with a ~150 ms stagger.
- Population time series animates: each species curve draws across the time horizon, ~2 s.
- If an event is added mid-timeline, a vertical dashed line drops in with a label.

#### Knowledge base anchor data
- ~200 species spanning all major biomes: binomial name, trophic level, diet, climate range, habitat, water needs, social structure, lifespan, IUCN status, geographic range, ecological role description, top three real-world facts.
- ~40 documented interactions: predator-prey, mutualism, competition — these anchor Claude’s reasoning about cascades.
- 12 biome profiles: typical climate parameters, characteristic species lists, threats, real-world examples.
- 8 disturbance archetypes with documented case studies (Yellowstone wolves, Burmese python in the Everglades, the Black Death, etc.).

### 3.3  Planet / Exoplanet Builder
Premise. Build a planet from physical first principles — pick a star, choose distance, gravity, atmosphere, and water budget — and discover what kind of world you get, whether life could exist, and what its sky would look like at noon.

#### Inputs
- Star selector: spectral class (O, B, A, F, G, K, M) with characteristic temperature, mass, luminosity, lifespan, color presets.
- Orbital distance: slider in AU, log scale (0.01 – 100).
- Planet mass / radius: linked sliders (in Earth masses / Earth radii) with density auto-calculation.
- Atmosphere composition: pie chart-style allocator across N₂, O₂, CO₂, H₂O, CH₄, NH₃, H₂, He, Ar, other.
- Water budget: slider from 0% (desert) to 100% (ocean world).
- Optional moons: 0 / 1 / 2 / many.

#### Outputs
- Habitability assessment: clear verdict (habitable / extremophile-only / non-habitable) with stellar habitable-zone position visualized.
- Surface conditions: average temperature, pressure, radiation environment, day length (assuming Earth-like rotation), gravity in g.
- Sky description: what the dominant star looks like at noon — color, apparent size, brightness — and how the sky scatters light at this composition.
- Plausible life forms: Claude reasons about what biochemistry would be possible, with explicit speculation labels.
- Closest real exoplanet analogue: nearest match from the NASA Exoplanet Archive subset, with a “Compare to” button.
- Three follow-up scenarios.

#### Animation moments
- Star + orbit diagram: 2D top-down view of the system with the habitable zone shaded; the planet orbits along its path with a slow rotation.
- Atmosphere composition animates as a stacked pie that grows from 0% to user values, ~800 ms.
- Sky preview: a soft gradient swatch shifts based on stellar color and atmosphere — animated cross-fade between presets.

#### Knowledge base anchor data
- Stellar classification table: temperature, mass, luminosity, lifespan, color, examples.
- Habitable-zone formulas: liberal and conservative bounds based on stellar luminosity (Kasting, Kopparapu).
- Atmosphere composition archetypes: Earth-like, Venus-like, Mars-like, Titan-like, gas giant, ice world.
- Real exoplanet subset: 50 well-known exoplanets from the NASA Exoplanet Archive — mass, radius, orbital period, host star, in/out of HZ, discovery year.

## 4.  Architecture

### 4.1  Tech stack
Frontend & framework
Streamlit ≥ 1.40, Python 3.11+
Hosting
Streamlit Community Cloud (free tier; auto-deploys on push to main)
LLM provider
Anthropic API — Claude Haiku 4.5 (claude-haiku-4-5-20251001)
Knowledge base
Hand-curated JSON files in /data, version-controlled with the code
Charts
Plotly (animations), Altair (some static), Matplotlib (fallback)
Chemistry rendering
RDKit (2D structures via SVG)
Network graphs
NetworkX → Plotly
Math typesetting
LaTeX via Streamlit st.latex
Repo layout
Multipage Streamlit app: Home + 3 pages, one per domain
Secrets
Streamlit Cloud Secrets manager (ANTHROPIC_API_KEY)
Testing
pytest for KB validators and prompt regression; manual smoke tests via deploy preview
Code quality
ruff (lint), black (format), pre-commit hooks

### 4.2  Repository structure
```
curious-minds/
├── README.md
├── LICENSE                       (MIT)
├── pyproject.toml                (or requirements.txt — see §4.3)
├── .streamlit/
│   ├── config.toml               (theme: SenSym brand colors)
│   └── secrets.toml.example
├── streamlit_app.py              (Home page — landing + nav)
├── pages/
│   ├── 1_Chemistry_Lab.py
│   ├── 2_Ecosystem_Lab.py
│   └── 3_Planet_Lab.py
├── curious_mind/
│   ├── __init__.py
│   ├── llm.py                    (Claude Haiku 4.5 client + prompt cache)
│   ├── ui.py                     (shared Streamlit components, theming)
│   ├── animations.py             (Plotly animation factories)
│   ├── chemistry/
│   │   ├── data_loader.py
│   │   ├── prompts.py
│   │   ├── visuals.py            (RDKit + Plotly energy diagram)
│   │   └── schemas.py            (Pydantic output schemas)
│   ├── ecosystem/                (same shape as chemistry/)
│   └── planets/                  (same shape as chemistry/)
├── data/
│   ├── chemistry/
│   │   ├── elements.json         (118 elements)
│   │   ├── compounds.json        (~150 common compounds)
│   │   └── reactions.json        (~40 anchor reactions)
│   ├── ecosystem/
│   │   ├── species.json          (~200 species)
│   │   ├── biomes.json           (12 biomes)
│   │   ├── interactions.json     (~40 documented interactions)
│   │   └── disturbances.json     (8 archetypes)
│   └── planets/
│       ├── stars.json
│       ├── atmospheres.json
│       └── exoplanets.json       (NASA Exoplanet Archive subset)
├── tests/
│   ├── test_kb_validators.py
│   ├── test_prompt_regression.py
│   └── fixtures/
├── docs/
│   ├── PRD.md
│   ├── DATA_SCHEMA.md
│   ├── PROMPT_GUIDE.md
│   └── DEPLOYMENT.md
└── .github/
    └── workflows/
        └── ci.yml                (lint + tests + KB schema check)
```

### 4.3  Dependencies (pyproject.toml)
```
[project]
name = "curious-minds"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "streamlit>=1.40",
  "anthropic>=0.39",
  "pydantic>=2.6",
  "plotly>=5.20",
  "networkx>=3.2",
  "numpy>=1.26",
  "pandas>=2.2",
  "rdkit>=2024.3",
  "pillow>=10.2",
  "python-dotenv>=1.0",
]
[project.optional-dependencies]
dev = ["pytest>=8.0", "ruff>=0.5", "black>=24", "pre-commit"]
```

> **Note:** requirements.txt will also be generated and committed for Streamlit Cloud compatibility — Cloud reads either, but requirements.txt is the well-trodden path.

### 4.4  Knowledge-base schemas (representative records)

#### 4.4.1  data/chemistry/elements.json
```
{
  "symbol": "H",
  "name": "Hydrogen",
  "atomic_number": 1,
  "atomic_mass": 1.008,
  "category": "nonmetal",
  "group": 1,
  "period": 1,
  "electron_configuration": "1s¹",
  "electronegativity": 2.20,
  "melting_point_K": 14.01,
  "boiling_point_K": 20.28,
  "density_g_per_cm3": 0.00008988,
  "phase_at_stp": "gas",
  "oxidation_states": [-1, 1],
  "common_compounds": ["H2O", "HCl", "NH3", "CH4"],
  "abundance_universe_pct": 75.0,
  "abundance_earth_crust_pct": 0.14,
  "hazards": ["highly flammable", "asphyxiant in confined spaces"],
  "top_uses": ["ammonia synthesis", "hydrogenation", "rocket propellant"],
  "fun_fact": "Hydrogen makes up ~75% of normal matter in the universe.",
  "discovery": { "year": 1766, "discoverer": "Henry Cavendish" }
}
```

#### 4.4.2  data/ecosystem/species.json
```
{
  "id": "wolf_gray",
  "common_name": "Gray wolf",
  "binomial": "Canis lupus",
  "trophic_level": "apex_predator",
  "diet": ["elk", "deer", "hare", "rodent", "carrion"],
  "climate_range": ["temperate", "boreal", "arctic"],
  "habitat": ["forest", "tundra", "mountain", "grassland"],
  "water_dependency": "freshwater_drinker",
  "social_structure": "pack",
  "lifespan_years": [6, 8, 13],
  "weight_kg": [25, 45, 65],
  "iucn_status": "Least Concern",
  "geographic_range": ["North America", "Europe", "Asia"],
  "role": "Top-down predator that regulates ungulate populations and triggers trophic cascades.",
  "famous_case_studies": ["yellowstone_reintroduction_1995"],
  "emoji": "🐺"
}
```

#### 4.4.3  data/planets/stars.json
```
{
  "spectral_class": "M",
  "name": "Red dwarf",
  "temperature_K": [2500, 3700],
  "mass_solar": [0.08, 0.45],
  "luminosity_solar": [0.001, 0.04],
  "lifespan_billions_years": [50, 1000],
  "habitable_zone_AU": [0.05, 0.4],
  "color_hex": "#FF6B3D",
  "prevalence_in_galaxy_pct": 75,
  "famous_examples": ["Proxima Centauri", "TRAPPIST-1", "Barnard's Star"],
  "sky_appearance": "deep red-orange disk; sky scatters orange even in clear atmosphere"
}
```

#### 4.4.4  Schema validation
Every JSON file is validated against a Pydantic v2 model on app boot. A schema-violation fails the app fast and visibly so that a contributor adding new data sees the error during local development. CI re-runs the validator on every push.

### 4.5  Data persistence
Curious Minds is fully stateless on the server. There are no user accounts, no databases, and no server-side storage of any kind. Persistence is entirely client-side and lives in two layers, each scoped to a different real use case.

#### 4.5.1  Layer 1 — Browser localStorage (in-session continuity)
- Purpose: a teacher closes the tab, comes back tomorrow, picks up exactly where they left off. Zero clicks, zero clutter.
- Mechanism: streamlit-local-storage component (or a small custom Streamlit component) writes the input state to localStorage on every change; on page load the app reads localStorage and restores. Per-app keys (curious-minds-chemistry-state, etc.).
- Limits and caveats: localStorage is per-origin, per-browser, per-device. ~5–10 MB cap. Cleared by browser cache reset or private browsing mode. Treated as ephemeral — appropriate for resuming a session, not for permanent saves.
- UX: a small status indicator in the sidebar — “Auto-saved to this browser” — keeps the user honest about durability.

#### 4.5.2  Layer 2 — JSON file export / import (durable, portable, distributable)
- Purpose: the primary save mechanism. Permanent records, distribution to students, building libraries of pre-cooked experiments, sharing with colleagues.
- Mechanism: “💾 Save experiment” → file downloads as my-experiment.curious. “📂 Load experiment” → drag any .curious file in → state restored, including a banner showing the file’s title, creation date, and notes.
- Privacy: files contain only the user’s input state and timestamp. No identifiers. Can be emailed, dropped in Drive, version-controlled in git, attached to assignments — all without privacy concerns.
```
{
  "schema": "curious-minds.experiment",
  "version": "1.0",
  "app": "chemistry" | "ecosystem" | "planet",
  "created_at": "2026-05-09T14:32:00Z",
  "title": "Hydrogen-oxygen with spark",
  "inputs": { ... domain-specific input state ... },
  "notes": "Optional teacher commentary, e.g. what students predicted before running"
}
```

- File extension: .curious (also accepts .json on import for forgiving UX).
- Forward compatibility: the version field allows future schema changes; v1 readers ignore unknown fields, v1 writers always emit version: 1.0.

#### 4.5.3  Library of starter experiments (shipped in the repo)
- The repo ships /examples/<app>/*.curious — six to ten hand-curated starter experiments per sandbox, version-controlled with the code.
- In-app: a “🧪 Load starter experiment” gallery in each sandbox’s sidebar lets users one-click load a starter.
- Forks inherit the same gallery; teachers can replace the starters with their own .curious files in their fork.

#### 4.5.4  Explicitly out of scope for v1
- Share-link URLs (URL-encoded state). Considered, deferred — not requested by the stakeholder, and file export covers the primary distribution use case.
- Cloud saves / GitHub gists / Google Drive integration. Adds OAuth, user accounts, and dependencies — all rejected for v1.
- Database persistence of any kind. No.

#### 4.5.5  Risk: localStorage loss
A teacher who relies only on localStorage and clears their browser cache loses their session state. Mitigation: a prominent “💾 Save to file” button sits next to the localStorage indicator; UI copy makes the durable-vs-ephemeral distinction explicit (“Auto-saved here · Save to file for keeps”). The starter-experiment gallery also gives every user a no-effort way to start fresh after a loss.

## 5.  UI / UX Specification

### 5.1  Design principles
- Scientific seriousness over cuteness. The app should feel like a small NASA / NOAA / NIST tool, not a kids’ game.
- One job per screen. Each app does one thing the user understands within five seconds.
- Inputs on the left (sidebar), outputs on the right (main pane). Conventional and predictable.
- Empty state is inviting. A minimal sample is pre-loaded so the app is interactive on first paint.
- No spinners without context. While Claude is reasoning, show what it’s doing (“Computing reaction enthalpy…”).
- Error states are honest. If the LLM is unreachable, the app degrades to its cached examples gracefully.
- Accessibility: WCAG 2.1 AA. Keyboard-navigable, sufficient color contrast, screen-reader labels on every chart.

### 5.2  Theme and visual language
- Color palette: deep navy (#1F3864) primary, teal-blue (#2E5496) secondary, warm amber (#D97706) accent, neutral grays for body text.
- Typography: Inter for sans, JetBrains Mono for code/numbers.
- Iconography: Streamlit emoji where helpful (🧪 🌿 🪐); no third-party icon library to keep weight down.
- Streamlit theme is set in .streamlit/config.toml so all three apps inherit consistently.

### 5.3  Shared components (curious_mind/ui.py)
- header(): consistent title bar with app name, navigation breadcrumb, GitHub link.
- info_panel(): styled callout for caveats, citations, and “where Claude is speculating” notes.
- loading_state(message): contextual spinner with descriptive text.
- source_card(citation): renders a citation block (linked to the underlying JSON record + any external reference).
- follow_up_buttons(suggestions): renders the LLM’s three follow-up suggestions as one-click buttons that re-run the page with new inputs.
- share_link(): generates a permalink encoding the current input state (useful for teachers sharing setups with students).

### 5.4  Per-app layout
App
Sidebar (inputs)
Main (outputs)
Chemistry
Element/compound multiselect; quantity sliders; T/P/catalyst panel; Mode toggle
Reaction equation (LaTeX) → Energy diagram → 2D structures → Real-world connection → Safety panel → Follow-ups
Ecosystem
Biome selector; species multiselect with population sliders; event injector; time horizon
Food web graph → Population dynamics → Cascade narrative → Conservation note → Follow-ups
Planets
Star spectral class; orbit slider; mass/radius; atmosphere allocator; water budget; moons
Habitability verdict → Surface conditions → Sky preview → Plausible life → Closest real exoplanet → Follow-ups

## 6.  Animation and Visualization

### 6.1  Animation principles
- Animation must clarify, not decorate. If a static chart is clearer, use a static chart.
- Animation duration: 600–1500 ms. Long enough to read; short enough not to slow exploration.
- Skip-animations affordance: a small toggle in the sidebar that disables animation for users on slow Chromebooks or with motion sensitivity.
- All animations use Plotly frame-based animation (works in Streamlit Cloud’s sandboxed environment without extra deps).

### 6.2  Chemistry — visualization details
- Reaction equation: rendered with st.latex; reveals via st.write_stream — letter-by-letter ~30 ms per character.
- Energy diagram (Plotly): x-axis = reaction coordinate; y-axis = energy (kJ/mol). Reactant line, transition state hump, product line. Frame-animated reveal: reactant line first, then climb to transition state, then descent to products. Total 1.5 s.
- 2D structures (RDKit → SVG): inline-rendered after LLM call returns; fade-in via st.markdown CSS transition.
- Phase indicator: small tagged badge — “Product is liquid at 25°C, 1 atm.”

### 6.3  Ecosystem — visualization details
- Food web graph: NetworkX builds a directed graph; Plotly renders with trophic-level y-coordinates and force-directed x-coordinates. Nodes appear in trophic order: producers → primary consumers → secondary → tertiary, with 150 ms staggered reveal.
- Population dynamics: Plotly multi-line time series. Each species curve animates left-to-right over 2 s. Event markers drop vertical dashed lines at the event time with hover tooltips.
- Cascade narrative: rendered as an ordered list with confidence-tagged badges (well-documented / probable / speculative) — color-coded green / amber / gray.

### 6.4  Planets — visualization details
- System diagram: 2D top-down view of the star with concentric circles for the conservative and liberal habitable zones. Planet appears at its orbit; orbits with a slow ~10 s loop. Implemented as a Plotly polar plot with an animation frame loop.
- Atmosphere donut: stacked pie chart that grows from 0% to user-allocated values over 800 ms.
- Sky swatch: a CSS gradient block computed from stellar color × atmospheric scattering; cross-fades when inputs change (200 ms).
- Comparison panel: when “Compare to nearest real exoplanet” is clicked, both worlds render side-by-side with their key parameters in a small table.

## 7.  Prompt Engineering

### 7.1  Design philosophy
- All Claude calls produce structured JSON. We never parse free text as the primary signal.
- Pydantic schemas validate every response. Validation failure triggers a single retry with a stricter system message; second failure shows a graceful error and a cached fallback.
- System prompts are version-controlled in /curious_mind/<domain>/prompts.py; every change is a PR with a regression test.
- Each prompt receives only the relevant subset of the knowledge base (the elements / species / stars actually selected). This keeps tokens low and Claude focused.

### 7.2  System prompt — Chemistry (excerpted)
```
You are a chemistry educator who reasons over a curated knowledge
base of elements and compounds. You explain at the level of a curious
high-school student.
GROUND RULES
1. Use only the chemistry data provided; do not invent compounds or
   conditions you cannot defend.
2. Distinguish three confidence tiers in your reasoning:
   - WELL-DOCUMENTED:  ordinary, textbook chemistry under STP-ish
     conditions.
   - PROBABLE:  the system is unusual, but extrapolation from known
     thermodynamics or analogous reactions is reasonable.
   - SPECULATIVE:  combinations the field has not characterized;
     label these explicitly.
3. Never give synthesis instructions for explosives, weapons, or
   illicit drugs. Refuse politely and redirect.
4. Always return the exact JSON schema specified — no prose outside
   the JSON.
```

### 7.3  Output schema — Chemistry
```
class ReactionResult(BaseModel):
    primary_product: Product
    byproducts: list[Product] = []
    balanced_equation: str          # LaTeX-ready
    enthalpy_kJ_per_mol: float | None
    enthalpy_class: Literal["strongly_exothermic", "exothermic",
                            "thermoneutral", "endothermic",
                            "strongly_endothermic"]
    phase_at_conditions: str
    mechanism: str                  # one paragraph plain English
    real_world_connection: str      # one paragraph
    confidence: Literal["well_documented", "probable", "speculative"]
    safety_notes: list[str]
    follow_ups: list[str]           # exactly 3 short strings
```

### 7.4  System prompts — Ecosystem and Planets
Same structural pattern. Each domain has: a system prompt setting tone and ground rules; a Pydantic output schema; a unit test asserting that the schema parses for ten canonical inputs. The full prompt texts will live in PROMPT_GUIDE.md, version-controlled and reviewable.

### 7.5  Token budget and caching
- Typical chemistry prompt: ~1.2k input tokens (system + selected KB records) + ~600 output tokens = ~1.8k total. At Haiku 4.5 pricing, ~$0.001 per call.
- Streamlit st.cache_data wraps every LLM call keyed on (domain, inputs). Re-running the same combination is free.
- Cached example outputs for the top 20 inputs per domain ship with the repo so the app is demoable offline / behind firewalls.

## 8.  Deployment

### 8.1  Streamlit Community Cloud setup
- Push the public repo to github.com/isac-artzi/curious-minds.
- On streamlit.io/cloud → New app → connect the repo, branch main, entry point streamlit_app.py.
- Set Secrets in the Streamlit Cloud UI: ANTHROPIC_API_KEY=sk-ant-… (only key required).
- Choose a subdomain: curious-minds.streamlit.app (or sensym-curious-minds.streamlit.app if the first is taken).
- Initial deploy completes in ~3 minutes. Subsequent deploys auto-trigger on push to main.

### 8.2  Custom domain (optional, post-launch)
Streamlit Cloud’s free tier does not include custom domains. If a custom domain becomes important (e.g., curious.sensym.org), the cleanest options are: (a) put a Cloudflare proxy in front of the *.streamlit.app URL, (b) move to a paid Streamlit tier, or (c) re-deploy on Render. None are required for v1.

### 8.3  Local development
```
git clone git@github.com:isac-artzi/curious-minds.git
cd curious-minds
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# add your ANTHROPIC_API_KEY
streamlit run streamlit_app.py
```

### 8.4  CI / CD
- GitHub Actions workflow runs on every PR: ruff lint, black --check, pytest with KB schema validation, prompt-regression tests against a small recorded fixture.
- Streamlit Cloud auto-deploys main; staging environments are achieved via long-lived feature branches deployed as separate Streamlit apps when needed.
- Tagged releases (v0.1.0, v0.2.0, …) cut from main; release notes generated from PR titles.

### 8.5  Forking workflow for teachers
- Teacher forks isac-artzi/curious-minds on GitHub.
- Teacher edits any /data/*.json file (e.g., adds local-region species, swaps in their own elements list).
- Teacher creates a Streamlit Cloud account (free) and connects their fork.
- Teacher adds their own ANTHROPIC_API_KEY (or omits it to run only the cached-examples mode).
- Teacher gets their own *.streamlit.app URL — typically within 15 minutes of starting.

## 9.  Cost and Performance

### 9.1  Anthropic API cost projection
Scenario
Volume
Estimated cost
Conference session
50 attendees × 20 mixes each × 3 apps
≈ $3.00
Single classroom (30 students), one period
30 × 10 mixes × 1 app
≈ $0.30
Single classroom, full school year
30 × 10/week × 30 weeks
≈ $9.00
Power user (one teacher prepping lessons)
200 mixes / month
≈ $0.20 / month
Heavy public traffic spike
10,000 mixes / month
≈ $10 / month
> **Note:** Assumes Claude Haiku 4.5 input ≈ $0.0008 / 1K tokens, output ≈ $0.004 / 1K tokens (subject to current Anthropic pricing).

### 9.2  Latency
- Cold-start of the Streamlit Cloud app: ~10–15 s after a period of inactivity. First user warms it; subsequent users get <1 s page loads.
- Claude Haiku 4.5 typical latency: 1–3 s per call. Streamlit shows a contextual progress spinner during the call.
- KB load: <50 ms (all JSON files together are < 500 KB).

### 9.3  Resource limits
- Streamlit Cloud free tier: 1 GB RAM per app. The trio runs comfortably under 200 MB even with RDKit loaded.
- Concurrent users: Streamlit Cloud free tier handles ~10 concurrent active sessions cleanly. For a 50-attendee conference room, sessions are short and bursty — should be fine. We will load-test with a synthetic 30-user run before the conference.

## 10.  Testing & Quality

### 10.1  Knowledge-base validation
- Pydantic schemas in curious_mind/<domain>/schemas.py.
- CI test that loads every record from every JSON file and validates it against the schema.
- Property checks: every reaction in chemistry/reactions.json references only elements present in elements.json.
- Property checks: every interaction in ecosystem/interactions.json references species present in species.json.

### 10.2  Prompt regression tests
- For each domain, 10 canonical inputs are recorded with their expected output structure (not exact text).
- Tests assert: schema parses, required fields present, no profanity / safety violations, follow-ups always exactly 3.
- Drift detection: if the LLM significantly changes outputs, the test surfaces it for human review (snapshot comparison with tolerance).

### 10.3  Manual QA before conference
- Two-week soft launch on a public URL with a small private group of teachers; collect feedback on accuracy and UX.
- Subject-matter review: one chemistry teacher, one biology teacher, one earth-science teacher each spend 30 minutes red-teaming their domain.
- Chromebook smoke test: run all three apps on a real classroom Chromebook (school-managed) on school Wi-Fi. Capture any blocked-domain or performance issues.

## 11.  Roadmap and Milestones

### 11.1  Build phases
Milestone
Calendar week (target)
Definition of done
M0 — Repo bootstrap
Week of May 11, 2026
Public repo created, Streamlit Cloud connected, Hello-World page live, CI green.
M1 — Chemistry app v0.1
End of May
Element multiselect, sliders, single LLM call, structured output, energy-diagram animation, RDKit structures, mobile-friendly layout.
M2 — Ecosystem app v0.1
Mid June
Biome + species pickers, food web graph, population dynamics chart, cascade narrative, three follow-ups.
M3 — Planets app v0.1
End of June
Star + orbit + atmosphere inputs, habitability verdict, system diagram, sky swatch, real-exoplanet comparison.
M4 — Polish + cached examples
Mid July
Cached example library; offline-friendly mode; share-link permalinks; design QA pass.
M5 — Subject-matter review
End of July
Chemistry / biology / earth-science teacher reviews complete; feedback merged.
M6 — Conference rehearsal
Mid August
Full 55-minute breakout simulated with 10 colleagues; load-test with 30 synthetic concurrent users; bug freeze.
M7 — Conference
Sept 3–4, 2026
Live deployment stable, fallback ready, attendee feedback collected.
M8 — Time Machine app (post-conference)
October 2026 (stretch)
Fourth page added — historical counterfactuals.

### 11.2  Scope discipline
Anything beyond the phase definitions above is a stretch goal until v1.0 ships. Likely stretch goals worth tracking: localization to Spanish for rural border-state classrooms, a “teacher mode” with curriculum-tied lesson prompts, and Time Machine as a fourth page.

## 12.  Risks and Mitigations
Risk
Likelihood
Mitigation
Anthropic API outage during conference
Low
Cached example library covers top 20 prompts per app; UI degrades gracefully with a banner.
Claude generates a chemistry hallucination a teacher catches
Medium
Tiered confidence labels in every output; safety prompt ground rules; subject-matter review cycle.
Streamlit Cloud free-tier resource limits hit during a conference spike
Low–Medium
Pre-conference load test; have a paid-tier upgrade as standby (~$20/mo); cached examples reduce real LLM calls.
School / district network blocks Streamlit subdomains
Medium
Pre-conference reconnaissance with one rural teacher; Cloudflare reverse proxy on a generic domain as backup.
RDKit install fails on Streamlit Cloud
Low
Tested up front in Milestone M0; if issues, fall back to cached SVGs of common structures + an SMILES viewer like rdkit-pypi or kept-pure-text mode.
UX feels infantile or feels too complex
Medium
Iterate after first teacher review (Milestone M5); design language is calibrated to NIST/NOAA tools, not games.
Speculative outputs cross a line into misinformation
Medium
Confidence tiers explicit in every output; a “Speculation only” banner triggers when Claude self-reports SPECULATIVE; human-readable disclaimers in the footer.

## 13.  Conference-Readiness Checklist

### 13.1  Two weeks before
- All three apps deployed to *.streamlit.app, stable for 14 days.
- Cached example library complete for all three apps.
- Subject-matter review complete; all flagged issues resolved or documented.
- Printed handouts: 1-page “What is Curious Minds?” + 1-page algorithm explainer per app + QR code to the live site.
- Slides finalized; rehearsed at least twice end-to-end.

### 13.2  One day before
- Confirm Streamlit Cloud app warm by visiting it from the conference Wi-Fi.
- Verify Anthropic API key has at least $50 of margin on the budget.
- Have an offline-mode demo recording (3 minutes) as ultimate backup.
- Charge two laptops. Bring an HDMI + USB-C dongle, two USB-C chargers, a power strip, and 25 ft of HDMI cable.

### 13.3  In the room
- Open all three apps in three browser tabs before walking on stage.
- Pre-load one canonical example per app so the first reveal is instant.
- QR code on screen at the start so attendees can scan and follow along.
- Watch the time. Each app gets ~12 minutes of demo + hands-on, leaving 19 min for intro + closing + Q&A.

## Appendix A.  Sample LLM call — Chemistry

#### Input
```
components: [{ symbol: "H", moles: 2 }, { symbol: "O", moles: 1 }]
conditions:  { temperature_C: 25, pressure_atm: 1, catalyst: "spark" }
mode: "realistic"
```

#### Expected output (structured JSON)
```
{
  "primary_product": {
    "formula": "H2O",
    "name": "Water",
    "phase": "liquid",
    "amount_estimation": "~2 mol"
  },
  "byproducts": [],
  "balanced_equation": "2H_2 + O_2 \\rightarrow 2H_2O",
  "enthalpy_kJ_per_mol": -286,
  "enthalpy_class": "strongly_exothermic",
  "phase_at_conditions": "liquid water at 25°C, 1 atm",
  "mechanism": "Hydrogen and oxygen do not react spontaneously at room temperature; an activation source (here, a spark) initiates a radical chain reaction. The exothermic combustion releases ~286 kJ per mole of water formed.",
  "real_world_connection": "This is the reaction in hydrogen fuel cells (without combustion) and in liquid-fueled rocket engines like the Space Shuttle main engine.",
  "confidence": "well_documented",
  "safety_notes": ["Hydrogen-oxygen mixtures detonate over a wide range of mixing ratios. Do not attempt outside a controlled lab."],
  "follow_ups": [
    "What happens if you replace H with deuterium (D)?",
    "What if you raise the temperature to 1000 K with no catalyst?",
    "How does this compare to the energy released by burning methane?"
  ]
}
```

## Appendix B.  External data sources
- NIST Chemistry WebBook — element properties, thermodynamic data.
- PubChem — compound metadata, IUPAC names.
- IUCN Red List — species conservation status.
- Encyclopedia of Life (EOL) — species traits and ranges.
- NASA Exoplanet Archive — confirmed exoplanet catalog.
- NASA Astrobiology Habitable Zone tool — Kasting / Kopparapu HZ formulas.
> **Note:** All ingested data ships with attribution in /data/<domain>/SOURCES.md and is selected to fall under permissive use for educational purposes.

## Appendix C.  Open questions for review
- Repo license: MIT is the default proposed. Confirm or substitute (Apache 2.0, BSD-3, AGPL)?
- Subdomain preference: curious-minds.streamlit.app vs. sensym-curious-minds.streamlit.app — first available wins, or hold for one?
- Should the v1 prompt explicitly include grade-level tone (e.g., 7th grade default), or leave the LLM to calibrate per query?
- Should we ship with a “teacher mode” toggle in v1 (different prompt set focused on lesson-plan tie-ins), or save for v0.2?
- Time Machine: build it post-conference as a fourth page in the same repo, or spin out as a sibling project sharing the same architecture?

> **Note:** Awaiting approval to begin Milestone M0 (repo bootstrap). On approval I will: (a) initialize the repo skeleton, (b) draft the four /data/chemistry JSON schemas with first 30 elements as seed, (c) wire the Anthropic call + Pydantic validation, (d) push a working Streamlit Cloud deploy, all within Milestone M0’s end-of-week target.