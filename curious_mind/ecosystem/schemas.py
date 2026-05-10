"""Pydantic output schemas for the Ecosystem sandbox (lenient by design)."""

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

_DIR = {"thriving", "stable", "stressed", "extirpated"}
_DIR_SYN = {
    "increasing": "thriving",
    "growing": "thriving",
    "expanding": "thriving",
    "recovering": "thriving",
    "steady": "stable",
    "unchanged": "stable",
    "declining": "stressed",
    "decreasing": "stressed",
    "stressed_population": "stressed",
    "extinct": "extirpated",
    "locally_extinct": "extirpated",
    "lost": "extirpated",
}

_RISK = {"none", "low", "moderate", "high"}
_RISK_SYN = {
    "minimal": "none",
    "negligible": "none",
    "very_low": "low",
    "medium": "moderate",
    "elevated": "moderate",
    "very_high": "high",
    "severe": "high",
    "extreme": "high",
}

_BIODIV_CHANGE = {"increases", "stable", "decreases", "collapses"}
_BIODIV_SYN = {
    "rising": "increases",
    "growing": "increases",
    "improving": "increases",
    "unchanged": "stable",
    "steady": "stable",
    "declining": "decreases",
    "falling": "decreases",
    "shrinking": "decreases",
    "collapse": "collapses",
    "crash": "collapses",
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


class CascadeStep(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)
    step: str
    confidence: str = "probable"

    @field_validator("confidence", mode="before")
    @classmethod
    def _norm_conf(cls, v):
        return _norm(v, _CONF, _CONF_SYN, "probable")

    @field_validator("step", mode="before")
    @classmethod
    def _coerce_step(cls, v):
        return "" if v is None else str(v)


class SpeciesOutcome(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)
    species_id: str
    common_name: str = ""
    direction: str = "stable"
    note: str = ""

    @field_validator("direction", mode="before")
    @classmethod
    def _norm_dir(cls, v):
        return _norm(v, _DIR, _DIR_SYN, "stable")

    @field_validator("common_name", "note", mode="before")
    @classmethod
    def _coerce(cls, v):
        return "" if v is None else str(v)


class EcosystemResult(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    biome_id: str = ""
    summary: str = ""
    cascade: list[CascadeStep] = Field(default_factory=list)
    species_outcomes: list[SpeciesOutcome] = Field(default_factory=list)
    keystone_species: list[str] = Field(default_factory=list)
    invasive_risk: str = "none"
    recovery_timescale_years: int | None = None
    biodiversity_index_change: str = "stable"
    real_world_analogue: str = ""
    conservation_note: str = ""
    confidence: str = "probable"
    follow_ups: list[str] = Field(default_factory=list)

    @field_validator("confidence", mode="before")
    @classmethod
    def _norm_conf(cls, v):
        return _norm(v, _CONF, _CONF_SYN, "probable")

    @field_validator("invasive_risk", mode="before")
    @classmethod
    def _norm_risk(cls, v):
        return _norm(v, _RISK, _RISK_SYN, "none")

    @field_validator("biodiversity_index_change", mode="before")
    @classmethod
    def _norm_biodiv(cls, v):
        return _norm(v, _BIODIV_CHANGE, _BIODIV_SYN, "stable")

    @field_validator("recovery_timescale_years", mode="before")
    @classmethod
    def _coerce_recovery(cls, v):
        if v is None or v == "":
            return None
        try:
            n = int(round(float(v)))
            return max(0, n)
        except (TypeError, ValueError):
            return None

    @field_validator("cascade", "species_outcomes", "follow_ups", "keystone_species", mode="before")
    @classmethod
    def _coerce_list(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        return list(v)

    @field_validator("keystone_species")
    @classmethod
    def _stringify_keystone(cls, v):
        return [str(s) for s in v if s]

    @field_validator("follow_ups")
    @classmethod
    def _cap(cls, v):
        return [str(s) for s in v[:3] if s]

    @field_validator("summary", "real_world_analogue", "conservation_note", mode="before")
    @classmethod
    def _coerce_str(cls, v):
        return "" if v is None else str(v)
