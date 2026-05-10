"""Anthropic Claude client + structured-output helpers + cached fallback."""

from __future__ import annotations

import json
import os
import re
from typing import Any, Type, TypeVar

import streamlit as st
from pydantic import BaseModel, ValidationError

from . import MODEL_ID

T = TypeVar("T", bound=BaseModel)

# When True, validation failures show the raw model output + the validator error
# in an expander so we can see exactly what Claude produced.
DEBUG = os.environ.get("CURIOUS_MINDS_DEBUG", "1") == "1"


def _api_key() -> str | None:
    """Resolve the Anthropic key from Streamlit secrets, then env."""
    try:
        return st.secrets["ANTHROPIC_API_KEY"]  # type: ignore[index]
    except Exception:
        return os.environ.get("ANTHROPIC_API_KEY")


def have_api_key() -> bool:
    return bool(_api_key())


def _client():
    """Lazy Anthropic client. Returns None if no key configured."""
    key = _api_key()
    if not key:
        return None
    try:
        import anthropic
    except ImportError:
        return None
    return anthropic.Anthropic(api_key=key)


_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)


def _repair_truncated_json(text: str) -> str:
    """Best-effort repair of a truncated JSON document.

    Walks the text tracking the bracket stack and string state. When a value
    or token is left dangling (because the model's response was cut by
    ``max_tokens``), we truncate back to the last safe boundary, drop any
    trailing comma, then append the closers for any still-open arrays /
    objects so the result parses. Pydantic validators will fill defaults
    for any fields that are missing.
    """
    stack: list[str] = []
    in_str = False
    esc = False
    safe = 0
    expect = "value"  # 'value', 'key', 'colon', 'comma_or_close'

    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
                if expect == "value":
                    expect = "comma_or_close"
                    safe = i + 1
                elif expect == "key":
                    expect = "colon"
            i += 1
            continue
        if ch in " \t\n\r":
            i += 1
            continue
        if ch == '"':
            in_str = True
            i += 1
            continue
        if ch == "{":
            stack.append("{")
            expect = "key"
            i += 1
            continue
        if ch == "[":
            stack.append("[")
            expect = "value"
            i += 1
            continue
        if ch in "}]":
            if stack:
                stack.pop()
            expect = "comma_or_close"
            safe = i + 1
            i += 1
            continue
        if ch == ":":
            expect = "value"
            i += 1
            continue
        if ch == ",":
            expect = "key" if (stack and stack[-1] == "{") else "value"
            safe = i  # cut before the comma if we have to truncate here
            i += 1
            continue
        # Scalar token: number / true / false / null
        j = i
        while j < n and text[j] not in ",}] \t\n\r":
            j += 1
        if j >= n:
            break  # truncated mid-token; do not advance `safe`
        expect = "comma_or_close"
        safe = j
        i = j

    out = text[:safe].rstrip()
    while out.endswith(","):
        out = out[:-1].rstrip()

    # Recompute the stack at the truncation point — items opened after `safe`
    # are no longer part of the document.
    final_stack: list[str] = []
    in_str2 = False
    esc2 = False
    for ch in out:
        if in_str2:
            if esc2:
                esc2 = False
            elif ch == "\\":
                esc2 = True
            elif ch == '"':
                in_str2 = False
        else:
            if ch == '"':
                in_str2 = True
            elif ch in "{[":
                final_stack.append(ch)
            elif ch in "}]" and final_stack:
                final_stack.pop()

    for ch in reversed(final_stack):
        out += "}" if ch == "{" else "]"
    return out


def _extract_json(text: str) -> str:
    """Pull a JSON object out of a model response. Handles ```json fences and prose."""
    # 1. Prefer fenced code block content if present.
    m = _FENCE_RE.search(text)
    if m:
        candidate = m.group(1).strip()
        if candidate.startswith("{") and candidate.endswith("}"):
            return candidate
    # 2. Otherwise grab the largest balanced {...} span.
    start = text.find("{")
    if start == -1:
        raise ValueError("No JSON object found in model response.")
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]
    # Fall back to greedy slice
    end = text.rfind("}")
    if end == -1 or end < start:
        raise ValueError("Unbalanced JSON in model response.")
    return text[start : end + 1]


@st.cache_data(show_spinner=False)
def _cached_call(
    domain: str,
    system_prompt: str,
    user_payload_json: str,
    schema_name: str,
    max_tokens: int,
    schema_skeleton: str = "",
) -> str:
    """Cached raw Claude call. Cache key includes the full prompt + payload."""
    client = _client()
    if client is None:
        raise RuntimeError("No Anthropic client available.")
    skeleton_block = (
        f"\n\nSCHEMA (JSON skeleton — fill every field; do not rename, wrap, or add keys):\n"
        f"{schema_skeleton}"
        if schema_skeleton
        else ""
    )
    msg = client.messages.create(
        model=MODEL_ID,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Return ONLY a single JSON object matching the {schema_name} schema. "
                    f"No prose, no markdown fences, no wrapper keys."
                    f"{skeleton_block}\n\nINPUT:\n{user_payload_json}"
                ),
            }
        ],
    )
    parts = [b.text for b in msg.content if getattr(b, "type", None) == "text"]
    return "".join(parts)


