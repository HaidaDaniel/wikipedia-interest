# Methodology

## What pageviews measure

Wikimedia Pageviews counts requests for a Wikipedia article under the selected access and agent filters. This project uses `all-access` and `user` data from the official Wikimedia Analytics API. A view is evidence that people accessed information, not a person, lead or transaction.

## Metrics

The default monthly series is a sum of API observations in each calendar month. We report total, mean, median, first/last robust-window growth, 12-period year-over-year growth when available, volatility (MAD divided by median), completeness and an annualized log-linear trend.

The main trend fits `log(1 + views)` against equally spaced periods. The slope is annualized (`exp(slope * periods_per_year) - 1`) so it is less dominated by one very large month than first-vs-last growth. A centered rolling mean is fitted as a smoothed companion. `growing` means trend >= +10% per year and a usable fit; `declining` means <= -10%; otherwise the series is `flat` when the fit is reasonably consistent and `uncertain` when noise or data quality prevents a directional claim.

## Why first and last points are insufficient

Endpoints can be incomplete, seasonal or event-driven. Window means, a fitted trend and YoY comparison use more of the series and reduce endpoint sensitivity. The tool never treats one endpoint difference as the whole conclusion.

## Seasonality

For 24 or more monthly observations, the recent year is compared with the prior year. That avoids comparing adjacent months from different seasons as if they were a structural change. This is a lightweight seasonal check, not SARIMA or causal decomposition.

## Spikes and anomalies

An observation is a candidate spike when its robust z-score exceeds 3.5, using median and MAD (with IQR/std fallbacks for constant or tiny series). We report the date, value, robust deviation and share of total views. A large spike can make a positive endpoint or fitted slope misleading; it lowers evidence quality and is called out in the report.

## Evidence quality

Reliability is not a statistical confidence interval. The score is an explainable heuristic: 0–100 points from duration, completeness, trend signal, fit consistency, volatility and article-resolution quality, with penalties for anomalies. `high` (70–100), `medium` (45–69), and `low` (0–44) describe how much weight to give the directional signal in this dataset.

## Cross-language comparisons

Absolute views are shown as article attention, not comparable market size. Editions differ in population, Wikipedia usage, article coverage, naming, alternative pages and traffic mix. Comparisons prioritize relative growth dynamics, stability and evidence quality. A result can say “stronger signal for further validation”; it cannot establish product-market fit, conversion or willingness to pay.

