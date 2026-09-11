"use client";

import { useState } from "react";
import { AlertTriangle, CheckCircle2, CircleHelp, ShieldCheck } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@repowise-dev/ui/ui/card";
import type { CanonicalHealthReport } from "@repowise-dev/types/health";
import { SIGILS_HEALTH_PANELS } from "@/lib/health-panels/sigils";

function pct(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function statusIcon(status: string) {
  if (status === "pass") return <CheckCircle2 className="h-4 w-4 text-[var(--color-success)]" aria-hidden />;
  if (status === "error" || status === "fail") return <AlertTriangle className="h-4 w-4 text-[var(--color-danger)]" aria-hidden />;
  return <CircleHelp className="h-4 w-4 text-[var(--color-warning)]" aria-hidden />;
}

export function CanonicalHealthSummary({
  data,
  loadEvidence,
}: {
  data?: CanonicalHealthReport;
  loadEvidence: () => Promise<CanonicalHealthReport>;
}) {
  const [detailed, setDetailed] = useState<CanonicalHealthReport>();
  const [loadingEvidence, setLoadingEvidence] = useState(false);
  const report = detailed ?? data;

  if (!report) return null;

  const snapshot = report.snapshot;
  const findings = report.recommendations.slice(0, 5);
  const loadFullEvidence = async () => {
    if (detailed || loadingEvidence) return;
    setLoadingEvidence(true);
    try {
      setDetailed(await loadEvidence());
    } finally {
      setLoadingEvidence(false);
    }
  };

  return (
    <Card className="mb-4">
      <CardHeader className="pb-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-[var(--color-accent-primary)]" aria-hidden />
            <CardTitle className="text-sm">Persisted health evidence</CardTitle>
          </div>
          <div className="flex items-center gap-2 text-xs text-[var(--color-text-secondary)]">
            {statusIcon(snapshot.status)}
            <span className="capitalize">{snapshot.status}</span>
            <span>·</span>
            <span>{snapshot.score == null ? "Unknown score" : `${snapshot.score.toFixed(1)}/10`}</span>
          </div>
        </div>
        <p className="text-xs text-[var(--color-text-tertiary)]">
          Read model: {snapshot.id.slice(0, 8)} · confidence {pct(snapshot.confidence)} · scope {snapshot.scope}
          {snapshot.is_stale ? " · stale" : ""}
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-2 sm:grid-cols-4">
          <Stat label="Evidence" value={pct(snapshot.evidence_coverage)} />
          <Stat label="Metrics" value={String(report.coverage.metric_count)} />
          <Stat label="Risks" value={String(report.recommendations.length)} />
          <Stat label="Criticality" value={pct(report.criticality.score)} />
        </div>

        {report.dimensions.length > 0 ? (
          <div>
            <p className="mb-2 text-[10px] font-medium uppercase tracking-[0.12em] text-[var(--color-text-tertiary)]">
              Dimensions
            </p>
            <div className="grid gap-2 sm:grid-cols-3">
              {report.dimensions.map((dimension) => (
                <div key={`${dimension.dimension}:${dimension.name}`} className="rounded-md border border-[var(--color-border-default)] px-3 py-2">
                  <div className="flex items-center justify-between gap-2 text-xs">
                    <span className="truncate text-[var(--color-text-secondary)]">{dimension.dimension}</span>
                    <span className="font-mono tabular-nums text-[var(--color-text-primary)]">
                      {dimension.score == null ? "?" : dimension.score.toFixed(1)}
                    </span>
                  </div>
                  <div className="mt-1 text-[10px] text-[var(--color-text-tertiary)]">
                    evidence {pct(dimension.evidence_coverage)} · unknown {dimension.unknown_count} · errors {dimension.error_count}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : null}

        {findings.length > 0 ? (
          <div>
            <p className="mb-2 text-[10px] font-medium uppercase tracking-[0.12em] text-[var(--color-text-tertiary)]">
              Top risks and recommendations
            </p>
            <div className="space-y-1.5">
              {findings.map((finding) => (
                <details key={finding.recommendation_id} className="rounded-md border border-[var(--color-border-default)] px-3 py-2">
                  <summary className="cursor-pointer list-none text-xs text-[var(--color-text-primary)]">
                    <span className="mr-2 uppercase text-[10px] text-[var(--color-text-tertiary)]">{finding.severity}</span>
                    {finding.subject} <span className="text-[var(--color-text-tertiary)]">· priority {finding.priority.toFixed(2)}</span>
                  </summary>
                  <p className="mt-2 text-xs text-[var(--color-text-secondary)]">{finding.reason}</p>
                  <p className="mt-1 text-[10px] text-[var(--color-text-tertiary)]">
                    evidence {finding.evidence.count} · {finding.evidence.locations.length} location(s) · {finding.evidence.raw_refs.length} raw ref(s)
                  </p>
                  {detailed ? (
                    <div className="mt-2 space-y-1 border-t border-[var(--color-border-default)] pt-2 text-[10px] text-[var(--color-text-tertiary)]">
                      {(finding.evidence.refs ?? []).map((ref, index) => (
                        <div key={`${ref.raw_ref ?? ref.source}:${index}`}>
                          {ref.source} · {ref.path ?? "no path"}
                          {ref.line_start != null ? `:${ref.line_start}` : ""}
                          {ref.raw_ref ? ` · ${ref.raw_ref}` : ""}
                        </div>
                      ))}
                    </div>
                  ) : null}
                </details>
              ))}
            </div>
            <button
              type="button"
              onClick={loadFullEvidence}
              disabled={loadingEvidence || Boolean(detailed)}
              className="mt-2 text-[10px] uppercase tracking-[0.12em] text-[var(--color-accent-primary)] disabled:opacity-50"
            >
              {detailed ? "Evidence details loaded" : loadingEvidence ? "Loading evidence…" : "Load evidence details"}
            </button>
          </div>
        ) : null}

        {report.limitations.length > 0 ? (
          <div className="rounded-md bg-[var(--color-bg-elevated)] px-3 py-2 text-xs text-[var(--color-text-secondary)]">
            {report.limitations.map((limitation) => (
              <div key={limitation.code}>• {limitation.message}</div>
            ))}
          </div>
        ) : null}

        <details className="border-t border-[var(--color-border-default)] pt-3">
          <summary className="cursor-pointer text-[10px] font-medium uppercase tracking-[0.12em] text-[var(--color-text-tertiary)]">
            Reused community signal recipes ({SIGILS_HEALTH_PANELS.length})
          </summary>
          <div className="mt-2 grid gap-2 sm:grid-cols-2">
            {SIGILS_HEALTH_PANELS.slice(0, 6).map((panel) => (
              <div key={panel.id} className="rounded-md border border-[var(--color-border-default)] px-3 py-2">
                <div className="text-xs text-[var(--color-text-primary)]">{panel.title}</div>
                <div className="mt-1 text-[10px] text-[var(--color-text-tertiary)]">
                  {panel.source} · {panel.measures.join(" · ")}
                </div>
              </div>
            ))}
          </div>
        </details>
      </CardContent>
    </Card>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md bg-[var(--color-bg-elevated)] px-3 py-2">
      <div className="text-[10px] uppercase tracking-[0.12em] text-[var(--color-text-tertiary)]">{label}</div>
      <div className="mt-1 font-mono text-sm tabular-nums text-[var(--color-text-primary)]">{value}</div>
    </div>
  );
}
