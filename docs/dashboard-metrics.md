# Dashboard Metrics

This document defines the current Phase 4/5 metric formulas used by the CLI
aggregate summary and initial dashboard data-access layer.

## Data source notes

- Demo mode (`DEMO_MODE=true`): metrics are computed from `data/demo/demo_dataset.csv`.
- Live mode (`DEMO_MODE=false`): analytics data adapters are prepared to read SQL views
  (`v_analysed_content`, `v_pipeline_health`) through Supabase.
- Deleted content is excluded from all metrics.

## KPI snapshot formulas

Window: last `N` days (`N` defaults to 30).

- `total_relevant_records`
  - count of records where `relevant=true` and `is_deleted=false`.
- `avg_sentiment_score`
  - arithmetic mean of `sentiment_score`.
- `negative_rate`
  - mean of indicator `(sentiment_label == "negative")`.
- `avg_confidence`
  - arithmetic mean of `confidence`.
- `sarcasm_rate`
  - mean of indicator `(sarcasm_detected == true)`.

## Trend formulas

For metric windows of size `N` days:

- current window: `[reference_day - N, reference_day)`
- previous window: `[reference_day - 2N, reference_day - N)`

### Volume trend

- `current_value = count(records in current window)`
- `previous_value = count(records in previous window)`
- `delta_absolute = current_value - previous_value`
- `delta_percent = (current - previous) / abs(previous)` when `previous != 0`; otherwise `null`.

### Sentiment trend

- `current_value = avg(sentiment_score in current window)`
- `previous_value = avg(sentiment_score in previous window)`
- `delta_absolute = current_value - previous_value`
- `delta_percent` as above.

## View-like summary formulas

- `daily_sentiment`: grouped by `(day, subreddit, sentiment_label)`.
- `theme_summary`: grouped by `(theme, subtheme)` with `negative_rate`, `avg_severity`, `avg_confidence`.
- `feature_summary`: grouped by `feature`, includes `top_theme` by count (ties sorted alphabetically).
- `segment_summary`: grouped by `user_segment`, includes `top_pain_point` by count.
- `emerging_themes`: theme qualifies when:
  - `recent_weekly_volume >= 5`
  - `recent_distinct_sources >= 2`
  - `avg_confidence >= 0.65`
  - `emergence_score = recent_weekly_volume / max(baseline_weekly_volume, 1)`

## Pipeline health metrics

Current helper aligns with `v_pipeline_health` fields:

- latest crawl/analysis run IDs and statuses
- pending/failed/stale/complete record counts
- cumulative estimated AI cost (INR)
- 30-day crawl success rate:
  - `successful_runs_30d / total_runs_30d`, where successful statuses are
    `success`, `partial`, `budget_stopped`.
