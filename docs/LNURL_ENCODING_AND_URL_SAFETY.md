# LNURL Encoding and URL Safety

A valid LNURL checksum does not make the decoded URL trusted. The checksum only proves that the Bech32 string was transcribed consistently; it does not prove domain ownership, HTTPS safety, callback legitimacy, settlement, wallet identity, or authorization.

## Supported input forms

The LNURL boundary accepts lowercase or uppercase `lnurl1...` values and the optional `lightning:lnurl1...` URI wrapper. Mixed-case Bech32 values are rejected. Bastion uses the original LNURL Bech32 checksum profile, not Bech32m.

## URL validation

Every encoded or decoded URL must pass the central `LNURLURLPolicy` validator before use. Production policies require HTTPS by default, reject embedded credentials, reject fragments, reject control characters, and preserve path/query semantics without trusting query values.

## Onion and development exceptions

Plain HTTP is allowed only for explicit Tor v3 `.onion` policies or explicit development policies. Deprecated v2 onion names and arbitrary public HTTP URLs are rejected.

## Service-owned domains

Service-owned LNURL-auth, callback, pay, and withdraw URLs use exact normalized host allowlists. Suffix tricks such as `evil-bitcoin-bastion.com` or `bitcoin-bastion.com.attacker.example` are not accepted. Stable LNURL-auth domain policy rejects unexpected host, scheme, or port changes.

## IDNA and host normalization

Hostnames are lowercased and normalized to ASCII with IDNA before policy comparison. Malformed names, empty labels, URL credentials, loopback/private/link-local literals, and ambiguous IPv6 zone identifiers are rejected for production remote-fetch policies.

## SSRF and DNS rebinding protections

The pure decoder never performs DNS or HTTP requests. Network clients must use the injectable resolver contract: validate URL, resolve all A/AAAA records, reject if any result is private/loopback/link-local/reserved, connect only to an approved address, verify the connected peer address where possible, and revalidate every redirect. Empty DNS answers fail closed.

## Redirect validation

Redirect targets pass through the same URL validator. HTTPS-to-HTTP downgrades are rejected except under explicit onion/development policy, and service-owned stable auth redirects cannot silently leave the configured auth domain.

## Sensitive query redaction

Sensitive parameters such as `k1`, `sig`, `key`, `pr`, `preimage`, `payerData`, `auth`, `token`, `session_token`, `access_pass`, and `withdraw_id` are redacted in logs and model representations. Fingerprints are used for correlation without exposing raw callback URLs or encoded LNURLs.

## Size limits

The default maximum decoded URL length is 2048 UTF-8 bytes. The default maximum encoded LNURL length is 4096 characters. These limits are policy constants and may be tightened by later deployment configuration.

## Security boundaries

LNURL-auth is not Bitcoin treasury ownership proof. Lightning Address is not identity. An issued LNURL-pay invoice is not proof of settlement. This layer does not fetch URLs, verify LNURL-auth signatures, manage `k1`, issue sessions, create principals, perform withdrawals, or verify payments.

## Prohibited shortcuts

Do not trust Bech32 checksum as authorization, accept arbitrary HTTP, allow localhost/private IPs in production, log full callback URLs, follow redirects without revalidation, resolve only one DNS record, compare domains with naive suffix matching, or convert payerData/comments into authorization.
