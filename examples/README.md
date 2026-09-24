# Scenario examples

These are intentionally reproducible commands. They use live Wikimedia data on first run and then the local cache. Dates below are the brief's “last approximately two years” shape; change them when reproducing.

## A — intermittent fasting, Polish vs Czech

```bash
uv run wikipedia-interest analyze \
  --topic "intermittent fasting" --languages pl,cs \
  --start 2024-09 --end 2026-09 --granularity monthly
```

Expected behavior: English canonical search plus interlanguage links should resolve the Czech article; Polish may be unresolved or low-confidence if the edition has no exact concept page. Check `resolution.warnings`; do not assume equal article coverage means equal audience size. Compare `trend_pct_per_year`, `trend_label` and `reliability`.

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

Expected flow: parse flags → run CLI → read `comparison` and per-series fields → give a conservative answer. This flow was validated with OpenCode and `opencode/mimo-v2.6-flash-free`; Claude Haiku was attempted separately but its provider reported insufficient account funds.

## Validation note

On 2026-09-24, all three scenarios completed against live Wikimedia data. Scenario B resolved `uk.wikipedia.org/Астрономія`; its committed chart and one-page PDF are in `examples/artifacts/astronomy-uk/`. Scenario A resolved Czech to `Přerušovaný půst`; Polish used an explicitly low-confidence target-search result and must be treated as unverified. Scenario C exercised four languages and generated both chart and one-page PDF; all four target-search resolutions are low confidence and the output explicitly warns that “learning English” is ambiguous.
