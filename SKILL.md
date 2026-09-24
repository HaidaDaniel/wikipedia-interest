---
name: wikipedia-interest
description: Analyze audience interest in arbitrary topics across Wikipedia language editions using deterministic Wikimedia Pageviews retrieval, trend metrics, anomaly detection, evidence-quality scoring, charts and one-page PDF reports. Use when a user asks whether interest is growing, compares languages or time ranges, requests a follow-up analysis, graph, or shareable research brief. Do not use pageviews alone to claim market size, willingness to pay, conversion or product-market fit.
compatibility: Requires Python 3.12+, uv, network access to Wikimedia APIs, and a writable local workspace. Run commands from the repository root containing pyproject.toml.
metadata:
  version: "0.1.0"
  source: "Wikimedia Pageviews API"
---

# Wikipedia Interest

Use this skill for questions such as “is interest in astronomy growing in Ukrainian Wikipedia?”, “compare intermittent fasting in Polish and Czech Wikipedia”, or “give me a one-page report for language-learning research”. The CLI resolves a conceptual topic into concrete Wikipedia articles and performs all calculations deterministically.

## Fixed workflow

1. Convert the request into `topic`, comma-separated `languages`, inclusive `start` and `end`, and optional `criterion` (`balanced`, `growth`, or `stability`). Use `monthly` for roughly annual or longer windows; `auto` chooses monthly above 180 days. For “last N months”, use the last N complete calendar months: set `start` to N calendar months before the current month and `end` to the current month, because the CLI excludes the current incomplete month. For example, on 2026-09-24, “last 24 months” means `--start 2024-09 --end 2026-09` and yields 2024-09 through 2026-08.
2. Run:

   ```bash
   uv run wikipedia-interest analyze --topic "intermittent fasting" --languages pl,cs --start 2024-09 --end 2026-09 --granularity auto --output output
   ```

3. Read the single compact JSON object on stdout. Full observations are persisted in `output/<run-id>/result.json`; use `--verbose-json` only when explicitly needed. Do not inspect `data.csv` to calculate metrics. Use `series[].resolution`, `series[].metrics`, `series[].anomalies`, `series[].reliability`, `comparison`, and `limitations`.
4. Mention resolution warnings and evidence quality. Describe outputs as “interest signal” or “worth further validation”, never as confirmed market demand.
5. For a human-shareable brief, run `uv run wikipedia-interest report --run output/<run-id>`. For a short follow-up context, run `uv run wikipedia-interest inspect-run output/<run-id>`.

Do not promise an article override, exclusion rule, or other operation unless the CLI help shows a supported option. This CLI has no `--article`, `--title`, or article-override flag; use the resolver warnings and a new supported request instead.

## Output contract

Successful `analyze` output has `status`, `run_id`, `request`, `series`, `comparison`, `limitations`, and `artifacts`. Each successful series contains `language`, `project`, `article`, `resolution`, `metrics`, `reliability`, and `anomalies`; full observations are in persisted `result.json`, not default stdout. `metrics.trend_label` is one of `growing`, `declining`, `flat`, or `uncertain`; `reliability.level` is `high`, `medium`, or `low`. The reliability score is evidence quality, not a confidence interval.

Errors are JSON on stdout with `status: "error"` and `error.code`; a short human-readable line goes to stderr. Argument-parser errors use `INVALID_REQUEST` and exit code 2.

Top-level error codes are `INVALID_REQUEST`, `INVALID_DATE`, `INVALID_DATE_RANGE`, `INVALID_LANGUAGES`, `INVALID_TOPIC`, `NO_DATA`, `WIKIMEDIA_API_ERROR`, and `LOCAL_ERROR`.

Per-series error codes are `ARTICLE_NOT_FOUND`, `NO_DATA`, and `WIKIMEDIA_API_ERROR`. `ARTICLE_NOT_FOUND` is a series resolution result, not a top-level error code.

## Follow-ups and assumptions

- “Now exclude the March spike”: inspect the run, then re-run with a changed date range or a future explicit exclusion rule; do not manually alter JSON.
- “Compare the last 12 months”: `analyze --from-run output/<run-id> --start YYYY-MM --end YYYY-MM`.
- “Add Slovak”: `analyze --from-run output/<run-id> --languages pl,cs,sk`.
- “Prioritize stable interest”: `analyze --from-run output/<run-id> --criterion stability`.

`--from-run` reuses the prior request fields and the filesystem cache but always creates a new run directory. Cached retrieval is keyed by project, article, access, agent, granularity and date range.

Monthly analysis excludes the current incomplete calendar month and returns `request.data_through` plus `request.partial_period_excluded`. Missing periods are `views: null, observed: false`; genuine zero observations remain `views: 0, observed: true`. If some languages fail, continue with successful series and mention `partial`, `languages_failed`, and resolution warnings. `partial` describes retrieval success: successful low-confidence series still count as retrieved even when comparison excludes them. Use `comparison.eligible_series_count`, `excluded_series_count`, and `no_eligible_series` to explain comparison eligibility. If all retrievals fail, report the machine-readable `NO_DATA` error.

Low-confidence article matches remain visible for inspection but are excluded from comparison. Refine the topic and rerun if a resolved title does not represent the intended concept; the CLI has no article verification or override state. If no series is eligible, `comparison.no_positive_growth_signal` is `null`. If eligible series exist but none shows positive growth, it is `true`. A `growing` or `declining` label describes direction only, not stability or strong evidence. Use `trend_fit_r2`, reliability, volatility, data completeness, resolution confidence and baseline size before calling a signal consistent or robust; growth from a very low base with a modest fit is provisional.

## Interpretation guardrails

Always distinguish absolute article attention, growth dynamics and evidence quality. Cross-language totals are not market size because editions differ in audience, coverage, naming and traffic mix. A spike, unresolved/low-confidence article, incomplete periods or `uncertain` trend must be stated. Recommend external validation such as interviews, search demand, product analytics or conversion research before product decisions.

For implementation details, see `METHODOLOGY.md`; for the exact project design, see `PLAN.md`.
