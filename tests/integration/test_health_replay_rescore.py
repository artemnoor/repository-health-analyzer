from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from repowise.core.analysis.health.integrations.contracts import (
    AnalyzerContext,
    AnalyzerResult,
    AnalyzerStatus,
    EvidenceRef,
    MetricValue,
)
from repowise.core.persistence.crud import rescore_health_snapshot, save_health_envelope
from repowise.core.persistence.database import init_db
from repowise.core.persistence.models import HealthRawFact, HealthScoreProjection
from tests.unit.persistence.helpers import insert_repo


@pytest.fixture
async def async_session(tmp_path: Path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'health.db'}")
    await init_db(engine)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with factory() as session:
        yield session
    await engine.dispose()


async def test_rescore_reuses_stored_metrics_and_marks_projection_recomputed(async_session) -> None:
    repo = await insert_repo(async_session, name="rescore-health")
    as_of = datetime(2026, 9, 10, tzinfo=UTC)
    ref = EvidenceRef(source="fixture", collected_at=as_of)
    context = AnalyzerContext(
        repo_path=Path("."),
        repo_id=repo.id,
        head_sha="a" * 40,
        as_of_ts=as_of,
        capabilities=["local_scan"],
        inventory={"raw_facts": [{"source": "fixture", "event_type": "commit", "stable_event_id": "c1", "payload": {}}]},
    )
    result = AnalyzerResult(
        analyzer_id="fixture.code",
        analyzer_version="1",
        status=AnalyzerStatus.PASS,
        metrics=(MetricValue(name="code:quality", dimension="code", score=80, denominator=1, evidence_refs=(ref,)),),
        evidence=(ref,),
        available_weight=1,
        total_weight=1,
    )
    snapshot = await save_health_envelope(async_session, repo.id, context, [result])
    await async_session.commit()
    raw_before = len((await async_session.execute(select(HealthRawFact))).scalars().all())

    await rescore_health_snapshot(async_session, snapshot.id, {"weights": {"code": 1}}, score_config_digest="rescored")
    await async_session.commit()
    projection = (
        await async_session.execute(
            select(HealthScoreProjection).where(
                HealthScoreProjection.snapshot_id == snapshot.id,
                HealthScoreProjection.score_config_digest == "rescored",
            )
        )
    ).scalar_one()

    assert projection.overall_score == 80
    assert projection.score_recomputed is True
    assert len((await async_session.execute(select(HealthRawFact))).scalars().all()) == raw_before
