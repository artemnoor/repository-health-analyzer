// @vitest-environment jsdom

import * as React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import type { HealthRankingEntry } from "@repowise-dev/types/health-ranking";
import { RankingTrendChart } from "./trend-chart";
import { EntryDimensionBars, ScoreBreakdown } from "./score-breakdown";

afterEach(cleanup);

const rows: HealthRankingEntry[] = [
  {
    repository_id: "a",
    name: "alpha",
    url: "",
    snapshot_id: "s-a",
    score_config_digest: "same",
    overall_score: 91,
    grade: "A",
    status: "ready",
    dimensions: { code: 95, tests: 88 },
    languages: ["Rust"],
    confidence: 0.9,
    coverage: 0.9,
    evidence_coverage: 0.9,
    analyzed_at: null,
    stale: false,
    eligible: true,
    eligibility_reason: null,
    score_delta: 3.5,
  },
  {
    repository_id: "b",
    name: "beta",
    url: "",
    snapshot_id: "s-b",
    score_config_digest: "same",
    overall_score: 54,
    grade: "D",
    status: "partial",
    dimensions: { code: null, tests: 42 },
    languages: ["Python"],
    confidence: 0.4,
    coverage: 0.4,
    evidence_coverage: 0.35,
    analyzed_at: null,
    stale: true,
    eligible: true,
    eligibility_reason: null,
    score_delta: -2.25,
  },
];

describe("extended ranking summaries", () => {
  it("shows distribution and separates missing dimensions from zero", () => {
    render(
      <>
        <ScoreBreakdown entries={rows} />
        <EntryDimensionBars entry={rows[1]!} />
      </>,
    );
    expect(screen.getByText("Score distribution")).toBeTruthy();
    expect(screen.getByText("Dimension coverage")).toBeTruthy();
    expect(screen.getAllByText("Code quality").length).toBeGreaterThan(0);
    expect(screen.getAllByText("—").length).toBeGreaterThan(0);
  });

  it("renders score movement with direction and previous-snapshot context", () => {
    render(<RankingTrendChart entries={rows} />);
    expect(screen.getByText("Recent score movement")).toBeTruthy();
    expect(screen.getByText("vs previous published snapshot")).toBeTruthy();
    expect(screen.getByText("+3.50")).toBeTruthy();
    expect(screen.getByText("-2.25")).toBeTruthy();
  });
});
