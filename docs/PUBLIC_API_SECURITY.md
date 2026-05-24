# Public API Security

Public endpoints apply baseline rate limiting and request-size limits.
Sensitive wallet material is rejected and must not be logged or echoed.
Infrastructure-level WAF/CDN/rate limiting is still recommended.
