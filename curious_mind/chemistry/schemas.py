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

    @field_validator("byproducts", "safety_notes", "follow_ups", mode="before")
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

    @field_validator(
        "balanced_equation",
        "phase_at_conditions",
        "mechanism",
        "real_world_connection",
        "equilibrium_notes",
        mode="before",
    )
    @classmethod
    def _coerce_str(cls, v: Any) -> str:
        if v is None:
            return ""
        return str(v)
