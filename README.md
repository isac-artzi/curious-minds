# Curious Minds

Four Streamlit science sandboxes powered by Claude — **Chemistry · Ecosystem · Planets · Physics**.

Built for K–12 STEM teachers, students, and the genuinely curious. Combine real, curated facts in unexpected ways and let Claude reason over them. The lesson is that AI is leverage on real knowledge, not a magician's hat.

## Quickstart

```bash
git clone https://github.com/isac-artzi/curious-minds
cd curious-minds
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# add your ANTHROPIC_API_KEY (or set env var)

streamlit run streamlit_app.py
```

Open http://localhost:8501.

## The four apps

- **🧪 Chemistry What-If Lab** — combine elements + conditions, get a balanced reaction, energy diagram, hazards, real-world connection.
- **🌿 Ecosystem / Biome Lab** — pick a biome, populate species, inject events, watch the food web reorganize.
- **🪐 Planet / Exoplanet Builder** — pick a star, dial in orbit / mass / atmosphere / water, get a habitability verdict + closest real exoplanet.
- **🔬 Physics Lab** — seven scenarios from projectile motion to the photoelectric effect, each with a deterministic simulator plus Claude's narrative explanation.

## Knowledge bases

All curated data lives in `/data/<domain>/*.json`. Edit, fork, redeploy — that's the intended workflow for teachers.

## Saving experiments

- **💾 Save experiment** writes a portable `.curious` file. Email it, drop it in Drive, hand it to a student.
- **📂 Load experiment** restores a saved `.curious` file from the sidebar.
- **🧪 Starter experiments** gallery in each sandbox's sidebar — pre-built classroom-ready setups.

## Offline mode

If `ANTHROPIC_API_KEY` is missing or the API is unreachable, the apps fall back to cached example outputs.

## Documentation

Full guides live in **[docs/](docs/)**:

- **[Fork & Deploy](docs/FORK_AND_DEPLOY.md)** — your own copy in ~15 minutes, with real cost numbers
- **[Prompt Cards](docs/PROMPT_CARDS.md)** — 24 classroom starters, six per lab
- **[Lesson Plans](docs/lesson-plans/)** — eight 50-minute plans, two per lab
- **[NGSS / CSTA Alignment](docs/NGSS_CSTA_ALIGNMENT.md)** — standards mapping
- **[Architecture](docs/ARCHITECTURE.md)** — how the app actually works
- **[Modifying](docs/MODIFYING.md)** — from JSON edits to adding a new lab
- **[PRD](docs/PRD.md)** — the original spec, annotated with what changed

## License

MIT. See `LICENSE`.
