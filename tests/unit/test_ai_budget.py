from __future__ import annotations

from reddit_intelligence.ai.budget import BudgetGuard, estimate_cost_inr


def test_budget_guard_stops_when_monthly_budget_exceeded() -> None:
    guard = BudgetGuard(monthly_budget_inr=10, max_records_per_run=100, max_calls_per_run=5)
    decision = guard.evaluate(
        processed_records=10,
        call_count=1,
        month_to_date_inr=9.5,
        next_call_estimated_inr=1.0,
    )
    assert decision.allowed is False
    assert decision.reason == "monthly_budget_exceeded"
    assert decision.status == "budget_stopped"


def test_budget_guard_allows_when_within_limits() -> None:
    guard = BudgetGuard(monthly_budget_inr=50, max_records_per_run=100, max_calls_per_run=5)
    decision = guard.evaluate(
        processed_records=20,
        call_count=2,
        month_to_date_inr=5,
        next_call_estimated_inr=1,
    )
    assert decision.allowed is True
    assert decision.reason == "allowed"


def test_estimate_cost_inr_computes_usd_and_inr() -> None:
    usd, inr = estimate_cost_inr(
        input_tokens=1000,
        output_tokens=500,
        input_cost_per_1k_usd=0.0025,
        output_cost_per_1k_usd=0.01,
        usd_to_inr_rate=80,
    )
    assert usd == 0.0075
    assert inr == 0.6
