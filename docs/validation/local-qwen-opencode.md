# Local Qwen OpenCode validation

Status: **PASS**

- Date: 2026-09-24
- Harness: OpenCode 1.18.31
- Model: `Qwen3.8-27B-UD-Q4_K_M.gguf`
- Provider: `llamacpp95` / llama.cpp OpenAI-compatible endpoint
- Endpoint: `http://192.168.0.95:8000/v1`
- Working directory: repository root

## Prompt

> Use the wikipedia-interest skill for this exact task. Do not edit repository files and do not write custom Python or calculate statistics yourself. Analyze whether interest in astronomy is growing in Ukrainian Wikipedia over the last two years: run the deterministic CLI from the repository root with topic astronomy, language uk, start 2024-09, end 2026-09, monthly if appropriate. Read only the compact stdout JSON, explain the resolved article, trend, reliability, current-period cutoff and caveats. Then create a one-page PDF by running the report command for the returned run. End with a concise conservative answer and the generated report path.

## Observed tool flow

1. OpenCode discovered and loaded the root-canonical `wikipedia-interest` skill through `.agents/skills/wikipedia-interest`.
2. It ran:

   ```bash
   uv run wikipedia-interest analyze --topic "astronomy" --languages uk --start 2024-09 --end 2026-09 --granularity monthly --output output
   ```

3. It read the compact JSON output and did not calculate metrics or write custom Python.
4. It ran:

   ```bash
   uv run wikipedia-interest report --run output/20260924T064010989656Z-bc07ab6a
   ```

5. It returned a conservative answer with the report path.

OpenCode also attempted an unrelated small title-generation request through another configured provider; that helper connection failed, but the main local Qwen task continued and completed successfully.

## Deterministic result

- article: `Астрономія` via high-confidence interlanguage link
- trend: declining, `-63.82%/yr`
- reliability: `high / 89`
- data through: `2026-08-31`
- report: `output/20260924T064010989656Z-bc07ab6a/report.pdf` (one page)

## Result

PASS. The local model completed skill discovery, deterministic analysis, compact-output interpretation and PDF generation without repository edits or custom statistics.
