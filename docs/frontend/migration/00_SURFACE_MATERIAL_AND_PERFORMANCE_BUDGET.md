# Surface Material and Performance Budget

Roles (`shell`, `panel`, `reading`, `critical`) and finishes (`clear`, `frosted/matte`, `solid`) are independent. Values are verification ranges, not committed CSS. Warm-white/graphite/true-black and Bitcoin Orange `#F7931A` are brand colors; green/red/amber/purple are semantic only. Blue/cyan is not generic brand/info UI.

| Screen / zone | Current opacity estimate | Role → finish | Density / contrast | Candidate blur, opacity, saturation | Risks/fallback/mobile budget/evidence |
|---|---:|---|---|---|---|
| Global shell/nav | unknown; audit in Prompt 9 | shell → clear/matte | sparse; WCAG AA | 8–14px, .72–.88, 100–115% | one blur depth; solid warm graphite reduced-transparency; ≤20% blurred viewport; screenshots both sizes |
| Overview hero/living geometry | unknown | panel → frosted/matte | sparse topology; AA | 10–18px, .62–.80, 105–120% | geometry conveys freshness; static/solid on motion/transparency/low-power; ≤25% area |
| Overview reading/status | unknown | reading/critical → solid | text/status dense; AA/AAA target | 0px, .94–1, 100% | no haze; mobile full-width; field/contrast browser assertions |
| Operations topology | unknown | panel → matte | medium living topology; AA | 8–14px, .72–.86, 100–110% | cap animated nodes, static low power; ≤20% area |
| Operations tables/errors | unknown | reading/critical → solid | dense; AA | 0px, .96–1 | no backdrop filter; horizontal semantics not color-only |
| Market ambient/header | unknown | panel → matte | sparse; AA | 8–12px, .74–.88 | pause background when hidden; ≤15% area |
| Market candles/axes/tables/tooltips | unknown | reading/critical → solid | very dense; AA | 0px, .97–1 | canvas/SVG dependency gated; table alternative; 30fps low-power ceiling |
| Trace graph surround | unknown | panel → matte | topology; AA | 8–14px, .70–.84 | node labels stay solid; static graph/text alternative; ≤20% area |
| Trace warnings/input/disagreement | unknown | critical/reading → solid | dense/safety; AA/AAA | 0px, .97–1 | never obscure limitations; keyboard graph alternative |
| Evidence flow surround | unknown | panel → matte | sparse chain; AA | 8–14px, .72–.86 | reduced motion removes flow; ordered-list fallback |
| Evidence proofs/export/verification | unknown | critical/reading → solid | dense hashes; AA | 0px, .98–1 | safe copy classification; wrap/mobile scroll |

No nested backdrop filters at the same depth. Total blur area, long-task rate, frame rate, memory and battery proxy are captured at 1440×900 and 430×932. Unsupported browser, reduced transparency and low-power modes use solid warm-neutral surfaces without loss of hierarchy.

No visualization dependency is added here. Approval requires need/vanilla alternative, SPDX/license and maintainer review, lock integrity/SBOM, CSP (`unsafe-eval`/dynamic script/unsafe HTML forbidden), SSR/export behavior, bundle/runtime measurement, feature flag and removal test.
