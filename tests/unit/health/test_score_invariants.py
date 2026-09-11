from datetime import UTC, datetime, timedelta

from repowise.core.analysis.health.composite import compose_health_score
from repowise.core.analysis.health.integrations.contracts import (
    AnalyzerResult,
    AnalyzerStatus,
    EvidenceRef,
)
from repowise.core.analysis.health.ranking_projection import (
    RankingCandidate,
    evaluate_eligibility,
    rank_candidates,
)


def _result(
    analyzer_id: str,
    score: float | None,
    dimension: str | None,
    *,
    status: AnalyzerStatus = AnalyzerStatus.PASS,
    evidence: bool = True,
) -> AnalyzerResult:
    refs = (
        (
            EvidenceRef(
                source="fixture",
                source_commit="head",
                collected_at=datetime(2026, 9, 10, tzinfo=UTC),
            ),
        )
        if evidence
        else ()
    )
    return AnalyzerResult(
        analyzer_id=analyzer_id,
        analyzer_version="fixture-v1",
        status=status,
        score=score,
        score_dimension=dimension,
        evidence=refs,
        available_weight=1 if score is not None else 0,
        total_weight=1,
    )


def _candidate(repository_id: str, name: str, score: float | None, **overrides) -> RankingCandidate:
    values = dict(
        repository_id=repository_id,
        name=name,
        url="https://example.test/" + repository_id,
        visibility="public",
        snapshot_id="snapshot-" + repository_id,
        score_config_digest="config-v1",
        overall_score=score,
        status="pass",
        dimensions={"code": score},
        languages=("python",),
        confidence=0.9,
        coverage=0.9,
        evidence_coverage=0.9,
        analyzed_at=datetime(2026, 9, 10, tzinfo=UTC),
        mode="full",
        eligible=score is not None,
    )
    values.update(overrides)
    return RankingCandidate(**values)


def test_scores_stay_bounded_and_improve_monotonically_with_a_dimension() -> None:
    low = compose_health_score([_result("fixture.code", 15, "code")])
    high = compose_health_score([_result("fixture.code", 85, "code")])

    assert low.overall is not None and 0 <= low.overall <= 100
    assert high.overall is not None and 0 <= high.overall <= 100
    assert high.overall > low.overall


def test_missing_data_is_neutral_and_not_a_measured_zero() -> None:
    measured = compose_health_score([_result("fixture.code", 80, "code")])
    with_missing = compose_health_score(
        [
            _result("fixture.code", 80, "code"),
            _result("fixture.tests", None, "tests", status=AnalyzerStatus.SKIPPED, evidence=False),
        ]
    )

    assert with_missing.overall == measured.overall
    assert with_missing.dimensions["tests"] is None
    assert with_missing.status is AnalyzerStatus.WARN


def test_criticality_is_not_allowed_to_change_health() -> None:
    health = compose_health_score([_result("fixture.code", 80, "code")])
    with_criticality = compose_health_score(
        [
            _result("fixture.code", 80, "code"),
            _result("criticality.importance", 100, "priority"),
        ]
    )
    assert with_criticality.overall == health.overall
    assert "priority" not in with_criticality.dimensions


def test_stale_and_low_evidence_rows_cannot_rank_as_healthy() -> None:
    now = datetime(2026, 9, 11, tzinfo=UTC)
    fresh = _candidate("fresh", "Fresh", 90)
    stale = _candidate("stale", "Stale", 99, analyzed_at=now - timedelta(days=31))
    thin = _candidate("thin", "Thin", 99, evidence_coverage=0.2)

    assert evaluate_eligibility(fresh, now=now).eligible
    assert not evaluate_eligibility(stale, now=now).eligible
    assert not evaluate_eligibility(thin, now=now).eligible


def test_ordering_and_pagination_are_deterministic_under_ties() -> None:
    candidates = [
        _candidate("b", "Beta", 80),
        _candidate("a", "Alpha", 80),
        _candidate("c", "Gamma", 70),
    ]
    first_page, total = rank_candidates(candidates, page=1, limit=1)
    second_page, _ = rank_candidates(candidates, page=2, limit=1)

    assert total == 3
    assert first_page[0].repository_id == "a"
    assert second_page[0].repository_id == "b"
