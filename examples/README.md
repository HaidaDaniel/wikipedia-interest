# Reproduce the showcase

The committed artifacts in [`artifacts/`](artifacts/) came from three OpenCode agent runs using the `wikipedia-interest` skill and deterministic CLI on 2026-09-24. OpenCode read the compact `analyze` JSON, then ran `report`; it did not calculate metrics from `data.csv`. The requested end month, September 2026, was incomplete and excluded, so all data ends on 2026-08-31. Live Wikimedia data may change if these commands are rerun later.

Run these commands from the repository root. Each `analyze` command prints its run path; use that path with `report`.

## Mini PC: four editions, 36 complete months

```bash
uv run wikipedia-interest analyze --topic "mini PCs" --languages en,de,ja,zh \
  --start 2023-09 --end 2026-09 --granularity auto --output output
uv run wikipedia-interest report --run output/<run-id>
```

The German result points to `Netbook#Nettop`, while pageviews cover the parent `Netbook` article. The Japanese search result points to an iPad article. Both are low-confidence candidates excluded from comparison; only English and Chinese are eligible. [Chart](artifacts/mini-pc/chart.png) · [PDF](artifacts/mini-pc/report.pdf) · [JSON](artifacts/mini-pc/result.json)

## 3D printing: three editions, 24 complete months

```bash
uv run wikipedia-interest analyze --topic "3D printing" --languages en,ja,ko \
  --start 2024-09 --end 2026-09 --granularity auto --output output
uv run wikipedia-interest report --run output/<run-id>
```

All three articles resolve with high confidence. Japanese pageviews rise from a small baseline and have a modest trend fit, so the percentage change is provisional even though the heuristic reliability score is high. [Chart](artifacts/3d-printing/chart.png) · [PDF](artifacts/3d-printing/report.pdf) · [JSON](artifacts/3d-printing/result.json)

## Astronomy: Ukrainian edition, 24 complete months

```bash
uv run wikipedia-interest analyze --topic astronomy --languages uk \
  --start 2024-09 --end 2026-09 --granularity auto --output output
uv run wikipedia-interest report --run output/<run-id>
```

The high-confidence `Астрономія` article shows a decline, with one prominent spike at the start of the window. [Chart](artifacts/astronomy-uk/chart.png) · [PDF](artifacts/astronomy-uk/report.pdf) · [JSON](artifacts/astronomy-uk/result.json)

Pageviews measure article attention. Cross-language totals do not measure market size, and `trend_fit_r2` describes fit rather than statistical significance.
