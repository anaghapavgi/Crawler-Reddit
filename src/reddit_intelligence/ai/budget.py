"""Budget-guard helpers for AI analysis calls."""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_USD_TO_INR_RATE = 83.0


@dataclass(frozen=True)
class BudgetDecision:
    """Result of evaluating whether another AI call is allowed."""

    allowed: bool
    status: str
    reason: str
    projected_monthly_spend_inr: float


class BudgetGuard:
    """Enforce per-run and monthly spend caps before provider calls."""

    def __init__(
        self,
        *,
        monthly_budget_inr: float,
        max_records_per_run: int,
        max_calls_per_run: int,
    ) -> None:
        self.monthly_budget_inr = monthly_budget_inr
        self.max_records_per_run = max_records_per_run
        self.max_calls_per_run = max_calls_per_run

    def evaluate(
        self,
        *,
        processed_records: int,
        call_count: int,
        month_to_date_inr: float,
        next_call_estimated_inr: float,
    ) -> BudgetDecision:
        """Check limits and return a machine-friendly decision."""
        projected = month_to_date_inr + next_call_estimated_inr
        if processed_records >= self.max_records_per_run:
            return BudgetDecision(
                allowed=False,
                status="budget_stopped",
                reason="max_records_per_run_reached",
                projected_monthly_spend_inr=projected,
            )
        if call_count >= self.max_calls_per_run:
            return BudgetDecision(
                allowed=False,
                status="budget_stopped",
                reason="max_calls_per_run_reached",
                projected_monthly_spend_inr=projected,
            )
        if projected > self.monthly_budget_inr:
            return BudgetDecision(
                allowed=False,
                status="budget_stopped",
                reason="monthly_budget_exceeded",
                projected_monthly_spend_inr=projected,
            )
        return BudgetDecision(
            allowed=True,
            status="success",
            reason="allowed",
            projected_monthly_spend_inr=projected,
        )


def estimate_cost_inr(
    *,
    input_tokens: int,
    output_tokens: int,
    input_cost_per_1k_usd: float,
    output_cost_per_1k_usd: float,
    usd_to_inr_rate: float = DEFAULT_USD_TO_INR_RATE,
) -> tuple[float, float]:
    """Estimate USD and INR cost from token usage."""
    input_cost_usd = (input_tokens / 1000.0) * input_cost_per_1k_usd
    output_cost_usd = (output_tokens / 1000.0) * output_cost_per_1k_usd
    total_usd = input_cost_usd + output_cost_usd
    return total_usd, total_usd * usd_to_inr_rate
