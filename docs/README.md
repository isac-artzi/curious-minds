# Curious Minds — Documentation

## For teachers

| Document | What it's for |
|---|---|
| **[FORK_AND_DEPLOY.md](FORK_AND_DEPLOY.md)** | Get your own copy running in ~15 minutes. Includes API keys and real cost numbers. **Start here.** |
| **[PROMPT_CARDS.md](PROMPT_CARDS.md)** | 24 starter explorations, six per lab, tagged by grade band. Printable. |
| **[lesson-plans/](lesson-plans/)** | Eight classroom-ready plans, two per lab, each one 45–50 minutes. |
| **[NGSS_CSTA_ALIGNMENT.md](NGSS_CSTA_ALIGNMENT.md)** | Standards mapping for lesson plans and administrator conversations. |

## For anyone modifying the code

| Document | What it's for |
|---|---|
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | How the app works — the "how did they do that?" answer. |
| **[MODIFYING.md](MODIFYING.md)** | Three tiers of change, from no-code JSON edits to adding a whole new lab. |
| **[PRD.md](PRD.md)** | The original planning document, annotated with what changed between plan and product. |

## The short version

Four science sandboxes. Each one is a **hand-curated JSON knowledge base**, a
**prompt** that ships only the relevant slice of it to **Claude Haiku 4.5**, a
**Pydantic schema** the response must satisfy, and **Plotly visuals** that render
the result. Every claim is labeled `well_documented`, `probable`, or
`speculative`.

Without an API key it runs on hand-written cached examples — free, and still
usable in a classroom. With one, students can ask it anything.
