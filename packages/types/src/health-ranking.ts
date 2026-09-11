/** Public-safe repository health ranking contract. */

export interface HealthRankingEntry {
  repository_id: string;
  name: string;
  url: string;
  snapshot_id: string;
  score_config_digest: string;
  overall_score: number | null;
  grade: string;
  status: string;
  dimensions: Record<string, number | null>;
  languages: string[];
  confidence: number;
  coverage: number;
  evidence_coverage: number;
  analyzed_at: string | null;
  stale: boolean;
  eligible: boolean;
  eligibility_reason: string | null;
  score_delta: number | null;
}

export interface HealthRankingQuery extends Record<string, string | number | boolean | undefined> {
  page?: number;
  limit?: number;
  band?: string;
  dimension?: string;
  language?: string;
  status?: string;
  stale?: boolean;
  eligible?: boolean;
  include_ineligible?: boolean;
}

export interface HealthRankingResponse {
  items: HealthRankingEntry[];
  page: number;
  limit: number;
  total: number;
  generated_at: string;
}

export interface HealthRankingCompareResponse {
  items: HealthRankingEntry[];
  dimensions: Record<string, Record<string, number | null>>;
  score_config_digests: string[];
  truncated: boolean;
  generated_at: string;
}

export interface HealthRankingTrendPoint {
  snapshot_id: string;
  score_config_digest: string;
  overall_score: number | null;
  grade: string;
  status: string;
  analyzed_at: string | null;
}

export interface HealthRankingTrendSeries {
  repository_id: string;
  name: string;
  points: HealthRankingTrendPoint[];
}

export interface HealthRankingTrendResponse {
  items: HealthRankingTrendSeries[];
  limit: number;
  generated_at: string;
}
