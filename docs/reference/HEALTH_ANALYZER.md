# Health Analyzer reference

## Analyzer IDs

| ID | Dimension(s) | Source / behavior |
| --- | --- | --- |
| `repowise.health` | code, history, performance | Copied RepoWise biomarkers, Git history, churn/hotspots, ownership and defect context |
| `scorecard.local` | security, delivery, repository-hygiene | OpenSSF Scorecard JSON checks and evidence |
| `repohealth.baseline` | repository-hygiene, documentation, delivery | RepoHealth deterministic baseline checks |
| `criticality.importance` | criticality | OpenSSF Criticality Score; stored separately from health |
| `qlty.check` | code-quality, security, tests | Qlty SARIF/rdjson/plugin result boundary |
| `sokrates.analysis` | code-quality, architecture | Sokrates measures and exported analysis JSON |
| `forge.metadata` | repository-hygiene, documentation, architecture | RepoCrunch repository/language/tree/branch metadata |
| `forge.community` | community, issues, maintenance | RepoCrunch contributors and community signals |
| `chaoss.activity` | community, history | CollectOSS/Perceval activity metric rows |
| `chaoss.issues_prs` | issues, delivery | Forge issue and pull-request metrics |
| `chaoss.releases` | delivery | Release cadence and release evidence |
| `chaoss.dependencies` | dependencies | Dependency activity and libyear-style facts |
| `graal.external_tools` | code-quality, security | Copied GrimoireLab Graal external analyzer rows |
| `events.temporal` | history, maintenance | UTC/as-of event enrichment |
| `identity.enrichment` | community, ownership | SortingHat-style aliases and contributor identity facts |
| `dependencies.enrichment` | dependencies | Manifest parser and dependency facts |

## Status semantics

| Status | Meaning | Gate behavior |
| --- | --- | --- |
| `pass` | Evidence supports the configured check | Does not fail the default CI gate |
| `warn` | Check ran and found a bounded risk | Visible; policy may promote it in a repository-specific gate |
| `fail` | Check ran and violated a configured gate | Fails the default CI gate |
| `skipped` | Capability, permission or mode does not allow collection | Visible skip; never treated as pass or zero |
| `inconclusive` | Collection ran but denominator/data is insufficient | Visible limitation; no fabricated score |
| `error` | Process, parser or provider boundary failed | Visible diagnostic; unrelated analyzers survive |

The default policy is encoded in `config/analyzers/native-tools.yaml`:
only `fail` exits the health gate. `scripts/check_health_gate.py` always logs
`skipped`, `inconclusive` and `error` counts.

## Evidence and scoring rules

Each metric/finding can carry source, pinned source commit, tool version, path,
line range, JSON pointer, snippet hash, collection time and confidence. The
canonical projection always includes evidence counts and locations; full raw
references are opt-in.

Absence is `null` or an explicit non-pass status, not numeric zero. Code rollups
use the persisted denominator/NLOC information; temporal metrics use their
declared window; criticality is only a priority context. Sorting is deterministic
by dimension, severity, subject and stable ID.

## Repository score and public ranking

The repository-level score is a versioned weighted mean of eight normalized
health dimensions: code, history, tests, dependencies, security, delivery,
community and docs. The default weights are 25%, 15%, 15%, 10%, 15%, 10%, 5%
and 5%; the denominator includes only measured dimensions. Every score carries
the SHA-256 digest of this policy and an explainable dimension breakdown.
Criticality is stored and displayed separately as importance, not added to
health.

The public read model is rebuilt from committed snapshots and is intentionally
smaller than the canonical per-repository report:

```bash
curl 'http://localhost:8000/api/health/ranking?limit=50'
curl 'http://localhost:8000/api/health/ranking?band=good&language=python'
curl 'http://localhost:8000/api/health/ranking/compare?repo_ids=<id>,<id>'
curl 'http://localhost:8000/api/health/ranking/trend?repo_ids=<id>&limit=12'
```

Rows become eligible only when visibility is public, the snapshot mode is
rankable, the analysis is fresh and evidence coverage is at least 0.5. Ties
sort by score, evidence coverage, freshness, case-folded name and repository
ID. `include_ineligible=true` is an explicit diagnostic view; it may show why
a row is not ranked, but still never returns local paths or raw payload refs.

## CLI

```bash
repowise health . --format table --health-mode full
repowise health . --format json --health-mode full --explain
repowise health . --format json --health-mode diff --scope production
repowise health . --format md --dimension security --subject workflow
repowise health . --trend
repowise health-batch --all --concurrency 2 --resume
```

Modes:

- `fast` — low-cost local analysis and recent history;
- `full` — all enabled local analyzers and complete configured history;
- `offline` — no Forge network collection;
- `diff` — changed files and declared dependent/blast-radius scope;
- `backfill` — historical replay and materialization.

`--as-of 2026-01-01T00:00:00Z` fixes the temporal boundary for replay. The
snapshot is also bound to HEAD and the configuration digest.

## REST and MCP

Canonical REST projection:

```bash
curl 'http://localhost:8000/api/repos/<repo_id>/health/canonical?scope=production&include_evidence=false'
curl 'http://localhost:8000/api/repos/<repo_id>/health/canonical?dimension=security&severity=high&include_evidence=true'
```

MCP `get_health` supports `include=["canonical"]` or
`only=["canonical"]` and the same `snapshot_id`, `dimension`, `status`,
`severity`, `subject`, `window` and `include_evidence` filters. CLI, REST and
MCP read the same persisted canonical snapshot rather than rerunning detectors.

## Troubleshooting

- Missing executable: run `make build-native`; inspect `bin/` and
  `config/analyzers/native-tools.yaml`.
- `skipped` Forge results: verify provider capability/permission and inspect
  the bounded limitation; use `--health-mode offline` when network collection
  is intentionally unavailable.
- `inconclusive`: inspect denominator and window coverage; do not replace it
  with zero.
- Stale data: compare `collected_at`, `stale_after_seconds` and the snapshot
  source runs; rerun full mode or use backfill.
- Persistence/replay issue: run `make health-replay`, then inspect only the
  redacted diagnostics emitted by `scripts/verify_health_stack.py`.
- Ranking projection issue: run `make health-completion`, then rebuild the
  materialized rows from committed snapshots. A stale or low-evidence row is
  intentionally visible as not ranked; do not turn that state into a score.
- UI dependencies absent: run `npm ci`, then `npm run type-check --workspace packages/web`.
