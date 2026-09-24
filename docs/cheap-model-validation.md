# Cheap-model validation

Status: **passed** with a free OpenCode model.

- Date: 2026-09-24
- Harness: OpenCode 1.18.31
- Model: `opencode/mimo-v2.6-flash-free`
- Working directory: repository root
- Skill discovery: `.agents/skills/wikipedia-interest/SKILL.md`

## Prompt

> Use the wikipedia-interest skill for this exact task. Do not edit repository files and do not write custom Python or calculate statistics yourself. Analyze whether interest in astronomy is growing in Ukrainian Wikipedia over the last two years: run the deterministic CLI from the repository root with topic astronomy, language uk, start 2024-09, end 2026-09, monthly if appropriate. Read only the compact stdout JSON, explain the resolved article, trend, reliability, current-period cutoff and caveats. Then create a one-page PDF by running the report command for the returned run. End with a concise conservative answer and the generated report path.

## Observed result

Pass. OpenCode discovered and loaded the skill, ran `analyze`, used the compact JSON contract, and then ran `report`. It did not write custom Python or recalculate the metrics. It correctly reported:

- resolved article: `Астрономія`, high-confidence interlanguage link;
- trend: declining, approximately `-63.8%/yr`;
- reliability: high, score `89`;
- cutoff: requested September 2026 excluded, `data_through=2026-08-31`;
- conservative caveats about attention vs demand and cross-language comparability;
- report: `output/20260924T055927519636Z-bc07ab6a/report.pdf`.

The same prompt was attempted with `opencode/claude-haiku-4-5`; the provider stopped before model output with `Insufficient account funds`. That failed attempt is not counted as validation; the free-model run above is the successful evidence.

## Local-provider validation

Status: **passed** with the configured local Llama.cpp provider.

- Date: 2026-09-24
- Harness: OpenCode 1.18.31
- Provider/model: `llamacpp95//home/virtusdno/llama-models/Qwen3.8-27B-UD-Q4_K_M.gguf`
- Endpoint: `http://192.168.0.95:8000/v1`
- Working directory: repository root

The same prompt completed end to end through the local model: it discovered the skill, ran `analyze`, read the compact JSON, ran `report`, and returned a conservative answer. The generated report was `output/20260924T061457546715Z-bc07ab6a/report.pdf`; it is a one-page PDF. The result matched the deterministic CLI: `Астрономія`, declining approximately `-63.8%/yr`, high reliability score `89`, with data through `2026-08-31`.
