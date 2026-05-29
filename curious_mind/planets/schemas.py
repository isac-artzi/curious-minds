"""Pydantic output schemas for the Planets sandbox (lenient by design)."""

from __future__ import annotations

from typing import Any, Optional

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

_VERDICT = {"habitable", "extremophile_only", "non_habitable"}
_VERDICT_SYN = {
    "habitable_for_life": "habitable",
    "earth_like": "habitable",
    "extremophile": "extremophile_only",
    "extremophiles_only": "extremophile_only",
    "marginal": "extremophile_only",
    "uninhabitable": "non_habitable",
    "non-habitable": "non_habitable",
    "not_habitable": "non_habitable",
    "hostile": "non_habitable",
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


def _coerce_float(v: Any, default: float = 0.0) -> float:
    if v is None or v == "":
        return default
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


class QuizItem(BaseModel):
    """A single MCQ Claude generates about the specific planet scenario."""

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


class SurfaceConditions(BaseModel):
    model_config = ConfigDict(extra="ignore")
    avg_temperature_C: float = 0.0
    surface_pressure_atm: float = 1.0
    gravity_g: float = 1.0
    day_length_hours: float = 24.0
    radiation_environment: str = ""

    @field_validator(
        "avg_temperature_C", "surface_pressure_atm", "gravity_g", "day_length_hours",
        mode="before",
    )
    @classmethod
    def _coerce_num(cls, v):
        return _coerce_float(v, 0.0)

    @field_validator("radiation_environment", mode="before")
    @classmethod
    def _coerce_str(cls, v):
        return "" if v is None else str(v)


class TerraformingPlan(BaseModel):
    """How the user might engineer this world toward habitability."""
    model_config = ConfigDict(extra="ignore")

    feasible: bool = True
    difficulty_1_to_10: int = 5
    estimated_timescale: str = ""
    steps: list[str] = Field(default_factory=list)

    @field_validator("feasible", mode="before")
    @classmethod
    def _coerce_bool(cls, v):
        if isinstance(v, bool):
            return v
        if v is None:
            return True
        s = str(v).strip().lower()
        if s in ("true", "yes", "y", "1", "feasible"):
            return True
        if s in ("false", "no", "n", "0", "infeasible", "impossible"):
            return False
        return True

    @field_validator("difficulty_1_to_10", mode="before")
    @classmethod
    def _norm_diff(cls, v):
        try:
            n = int(round(float(v)))
        except (TypeError, ValueError):
            return 5
        return max(1, min(10, n))

    @field_validator("estimated_timescale", mode="before")
    @classmethod
    def _coerce_str(cls, v):
        return "" if v is None else str(v)

    @field_validator("steps", mode="before")
    @classmethod
    def _coerce_steps(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        return [str(s) for s in v if s][:8]


class PlanetResult(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    verdict: str = "extremophile_only"
    verdict_reason: str = ""
    surface: SurfaceConditions = Field(default_factory=SurfaceConditions)
    sky_description: str = ""
    plausible_life: str = ""
    plausible_life_confidence: str = "speculative"
    closest_real_exoplanet_name: str = ""
    comparison_note: str = ""
    confidence: str = "probable"
    follow_ups: list[str] = Field(default_factory=list)

    # New: hard blockers Claude identified for habitability
    habitability_blockers: list[str] = Field(default_factory=list)

    # New: optional terraforming plan (only populated when terraforming_target is set)
    terraforming: Optional[TerraformingPlan] = None

    # New: optional speculative abiogenesis assessment (only when seeding scenario active)
    abiogenesis_prospects: str = ""

    # ---- Spectacle hints (Planet Forge & Sky View) -----------------------
    dramatic_moment: str = ""    # one vivid sentence about the headline visible thing
    visual_caption: str = ""     # short caption pinned to the scene (≤ 12 words)

    # ---- Quiz items (Challenge / Quiz panel) -----------------------------
    quiz: list[QuizItem] = Field(default_factory=list)

    @field_validator("verdict", mode="before")
    @classmethod
    def _norm_v(cls, v):
        return _norm(v, _VERDICT, _VERDICT_SYN, "extremophile_only")

    @field_validator("plausible_life_confidence", "confidence", mode="before")
    @classmethod
    def _norm_conf(cls, v):
        return _norm(v, _CONF, _CONF_SYN, "probable")

    @field_validator("follow_ups", mode="before")
    @classmethod
    def _coerce_list(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        return list(v)

    @field_validator("follow_ups")
    @classmethod
    def _cap(cls, v):
        return [str(s) for s in v[:3] if s]

    @field_validator("habitability_blockers", mode="before")
    @classmethod
    def _coerce_blockers(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        return [str(s) for s in v if s][:6]

    @field_validator(
        "verdict_reason", "sky_description", "plausible_life",
        "closest_real_exoplanet_name", "comparison_note", "abiogenesis_prospects",
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
        return list(v)[:5]

    @field_validator("quiz")
    @classmethod
    def _drop_bad_quiz(cls, v):
        out = []
        for q in v:
            if len(q.choices) >= 2 and 0 <= q.correct_index < len(q.choices):
                out.append(q)
        return out[:2]
