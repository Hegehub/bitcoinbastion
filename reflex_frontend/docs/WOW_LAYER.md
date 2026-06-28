# Reflex Wow Layer

## Purpose

The wow layer provides operator-oriented visualizations for Trace, Evidence, Provider Health, Market Intelligence, Policy, Audit, and runtime posture. It is designed to improve comprehension of degraded states, provider disagreement, evidence chains, and sovereignty posture.

## Components

- Trace Radar
- Evidence Chain Viewer
- Provider Trust Matrix
- Node Pulse
- Sovereignty Score Panel
- Risk Heatmap
- Degraded Mode Banner
- Policy Simulator Preview
- Audit Replay Timeline
- Market Intelligence Wall
- Historical Similarity Lens
- Sovereign Grid Map
- API Contract Explorer
- Privacy Exposure Lens
- Citadel Mode Panel

## Data dependencies

The components use existing backend-oriented clients where available and otherwise show safe unavailable states. No fake live data is created.

## Safety language

Visible copy includes advisory-only, not legal verification, not Bitcoin consensus proof, no custody, public Bitcoin addresses only, not financial advice for market intelligence, and human operator review for policy simulation.

## Degraded and unavailable behavior

If backend data is unavailable, the route shows: "Live operational data is unavailable. This panel is displaying safe unavailable states only." Degraded, stale, fallback, partial, unavailable, and unknown states remain visible.

## Frontend-only scope

The wow layer is a Reflex-native visualization layer using lightweight chart primitives. It does not calculate final risk verdicts, market predictions, legal conclusions, or Bitcoin consensus proof.

## Backend-owned behavior

Backend services remain the source of truth for Trace analysis, Evidence packets, provider health, market intelligence, policy evaluation, audit logs, and runtime status.

## Known limitations

Some visual panels are safe placeholders until backend DTO endpoints are available. Provider matrices, evidence chains, and audit replay may be incomplete or unavailable.

## Future React/WebGL wrapper opportunities

Future prompts may add richer radar charts, heatmaps, node graphs, or timeline animations through React wrappers if they include documented package requirements, fallback states, and accessibility behavior.
