export type BastionEventType =
  | "news.article.created"
  | "news.article.scored"
  | "news.event.created"
  | "news.event.high_impact"
  | "signal.created"
  | "signal.published"
  | "signal.suppressed"
  | "onchain.large_transfer"
  | "onchain.watchlist_hit"
  | "onchain.fee_spike"
  | "trace.report.created"
  | "trace.risk_band.changed"
  | "trace.batch.completed"
  | "wallet.health.generated"
  | "wallet.privacy_risk.high"
  | "treasury.request.created"
  | "treasury.policy.failed"
  | "treasury.approval.required"
  | "policy.execution.failed"
  | "policy.warning.created"
  | "market.regime.changed"
  | "market.candle.attributed"
  | "provider.degraded"
  | "pipeline.lag.high"
  | "job.failed";

export interface BastionEventEnvelope<TPayload = unknown> {
  type: string;
  id: string;
  occurredAt: string;
  source: string;
  payload: TPayload;
  limitations?: string[];
  confidence?: number;
  degraded?: boolean;
  stale?: boolean;
  eventType?: BastionEventType | string;
  topic?: string;
  version?: number;
}
