// @vitest-environment jsdom

import * as React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { HealthRankingEntry } from "@repowise-dev/types/health-ranking";
import { RankingStatus } from "./ranking-status";
import { RankingTable } from "./ranking-table";
import { rankingFiltersFromSearch, rankingQueryForFilters } from "./filters";

vi.mock("next/link", () => ({
  default: ({ children, ...props }: React.AnchorHTMLAttributes<HTMLAnchorElement>) => (
    <a {...props}>{children}</a>
  ),
}));

afterEach(cleanup);

const entry: HealthRankingEntry = {
  repository_id: "repo-1",
  name: "healthy-api",
  url: "https://example.test/healthy-api",
  snapshot_id: "snapshot-1",
  score_config_digest: "config-1",
  overall_score: 86.5,
  grade: "B",
  status: "ready",
  dimensions: { code: 90, security: 82 },
  languages: ["TypeScript"],
  confidence: 0.92,
  coverage: 0.88,
  evidence_coverage: 0.84,
  analyzed_at: "2026-09-10T12:00:00Z",
  stale: false,
  eligible: true,
  eligibility_reason: null,
  score_delta: 1.25,
};

describe("public ranking UI", () => {
  it("renders the public score row without private repository paths", () => {
    render(<RankingTable entries={[entry]} page={1} />);

    expect(screen.getByRole("link", { name: "healthy-api" }).getAttribute("href")).toBe(
      "/repos/repo-1/code-health",
    );
    expect(screen.getByText("86.5")).toBeTruthy();
    expect(screen.getByText("B")).toBeTruthy();
    expect(screen.queryByText(/local|Users|workspace/i)).toBeNull();
  });

  it("keeps unavailable and empty ranking states explicit", () => {
    const { rerender } = render(<RankingStatus state="loading" />);
    expect(screen.getByRole("status", { name: "Loading repository ranking" })).toBeTruthy();

    rerender(<RankingStatus state="empty" />);
    expect(screen.getByText("No public health scores yet")).toBeTruthy();
  });

  it("round-trips shareable filters into the server query", () => {
    const filters = rankingFiltersFromSearch(
      "page=2&band=good&dimension=security&language=TypeScript&stale=true&include_ineligible=true",
    );
    expect(filters).toEqual({
      page: 2,
      band: "good",
      dimension: "security",
      language: "TypeScript",
      status: "",
      freshness: "stale",
      eligibility: "all",
    });
    expect(rankingQueryForFilters(filters)).toMatchObject({
      page: 2,
      band: "good",
      dimension: "security",
      language: "TypeScript",
      stale: true,
      include_ineligible: true,
    });
  });
});
