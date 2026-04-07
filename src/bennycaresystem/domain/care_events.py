from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


# -----------------------------------------------------------------------------
# Allowed minimal event vocabulary for v1.
#
# Keep this tiny on purpose. The whole point is low-friction logging.
# -----------------------------------------------------------------------------
ALLOWED_CARE_EVENT_TYPES: frozenset[str] = frozenset(
    {
        "kibble",
        "honey",
        "walk",
        "sun",
    }
)


# -----------------------------------------------------------------------------
# Canonical units for the minimal event vocabulary.
#
# This is intentionally strict:
# - kibble -> grams
# - honey  -> grams
# - walk   -> minutes
# - sun    -> minutes
#
# Keeping the unit fixed per event type makes later analysis simpler and avoids
# "15g vs 0.015kg" nonsense in your first pass.
# -----------------------------------------------------------------------------
CANONICAL_UNITS_BY_EVENT_TYPE: dict[str, str] = {
    "kibble": "g",
    "honey": "g",
    "walk": "m",
    "sun": "m",
}


@dataclass(frozen=True)
class CareEvent:
    """
    One minimal manual care log entry.

    Invariants:
    - timestamp_utc is timezone-aware and normalized to UTC
    - created_at_utc is timezone-aware and normalized to UTC
    - event_type is one of the allowed v1 event types
    - value is positive
    - unit matches the canonical unit for the event type
    """

    timestamp_utc: datetime
    event_type: str
    value: float
    unit: str
    created_at_utc: datetime

    def __post_init__(self) -> None:
        _require_aware_utc(self.timestamp_utc, field_name="timestamp_utc")
        _require_aware_utc(self.created_at_utc, field_name="created_at_utc")

        if self.event_type not in ALLOWED_CARE_EVENT_TYPES:
            raise ValueError(
                f"Unsupported care event type: {self.event_type!r}. "
                f"Allowed types: {sorted(ALLOWED_CARE_EVENT_TYPES)!r}"
            )

        if self.value <= 0:
            raise ValueError("Care event value must be positive.")

        expected_unit = CANONICAL_UNITS_BY_EVENT_TYPE[self.event_type]
        if self.unit != expected_unit:
            raise ValueError(
                f"Invalid unit {self.unit!r} for event type {self.event_type!r}. "
                f"Expected {expected_unit!r}."
            )


def build_care_event(
    *,
    event_type: str,
    value: float,
    timestamp_utc: datetime | None = None,
    created_at_utc: datetime | None = None,
) -> CareEvent:
    """
    Build a validated CareEvent using the canonical unit for the event type.

    This helper keeps call sites simple:
        build_care_event(event_type="kibble", value=15)

    Preconditions:
    - event_type must be in ALLOWED_CARE_EVENT_TYPES
    - value must be positive

    Postconditions:
    - returned CareEvent is fully validated
    - timestamps are UTC-aware
    """
    now_utc = datetime.now(timezone.utc)

    normalized_timestamp_utc = timestamp_utc or now_utc
    normalized_created_at_utc = created_at_utc or now_utc

    event_type = event_type.strip().lower()
    if event_type not in CANONICAL_UNITS_BY_EVENT_TYPE:
        raise ValueError(
            f"Unsupported care event type: {event_type!r}. "
            f"Allowed types: {sorted(ALLOWED_CARE_EVENT_TYPES)!r}"
        )

    unit = CANONICAL_UNITS_BY_EVENT_TYPE[event_type]

    return CareEvent(
        timestamp_utc=_normalize_to_utc(normalized_timestamp_utc),
        event_type=event_type,
        value=float(value),
        unit=unit,
        created_at_utc=_normalize_to_utc(normalized_created_at_utc),
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