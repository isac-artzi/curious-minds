---
layout: default
title: Home
nav_order: 1
description: "Four browser-based science sandboxes for K-12 classrooms — free, forkable, no install."
permalink: /
---

# Curious Minds
{: .fs-9 }

Four science sandboxes where students ask *“what happens if…?”* and get a real
scientific answer — labeled by how confident it should be.
{: .fs-6 .fw-300 }

[🔬 Open the app](https://rural-stem-curious-minds.streamlit.app/){: .btn .btn-primary .fs-5 .mb-4 .mb-md-0 .mr-2 }
[💻 Fork it on GitHub](https://github.com/isac-artzi/curious-minds){: .btn .fs-5 .mb-4 .mb-md-0 }

---

## The four labs

| | Lab | What students do |
|:--|:--|:--|
| 🧪 | **Chemistry** | Mix elements, set temperature and pressure, watch reactions unfold |
| 🌿 | **Ecosystem** | Remove a predator, trace the cascade across 25 simulated years |
| 🪐 | **Planets** | Build a world around a real star, find out if life could live there |
| 🔬 | **Physics** | 15 scenarios from Galileo's tower to the photoelectric effect |

No login. No install. Runs on any Chromebook.

---

## Start here

Depending on why you're here:

<div class="code-example" markdown="1">

**I want to use this in my classroom tomorrow**
→ [Prompt Cards]({{ site.baseurl }}/PROMPT_CARDS.html) — 24 starters, six per lab, by grade band

**I want a full lesson plan**
→ [Lesson Plans]({{ site.baseurl }}/lesson-plans/) — eight 45–50 minute plans with rubrics

**I need standards alignment for my administrator**
→ [NGSS / CSTA Alignment]({{ site.baseurl }}/NGSS_CSTA_ALIGNMENT.html)

**I want my own copy I can change**
→ [Fork & Deploy]({{ site.baseurl }}/FORK_AND_DEPLOY.html) — about 15 minutes, browser only

**I want to know how it actually works**
→ [Architecture]({{ site.baseurl }}/ARCHITECTURE.html) — the "how did they do that?" answer

</div>

---

## The honest version of "free"

{: .warning }
> The app is MIT-licensed and free forever. **The AI reasoning is not.**
>
> **Without an API key — $0.** Every lab, visual, and control still works, running
> on hand-written cached examples. Nothing errors out. This is genuinely usable in
> a classroom.
>
> **With your own key — about 1–2¢ per experiment.** A class of 30 doing five
> experiments each costs roughly **$2**. Then students can ask it anything.
>
> Full numbers in [Fork & Deploy]({{ site.baseurl }}/FORK_AND_DEPLOY.html).

---

## What makes this different from a chatbot

Every answer is built on a **hand-curated JSON knowledge base** you can open and
correct — 118 elements, 81 species with real IUCN status, 21 named stars, 20 real
exoplanets from the NASA Exoplanet Archive, 15 physics scenarios.

The model isn't recalling that wolves eat elk. It's **reading it from a file you
control**. When a student asks *how do you know?*, you open the JSON on the
projector.

And every claim it makes is tagged:

<span style="color:#16A34A">**● well documented**</span> ·
<span style="color:#D97706">**● probable**</span> ·
<span style="color:#6B7280">**● speculative**</span>

{: .tip }
> Turn on **🎯 Challenge mode** in any lab. It hides the result until the student
> commits to a prediction. It's the single highest-leverage switch in the app.

---

## Built for

The **National Rural STEM Learning Summit**, Sept 3–4 2026 — Midwestern
University, Glendale AZ. Every component ships MIT-licensed so any teacher can
fork it, swap in local-region species, and deploy their own classroom version.

*Curious Minds is a project of SenSym LLC.*
