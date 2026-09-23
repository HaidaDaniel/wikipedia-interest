# Scenario examples

These are intentionally reproducible commands. They use live Wikimedia data on first run and then the local cache. Dates below are the brief's “last approximately two years” shape; change them when reproducing.

## A — intermittent fasting, Polish vs Czech

```bash
uv run wikipedia-interest analyze \
  --topic "intermittent fasting" --languages pl,cs \
  --start 2024-09 --end 2026-09 --granularity monthly
```

Expected behavior: English canonical search plus interlanguage links should resolve `pl.wikipedia` to `Post przerywany` and `cs.wikipedia` to the Czech article for the same concept. Check `resolution.warnings`; do not assume equal article coverage means equal audience size. Compare `trend_pct_per_year`, `trend_label` and `reliability`.

## B — astronomy, Ukrainian

```bash
uv run wikipedia-interest analyze \
  --topic astronomy --languages uk \
  --start 2024-09 --end 2026-09 --granularity monthly
```

Expected behavior: resolve the Ukrainian interlanguage article, return a trend label and explain whether the signal remains reliable after missing-period and spike checks.

## C — learning English, several editions + PDF

```bash
uv run wikipedia-interest analyze \
  --topic "learning English" --languages pl,uk,es,de \
  --start 2024-09 --end 2026-09 --criterion stability
uv run wikipedia-interest report --run output/<run-id>
```

“Learning English” can map to different concepts (language learning, English language, or a course). The resolver may return a low-confidence search result or warning. That ambiguity is part of the result and should be resolved before making a product decision.

## Cheap-model validation prompt

Use this prompt with a tool-capable model after placing the skill in its skill directory:

> Analyze whether interest in intermittent fasting is growing in Polish and Czech Wikipedia from 2024-09 through 2026-09. Use the Wikipedia Interest skill. Run the deterministic `analyze` command, read only its compact JSON, compare trend and reliability, and explain the article-resolution warnings and cross-language caveat. Do not calculate statistics yourself. Offer a PDF only if requested.

Expected flow: parse flags → run CLI → read `comparison` and per-series fields → give a conservative answer. External model validation was not performed in this repository because no Claude Haiku or equivalent model endpoint is available in the local environment.

## Validation note

On 2026-09-23, scenario B completed against live Wikimedia data and resolved `uk.wikipedia.org/Астрономія`; its chart and one-page PDF are in `output/20260923T214035Z-9bc5d026/`. Scenario A completed partially: Czech resolved to `Přerušovaný půst`, while Polish was correctly marked unresolved because no confident matching article was found. Scenario C was attempted, but Wikimedia returned HTTP 429 during the English resolver search after the live checks; the command remains reproducible and this limitation is reported honestly rather than replaced with fabricated output.
