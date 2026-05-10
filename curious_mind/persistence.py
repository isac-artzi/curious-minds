"""File-based persistence for .curious experiment files."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import streamlit as st

SCHEMA = "curious-minds.experiment"
SCHEMA_VERSION = "1.0"

App = Literal["chemistry", "ecosystem", "planet"]


def serialize(app: App, title: str, inputs: dict[str, Any], notes: str = "") -> str:
    payload = {
        "schema": SCHEMA,
        "version": SCHEMA_VERSION,
        "app": app,
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "title": title,
        "inputs": inputs,
        "notes": notes,
    }
    return json.dumps(payload, indent=2)


def deserialize(raw: bytes | str, expected_app: App) -> dict[str, Any]:
    """Parse a .curious file. Raises ValueError on schema/app mismatch."""
    text = raw.decode("utf-8") if isinstance(raw, bytes) else raw
    obj = json.loads(text)
    if obj.get("schema") != SCHEMA:
        raise ValueError(f"Not a Curious Minds experiment file (schema={obj.get('schema')!r}).")
    if obj.get("app") != expected_app:
        raise ValueError(
            f"This file is for the '{obj.get('app')}' sandbox, not '{expected_app}'."
        )
    return obj


def list_starter_examples(app: App) -> list[Path]:
    """Return all .curious starters shipped in /examples/<app>/."""
    base = Path(__file__).resolve().parent.parent / "examples" / app
    if not base.exists():
        return []
    return sorted(base.glob("*.curious"))


def load_starter(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def render_persistence_sidebar(
    app: App,
    inputs: dict[str, Any],
    title_default: str = "Untitled experiment",
) -> dict[str, Any] | None:
    """
    Render save / load / starter UI in the sidebar.
    Returns loaded inputs dict if user just loaded one (caller should rerun), else None.
    """
    loaded: dict[str, Any] | None = None

    with st.sidebar.expander("💾 Save / load", expanded=False):
        title = st.text_input("Experiment title", value=title_default, key=f"{app}_save_title")
        notes = st.text_area("Notes (optional)", value="", height=68, key=f"{app}_save_notes")
        st.download_button(
            "💾 Save experiment",
            data=serialize(app, title, inputs, notes),
            file_name=f"{title.lower().replace(' ', '_') or 'experiment'}.curious",
            mime="application/json",
            key=f"{app}_save_btn",
            use_container_width=True,
        )

        uploaded = st.file_uploader(
            "📂 Load experiment (.curious)",
            type=["curious", "json"],
            key=f"{app}_load_uploader",
        )
        # st.file_uploader keeps returning the same UploadedFile on every rerun
        # until the user manually clears it. Track the file_id so we only act
        # once per actual upload.
        if uploaded is not None:
            seen_key = f"{app}_load_seen_id"
            file_id = getattr(uploaded, "file_id", None) or uploaded.name
            if st.session_state.get(seen_key) != file_id:
                try:
                    obj = deserialize(uploaded.getvalue(), expected_app=app)
                    st.success(f"Loaded: {obj.get('title', '(untitled)')}")
                    loaded = obj.get("inputs", {})
                    st.session_state[seen_key] = file_id
                except (ValueError, json.JSONDecodeError) as e:
                    st.error(f"Could not load file: {e}")
                    st.session_state[seen_key] = file_id

    with st.sidebar.expander("🧪 Starter experiments", expanded=False):
        starters = list_starter_examples(app)
        if not starters:
            st.caption("No starters shipped for this app yet.")
        for p in starters:
            try:
                obj = load_starter(p)
                label = obj.get("title", p.stem)
            except Exception:
                label = p.stem
            if st.button(label, key=f"{app}_starter_{p.name}", use_container_width=True):
                loaded = obj.get("inputs", {})

    st.sidebar.caption("🔒 Auto-saved to this browser · Save to file for keeps")
    return loaded
