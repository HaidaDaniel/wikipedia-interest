---
name: wikipedia-interest
description: Analyze audience interest in arbitrary topics across Wikipedia language editions using deterministic Wikimedia Pageviews retrieval, trend metrics, anomaly detection, evidence-quality scoring, charts and one-page PDF reports. Use when a user asks whether interest is growing, compares languages or time ranges, requests a follow-up analysis, graph, or shareable research brief. Do not use pageviews alone to claim market size, willingness to pay, conversion or product-market fit.
compatibility: Requires Python 3.12+, uv, network access to Wikimedia APIs, and a writable local workspace. Run commands from the repository root containing pyproject.toml.
metadata:
  version: "0.1.0"
  source: "Wikimedia Pageviews API"
---

# Wikipedia Interest

This repository contains an executable `wikipedia-interest` CLI. Use it for audience-research questions involving Wikipedia Pageviews, arbitrary topics/languages/date ranges, trend comparisons, charts, follow-up analyses, and one-page PDF reports.

Run commands from the repository root (the directory containing `pyproject.toml`):

```bash
uv run wikipedia-interest analyze --topic "intermittent fasting" --languages pl,cs --start 2024-09 --end 2026-09 --granularity auto --output output
```

Read the single compact JSON object from stdout. Full observations are persisted in `output/<run-id>/result.json`; do not calculate statistics yourself or inspect raw CSV rows. Use `series[].resolution`, `series[].metrics`, `series[].anomalies`, `series[].reliability`, `comparison`, and `limitations`. Mention resolution warnings, spikes, evidence quality, and `data_through` when the requested end includes an incomplete current period. Never describe Wikipedia pageviews as confirmed market demand, market size, conversion or product-market fit.

For a PDF, run `uv run wikipedia-interest report --run output/<run-id>`. For a follow-up, run `uv run wikipedia-interest inspect-run output/<run-id>` and then `uv run wikipedia-interest analyze --from-run output/<run-id> ...`. Supported criteria are `balanced`, `growth`, and `stability`; cached retrieval is local and every follow-up creates a new run.

Partial language failures remain explicit; if all languages fail, report `NO_DATA`.

See the repository root `SKILL.md`, `README.md`, and `METHODOLOGY.md` for the full workflow and caveats.
