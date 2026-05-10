"""Shared Streamlit UI components and theming."""

from __future__ import annotations

import streamlit as st

NAVY = "#1F3864"
TEAL = "#2E5496"
AMBER = "#D97706"
GRAY = "#5B6478"

CONFIDENCE_COLOR = {
    "well_documented": "#16A34A",
    "probable": "#D97706",
    "speculative": "#6B7280",
}


def page_setup(title: str, icon: str) -> None:
    st.set_page_config(
        page_title=f"{title} · Curious Minds",
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    # Inject brand CSS once per page
    st.markdown(
        f"""
        <style>
          .cm-header {{
            border-left: 4px solid {NAVY};
            padding: 0.25rem 0 0.25rem 0.75rem;
            margin-bottom: 1rem;
          }}
          .cm-header h1 {{ margin: 0; color: {NAVY}; font-size: 1.6rem; }}
          .cm-header .crumb {{ color: {GRAY}; font-size: 0.85rem; }}
          .cm-info {{
            background: #F4F6FA;
            border-left: 3px solid {TEAL};
            padding: 0.6rem 0.9rem;
            border-radius: 4px;
            margin: 0.5rem 0;
            font-size: 0.92rem;
          }}
          .cm-warn {{
            background: #FFF7ED;
            border-left: 3px solid {AMBER};
            padding: 0.6rem 0.9rem;
            border-radius: 4px;
            margin: 0.5rem 0;
            font-size: 0.92rem;
          }}
          .cm-badge {{
            display: inline-block;
            padding: 0.1rem 0.55rem;
            border-radius: 999px;
            font-size: 0.75rem;
            color: white;
            font-weight: 600;
            letter-spacing: 0.02em;
          }}
          .cm-source {{
            font-size: 0.78rem;
            color: {GRAY};
            font-family: "JetBrains Mono", ui-monospace, monospace;
          }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def header(title: str, crumb: str = "Curious Minds") -> None:
    st.markdown(
        f"""
        <div class="cm-header">
          <div class="crumb">{crumb}</div>
          <h1>{title}</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )


def info_panel(text: str) -> None:
    st.markdown(f'<div class="cm-info">{text}</div>', unsafe_allow_html=True)


def warn_panel(text: str) -> None:
    st.markdown(f'<div class="cm-warn">{text}</div>', unsafe_allow_html=True)


def confidence_badge(level: str) -> str:
    color = CONFIDENCE_COLOR.get(level, GRAY)
    label = level.replace("_", " ").title()
    return f'<span class="cm-badge" style="background:{color}">{label}</span>'


def source_indicator(source: str) -> None:
    """Tiny line showing whether output came from live LLM, cache, or fallback."""
    label = {
        "live": "🟢 Live response from Claude Haiku 4.5",
        "cached": "🔵 Cached response (same inputs as before)",
        "fallback": "⚪ Cached example (offline / API unavailable)",
    }.get(source, source)
    st.markdown(f'<div class="cm-source">{label}</div>', unsafe_allow_html=True)


def follow_up_buttons(suggestions: list[str], state_key_prefix: str) -> str | None:
    """Render up to 3 follow-up suggestions; return clicked text or None."""
    if not suggestions:
        return None
    st.markdown("**Try next:**")
    cols = st.columns(min(3, len(suggestions)))
    clicked: str | None = None
    for i, sug in enumerate(suggestions[:3]):
        with cols[i]:
            if st.button(sug, key=f"{state_key_prefix}_followup_{i}", use_container_width=True):
                clicked = sug
    return clicked


def offline_banner() -> None:
    warn_panel(
        "🔌 <b>Offline / demo mode.</b> No Anthropic API key detected — showing cached example "
        "outputs. Add <code>ANTHROPIC_API_KEY</code> to <code>.streamlit/secrets.toml</code> or "
        "the Streamlit Cloud Secrets manager to enable live reasoning."
    )


def speculation_banner() -> None:
    warn_panel(
        "⚠️ <b>Speculation only.</b> The reasoning below extrapolates beyond well-documented "
        "science. Treat as a thought experiment, not a textbook fact."
    )
