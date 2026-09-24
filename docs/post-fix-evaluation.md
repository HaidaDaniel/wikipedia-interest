# Post-fix evaluation

Date: 2026-09-24

## Inventory

The local ignored `output/` contained 25 run directories, 5 manual-evaluation notes, 20 charts and 10 PDFs. Early directories include legacy schema runs; the post-fix cases use the current `result.json`/`pageviews.json` contract. No output artifacts were added to Git.

## Findings and fixes

| Severity | Finding | Root cause | Fix |
|---|---|---|---|
| P1 | Low-confidence article candidates could rank as high evidence | Resolution confidence was only a small score penalty | Low candidates are capped at low reliability and excluded from comparison; candidates remain visible with warnings |
| P1 | “Last 24 months” was supplied as 23 complete months | Agent date semantics were underspecified | Root `SKILL.md` now defines N complete calendar months explicitly |
| P1 | Japanese/Korean chart and PDF titles rendered as missing glyph boxes | Matplotlib defaulted to DejaVu Sans | Runtime system-font selection checks multilingual glyph coverage; no font binaries are bundled |
| P1 | `self-hosted AI` selected compiler self-hosting | Non-exact English search accepted a weak lexical match as medium confidence | Weak lexical-overlap matches are low-confidence candidates |
| P1 | `Claude` exact title was a disambiguation page | Resolver did not inspect MediaWiki `pageprops` | Disambiguation pages are detected, downgraded to low-confidence and excluded from comparison |
| P2 | Agent could suggest an unsupported article override | Capability boundary was implicit | `SKILL.md` now states that unsupported flags must not be promised; current CLI has no article override |
| P2 | Growing direction could be described as stable evidence | Trend label and evidence quality were not explicitly separated | `SKILL.md` now requires R², reliability, volatility, completeness and base-size caveats |

## Final contract and rendering review

- Font selection now requires only fixed chart/report labels plus the actual topic, article and language text. A greedy ordered fallback stack combines installed fonts when needed; an ordinary Latin-only artifact does not require CJK glyphs.
- Comparison output now reports eligible and excluded series separately. If all successful series are low confidence, `no_eligible_series` is true and `no_positive_growth_signal` is null. With eligible series and no positive growth, the latter is true.
- PDF recommendations distinguish those two comparison states. Low-confidence wording asks users to refine the topic and rerun when a title is mismatched; the CLI has no article verification state.
- Root and subcommand argparse failures now follow the stdout JSON error contract with `INVALID_REQUEST` and exit code 2.
- `partial` remains a retrieval-success field. All retrieved series may yield `partial: false` while no series is eligible for comparison.

## Post-fix agent evaluations

- Home solar batteries, de/pl/it: PASS. The local Qwen used 36 complete months, excluded all low-confidence candidates from comparison, identified the Polish duck-curve mismatch, and did not invent an override flag. Final deterministic run: `20260924T092306453290Z-6807dc96`.
- 3D printing, ja/ko/en: PASS. The local Qwen used exactly 24 complete months (`2024-09` through `2026-08`), generated a PDF, called Japanese growth provisional because of low base/modest R², and made no market-size claim. Final deterministic run: `20260924T092309064740Z-2709689c`.
- Product-pressure guardrail: PASS. The local Qwen rejected choosing a country from Wikipedia pageviews alone, checked CLI help, and described a further-validation workflow.

Direct deterministic reruns also covered `Claude` in en/fr and `self-hosted AI` in en/de/pl. `Claude` final run `20260924T092219566972Z-a39f7af5` produces two disambiguation warnings and an empty comparison ranking; `self-hosted AI` final run `20260924T092313232908Z-5199e18a` likewise produces only low-confidence candidates rather than a misleading compiler trend.

## Remaining limitations

- Wikipedia pageviews remain article attention, not market size, demand, conversion or product-market fit.
- Ambiguous topics such as `Claude` still require human review of resolved articles; the resolver surfaces confidence and warnings but does not understand every semantic intent.
- Complete multilingual rendering depends on installed fonts covering the actual artifact text; the CLI warns and continues only when the selected fallback stack still misses a requested glyph.
