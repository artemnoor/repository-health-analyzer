"""Public-safe health ranking response models."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class HealthRankingEntryResponse(BaseModel):
    repository_id: str
    name: str
    url: str = ""
    snapshot_id: str
    score_config_digest: str
    overall_score: float | None = None
    grade: str
    status: str
    dimensions: dict[str, float | None] = Field(default_factory=dict)
    languages: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    coverage: float = 0.0
    evidence_coverage: float = 0.0
    analyzed_at: datetime | None = None
    stale: bool = False
    eligible: bool = False
    eligibility_reason: str | None = None
    score_delta: float | None = None


class HealthRankingResponse(BaseModel):
    items: list[HealthRankingEntryResponse] = Field(default_factory=list)
    page: int = 1
    limit: int = 50
    total: int = 0
    generated_at: datetime


class HealthRankingCompareResponse(BaseModel):
    items: list[HealthRankingEntryResponse] = Field(default_factory=list)
    dimensions: dict[str, dict[str, float | None]] = Field(default_factory=dict)
    score_config_digests: list[str] = Field(default_factory=list)
    truncated: bool = False
    generated_at: datetime


class HealthRankingTrendPointResponse(BaseModel):
    snapshot_id: str
    score_config_digest: str
    overall_score: float | None = None
    grade: str
    status: str
    analyzed_at: datetime | None = None


class HealthRankingTrendSeriesResponse(BaseModel):
    repository_id: str
    name: str
    points: list[HealthRankingTrendPointResponse] = Field(default_factory=list)


class HealthRankingTrendResponse(BaseModel):
    items: list[HealthRankingTrendSeriesResponse] = Field(default_factory=list)
    limit: int = 12
    generated_at: datetime


__all__ = [
    "HealthRankingCompareResponse",
    "HealthRankingEntryResponse",
    "HealthRankingResponse",
    "HealthRankingTrendPointResponse",
    "HealthRankingTrendResponse",
    "HealthRankingTrendSeriesResponse",
]
