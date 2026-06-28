"""Shared domain model placeholders for early scaffold."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class RunSummary:
    """Simple run summary used by scaffold commands."""

    started_at: datetime
    status: str
    message: str
