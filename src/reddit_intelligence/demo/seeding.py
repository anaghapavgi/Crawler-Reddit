"""Deterministic demo dataset generation."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from random import Random
from typing import Final

from pydantic import BaseModel, Field

from reddit_intelligence.config import load_research_config, load_taxonomy_config

SENTIMENT_LABELS: Final[tuple[str, ...]] = ("positive", "neutral", "negative", "mixed")
JOURNEY_STAGES: Final[tuple[str, ...]] = (
    "onboarding",
    "search",
    "discovery",
    "playlist_creation",
    "active_listening",
    "library_management",
    "retention",
)
EMOTION_BY_SENTIMENT: Final[dict[str, tuple[str, ...]]] = {
    "positive": ("delight", "satisfaction", "trust"),
    "neutral": ("indifference", "unknown"),
    "negative": ("frustration", "disappointment", "anger"),
    "mixed": ("confusion", "surprise", "boredom"),
}
SENTIMENT_RANGES: Final[dict[str, tuple[float, float]]] = {
    "positive": (0.2, 0.95),
    "neutral": (-0.1, 0.1),
    "negative": (-0.95, -0.2),
    "mixed": (-0.4, 0.4),
}
THEME_TEXT: Final[dict[str, tuple[str, str]]] = {
    "repetitive_recommendations": (
        "Recommendations keep repeating songs I already know.",
        "Surface fresh tracks from unfamiliar artists more often.",
    ),
    "lack_of_novelty": (
        "Discovery feels stale and too predictable.",
        "Increase novelty while keeping relevance high.",
    ),
    "recommendation_controls": (
        "I cannot steer recommendations enough.",
        "Provide clearer controls for tuning recommendations.",
    ),
    "new_release_discovery": (
        "I miss new releases from artists I follow.",
        "Highlight newly released tracks earlier.",
    ),
    "manual_search_effort": (
        "Finding good music requires too much manual searching.",
        "Reduce search effort with better context-aware suggestions.",
    ),
}


@dataclass(frozen=True)
class DemoRecord:
    """Synthetic analyzed content record for demo mode."""

    date: str
    subreddit: str
    source_type: str
    source_reddit_id: str
    permalink: str
    text: str
    sentiment_label: str
    sentiment_score: float
    baseline_sentiment_score: float
    theme: str
    subtheme: str
    feature: str
    segment: str
    journey_stage: str
    emotion: str
    severity: int
    confidence: float
    sarcasm_detected: bool
    pain_point: str
    desired_outcome: str
    relevant: bool
    is_deleted: bool


@dataclass(frozen=True)
class DemoRunRecord:
    """Synthetic operational run record for demo mode."""

    run_id: str
    run_type: str
    started_at: str
    finished_at: str
    status: str
    records_seen: int
    records_processed: int
    input_tokens: int
    output_tokens: int
    estimated_cost_inr: float


class DemoSeedResult(BaseModel):
    """Summary of generated demo artifacts."""

    records_path: Path
    runs_path: Path
    metrics_path: Path
    record_count: int = Field(ge=1)
    run_count: int = Field(ge=1)
    days: int = Field(ge=90)


def _format_float(value: float) -> float:
    return round(value, 4)


def _choose_sentiment(day_index: int, record_index: int, in_spike_window: bool) -> str:
    if in_spike_window and record_index % 3 != 0:
        return "negative"
    return SENTIMENT_LABELS[(day_index + record_index) % len(SENTIMENT_LABELS)]


def _score_for_sentiment(rng: Random, sentiment: str) -> float:
    lower, upper = SENTIMENT_RANGES[sentiment]
    return _format_float(rng.uniform(lower, upper))


def _build_text(theme: str, feature: str, sentiment: str, sarcasm_detected: bool) -> str:
    if sarcasm_detected:
        return (
            f"Oh great, {feature} totally solved everything... except it still feels like "
            f"{theme.replace('_', ' ')}."
        )
    return (
        f"Discussion about {feature}: users mention {theme.replace('_', ' ')} with "
        f"{sentiment} sentiment in music discovery journeys."
    )


def _theme_messages(theme: str) -> tuple[str, str]:
    return THEME_TEXT.get(
        theme,
        ("Users are discussing this product experience.", "Improve the underlying experience."),
    )


def generate_demo_records(
    days: int,
    seed: int,
    reference_date: date,
) -> list[DemoRecord]:
    """Generate deterministic analyzed-content records for dashboard demo mode."""
    if days < 90:
        msg = "Demo dataset must include at least 90 days."
        raise ValueError(msg)

    research = load_research_config()
    taxonomy = load_taxonomy_config()
    rng = Random(seed)

    subreddits = research.reddit.subreddits
    themes = taxonomy.themes
    features = taxonomy.features
    segments = taxonomy.behavioral_segments
    emotions = taxonomy.emotions
    start_date = reference_date - timedelta(days=days - 1)
    records: list[DemoRecord] = []

    for day_index in range(days):
        current_day = start_date + timedelta(days=day_index)
        in_spike_window = day_index >= days - 14
        base_volume = 14 + (day_index % 5)
        spike_extra = 8 if in_spike_window else 0
        day_volume = base_volume + spike_extra

        for record_index in range(day_volume):
            subreddit = subreddits[(day_index + record_index) % len(subreddits)]
            source_type = "post" if record_index % 4 == 0 else "comment"
            theme = themes[(day_index * 3 + record_index) % len(themes)]
            if in_spike_window and record_index < spike_extra:
                theme = "repetitive_recommendations"
            feature = features[(day_index * 2 + record_index) % len(features)]
            segment = segments[(day_index + record_index * 2) % len(segments)]
            journey_stage = JOURNEY_STAGES[(day_index + record_index) % len(JOURNEY_STAGES)]
            sentiment = _choose_sentiment(day_index, record_index, in_spike_window)
            sentiment_score = _score_for_sentiment(rng, sentiment)
            baseline_sentiment = _format_float(
                max(-1.0, min(1.0, sentiment_score + rng.uniform(-0.15, 0.15)))
            )
            confidence = _format_float(rng.uniform(0.62, 0.97))
            sarcasm_detected = sentiment in {"negative", "mixed"} and (record_index % 11 == 0)
            severity = 4 if sentiment == "negative" else 3 if sentiment == "mixed" else 2
            primary_emotions = [
                emotion for emotion in EMOTION_BY_SENTIMENT[sentiment] if emotion in emotions
            ]
            if not primary_emotions:
                primary_emotions = ["unknown"]
            emotion = primary_emotions[(record_index + day_index) % len(primary_emotions)]
            pain_point, desired_outcome = _theme_messages(theme)

            source_reddit_id = f"d{day_index:03d}_{record_index:03d}"
            permalink = f"https://reddit.com/r/{subreddit}/comments/{source_reddit_id}/demo/"
            text = _build_text(theme, feature, sentiment, sarcasm_detected)

            records.append(
                DemoRecord(
                    date=current_day.isoformat(),
                    subreddit=subreddit,
                    source_type=source_type,
                    source_reddit_id=source_reddit_id,
                    permalink=permalink,
                    text=text,
                    sentiment_label=sentiment,
                    sentiment_score=sentiment_score,
                    baseline_sentiment_score=baseline_sentiment,
                    theme=theme,
                    subtheme="demo_generated",
                    feature=feature,
                    segment=segment,
                    journey_stage=journey_stage,
                    emotion=emotion,
                    severity=severity,
                    confidence=confidence,
                    sarcasm_detected=sarcasm_detected,
                    pain_point=pain_point,
                    desired_outcome=desired_outcome,
                    relevant=True,
                    is_deleted=False,
                )
            )
    return records


def generate_run_history(
    records: list[DemoRecord],
    days: int,
    reference_date: date,
    seed: int,
) -> list[DemoRunRecord]:
    """Generate deterministic crawl/analysis run history with costs."""
    rng = Random(seed + 1000)
    by_day: dict[str, int] = {}
    for record in records:
        by_day[record.date] = by_day.get(record.date, 0) + 1

    start_date = reference_date - timedelta(days=days - 1)
    runs: list[DemoRunRecord] = []
    for day_index in range(days):
        current_day = start_date + timedelta(days=day_index)
        day_key = current_day.isoformat()
        record_count = by_day.get(day_key, 0)
        crawl_status = "partial" if day_index % 17 == 0 else "success"
        analysis_status = "budget_stopped" if day_index % 23 == 0 else "success"

        crawl_started = datetime.combine(current_day, time(3, 17, tzinfo=UTC))
        crawl_finished = crawl_started + timedelta(minutes=7 + (day_index % 4))
        analysis_started = datetime.combine(current_day, time(3, 31, tzinfo=UTC))
        analysis_finished = analysis_started + timedelta(minutes=9 + (day_index % 5))

        crawl_seen = int(record_count * rng.uniform(1.12, 1.3))
        input_tokens = int(record_count * rng.uniform(110, 170))
        output_tokens = int(record_count * rng.uniform(35, 65))
        estimated_cost = _format_float((input_tokens + output_tokens) * 0.00004)

        runs.append(
            DemoRunRecord(
                run_id=f"crawl-{current_day.strftime('%Y%m%d')}",
                run_type="crawl",
                started_at=crawl_started.isoformat(),
                finished_at=crawl_finished.isoformat(),
                status=crawl_status,
                records_seen=crawl_seen,
                records_processed=record_count,
                input_tokens=0,
                output_tokens=0,
                estimated_cost_inr=0.0,
            )
        )
        runs.append(
            DemoRunRecord(
                run_id=f"analysis-{current_day.strftime('%Y%m%d')}",
                run_type="analysis",
                started_at=analysis_started.isoformat(),
                finished_at=analysis_finished.isoformat(),
                status=analysis_status,
                records_seen=record_count,
                records_processed=record_count,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                estimated_cost_inr=estimated_cost,
            )
        )
    return runs


def build_cost_metrics(
    runs: list[DemoRunRecord],
    monthly_budget_inr: float = 250,
) -> dict[str, float]:
    """Aggregate budget/cost metrics from analysis runs."""
    analysis_runs = [run for run in runs if run.run_type == "analysis"]
    total_inr = _format_float(sum(run.estimated_cost_inr for run in analysis_runs))
    total_input_tokens = sum(run.input_tokens for run in analysis_runs)
    total_output_tokens = sum(run.output_tokens for run in analysis_runs)
    recent_30_runs = analysis_runs[-30:] if len(analysis_runs) > 30 else analysis_runs
    recent_30_cost = _format_float(sum(run.estimated_cost_inr for run in recent_30_runs))
    budget_remaining = _format_float(max(monthly_budget_inr - recent_30_cost, 0))
    return {
        "monthly_budget_inr": monthly_budget_inr,
        "estimated_month_to_date_cost_inr": recent_30_cost,
        "budget_remaining_inr": budget_remaining,
        "cumulative_estimated_cost_inr": total_inr,
        "cumulative_input_tokens": float(total_input_tokens),
        "cumulative_output_tokens": float(total_output_tokens),
    }


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        msg = f"No rows generated for {path}."
        raise ValueError(msg)
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_demo_artifacts(
    output_dir: Path = Path("data/demo"),
    days: int = 90,
    seed: int = 42,
    reference_date: date | None = None,
) -> DemoSeedResult:
    """Generate deterministic demo artifacts for local development and tests."""
    reference_day = reference_date or datetime.now(tz=UTC).date()
    output_dir.mkdir(parents=True, exist_ok=True)

    records = generate_demo_records(days=days, seed=seed, reference_date=reference_day)
    runs = generate_run_history(records=records, days=days, reference_date=reference_day, seed=seed)
    metrics = build_cost_metrics(runs)

    records_path = output_dir / "demo_dataset.csv"
    runs_path = output_dir / "demo_run_history.csv"
    metrics_path = output_dir / "demo_cost_metrics.json"

    _write_csv(records_path, [asdict(record) for record in records])
    _write_csv(runs_path, [asdict(run) for run in runs])
    with metrics_path.open("w", encoding="utf-8") as metrics_file:
        json.dump(metrics, metrics_file, indent=2, sort_keys=True)
        metrics_file.write("\n")

    return DemoSeedResult(
        records_path=records_path,
        runs_path=runs_path,
        metrics_path=metrics_path,
        record_count=len(records),
        run_count=len(runs),
        days=days,
    )
