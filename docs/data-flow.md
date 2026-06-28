# Data Flow Plan (Pre-Implementation)

## 1. End-to-end pipeline stages

1. **Trigger**
   - Source: local CLI or GitHub Actions.
   - Output: `crawl_runs`/`analysis_runs` start records and run context metadata.

2. **Collection (Reddit API via PRAW, read-only)**
   - Input: `config/research.yml` subreddits + queries + limits.
   - Output: raw mapped submissions/comments (without usernames).
   - Safety:
     - verify `read_only`;
     - cap comments;
     - avoid unbounded `replace_more(limit=None)`;
     - classify errors for retry vs stop.

3. **Cleaning + dedup + relevance**
   - Input: mapped raw content.
   - Transform:
     - normalize text;
     - detect deleted/removed;
     - compute stable SHA-256 content hashes;
     - calculate transparent rule-based relevance score.
   - Output:
     - upsert-ready post/comment records with idempotent keys and status fields.

4. **Persistence (Supabase/PostgreSQL)**
   - Input: cleaned records and run metadata.
   - Transform:
     - idempotent upsert by Reddit ID;
     - merge query matches;
     - mark stale analysis when hash changes.
   - Output:
     - `reddit_posts`, `reddit_comments`, `crawl_runs`, failure queue entries.

5. **AI analysis orchestration**
   - Input: eligible, non-deleted records above relevance threshold.
   - Guardrails:
     - per-run record/call caps;
     - monthly INR budget checks;
     - skip unchanged hash with same prompt version.
   - Transform:
     - VADER baseline score;
     - structured LLM classification/summarization;
     - strict Pydantic validation and taxonomy-bound labels.
   - Output:
     - `content_analysis`, `analysis_runs`, usage/cost metadata, retryable failures.

6. **Aggregation and analytics**
   - Input: base + analysis tables.
   - Transform:
     - SQL views and Python metrics/trend computations;
     - evidence sampling with diversity and confidence weighting.
   - Output:
     - dashboard-ready datasets excluding deleted content.

7. **Dashboard and assistant**
   - Input: filtered analytics data + bounded evidence samples.
   - Output:
     - KPI cards, trend charts, explorer export, evidence-grounded assistant answers.
   - Safety:
     - no direct Reddit calls;
     - no arbitrary SQL from model;
     - sanitized CSV export;
     - demo/live mode indicator.

8. **Maintenance and compliance**
   - Deletion sync:
     - revisit recently collected records;
     - scrub deleted content from raw text and downstream evidence.
   - Retry reconciliation:
     - process retryable failures with attempt caps/backoff.

## 2. Canonical data entities and movement

- **Run entities**
  - `crawl_runs`, `analysis_runs`: operational telemetry and status transitions.
- **Content entities**
  - `reddit_posts`, `reddit_comments`: idempotent source tables with content hash and analysis state.
- **Analysis entities**
  - `content_analysis`: structured insights with model/prompt/tokens/cost/confidence.
- **Operational entities**
  - `deletion_events`, `pipeline_failures`: compliance and recovery.
- **Derived entities**
  - analytics views: sentiment, theme, feature, segment, pipeline health, emerging trends.

## 3. Idempotency and state transitions

### Idempotency strategy

- Primary natural key: Reddit IDs.
- Content mutability detection: deterministic cleaned-text hash.
- AI dedup key: `(source_type, source_reddit_id, prompt_version, analyzed_text_hash)`.
- Upserts merge incremental metadata without duplicate rows.

### Lifecycle states

- Crawl run: `running -> success|partial|failed|budget_stopped`.
- Analysis status on content: `pending|processing|complete|failed|skipped|stale`.
- Stale criteria: cleaned hash changed since last successful analysis.

## 4. Failure and recovery flow

### Retryable categories
- rate limit, timeout, transient network, temporary provider/database error.

### Non-retryable categories
- invalid credentials, permission denied/private subreddit, malformed non-recoverable payload.

### Recovery mechanics
- exponential backoff with jitter;
- bounded retry attempts;
- enqueue failed work items with stage metadata in `pipeline_failures`;
- replay via explicit CLI command (`retry-failures`).

## 5. Privacy and compliance flow controls

- Strip/ignore author identifiers at mapping stage.
- Mark deleted/removed content and erase text in storage when detected.
- Exclude deleted rows from analytics views, exports, and assistant evidence.
- Keep only deletion audit metadata in `deletion_events`.
- Ensure prompt states that Reddit content is untrusted and instruction-like text must be ignored.

## 6. Demo mode data flow

When `DEMO_MODE=true`:
- collection and analysis stages can run against deterministic fixture/demo datasets;
- no external network credentials required;
- dashboard uses synthetic but realistic, bounded data;
- run history and cost telemetry are simulated transparently (never represented as live).

## 7. Observability plan

- Structured logs with run IDs and stage names.
- Metrics exposed through pipeline health view:
  - freshness, coverage, pending/failed/stale counts, cost and budget.
- Command exit codes:
  - non-zero on genuine failures;
  - success when budget guard intentionally stops analysis and status is persisted as `budget_stopped`.
