"""Pydantic output schemas for the Chemistry sandbox.

Schemas are intentionally lenient — Claude often returns slight variants on the
literal vocabulary (e.g. 'highly_exothermic', 'very exothermic') and we'd rather
normalize than fail.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Product(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    formula: str
    name: str = ""
    phase: str = "unknown"
    amount_estimation: str = ""
    smiles: str = ""

    @field_validator("name", "phase", "amount_estimation", "smiles", mode="before")
    @classmethod
    def _coerce_str(cls, v: Any) -> str:
        if v is None:
            return ""
        return str(v)


_ENTHALPY_CLASSES = {
    "strongly_exothermic",
    "exothermic",
    "thermoneutral",
    "endothermic",
    "strongly_endothermic",
}
_ENTHALPY_SYNONYMS = {
    "very_exothermic": "strongly_exothermic",
    "highly_exothermic": "strongly_exothermic",
    "extremely_exothermic": "strongly_exothermic",
    "mildly_exothermic": "exothermic",
    "weakly_exothermic": "exothermic",
    "slightly_exothermic": "exothermic",
    "neutral": "thermoneutral",
    "isothermic": "thermoneutral",
    "athermic": "thermoneutral",
    "mildly_endothermic": "endothermic",
    "weakly_endothermic": "endothermic",
    "slightly_endothermic": "endothermic",
    "very_endothermic": "strongly_endothermic",
    "highly_endothermic": "strongly_endothermic",
    "extremely_endothermic": "strongly_endothermic",
}

_REACTION_TYPES = {
    "synthesis",
    "decomposition",
    "single_replacement",
    "double_replacement",
    "acid_base",
    "redox",
    "combustion",
    "no_reaction",
    "other",
}
_REACTION_TYPE_SYNONYMS = {
    "combination": "synthesis",
    "addition": "synthesis",
    "analysis": "decomposition",
    "displacement": "single_replacement",
    "single_displacement": "single_replacement",
    "metathesis": "double_replacement",
    "double_displacement": "double_replacement",
    "neutralization": "acid_base",
    "oxidation_reduction": "redox",
    "oxidation": "redox",
    "reduction": "redox",
    "burning": "combustion",
    "none": "no_reaction",
    "no": "no_reaction",
    "inert": "no_reaction",
    "unknown": "other",
}

_VISUAL_EFFECTS = {
    "bubbles",         # gas evolution
    "precipitate",     # solid falling out of solution
    "flash",           # bright burst
    "color_change",    # solution/mixture changes color
    "smoke",           # plume rising
    "explosion",       # violent expansion
    "glow",            # sustained luminescence
    "crystal_growth",  # crystals forming
    "flame",           # combustion / sustained burning
    "fizz",            # vigorous bubbling
    "melt",            # solid → liquid
    "freeze",          # liquid → solid
    "vapor",           # liquid → gas plume
    "spark",           # short bright sparks
}
_VISUAL_EFFECT_SYNONYMS = {
    "gas": "bubbles",
    "bubble": "bubbles",
    "effervescence": "fizz",
    "boiling": "vapor",
    "steam": "vapor",
    "burn": "flame",
    "combustion": "flame",
    "fire": "flame",
    "light": "glow",
    "luminescence": "glow",
    "sparks": "spark",
    "burst": "flash",
    "boom": "explosion",
    "puff": "smoke",
    "fog": "smoke",
    "precipitation": "precipitate",
    "crystals": "crystal_growth",
    "crystallize": "crystal_growth",
    "color": "color_change",
    "colour_change": "color_change",
    "discoloration": "color_change",
}


_CONFIDENCE_CLASSES = {"well_documented", "probable", "speculative"}
_CONFIDENCE_SYNONYMS = {
    "well-documented": "well_documented",
    "documented": "well_documented",
    "established": "well_documented",
    "high": "well_documented",
    "likely": "probable",
    "plausible": "probable",
    "medium": "probable",
    "moderate": "probable",
    "speculation": "speculative",
    "exploratory": "speculative",
    "uncertain": "speculative",
    "low": "speculative",
    "hypothetical": "speculative",
}


def _normalize_enum(v: Any, valid: set[str], synonyms: dict[str, str], default: str) -> str:
    if v is None:
        return default
    s = str(v).strip().lower().replace(" ", "_").replace("-", "_")
    if s in valid:
        return s
    if s in synonyms:
        return synonyms[s]
    # Substring fall-through
    for term in valid:
        if term in s:
            return term
    return default


class QuizItem(BaseModel):
    """A single multiple-choice question Claude generates about the reaction."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    question: str = ""
    choices: list[str] = Field(default_factory=list)
    correct_index: int = 0
    explanation: str = ""

    @field_validator("choices", mode="before")
    @classmethod
    def _coerce_choices(cls, v: Any) -> list[str]:
        if v is None:
            return []
        if isinstance(v, str):
            v = [v]
        out = [str(c).strip() for c in v if str(c).strip()]
        return out[:4]  # cap at 4 options

    @field_validator("correct_index", mode="before")
    @classmethod
    def _coerce_idx(cls, v: Any) -> int:
        try:
            return max(0, int(v))
        except (TypeError, ValueError):
            return 0

    @field_validator("question", "explanation", mode="before")
    @classmethod
    def _coerce_str(cls, v: Any) -> str:
        return "" if v is None else str(v)


