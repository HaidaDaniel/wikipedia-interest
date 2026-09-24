# Free-model OpenCode validation

Status: **PASS**

- Date: 2026-09-24
- Harness: OpenCode 1.18.31
- Model: `opencode/mimo-v2.6-flash-free`
- Provider: OpenCode provider
- Working directory: repository root

## Prompt

> Use the wikipedia-interest skill for this exact task. Do not edit repository files and do not write custom Python or calculate statistics yourself. Analyze whether interest in astronomy is growing in Ukrainian Wikipedia over the last two years: run the deterministic CLI from the repository root with topic astronomy, language uk, start 2024-09, end 2026-09, monthly if appropriate. Read only the compact stdout JSON, explain the resolved article, trend, reliability, current-period cutoff and caveats. Then create a one-page PDF by running the report command for the returned run. End with a concise conservative answer and the generated report path.

## Observed tool flow

1. OpenCode discovered and loaded `wikipedia-interest`.
2. It ran:

   ```bash
   uv run wikipedia-interest analyze --topic "astronomy" --languages uk --start 2024-09 --end 2026-09 --granularity monthly --output output
   ```

3. It read the compact JSON output and did not calculate metrics or write custom Python.
4. It ran:

   ```bash
   uv run wikipedia-interest report --run output/20260924T055927519636Z-bc07ab6a
   ```

## Deterministic result

- article: `Астрономія` via high-confidence interlanguage link
- trend: declining, `-63.82%/yr`
- reliability: `high / 89`
- data through: `2026-08-31`
- report: `output/20260924T055927519636Z-bc07ab6a/report.pdf`

## Result

PASS. The model returned a conservative conclusion and stated that pageviews represent article attention, not market size or product-market fit. A separate Claude Haiku 4.5 attempt stopped before model output because the provider reported insufficient funds; it is not counted as validation.
