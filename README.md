# Wikipedia Interest

Wikipedia Interest is a small Agent Skill and CLI for turning fuzzy audience-research questions into reproducible signals from Wikimedia Pageviews. An agent supplies topic, languages and dates; deterministic Python code resolves Wikipedia articles, retrieves cached data, calculates robust trends and anomalies, assesses evidence quality, and produces a chart or one-page PDF.

It is intentionally not a market-size estimator. Wikipedia attention can help choose what to validate next; it cannot prove demand, conversion, willingness to pay or product-market fit.

## Example

Natural-language request:

> Compare the growth of interest in intermittent fasting in Polish and Czech Wikipedia over the last two years and tell me which signal is more reliable.

Command:

```bash
uv run wikipedia-interest analyze \
  --topic "intermittent fasting" --languages pl,cs \
  --start 2024-09 --end 2026-09 --granularity monthly --output output
```

The command prints one JSON object and saves `output/<run-id>/result.json`, `data.csv`, `raw.json`, and `chart.png`. The agent can summarize `comparison.strongest_signal`, explain each `series[].metrics.trend_label`, and quote `series[].reliability.reasons`.

## Architecture

```text
user question
    ↓ agent maps intent to CLI flags
resolver → MediaWiki search + interlanguage links
    ↓
cached Wikimedia Pageviews → deterministic metrics/anomalies/reliability
    ↓
JSON + chart + one-page PDF → agent explanation with caveats
```

The LLM handles natural language and presentation. It does not write Python, calculate statistics, inspect a large CSV or select formulas.

## Why this works with a small agent model

The model only maps a request to a short command, then reads compact JSON fields that already contain the article, metrics, labels, anomaly notes and evidence-quality reasons. Formula choice, thresholds, caching, artifact paths and error codes are fixed in code. Follow-ups reuse `inspect-run` and `--from-run`, so the model does not need to remember a hidden state or parse hundreds of raw observations.

## Quick start

Requires Python 3.12+, `uv`, and network access for the first request.

```bash
uv sync
uv run wikipedia-interest analyze --topic astronomy --languages uk --start 2024-09 --end 2026-09
uv run wikipedia-interest report --run output/<run-id>
uv run wikipedia-interest inspect-run output/<run-id>
```

## Commands

`analyze` resolves each article, fetches daily/monthly observations, writes a reproducible run and chart, and prints stable JSON. Use `--criterion growth|stability|balanced`, `--no-cache`, or `--from-run` for a follow-up.

`report` creates `report.pdf` from the saved run without another API call.

`inspect-run` returns a compact context suitable for an agent follow-up.

## Methodology and reliability

For longer windows the default is monthly aggregation. The main trend is an annualized linear regression on `log1p(pageviews)`, paired with a rolling-smoothed trend and a 12-period YoY comparison when possible. A robust median/MAD detector marks spikes. Labels use fixed thresholds: ±10% annualized with fit/data checks. The source is the [Wikimedia Pageviews API](https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/reference/page-views.html).

Reliability means evidence quality, not statistical confidence. A transparent 0–100 heuristic rewards duration, completeness, meaningful signal, fit consistency and confident article resolution, and penalizes noise and spikes. See [METHODOLOGY.md](METHODOLOGY.md).

## Follow-up workflow

```bash
uv run wikipedia-interest inspect-run output/<run-id>
uv run wikipedia-interest analyze --from-run output/<run-id> --start 2025-09 --end 2026-09 --criterion stability
```

Every follow-up is a new run; prior pageview data remains reusable through `.cache/`.

## Validation

```bash
uv run pytest
```

The test suite covers metric direction, seasonality-aware YoY, zeros and missing periods, anomalies, reliability, resolver edge cases, JSON shape and persistence. Three real-data scenario commands are documented in [examples/README.md](examples/README.md). Network integration is intentionally manual and cache-friendly.

## Limitations

One article is an imperfect proxy for a concept. Language editions vary in population, usage, coverage, title conventions and alternative pages. Pageviews can be event-driven and seasonal; recent periods may be incomplete. This MVP does not claim causal demand and does not combine external signals.

## Roadmap

Phase 2: Wikidata concept graphs, related-page groups, normalized language-audience signals and event annotation. Phase 3: batch topics, async retrieval and ranked research briefs. Phase 4: external product analytics integration and backtesting whether pageview signals predict validated demand.

## Reviewer path

Open `SKILL.md` for agent instructions, `PLAN.md` for architecture, `METHODOLOGY.md` for formulas, `src/wikipedia_interest/cli.py` for the contract, and `examples/README.md` for real scenario commands.