class ReactionResult(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    primary_product: Product
    byproducts: list[Product] = Field(default_factory=list)

    @field_validator("primary_product", mode="before")
    @classmethod
    def _coerce_product(cls, v: Any) -> Any:
        # Allow Claude to return a string formula instead of a dict.
        if isinstance(v, str) and v.strip():
            return {"formula": v, "name": v, "phase": "unknown"}
        return v
    balanced_equation: str = ""
    enthalpy_kJ_per_mol: float | None = None
    enthalpy_class: str = "thermoneutral"
    activation_energy_kJ_per_mol: float | None = None
    reaction_type: str = "other"
    equilibrium_notes: str = ""
    phase_at_conditions: str = ""
    mechanism: str = ""
    real_world_connection: str = ""
    confidence: str = "probable"
    safety_notes: list[str] = Field(default_factory=list)
    follow_ups: list[str] = Field(default_factory=list)

    # ---- Spectacle hints (Phase 1 Reaction Theater) ----------------------
    # All optional with sane defaults; older cached results and minimal
    # fallbacks keep working unchanged.
    visual_effects: list[str] = Field(default_factory=list)
    reactant_colors: list[str] = Field(default_factory=list)
    product_colors: list[str] = Field(default_factory=list)
    dramatic_moment: str = ""

    # ---- Quiz items (Phase 2 Challenge mode) -----------------------------
    quiz: list[QuizItem] = Field(default_factory=list)

    # ---- Normalizers -----------------------------------------------------
    @field_validator("enthalpy_kJ_per_mol", "activation_energy_kJ_per_mol", mode="before")
    @classmethod
    def _coerce_float(cls, v: Any) -> float | None:
        if v is None or v == "":
            return None
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    @field_validator("enthalpy_class", mode="before")
    @classmethod
    def _norm_enthalpy_class(cls, v: Any) -> str:
        return _normalize_enum(v, _ENTHALPY_CLASSES, _ENTHALPY_SYNONYMS, "thermoneutral")

    @field_validator("reaction_type", mode="before")
    @classmethod
    def _norm_reaction_type(cls, v: Any) -> str:
        return _normalize_enum(v, _REACTION_TYPES, _REACTION_TYPE_SYNONYMS, "other")

    @field_validator("confidence", mode="before")
    @classmethod
    def _norm_confidence(cls, v: Any) -> str:
        return _normalize_enum(v, _CONFIDENCE_CLASSES, _CONFIDENCE_SYNONYMS, "probable")

    @field_validator(
        "byproducts",
        "safety_notes",
        "follow_ups",
        "reactant_colors",
        "product_colors",
        mode="before",
    )
    @classmethod
    def _coerce_list(cls, v: Any) -> list:
        if v is None:
            return []
        if isinstance(v, str):
            # Sometimes a single string slips through where a list is expected
            return [v]
        return list(v)

    @field_validator("follow_ups")
    @classmethod
    def _cap_followups(cls, v: list[str]) -> list[str]:
        return [str(s) for s in v[:3] if s]

    @field_validator("visual_effects", mode="before")
    @classmethod
    def _norm_visual_effects(cls, v: Any) -> list[str]:
        if v is None:
            return []
        if isinstance(v, str):
            v = [v]
        out: list[str] = []
        seen: set[str] = set()
        for item in v:
            s = str(item).strip().lower().replace(" ", "_").replace("-", "_")
            if not s:
                continue
            s = _VISUAL_EFFECT_SYNONYMS.get(s, s)
            if s in _VISUAL_EFFECTS and s not in seen:
                out.append(s)
                seen.add(s)
            if len(out) >= 4:
                break
        return out

    @field_validator("quiz", mode="before")
    @classmethod
    def _coerce_quiz(cls, v: Any) -> list:
        if v is None:
            return []
        if isinstance(v, dict):
            v = [v]
        # Keep only dict-shaped items so one stray string can't invalidate
        # the whole result. Generous raw cap (5) so we can still pick 2 good
        # items after filtering.
        return [q for q in list(v) if isinstance(q, dict)][:5]

    @field_validator("quiz")
    @classmethod
    def _drop_bad_quiz(cls, v: list) -> list:
        # Drop items with no question, <2 choices, or out-of-range
        # correct_index, then cap at 2.
        out: list = []
        for q in v:
            if q.question and len(q.choices) >= 2 and 0 <= q.correct_index < len(q.choices):
                out.append(q)
        return out[:2]

    @field_validator("reactant_colors", "product_colors")
    @classmethod
    def _clean_colors(cls, v: list[str]) -> list[str]:
        # Cap at 4; strip; keep CSS-safe-ish strings only.
        out: list[str] = []
        for c in v[:4]:
            s = str(c).strip()
            if s:
                out.append(s)
        return out

    @field_validator(
        "balanced_equation",
        "phase_at_conditions",
        "mechanism",
        "real_world_connection",
        "equilibrium_notes",
        "dramatic_moment",
        mode="before",
    )
    @classmethod
    def _coerce_str(cls, v: Any) -> str:
        if v is None:
            return ""
        return str(v)
