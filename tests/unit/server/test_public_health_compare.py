import json
from datetime import UTC, datetime, timedelta

import pytest

from repowise.core.persistence.crud.analysis.health_ranking import publish_health_ranking
from repowise.core.persistence.models import HealthScoreProjection, RepositoryHealthSnapshot
from tests.unit.persistence.helpers import insert_repo


@pytest.mark.asyncio
async def test_public_compare_is_bounded_and_excludes_private_rows(client, session) -> None:
    now = datetime.now(UTC)
    public_rows = []
    for index, score in enumerate((91, 72)):
        repo = await insert_repo(
            session,
            name=f"public-{index}",
            local_path=f"/tmp/public-{index}",
            visibility="public",
        )
        snapshot = RepositoryHealthSnapshot(
            repository_id=repo.id,
            head_sha=f"{index + 1:x}" * 40,
            analyzed_at=now - timedelta(minutes=index),
            as_of_ts=now - timedelta(minutes=index),
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
        session.add(snapshot)
        await session.flush()
        projection = HealthScoreProjection(
            snapshot_id=snapshot.id,
            score_config_digest="score",
            overall_score=score,
            dimensions_json=json.dumps({"code": score}),
            breakdown_json="[]",
            configured_weight=1,
            available_weight=1,
            confidence=0.9,
            coverage=1,
            evidence_coverage=0.8,
            status="pass",
            limitations_json="[]",
        )
        session.add(projection)
        await session.flush()
        await publish_health_ranking(session, repo.id, snapshot, projection, now=now)
        public_rows.append(repo)

    private = await insert_repo(
        session,
        name="private",
        local_path="/tmp/private-ranking",
        visibility="private",
    )
    await session.commit()

    response = await client.get(
        "/api/health/ranking/compare",
        params={"repo_ids": ",".join([row.id for row in public_rows] + [private.id] * 4)},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["truncated"] is True
    assert {row["repository_id"] for row in payload["items"]} == {row.id for row in public_rows}
    assert payload["score_config_digests"] == ["score"]
