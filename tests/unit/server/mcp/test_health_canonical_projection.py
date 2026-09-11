"""MCP canonical-health projection parity."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from repowise.core.persistence.models import HealthAggregate, RepositoryHealthSnapshot


@pytest.mark.asyncio
async def test_get_health_can_return_the_same_persisted_canonical_shape(
    setup_mcp, session
) -> None:
    as_of = datetime(2026, 9, 10, 12, tzinfo=UTC)
    snapshot = RepositoryHealthSnapshot(
        repository_id=setup_mcp,
        head_sha="b" * 40,
        analyzed_at=as_of,
        as_of_ts=as_of,
        config_digest="config-mcp",
        analyzer_versions_digest="analyzers-mcp",
        score_config_digest="score-mcp",
        scope="all",
        mode="full",
        status="pass",
        score=9.1,
        confidence=1.0,
        evidence_coverage=1.0,
        criticality=0.4,
        diagnostics_json=json.dumps({"source_order": "raw-normalized-derived"}),
    )
    session.add(snapshot)
    await session.flush()
    session.add(
        HealthAggregate(
            snapshot_id=snapshot.id,
            score_config_digest="score-mcp",
            scope="all",
            dimension="repowise",
            name="repowise.health",
            value=9.1,
            score=9.1,
            evidence_coverage=1.0,
            criticality=0.4,
            provenance_json="[]",
        )
    )
    await session.commit()

    from repowise.server.mcp_server import get_health

    output = await get_health(
        include=["canonical"],
        only=["canonical"],
        snapshot_id=snapshot.id,
        include_evidence=True,
    )
    assert output["mode"] == "canonical"
    assert output["canonical"]["snapshot"]["id"] == snapshot.id
    assert output["canonical"]["snapshot"]["score"] == 9.1
    assert output["canonical"]["meta"]["score_recomputed"] is False
