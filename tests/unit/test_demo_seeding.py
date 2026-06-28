from __future__ import annotations

import csv
from datetime import date, timedelta
from pathlib import Path

from reddit_intelligence.demo.seeding import write_demo_artifacts


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as csv_file:
        return list(csv.DictReader(csv_file))


def test_demo_seed_writes_required_artifacts(tmp_path: Path) -> None:
    result = write_demo_artifacts(
        output_dir=tmp_path,
        days=90,
        seed=77,
        reference_date=date(2026, 6, 1),
    )
    assert result.records_path.exists()
    assert result.runs_path.exists()
    assert result.metrics_path.exists()
    rows = _read_csv_rows(result.records_path)
    dates = sorted({row["date"] for row in rows})
    assert len(rows) > 1200
    assert len(dates) == 90


def test_demo_seed_is_deterministic_for_same_inputs(tmp_path: Path) -> None:
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    first = write_demo_artifacts(
        output_dir=first_dir,
        days=90,
        seed=99,
        reference_date=date(2026, 6, 1),
    )
    second = write_demo_artifacts(
        output_dir=second_dir,
        days=90,
        seed=99,
        reference_date=date(2026, 6, 1),
    )

    assert first.records_path.read_text(encoding="utf-8") == second.records_path.read_text(
        encoding="utf-8"
    )
    assert first.runs_path.read_text(encoding="utf-8") == second.runs_path.read_text(
        encoding="utf-8"
    )
    assert first.metrics_path.read_text(encoding="utf-8") == second.metrics_path.read_text(
        encoding="utf-8"
    )


def test_demo_seed_includes_required_signals_and_spike(tmp_path: Path) -> None:
    reference = date(2026, 6, 1)
    result = write_demo_artifacts(
        output_dir=tmp_path,
        days=90,
        seed=42,
        reference_date=reference,
    )
    rows = _read_csv_rows(result.records_path)

    sentiment_labels = {row["sentiment_label"] for row in rows}
    assert {"positive", "neutral", "negative", "mixed"} <= sentiment_labels
    assert any(row["sarcasm_detected"] == "True" for row in rows)

    recent_start = reference - timedelta(days=13)
    baseline_start = reference - timedelta(days=69)
    baseline_end = reference - timedelta(days=14)

    recent_count = 0
    baseline_count = 0
    for row in rows:
        row_date = date.fromisoformat(row["date"])
        if row["theme"] != "repetitive_recommendations":
            continue
        if row_date >= recent_start:
            recent_count += 1
        elif baseline_start <= row_date <= baseline_end:
            baseline_count += 1

    baseline_weekly_avg = baseline_count / 8 if baseline_count > 0 else 0
    emergence_score = recent_count / max(baseline_weekly_avg, 1)
    assert emergence_score > 1.5
