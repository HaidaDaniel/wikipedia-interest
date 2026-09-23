---
name: wikipedia-interest
description: Analyze audience interest in arbitrary topics across Wikipedia language editions using deterministic Wikimedia Pageviews retrieval, trend metrics, anomaly detection, evidence-quality scoring, charts and one-page PDF reports. Use when a user asks whether interest is growing, compares languages or time ranges, requests a follow-up analysis, graph, or shareable research brief. Do not use pageviews alone to claim market size, willingness to pay, conversion or product-market fit.
compatibility: Requires Python 3.12+, uv, network access to Wikimedia APIs, and a writable local workspace. Run commands from the skill root.
metadata:
  version: "0.1.0"
  source: "Wikimedia Pageviews API"
---

# Wikipedia Interest

Use this skill for questions such as “is interest in astronomy growing in Ukrainian Wikipedia?”, “compare intermittent fasting in Polish and Czech Wikipedia”, or “give me a one-page report for language-learning research”. The CLI resolves a conceptual topic into concrete Wikipedia articles and performs all calculations deterministically.

## Fixed workflow

1. Convert the request into `topic`, comma-separated `languages`, inclusive `start` and `end`, and optional `criterion` (`balanced`, `growth`, or `stability`). Use `monthly` for roughly annual or longer windows; `auto` chooses monthly above 180 days.
2. Run:

   ```bash
   uv run wikipedia-interest analyze --topic "intermittent fasting" --languages pl,cs --start 2024-09 --end 2026-09 --granularity auto --output output
   ```

3. Read the single JSON object on stdout. Do not inspect `data.csv` to calculate metrics. Use `series[].resolution`, `series[].metrics`, `series[].anomalies`, `series[].reliability`, `comparison`, and `limitations`.
4. Mention resolution warnings and evidence quality. Describe outputs as “interest signal” or “worth further validation”, never as confirmed market demand.
5. For a human-shareable brief, run `uv run wikipedia-interest report --run output/<run-id>`. For a short follow-up context, run `uv run wikipedia-interest inspect-run output/<run-id>`.

## Output contract

Successful `analyze` output has `status`, `run_id`, `request`, `series`, `comparison`, `limitations`, and `artifacts`. Each successful series contains `language`, `project`, `article`, `resolution`, `metrics`, `reliability`, `anomalies`, and compact `observations`. `metrics.trend_label` is one of `growing`, `declining`, `flat`, or `uncertain`; `reliability.level` is `high`, `medium`, or `low`. The reliability score is evidence quality, not a confidence interval.

Errors are JSON on stdout with `status: "error"` and `error.code`; logs go to stderr. Useful codes include `INVALID_DATE_RANGE`, `ARTICLE_NOT_FOUND`, `NO_DATA`, `WIKIMEDIA_API_ERROR`, and `INSUFFICIENT_DATA`.

## Follow-ups and assumptions

- “Now exclude the March spike”: inspect the run, then re-run with a changed date range or a future explicit exclusion rule; do not manually alter JSON.
- “Compare the last 12 months”: `analyze --from-run output/<run-id> --start YYYY-MM --end YYYY-MM`.
- “Add Slovak”: `analyze --from-run output/<run-id> --languages pl,cs,sk`.
- “Prioritize stable interest”: `analyze --from-run output/<run-id> --criterion stability`.

`--from-run` reuses the prior request fields and the filesystem cache but always creates a new run directory. Cached retrieval is keyed by project, article, access, agent, granularity and date range.

## Interpretation guardrails

Always distinguish absolute article attention, growth dynamics and evidence quality. Cross-language totals are not market size because editions differ in audience, coverage, naming and traffic mix. A spike, unresolved/low-confidence article, incomplete periods or `uncertain` trend must be stated. Recommend external validation such as interviews, search demand, product analytics or conversion research before product decisions.

For implementation details, see `METHODOLOGY.md`; for the exact project design, see `PLAN.md`.

