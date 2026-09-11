import json
from datetime import UTC, datetime

import pytest

from repowise.core.persistence.models import HealthScoreProjection, RepositoryHealthSnapshot
from repowise.server.routers.code_health.canonical import build_canonical_health_report
from tests.unit.persistence.helpers import insert_repo


@pytest.mark.asyncio
async def test_canonical_reads_the_materialized_score_projection(session) -> None:
    repo = await insert_repo(session, name="projected-health")
    as_of = datetime(2026, 9, 10, tzinfo=UTC)
    snapshot = RepositoryHealthSnapshot(
        repository_id=repo.id,
        head_sha="a" * 40,
        analyzed_at=as_of,
        as_of_ts=as_of,
        config_digest="config",
        analyzer_versions_digest="analyzers",
        score_config_digest="score",
        scope="all",
        mode="full",
        status="warn",
        score=73,
        confidence=0.8,
        evidence_coverage=0.7,
        diagnostics_json="{}",
    )
    session.add(snapshot)
    await session.flush()
    session.add(
        HealthScoreProjection(
            snapshot_id=snapshot.id,
            score_config_digest="score",
            overall_score=73,
            dimensions_json=json.dumps({"code": 73, "security": None}),
            breakdown_json=json.dumps([{"dimension": "code", "score": 73}]),
            configured_weight=1,
            available_weight=0.25,
            confidence=0.8,
            coverage=0.25,
            evidence_coverage=0.7,
            status="warn",
            limitations_json=json.dumps([]),
            score_recomputed=True,
        )
    )
    await session.commit()

    payload = await build_canonical_health_report(session, repo.id, snapshot_id=snapshot.id)

    assert payload is not None
    assert payload["score_projection"]["overall_score"] == 73
    assert payload["meta"]["score_recomputed"] is True
    assert {row["dimension"] for row in payload["dimensions"]} == {"code", "security"}
