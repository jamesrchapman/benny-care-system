from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass(frozen=True)
class GlucoseReading:
    """
    One normalized glucose reading.

    Invariants:
    - device_timestamp_utc is timezone-aware and normalized to UTC
    - fetched_at_utc is either None or timezone-aware UTC
    - mgdl is positive
    - source is non-empty
    """

    device_timestamp_utc: datetime
    mgdl: float
    trend_label: Optional[str]
    source: str
    fetched_at_utc: Optional[datetime] = None

    def __post_init__(self) -> None:
        _require_aware_utc(
            self.device_timestamp_utc,
            field_name="device_timestamp_utc",
        )

        if self.fetched_at_utc is not None:
            _require_aware_utc(
                self.fetched_at_utc,
                field_name="fetched_at_utc",
            )

        if self.mgdl <= 0:
            raise ValueError("mgdl must be positive.")

        if not self.source.strip():
            raise ValueError("source must be non-empty.")


def build_glucose_reading(
    *,
    device_timestamp_utc: datetime,
    mgdl: float,
    source: str,
    trend_label: str | None = None,
    fetched_at_utc: datetime | None = None,
) -> GlucoseReading:
    """
    Build a validated normalized glucose reading.

    Preconditions:
    - device_timestamp_utc must be timezone-aware
    - mgdl must be positive
    - source must be non-empty

    Postconditions:
    - returned GlucoseReading timestamps are normalized to UTC
    """
    return GlucoseReading(
        device_timestamp_utc=_normalize_to_utc(device_timestamp_utc),
        mgdl=float(mgdl),
        trend_label=trend_label,
        source=source.strip(),
        fetched_at_utc=(
            _normalize_to_utc(fetched_at_utc)
            if fetched_at_utc is not None
            else None
        ),
    )


def _normalize_to_utc(value: datetime) -> datetime:
    """
    Normalize any timezone-aware datetime to UTC.

    Raises if the datetime is naive, because silent timezone guessing is bad.
    """
    if value.tzinfo is None:
        raise ValueError("Datetime must be timezone-aware.")
    return value.astimezone(timezone.utc)


def _require_aware_utc(value: datetime, *, field_name: str) -> None:
    """
    Validate that the datetime is timezone-aware and normalized to UTC.
    """
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware.")
    if value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError(f"{field_name} must be normalized to UTC.")