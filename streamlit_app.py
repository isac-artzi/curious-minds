"""Curious Minds — landing page."""

from __future__ import annotations

import streamlit as st

from curious_mind import MODEL_ID, ui

ui.page_setup("Curious Minds", "🔬")

st.markdown(
    """
    <div style="
      padding: 1.5rem 1.75rem;
      border-radius: 10px;
      background: linear-gradient(135deg, #1F3864 0%, #2E5496 100%);
      color: white;
      margin-bottom: 1.5rem;
    ">
      <div style="font-size:0.85rem; opacity:0.85; letter-spacing:0.08em;">SENSYM EDUCATION</div>
      <h1 style="margin:0.25rem 0 0.5rem 0; color:white;">Curious Minds</h1>
      <p style="margin:0; font-size:1.05rem; opacity:0.95;">
        Four browser-accessible science sandboxes — combine real, curated facts in unexpected
        ways and watch a small AI reason out the consequences.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown("### 🧪 Chemistry What-If Lab")
    st.markdown(
        "Drop hydrogen and oxygen onto the bench, dial up the temperature, "
        "watch water condense — or thermite ignite."
    )
    st.page_link("pages/1_Chemistry_Lab.py", label="Open Chemistry Lab →", icon="🧪")

with c2:
    st.markdown("### 🌿 Ecosystem / Biome Lab")
    st.markdown(
        "Place wolves into Yellowstone with no elk and watch the cascade. "
        "Burmese pythons in the Everglades. Climate +2 °C."
    )
    st.page_link("pages/2_Ecosystem_Lab.py", label="Open Ecosystem Lab →", icon="🌿")

with c3:
    st.markdown("### 🪐 Planet / Exoplanet Builder")
    st.markdown(
        "Build a planet at 0.3 AU around an M-dwarf and learn whether life could "
        "exist on it, why, and what kind."
    )
    st.page_link("pages/3_Planet_Lab.py", label="Open Planet Builder →", icon="🪐")

with c4:
    st.markdown("### 🔬 Physics Lab")
    st.markdown(
        "Launch a projectile at 45°, send a cart down a 3-hill coaster, "
        "test Einstein's photoelectric equation — seven scenarios, one schema."
    )
    st.page_link("pages/4_Physics_Lab.py", label="Open Physics Lab →", icon="🔬")

st.divider()

st.markdown("### How it works")
st.markdown(
    f"""
    Every output you see is the product of three layers working together:

    1. **A small, hand-curated knowledge base** of real elements, species, and stars — the same
       data a textbook author would consult.
    2. **Claude Haiku 4.5** (`{MODEL_ID}`) reasons over that knowledge base in response to your
       inputs.
    3. **Confidence-tiered output** distinguishes well-documented science, probable extrapolation,
       and explicit speculation.

    The intellectual hook — the question every visitor asks within thirty seconds — is
    *“how did they do that?”* The answer is the lesson. **AI is leverage on real knowledge,
    not a magician's hat.**
    """
)

st.markdown("### For teachers")
st.markdown(
    """
    - Every interaction can be **saved as a portable `.curious` file** and shared with students.
    - Browse the **Starter experiments** gallery in each app's sidebar.
    - **Fork the repo**, edit `/data/<domain>/*.json` to localize species or units, redeploy in
      ~15 minutes on Streamlit Community Cloud.
    - Scientifically calibrated to the level of a quality K-12 STEM textbook. Designed for the
      **National Rural STEM Learning Summit, Sept 3–4, 2026**.
    """
)

if not __import__("curious_mind.llm", fromlist=["have_api_key"]).have_api_key():
    ui.warn_panel(
        "🔌 <b>No <code>ANTHROPIC_API_KEY</code> detected.</b> The apps will run in cached "
        "example mode. Set the key in <code>.streamlit/secrets.toml</code> (local) or in the "
        "Streamlit Cloud Secrets manager (deployed) to enable live reasoning."
    )

st.caption("MIT licensed · github.com/isac-artzi/curious-minds")
