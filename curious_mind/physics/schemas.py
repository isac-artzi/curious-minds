"""Pydantic output schema for the Physics Lab (lenient by design)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

_CONF = {"well_documented", "probable", "speculative"}
_CONF_SYN = {
    "well-documented": "well_documented",
    "documented": "well_documented",
    "established": "well_documented",
    "high": "well_documented",
    "likely": "probable",
    "plausible": "probable",
    "medium": "probable",
    "moderate": "probable",
    "uncertain": "speculative",
    "low": "speculative",
    "exploratory": "speculative",
    "hypothetical": "speculative",
}


def _norm(v: Any, valid: set[str], syn: dict[str, str], default: str) -> str:
    if v is None:
        return default
    s = str(v).strip().lower().replace(" ", "_").replace("-", "_")
    if s in valid:
        return s
    if s in syn:
        return syn[s]
    for term in valid:
        if term in s:
            return term
    return default


class QuizItem(BaseModel):
    """A single MCQ Claude generates about the specific scenario."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    question: str = ""
    choices: list[str] = Field(default_factory=list)
    correct_index: int = 0
    explanation: str = ""

    @field_validator("choices", mode="before")
    @classmethod
    def _coerce_choices(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            v = [v]
        out = [str(c).strip() for c in v if str(c).strip()]
        return out[:4]

    @field_validator("correct_index", mode="before")
    @classmethod
    def _coerce_idx(cls, v):
        try:
            return max(0, int(v))
        except (TypeError, ValueError):
            return 0

    @field_validator("question", "explanation", mode="before")
    @classmethod
    def _coerce_str(cls, v):
        return "" if v is None else str(v)


class PhysicsResult(BaseModel):
    """One-size-fits-all result for any physics scenario.

    Deterministic numbers come from ``simulators.py``; Claude only writes the
    surrounding narrative, so a single schema covers all 7 scenarios.
    """

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    scenario_id: str = ""
    summary: str = ""
    intuition: str = ""
    key_concepts: list[str] = Field(default_factory=list)
    common_misconceptions: list[str] = Field(default_factory=list)
    real_world_examples: list[str] = Field(default_factory=list)
    limitations_or_assumptions: list[str] = Field(default_factory=list)
    follow_ups: list[str] = Field(default_factory=list)
    confidence: str = "probable"

    # ---- Spectacle hints (Phase 1 Apparatus Theater) --------------------
    dramatic_moment: str = ""    # one vivid line about the cool thing that happens
    visual_caption: str = ""     # short caption (≤ 12 words) shown over the animation

    # ---- Quiz items (Phase 2 Challenge mode) ----------------------------
    quiz: list[QuizItem] = Field(default_factory=list)

    @field_validator("confidence", mode="before")
    @classmethod
    def _norm_conf(cls, v):
        return _norm(v, _CONF, _CONF_SYN, "probable")

    @field_validator(
        "key_concepts",
        "common_misconceptions",
        "real_world_examples",
        "limitations_or_assumptions",
        "follow_ups",
        mode="before",
    )
    @classmethod
    def _coerce_list(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        return [str(x) for x in v if x]

    @field_validator("follow_ups")
    @classmethod
    def _cap_followups(cls, v):
        return [s for s in v[:3] if s]

    @field_validator(
        "scenario_id", "summary", "intuition",
        "dramatic_moment", "visual_caption",
        mode="before",
    )
    @classmethod
    def _coerce_str(cls, v):
        return "" if v is None else str(v)

    @field_validator("quiz", mode="before")
    @classmethod
    def _coerce_quiz(cls, v):
        if v is None:
            return []
        if isinstance(v, dict):
            v = [v]
        return list(v)[:5]  # generous cap before filtering

    @field_validator("quiz")
    @classmethod
    def _drop_bad_quiz(cls, v):
        out = []
        for q in v:
            if len(q.choices) >= 2 and 0 <= q.correct_index < len(q.choices):
                out.append(q)
        return out[:2]
