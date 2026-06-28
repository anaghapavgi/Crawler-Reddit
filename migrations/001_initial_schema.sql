CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS crawl_runs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    started_at timestamptz NOT NULL DEFAULT now(),
    finished_at timestamptz,
    trigger_source text NOT NULL,
    status text NOT NULL CHECK (status IN ('running', 'success', 'partial', 'failed', 'budget_stopped')),
    subreddits_count integer NOT NULL DEFAULT 0,
    queries_count integer NOT NULL DEFAULT 0,
    api_requests integer NOT NULL DEFAULT 0,
    posts_seen integer NOT NULL DEFAULT 0,
    posts_upserted integer NOT NULL DEFAULT 0,
    comments_seen integer NOT NULL DEFAULT 0,
    comments_upserted integer NOT NULL DEFAULT 0,
    records_queued_for_analysis integer NOT NULL DEFAULT 0,
    errors_count integer NOT NULL DEFAULT 0,
    rate_limit_remaining numeric,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    error_summary text
);

CREATE TABLE IF NOT EXISTS reddit_posts (
    reddit_id text PRIMARY KEY,
    subreddit text NOT NULL,
    title text NOT NULL DEFAULT '',
    body text NOT NULL DEFAULT '',
    permalink text NOT NULL,
    score integer NOT NULL DEFAULT 0,
    upvote_ratio numeric,
    num_comments integer NOT NULL DEFAULT 0,
    created_utc timestamptz NOT NULL,
    collected_at timestamptz NOT NULL DEFAULT now(),
    last_seen_at timestamptz NOT NULL DEFAULT now(),
    last_refreshed_at timestamptz NOT NULL DEFAULT now(),
    content_hash text NOT NULL,
    matched_queries text[] NOT NULL DEFAULT '{}'::text[],
    relevance_score numeric NOT NULL DEFAULT 0,
    is_deleted boolean NOT NULL DEFAULT false,
    deleted_at timestamptz,
    analysis_status text NOT NULL DEFAULT 'pending'
        CHECK (analysis_status IN ('pending', 'processing', 'complete', 'failed', 'skipped', 'stale')),
    raw_metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS reddit_comments (
    reddit_id text PRIMARY KEY,
    post_reddit_id text NOT NULL REFERENCES reddit_posts(reddit_id) ON DELETE CASCADE,
    parent_reddit_id text,
    subreddit text NOT NULL,
    body text NOT NULL DEFAULT '',
    permalink text NOT NULL,
    score integer NOT NULL DEFAULT 0,
    depth integer NOT NULL DEFAULT 0,
    created_utc timestamptz NOT NULL,
    collected_at timestamptz NOT NULL DEFAULT now(),
    last_seen_at timestamptz NOT NULL DEFAULT now(),
    last_refreshed_at timestamptz NOT NULL DEFAULT now(),
    content_hash text NOT NULL,
    relevance_score numeric NOT NULL DEFAULT 0,
    is_deleted boolean NOT NULL DEFAULT false,
    deleted_at timestamptz,
    analysis_status text NOT NULL DEFAULT 'pending'
        CHECK (analysis_status IN ('pending', 'processing', 'complete', 'failed', 'skipped', 'stale')),
    raw_metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS analysis_runs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    started_at timestamptz NOT NULL DEFAULT now(),
    finished_at timestamptz,
    status text NOT NULL,
    model_name text,
    prompt_version text,
    records_attempted integer NOT NULL DEFAULT 0,
    records_succeeded integer NOT NULL DEFAULT 0,
    records_failed integer NOT NULL DEFAULT 0,
    records_skipped integer NOT NULL DEFAULT 0,
    input_tokens bigint NOT NULL DEFAULT 0,
    output_tokens bigint NOT NULL DEFAULT 0,
    estimated_cost_usd numeric NOT NULL DEFAULT 0,
    estimated_cost_inr numeric NOT NULL DEFAULT 0,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    error_summary text
);

CREATE TABLE IF NOT EXISTS content_analysis (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type text NOT NULL CHECK (source_type IN ('post', 'comment')),
    source_reddit_id text NOT NULL,
    analyzed_text_hash text NOT NULL,
    prompt_version text NOT NULL,
    model_name text NOT NULL,
    relevant boolean NOT NULL,
    language text NOT NULL DEFAULT 'unknown',
    sentiment_label text NOT NULL
        CHECK (sentiment_label IN ('positive', 'neutral', 'negative', 'mixed', 'unknown')),
    sentiment_score numeric NOT NULL CHECK (sentiment_score >= -1 AND sentiment_score <= 1),
    primary_emotion text NOT NULL DEFAULT 'unknown',
    secondary_emotion text NOT NULL DEFAULT 'none',
    intensity smallint NOT NULL CHECK (intensity >= 1 AND intensity <= 5),
    sarcasm_detected boolean NOT NULL DEFAULT false,
    theme text NOT NULL DEFAULT 'other',
    subtheme text NOT NULL DEFAULT 'other',
    feature text NOT NULL DEFAULT 'unknown',
    journey_stage text NOT NULL DEFAULT 'unknown',
    user_segment text NOT NULL DEFAULT 'unknown',
    pain_point text NOT NULL DEFAULT '',
    desired_outcome text NOT NULL DEFAULT '',
    severity smallint NOT NULL CHECK (severity >= 1 AND severity <= 5),
    confidence numeric NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    one_line_summary text NOT NULL DEFAULT '',
    evidence_snippet text NOT NULL DEFAULT '',
    baseline_sentiment_score numeric,
    input_tokens integer NOT NULL DEFAULT 0,
    output_tokens integer NOT NULL DEFAULT 0,
    estimated_cost_usd numeric NOT NULL DEFAULT 0,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_analysis_dedup UNIQUE (
        source_type,
        source_reddit_id,
        prompt_version,
        analyzed_text_hash
    )
);

CREATE TABLE IF NOT EXISTS deletion_events (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type text NOT NULL CHECK (source_type IN ('post', 'comment')),
    source_reddit_id text NOT NULL,
    detected_at timestamptz NOT NULL DEFAULT now(),
    action_taken text NOT NULL,
    originating_job_id uuid,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS pipeline_failures (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type text NOT NULL CHECK (source_type IN ('post', 'comment', 'run')),
    source_reddit_id text NOT NULL DEFAULT '',
    stage text NOT NULL,
    error_category text NOT NULL,
    attempt_count integer NOT NULL DEFAULT 0,
    next_retry_at timestamptz,
    last_error text NOT NULL DEFAULT '',
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_crawl_runs_started_at ON crawl_runs(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_crawl_runs_status ON crawl_runs(status);

CREATE INDEX IF NOT EXISTS idx_reddit_posts_created_utc ON reddit_posts(created_utc DESC);
CREATE INDEX IF NOT EXISTS idx_reddit_posts_subreddit ON reddit_posts(subreddit);
CREATE INDEX IF NOT EXISTS idx_reddit_posts_analysis_status ON reddit_posts(analysis_status);
CREATE INDEX IF NOT EXISTS idx_reddit_posts_is_deleted ON reddit_posts(is_deleted);
CREATE INDEX IF NOT EXISTS idx_reddit_posts_content_hash ON reddit_posts(content_hash);
CREATE INDEX IF NOT EXISTS idx_reddit_posts_matched_queries_gin ON reddit_posts USING gin (matched_queries);

CREATE INDEX IF NOT EXISTS idx_reddit_comments_created_utc ON reddit_comments(created_utc DESC);
CREATE INDEX IF NOT EXISTS idx_reddit_comments_subreddit ON reddit_comments(subreddit);
CREATE INDEX IF NOT EXISTS idx_reddit_comments_post_reddit_id ON reddit_comments(post_reddit_id);
CREATE INDEX IF NOT EXISTS idx_reddit_comments_analysis_status ON reddit_comments(analysis_status);
CREATE INDEX IF NOT EXISTS idx_reddit_comments_is_deleted ON reddit_comments(is_deleted);
CREATE INDEX IF NOT EXISTS idx_reddit_comments_content_hash ON reddit_comments(content_hash);

CREATE INDEX IF NOT EXISTS idx_analysis_runs_started_at ON analysis_runs(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_analysis_runs_status ON analysis_runs(status);

CREATE INDEX IF NOT EXISTS idx_content_analysis_source ON content_analysis(source_type, source_reddit_id);
CREATE INDEX IF NOT EXISTS idx_content_analysis_sentiment_label ON content_analysis(sentiment_label);
CREATE INDEX IF NOT EXISTS idx_content_analysis_theme_feature_segment
    ON content_analysis(theme, feature, user_segment);
CREATE INDEX IF NOT EXISTS idx_content_analysis_confidence ON content_analysis(confidence DESC);
CREATE INDEX IF NOT EXISTS idx_content_analysis_created_at ON content_analysis(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_deletion_events_detected_at ON deletion_events(detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_deletion_events_source ON deletion_events(source_type, source_reddit_id);

CREATE INDEX IF NOT EXISTS idx_pipeline_failures_stage_retry
    ON pipeline_failures(stage, next_retry_at);

ALTER TABLE crawl_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE reddit_posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE reddit_comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE analysis_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE content_analysis ENABLE ROW LEVEL SECURITY;
ALTER TABLE deletion_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE pipeline_failures ENABLE ROW LEVEL SECURITY;

CREATE OR REPLACE VIEW v_analysed_content AS
WITH latest_analysis AS (
    SELECT DISTINCT ON (source_type, source_reddit_id)
        id,
        source_type,
        source_reddit_id,
        analyzed_text_hash,
        prompt_version,
        model_name,
        relevant,
        language,
        sentiment_label,
        sentiment_score,
        primary_emotion,
        secondary_emotion,
        intensity,
        sarcasm_detected,
        theme,
        subtheme,
        feature,
        journey_stage,
        user_segment,
        pain_point,
        desired_outcome,
        severity,
        confidence,
        one_line_summary,
        evidence_snippet,
        baseline_sentiment_score,
        input_tokens,
        output_tokens,
        estimated_cost_usd,
        created_at
    FROM content_analysis
    ORDER BY source_type, source_reddit_id, created_at DESC
)
SELECT
    'post'::text AS source_type,
    p.reddit_id AS source_reddit_id,
    p.subreddit,
    p.created_utc AS source_created_utc,
    p.permalink,
    p.score,
    p.relevance_score,
    p.analysis_status,
    p.content_hash,
    p.title,
    p.body AS text_body,
    la.relevant,
    la.sentiment_label,
    la.sentiment_score,
    la.primary_emotion,
    la.secondary_emotion,
    la.intensity,
    la.sarcasm_detected,
    la.theme,
    la.subtheme,
    la.feature,
    la.journey_stage,
    la.user_segment,
    la.pain_point,
    la.desired_outcome,
    la.severity,
    la.confidence,
    la.one_line_summary,
    la.evidence_snippet,
    la.model_name,
    la.prompt_version,
    la.baseline_sentiment_score,
    la.input_tokens,
    la.output_tokens,
    la.estimated_cost_usd,
    la.created_at AS analysis_created_at
FROM reddit_posts p
LEFT JOIN latest_analysis la
    ON la.source_type = 'post'
    AND la.source_reddit_id = p.reddit_id
WHERE p.is_deleted = false

UNION ALL

SELECT
    'comment'::text AS source_type,
    c.reddit_id AS source_reddit_id,
    c.subreddit,
    c.created_utc AS source_created_utc,
    c.permalink,
    c.score,
    c.relevance_score,
    c.analysis_status,
    c.content_hash,
    ''::text AS title,
    c.body AS text_body,
    la.relevant,
    la.sentiment_label,
    la.sentiment_score,
    la.primary_emotion,
    la.secondary_emotion,
    la.intensity,
    la.sarcasm_detected,
    la.theme,
    la.subtheme,
    la.feature,
    la.journey_stage,
    la.user_segment,
    la.pain_point,
    la.desired_outcome,
    la.severity,
    la.confidence,
    la.one_line_summary,
    la.evidence_snippet,
    la.model_name,
    la.prompt_version,
    la.baseline_sentiment_score,
    la.input_tokens,
    la.output_tokens,
    la.estimated_cost_usd,
    la.created_at AS analysis_created_at
FROM reddit_comments c
LEFT JOIN latest_analysis la
    ON la.source_type = 'comment'
    AND la.source_reddit_id = c.reddit_id
WHERE c.is_deleted = false;

CREATE OR REPLACE VIEW v_daily_sentiment AS
SELECT
    date_trunc('day', vac.source_created_utc)::date AS day,
    vac.subreddit,
    COALESCE(vac.sentiment_label, 'unknown') AS sentiment_label,
    count(*) AS record_count,
    avg(COALESCE(vac.sentiment_score, 0)) AS avg_sentiment_score,
    avg(COALESCE(vac.severity, 0)) AS avg_severity
FROM v_analysed_content vac
WHERE COALESCE(vac.relevant, false) = true
GROUP BY 1, 2, 3;

CREATE OR REPLACE VIEW v_theme_summary AS
SELECT
    COALESCE(vac.theme, 'other') AS theme,
    COALESCE(vac.subtheme, 'other') AS subtheme,
    count(*) AS record_count,
    avg(CASE WHEN vac.sentiment_label = 'negative' THEN 1.0 ELSE 0.0 END) AS negative_rate,
    avg(COALESCE(vac.severity, 0)) AS avg_severity,
    avg(COALESCE(vac.confidence, 0)) AS avg_confidence
FROM v_analysed_content vac
WHERE COALESCE(vac.relevant, false) = true
GROUP BY 1, 2;

CREATE OR REPLACE VIEW v_feature_summary AS
WITH base AS (
    SELECT *
    FROM v_analysed_content
    WHERE COALESCE(relevant, false) = true
), ranked_theme AS (
    SELECT
        feature,
        theme,
        count(*) AS theme_count,
        row_number() OVER (
            PARTITION BY feature
            ORDER BY count(*) DESC, theme ASC
        ) AS rank_in_feature
    FROM base
    GROUP BY feature, theme
)
SELECT
    COALESCE(b.feature, 'unknown') AS feature,
    count(*) AS record_count,
    avg(COALESCE(b.sentiment_score, 0)) AS avg_sentiment_score,
    avg(CASE WHEN b.sentiment_label = 'negative' THEN 1.0 ELSE 0.0 END) AS negative_rate,
    max(rt.theme) FILTER (WHERE rt.rank_in_feature = 1) AS top_theme
FROM base b
LEFT JOIN ranked_theme rt ON rt.feature = b.feature
GROUP BY 1;

CREATE OR REPLACE VIEW v_segment_summary AS
WITH base AS (
    SELECT *
    FROM v_analysed_content
    WHERE COALESCE(relevant, false) = true
), ranked_pain AS (
    SELECT
        user_segment,
        pain_point,
        count(*) AS pain_count,
        row_number() OVER (
            PARTITION BY user_segment
            ORDER BY count(*) DESC, pain_point ASC
        ) AS rank_in_segment
    FROM base
    GROUP BY user_segment, pain_point
)
SELECT
    COALESCE(b.user_segment, 'unknown') AS user_segment,
    count(*) AS record_count,
    avg(COALESCE(b.sentiment_score, 0)) AS avg_sentiment_score,
    max(rp.pain_point) FILTER (WHERE rp.rank_in_segment = 1) AS top_pain_point
FROM base b
LEFT JOIN ranked_pain rp ON rp.user_segment = b.user_segment
GROUP BY 1;

CREATE OR REPLACE VIEW v_pipeline_health AS
WITH latest_crawl AS (
    SELECT *
    FROM crawl_runs
    ORDER BY started_at DESC
    LIMIT 1
), latest_analysis AS (
    SELECT *
    FROM analysis_runs
    ORDER BY started_at DESC
    LIMIT 1
), run_stats AS (
    SELECT
        count(*) AS total_runs_30d,
        count(*) FILTER (WHERE status IN ('success', 'partial', 'budget_stopped')) AS successful_runs_30d
    FROM crawl_runs
    WHERE started_at >= now() - interval '30 days'
), content_totals AS (
    SELECT
        count(*) FILTER (WHERE analysis_status = 'pending') AS pending_records,
        count(*) FILTER (WHERE analysis_status = 'failed') AS failed_records,
        count(*) FILTER (WHERE analysis_status = 'stale') AS stale_records,
        count(*) FILTER (WHERE analysis_status = 'complete') AS complete_records
    FROM (
        SELECT analysis_status, is_deleted FROM reddit_posts
        UNION ALL
        SELECT analysis_status, is_deleted FROM reddit_comments
    ) records
    WHERE is_deleted = false
), cost_totals AS (
    SELECT COALESCE(sum(estimated_cost_inr), 0) AS cumulative_estimated_cost_inr
    FROM analysis_runs
)
SELECT
    now() AS computed_at,
    lc.id AS latest_crawl_run_id,
    lc.status AS latest_crawl_status,
    lc.finished_at AS latest_crawl_finished_at,
    CASE
        WHEN lc.finished_at IS NULL THEN NULL
        ELSE now() - lc.finished_at
    END AS data_freshness_interval,
    la.id AS latest_analysis_run_id,
    la.status AS latest_analysis_status,
    la.finished_at AS latest_analysis_finished_at,
    ct.pending_records,
    ct.failed_records,
    ct.stale_records,
    ct.complete_records,
    co.cumulative_estimated_cost_inr,
    CASE
        WHEN rs.total_runs_30d = 0 THEN 0
        ELSE rs.successful_runs_30d::numeric / rs.total_runs_30d::numeric
    END AS crawl_success_rate_30d
FROM latest_crawl lc
CROSS JOIN latest_analysis la
CROSS JOIN content_totals ct
CROSS JOIN cost_totals co
CROSS JOIN run_stats rs;

CREATE OR REPLACE VIEW v_emerging_themes AS
WITH base AS (
    SELECT
        theme,
        source_reddit_id,
        source_created_utc,
        confidence,
        sentiment_label
    FROM v_analysed_content
    WHERE COALESCE(relevant, false) = true
), recent AS (
    SELECT
        theme,
        count(*) AS recent_weekly_volume,
        count(DISTINCT source_reddit_id) AS recent_distinct_sources,
        avg(COALESCE(confidence, 0)) AS avg_confidence,
        avg(CASE WHEN sentiment_label = 'negative' THEN 1.0 ELSE 0.0 END) AS recent_negative_rate
    FROM base
    WHERE source_created_utc >= now() - interval '7 days'
    GROUP BY theme
), baseline AS (
    SELECT
        theme,
        count(*) / 4.0 AS baseline_weekly_volume
    FROM base
    WHERE source_created_utc >= now() - interval '35 days'
      AND source_created_utc < now() - interval '7 days'
    GROUP BY theme
)
SELECT
    r.theme,
    r.recent_weekly_volume,
    COALESCE(b.baseline_weekly_volume, 0) AS baseline_weekly_volume,
    r.recent_distinct_sources,
    r.avg_confidence,
    r.recent_negative_rate,
    r.recent_weekly_volume::numeric / GREATEST(COALESCE(b.baseline_weekly_volume, 0), 1) AS emergence_score
FROM recent r
LEFT JOIN baseline b ON b.theme = r.theme
WHERE r.recent_weekly_volume >= 5
  AND r.recent_distinct_sources >= 2
  AND r.avg_confidence >= 0.65;
