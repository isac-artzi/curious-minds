---
layout: default
title: "🚀 Fork & Deploy"
nav_order: 2
---

# Fork & Deploy: Your Own Curious Minds in ~15 Minutes

*You need: a GitHub account, a Streamlit account, and — for live AI reasoning —
an Anthropic API key. No installs. No terminal. Everything below happens in a
browser.*

---

## Read this first: the honest cost picture

Curious Minds is MIT-licensed and free. The **AI reasoning is not.**

You have two options, and both are legitimate:

| | What you get | Cost |
|---|---|---|
| **No API key** | All four labs, all visuals, all controls, all starter experiments — running on hand-written cached examples. Nothing errors. Every output is labeled "⚪ Cached example." | **$0.00** |
| **With an API key** | Live reasoning. Any combination a student invents gets a real, fresh scientific explanation. | **~1–2¢ per experiment** |

Fallback mode is genuinely usable — it is what the app does during a Wi-Fi
outage, and it is a defensible way to run a lesson. But the "ask anything"
magic requires a key.

### What a key actually costs

The app uses **Claude Haiku 4.5** — Anthropic's cheapest current model — at
**$1.00 per million input tokens** and **$5.00 per million output tokens**.

A single experiment sends roughly 2,000 tokens in (system prompt + the relevant
slice of the knowledge base) and gets 1,200–3,000 tokens back. That is about
**one to two cents**.

| Scenario | Runs | Approximate cost |
|---|---|---|
| You, testing for an evening | 40 | **$0.50** |
| One class period, 30 students, 5 experiments each | 150 | **$2** |
| A full teaching week, five classes | ~750 | **$10** |
| A 50-person conference session | ~500 | **$6** |

Anthropic requires a minimum prepaid credit purchase (currently $5). **Set a
spend limit** — instructions below — and you cannot be surprised.

> **Two caveats worth knowing.** Repeated identical inputs are cached and cost
> nothing extra. And if you deploy publicly with your key, *anyone who finds the
> URL spends your money* — see Step 6.

---

## Step 1 — Fork the repository (2 min)

1. Go to **github.com/isac-artzi/curious-minds**
2. Click **Fork** (top right) → **Create fork**

You now own a complete copy at `github.com/YOUR-USERNAME/curious-minds`.

## Step 2 — Get an Anthropic API key (4 min)

*Skip this step if you're deploying in free fallback mode. You can add a key later
without redeploying.*

1. Go to **console.anthropic.com** and sign up.
2. **Billing → Add credits.** Purchase the minimum (currently $5). This is
   prepaid — there is no subscription and no recurring charge.
3. **Set a spend limit now, before you forget.** In Billing, set a monthly cap
   (start at $5). This is your safety net.
4. **API keys → Create key.** Name it something like `curious-minds-classroom`.
5. **Copy it immediately.** It starts with `sk-ant-` and is shown exactly once.

Treat this key like a credit card number. Never paste it into a GitHub file, a
shared document, a Slack message, or a student handout.

## Step 3 — Deploy to Streamlit (5 min)

1. Go to **share.streamlit.io** and sign in **with GitHub**.
2. **Create app → Deploy a public app from GitHub.**
3. Fill in:
   - **Repository:** `YOUR-USERNAME/curious-minds`
   - **Branch:** `main`
   - **Main file path:** `streamlit_app.py`
4. Open **Advanced settings**:
   - **Python version:** `3.12`
   - **Secrets:** paste this, with your real key — or **leave it empty** to
     deploy in free fallback mode:
     ```toml
     ANTHROPIC_API_KEY = "sk-ant-your-actual-key-here"
     ```
5. Click **Deploy**. First build takes 3–5 minutes.

Your app is live at a URL you can hand to students.

> **Secrets go in Streamlit, never in GitHub.** GitHub Actions secrets are a
> different system that Streamlit cannot read. And a key committed to a public
> repository is public **forever** — scrapers index new commits within minutes.
> The repo's `.gitignore` already blocks `.streamlit/secrets.toml`; leave it alone.

## Step 4 — Confirm it worked (1 min)

Open your URL. On the landing page:

- **No yellow banner** → your key is live. Reasoning is real.
- **Yellow "No ANTHROPIC_API_KEY detected"** → fallback mode. Either you left
  Secrets empty (fine!) or the key didn't take — check for the `sk-ant-` prefix
  and the surrounding quotes.

Then open any lab and run one experiment. The source line under the result says
`live`, `cached`, or `fallback`.

## Step 5 — Make it yours (the fun part)

The knowledge bases are plain JSON you can edit **directly on GitHub** — click a
file, click the pencil icon, edit, commit. Streamlit redeploys automatically in
about a minute.

Swap in species from your own watershed. Add the reactions from your unit. See
**[MODIFYING.md](MODIFYING.html)** for exactly where and how.

## Step 6 — Decide who can see it

Streamlit Community Cloud apps are **public by default**. With your key
installed, anyone with the link spends your credits.

For classroom use, pick one:

- **Keep the URL unadvertised** and rely on your spend limit. Fine for most classes.
- **Restrict viewers:** app **Settings → Sharing** → invite specific emails.
- **Run key-less in class** and demo the live version from your own machine.
- **Deploy two apps:** a public fallback-mode one for students to keep, and a
  keyed private one for live lessons.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Build fails on dependencies | Confirm Python **3.12** in Advanced settings. |
| "Claude unreachable" warning | Key is wrong, out of credits, or past its spend limit. Check console.anthropic.com → Billing. |
| Yellow banner won't go away | Secrets must be TOML: `ANTHROPIC_API_KEY = "sk-ant-..."` — quotes required, no `export`, no trailing comma. |
| App is slow to wake | Community Cloud sleeps after inactivity. Cold start ≈30s. Open it a few minutes before class. |
| Physics starters missing | Your fork predates a fix — re-sync your fork from the upstream repo. |
| Everything says "cached example" | That's fallback mode working correctly. Add a key, or teach with it as-is. |

## Getting help

- **Questions, ideas, or "I broke it":** open a thread in **GitHub Discussions**
  on the upstream repo.
- **A bug in the science:** open an Issue. Corrections to the knowledge base are
  the most valuable contribution you can make — the JSON is the ground truth
  every user's output is built on.

---

*Curious Minds is MIT licensed. Fork it, change it, teach with it, keep it.*
