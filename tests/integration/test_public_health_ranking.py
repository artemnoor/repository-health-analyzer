from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from repowise.core.analysis.health.ranking_projection import normalize_filter
from repowise.core.persistence import init_db, upsert_repository
from repowise.core.persistence.crud.analysis.health_ranking import (
    list_health_ranking,
    publish_health_ranking,
    rebuild_health_ranking,
)
from repowise.core.persistence.models import HealthScoreProjection, RepositoryHealthSnapshot


@pytest.fixture
async def ranking_session():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    await init_db(engine)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with factory() as session:
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_ranking_rebuild_is_idempotent_and_hides_private_rows(ranking_session) -> None:
    now = datetime.now(UTC)
    public = await upsert_repository(
        ranking_session, name="public", local_path="/tmp/public", visibility="public"
    )
    private = await upsert_repository(
        ranking_session, name="private", local_path="/tmp/private", visibility="private"
    )
    for repo, score in ((public, 91), (private, 99)):
        snapshot = RepositoryHealthSnapshot(
            repository_id=repo.id,
            head_sha="b" * 40,
            analyzed_at=now,
            as_of_ts=now,
            config_digest="config",
            analyzer_versions_digest="analyzers",
            score_config_digest="score",
            scope="all",
            mode="full",
            status="pass",
            score=score,
            confidence=0.9,
            evidence_coverage=0.8,
            stale_after_ts=now + timedelta(days=1),
            diagnostics_json="{}",
        )
        ranking_session.add(snapshot)
        await ranking_session.flush()
        projection = HealthScoreProjection(
            snapshot_id=snapshot.id,
            score_config_digest="score",
            overall_score=score,
            dimensions_json='{"code": 90}',
            breakdown_json="[]",
            configured_weight=1,
            available_weight=1,
            confidence=0.9,
            coverage=1,
            evidence_coverage=0.8,
            status="pass",
            limitations_json="[]",
        )
        ranking_session.add(projection)
        await ranking_session.flush()
        await publish_health_ranking(ranking_session, repo.id, snapshot, projection, now=now)
    await ranking_session.commit()

    assert await rebuild_health_ranking(ranking_session, now=now) == 2
    await ranking_session.commit()
    rows, total = await list_health_ranking(
        ranking_session,
        ranking_filter=normalize_filter(),
        now=now,
    )
    assert total == 1
    assert rows[0]["name"] == "public"
    assert rows[0]["overall_score"] == 91
