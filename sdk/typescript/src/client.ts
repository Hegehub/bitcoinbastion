import { normalizeConfig, type BitcoinBastionClientConfig } from "./config.js";
import { BastionHttpClient } from "./http.js";
import { AccessResource } from "./resources/access.js";
import { EvidenceResource } from "./resources/evidence.js";
import { MarketResource } from "./resources/market.js";
import { NewsResource } from "./resources/news.js";
import { OnchainResource } from "./resources/onchain.js";
import { PolicyResource } from "./resources/policy.js";
import { ProviderHealthResource } from "./resources/providerHealth.js";
import { SignalsResource } from "./resources/signals.js";
import { TraceResource } from "./resources/trace.js";
import { TreasuryResource } from "./resources/treasury.js";
import { WalletResource } from "./resources/wallet.js";
import { WebhooksResource } from "./resources/webhooks.js";
import { WebSocketResource } from "./resources/websocket.js";

export class BitcoinBastionClient {
  readonly raw: BastionHttpClient;
  readonly access: AccessResource;
  readonly signals: SignalsResource;
  readonly news: NewsResource;
  readonly onchain: OnchainResource;
  readonly trace: TraceResource;
  readonly evidence: EvidenceResource;
  readonly market: MarketResource;
  readonly treasury: TreasuryResource;
  readonly policy: PolicyResource;
  readonly wallet: WalletResource;
  readonly providerHealth: ProviderHealthResource;
  readonly webhooks: WebhooksResource;
  readonly websocket: WebSocketResource;

  constructor(config: BitcoinBastionClientConfig) {
    const normalized = normalizeConfig(config);
    this.raw = new BastionHttpClient(normalized);
    this.access = new AccessResource(this.raw);
    this.signals = new SignalsResource(this.raw);
    this.news = new NewsResource(this.raw);
    this.onchain = new OnchainResource(this.raw);
    this.trace = new TraceResource(this.raw);
    this.evidence = new EvidenceResource(this.raw);
    this.market = new MarketResource(this.raw);
    this.treasury = new TreasuryResource(this.raw);
    this.policy = new PolicyResource(this.raw);
    this.wallet = new WalletResource(this.raw);
    this.providerHealth = new ProviderHealthResource(this.raw);
    this.webhooks = new WebhooksResource(this.raw);
    this.websocket = new WebSocketResource(normalized);
  }
}