def _schema_skeleton(schema: Type[T]) -> str:
    """Best-effort JSON skeleton from a pydantic schema for prompt grounding."""
    try:
        js = schema.model_json_schema()
    except Exception:
        return ""

    def shape(node: dict, defs: dict) -> Any:
        if "$ref" in node:
            ref = node["$ref"].rsplit("/", 1)[-1]
            return shape(defs.get(ref, {}), defs)
        if node.get("anyOf"):
            return shape(node["anyOf"][0], defs)
        t = node.get("type")
        if t == "object" or "properties" in node:
            return {k: shape(v, defs) for k, v in node.get("properties", {}).items()}
        if t == "array":
            return [shape(node.get("items", {}), defs)]
        if t == "string":
            return node.get("description", "string")
        if t == "integer":
            return 0
        if t == "number":
            return 0.0
        if t == "boolean":
            return False
        return None

    defs = js.get("$defs", {})
    return json.dumps(shape(js, defs), indent=2)


def _show_debug(stage: str, raw: str, err: Exception) -> None:
    if not DEBUG:
        return
    with st.expander(f"⚙️ Diagnostic — {stage} ({type(err).__name__})", expanded=True):
        st.caption("Set env var `CURIOUS_MINDS_DEBUG=0` to hide these.")
        st.code(str(err), language="text")
        st.markdown("**Raw model output:**")
        st.code(raw[:4000], language="json")


def _try_validate(schema: Type[T], obj: Any) -> T | None:
    """Validate `obj` against `schema`, transparently unwrapping common wrapper
    keys like {"result": {...}} or {"reaction": {...}}.

    Strategy: prefer the dict whose keys overlap most with the schema's fields.
    """
    field_names = set(getattr(schema, "model_fields", {}).keys())

    def overlap(d: Any) -> int:
        if not isinstance(d, dict):
            return -1
        return len(field_names & set(d.keys()))

    candidates: list[Any] = [obj]
    if isinstance(obj, dict):
        for v in obj.values():
            if isinstance(v, dict):
                candidates.append(v)

    # Try the candidate with the highest field overlap first.
    candidates.sort(key=overlap, reverse=True)
    last_err: Exception | None = None
    for c in candidates:
        try:
            return schema.model_validate(c)
        except ValidationError as e:
            last_err = e
            continue
    if last_err is not None:
        raise last_err
    return None


def call_structured(
    domain: str,
    system_prompt: str,
    user_payload: dict[str, Any],
    schema: Type[T],
    fallback: T,
    max_tokens: int = 1200,
) -> tuple[T, str]:
    """
    Call Claude, validate against `schema`, return (result, source).

    `source` is one of:
      - "live"     — got and validated a fresh response
      - "fallback" — no key, API error, or schema failure → returned `fallback`
    """
    if not have_api_key():
        return fallback, "fallback"

    payload_json = json.dumps(user_payload, sort_keys=True, default=str)
    skeleton = _schema_skeleton(schema)

    try:
        raw = _cached_call(
            domain, system_prompt, payload_json, schema.__name__, max_tokens, skeleton
        )
    except Exception as e:
        st.warning(f"Claude unreachable ({type(e).__name__}). Showing cached example.")
        if DEBUG:
            with st.expander(f"⚙️ Diagnostic — API call ({type(e).__name__})"):
                st.code(str(e), language="text")
        return fallback, "fallback"

    last_err: Exception | None = None
    last_raw: str = raw

    for attempt in range(2):
        try:
            json_text = _extract_json(raw)
            try:
                obj = json.loads(json_text)
            except json.JSONDecodeError:
                # Likely max_tokens truncation — try to repair and re-parse.
                obj = json.loads(_repair_truncated_json(json_text))
            validated = _try_validate(schema, obj)
            if validated is not None:
                return validated, "live"
        except (ValueError, json.JSONDecodeError, ValidationError) as e:
            last_err = e
            last_raw = raw
            if attempt == 0:
                # One stricter retry with the actual validator error included
                try:
                    raw = _cached_call(
                        domain,
                        system_prompt
                        + "\n\nIMPORTANT: a previous response failed schema validation with:\n"
                        + str(e)[:600]
                        + "\nReturn ONLY a single valid JSON object matching the schema exactly. "
                        "No prose, no markdown fences.",
                        payload_json,
                        schema.__name__ + "_retry",
                        max_tokens,
                        skeleton,
                    )
                    continue
                except Exception as e2:
                    last_err = e2
                    break
            break

    st.warning(f"Schema validation failed ({type(last_err).__name__}). Showing cached example.")
    _show_debug("validation", last_raw, last_err)  # type: ignore[arg-type]
    return fallback, "fallback"
