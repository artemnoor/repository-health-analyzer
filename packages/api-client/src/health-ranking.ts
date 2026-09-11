import { apiGet } from "./client";
import type {
  HealthRankingCompareResponse,
  HealthRankingQuery,
  HealthRankingResponse,
  HealthRankingTrendResponse,
} from "@repowise-dev/types/health-ranking";

export type {
  HealthRankingCompareResponse,
  HealthRankingEntry,
  HealthRankingQuery,
  HealthRankingResponse,
  HealthRankingTrendPoint,
  HealthRankingTrendResponse,
  HealthRankingTrendSeries,
} from "@repowise-dev/types/health-ranking";

export function getHealthRanking(query: HealthRankingQuery = {}): Promise<HealthRankingResponse> {
  return apiGet<HealthRankingResponse>("/api/health/ranking", query);
}

export function compareHealthRanking(repositoryIds: string[]): Promise<HealthRankingCompareResponse> {
  return apiGet<HealthRankingCompareResponse>("/api/health/ranking/compare", {
    repo_ids: repositoryIds.slice(0, 4).join(","),
  });
}

export function getHealthRankingTrend(
  repositoryIds: string[],
  limit = 12,
): Promise<HealthRankingTrendResponse> {
  return apiGet<HealthRankingTrendResponse>("/api/health/ranking/trend", {
    repo_ids: repositoryIds.slice(0, 8).join(","),
    limit,
  });
}
