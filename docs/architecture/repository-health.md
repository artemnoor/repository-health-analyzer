# Repository Health Analyzer: архитектура

Repository Health Analyzer — это композиция поверх целиком скопированного
RepoWise chassis. Основные алгоритмы не переписаны: в workspace лежит pinned
RepoWise tree, а внешние движки лежат в `vendor/` и запускаются через тонкие
адаптеры.

## Границы исходников

| Слой | Реальный путь | Роль |
| --- | --- | --- |
| Product chassis | `packages/core`, `packages/server`, `packages/cli`, `packages/web` | Git index, health engine, persistence, REST/MCP/CLI/UI |
| Native source trees | `vendor/scorecard`, `vendor/repohealth`, `vendor/criticality_score`, `vendor/qlty`, `vendor/sokrates`, `vendor/sonarqube` | Security checks, baseline, importance, SARIF/plugins, code metrics and duplication primitives |
| Forge/data source trees | `vendor/repocrunch`, `vendor/collectoss`, `vendor/chaoss/*` | GitHub/Forge collection, raw events, identity, temporal and metric definitions |
| Shared configuration | `config/analyzers/*.yaml` | Source commits, modes, limits, cache and failure policy |
| Reproducibility | `vendor/SOURCES.lock`, `scripts/vendor_sources.py` | Pinned commit and copied-tree verification |
| Imported dashboard assets | `packages/web/src/data/health/sigils` | Directly copied Sigils panel recipes, not a second report model |

`vendor/SOURCES.lock` is authoritative. A source update is valid only after
changing its explicit commit, copying the new tree, running the ledger check,
running the native tests and reviewing the replay diff.

## Common execution graph

```text
repository path / Git ref / as_of_ts / config digest
                         |
                         v
                 AnalyzerContext
                         |
                         v
              registry -> planned analyzers
                 |          |          |
                 v          v          v
       RepoWise/Git   native adapters   Forge/CHAOSS adapters
                 \          |          /
                  \         v         /
                   AnalyzerResult envelope
                         |
                         v
              raw facts -> normalized facts
                         |
                         v
       immutable snapshot -> aggregates/recommendations/evidence
                         |
              +----------+-----------+
              v                      v
       canonical REST/MCP/CLI       web health views
```

Every analyzer returns `AnalyzerResult` from
`packages/core/src/repowise/core/analysis/health/integrations/contracts.py`.
The result carries status, score, metrics, findings, evidence, limitations,
duration, cache state and source versions. Native algorithms stay behind their
original JSON/SARIF/CSV boundary.

## Persistence order

`save_health_envelope` writes the source runs first, then raw facts, normalized
facts, metric values, finding evidence, aggregates and recommendations, and
finally commits the immutable `RepositoryHealthSnapshot`. Replay is idempotent
for the same repository, HEAD, `as_of_ts` and config digest. A rescore reads
persisted raw facts and changes aggregates only; it never recollects Forge,
Git or native data.

Health and criticality are intentionally separate. Criticality is an importance
and blast-radius context used to rank remediation. It is not subtracted from
the health score and a missing criticality signal is not a health score of zero.

The canonical repository score is a weighted mean of the available normalized
dimensions (`code`, `history`, `tests`, `dependencies`, `security`, `delivery`,
`community`, `docs`) on a 0–100 scale. Missing dimensions remain `null` and
remove their configured weight from the denominator; they are not zeros. The
score configuration has a digest, so replay, rescore, API, MCP, CLI and UI can
identify the exact policy that produced a number.

## Public projection

The canonical read model is built by
`packages/server/src/repowise/server/routers/code_health/canonical.py` from
persisted rows only. It is exposed at:

```text
GET /api/repos/{repo_id}/health/canonical
```

The CLI and MCP use the same projection builder. Evidence summaries are always
available; detailed evidence references require `include_evidence=true` (REST
or MCP) or `--explain` (CLI). This keeps API/UI payloads bounded and prevents
raw source or security payloads from entering normal logs.

The materialized public ranking is a separate read model in
`repository_health_ranking`. It contains only a public repository headline,
score, grade, dimensions, evidence coverage, freshness and score delta. The
default eligibility policy requires a public repository, a `fast` or `full`
snapshot, a non-stale score and at least 50% evidence coverage. Use:

```text
GET /api/health/ranking
GET /api/health/ranking/compare?repo_ids=<id>,<id>
GET /api/health/ranking/trend?repo_ids=<id>,<id>&limit=12
```

`/ranking` is the public web view. It keeps filters in the URL, shows
unavailable/stale states explicitly and never exposes `local_path` or raw
evidence. Rebuild the projection after importing old snapshots with
`rebuild_health_ranking` or the corresponding server maintenance command.

## Failure isolation and limits

`packages/core/src/repowise/core/analysis/health/integrations/process.py`
owns bounded native subprocesses: argv execution, environment allow-list,
timeout, stdout/stderr cap and redacted diagnostics. The runner converts a
missing capability to `skipped`, insufficient data to `inconclusive`, and a
failed process/parser to `error`; unrelated analyzer results remain available.
Operational caps, retry budget, cache TTL/stale policy, history tiers and CI
status policy are versioned in `config/analyzers/native-tools.yaml` and
`config/analyzers/forge.yaml`.

## Verification entry points

```bash
make vendor-verify
make build-native
make test-python
make test-native
make test-composition
make health-sample
make health-replay
make health-completion
```

The full redacted gate is `uv run python scripts/verify_health_stack.py --full`.
It verifies source provenance, migrations, native golden parsers, replay
deduplication, rescore invariants and canonical projection stability. See
`uv run python scripts/verify_health_completion.py --run-tests` for the
source-level completion gate and focused ranking matrix. See
`docs/reference/HEALTH_ANALYZER.md` for report usage and
`docs/reference/NATIVE_TOOLS.md` for source/toolchain details.
