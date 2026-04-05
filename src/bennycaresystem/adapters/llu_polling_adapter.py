from __future__ import annotations

"""
LibreLinkUp polling adapter.

Purpose:
- authenticate against LibreLinkUp
- fetch current and recent glucose data
- normalize that data into local domain objects

Non-goals for this file:
- database storage
- graphing
- alerting
- scheduling
- routines
- Discord integration

This module is intentionally narrow.
It is the LLU acquisition boundary only.
"""

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Protocol, Sequence
from pathlib import Path
from dotenv import load_dotenv
from pprint import pprint

PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")

UTC = timezone.utc


# =============================================================================
# DOMAIN MODELS
# =============================================================================


@dataclass(frozen=True)
class GlucoseReading:
    """
    Normalized glucose reading.

    Invariants:
    - device_timestamp_utc is timezone-aware UTC
    - fetched_at_utc is timezone-aware UTC
    - mgdl is numeric
    """

    device_timestamp_utc: datetime
    fetched_at_utc: datetime
    mgdl: float
    trend_label: Optional[str] = None
    source: str = "llu"


@dataclass(frozen=True)
class LLUPollSnapshot:
    """
    Result of a single LLU poll.

    latest_reading:
        The newest reading returned by LLU, if any.

    recent_readings:
        Recent graph/history readings returned by LLU.
        Usually this is the more important set, because it lets us backfill.
    """

    polled_at_utc: datetime
    ok: bool
    latest_reading: Optional[GlucoseReading]
    recent_readings: tuple[GlucoseReading, ...]
    message: str = ""


# =============================================================================
# PORT
# =============================================================================


class LLUPoller(Protocol):
    """Interface for LLU data acquisition."""

    def poll(self) -> LLUPollSnapshot:
        ...


# =============================================================================
# ADAPTER
# =============================================================================


class LibreLinkUpPoller:
    """
    LibreLinkUp adapter using `pylibrelinkup`.

    Environment variables:
    - LIBRE_LINK_UP_EMAIL
    - LIBRE_LINK_UP_PASSWORD
    - LIBRE_LINK_UP_PATIENT_INDEX   optional, defaults to 0

    Design notes:
    - This class owns auth and remote fetch behavior.
    - This class does NOT know anything about SQLite or graphs.
    - This class returns normalized local domain objects only.
    """

    def __init__(self) -> None:
        self.email = os.environ.get("LIBRE_LINK_UP_EMAIL", "").strip()
        self.password = os.environ.get("LIBRE_LINK_UP_PASSWORD", "").strip()
        self.patient_index = int(os.environ.get("LIBRE_LINK_UP_PATIENT_INDEX", "0"))

        if not self.email or not self.password:
            raise RuntimeError(
                "Missing LibreLinkUp credentials. "
                "Set LIBRE_LINK_UP_EMAIL and LIBRE_LINK_UP_PASSWORD."
            )

        try:
            from pylibrelinkup import PyLibreLinkUp
        except ImportError as exc:
            raise RuntimeError(
                "Missing dependency `pylibrelinkup`. Install it with: pip install pylibrelinkup"
            ) from exc

        self._PyLibreLinkUp = PyLibreLinkUp
        self._client = self._PyLibreLinkUp(email=self.email, password=self.password)
        self._authenticated = False

    def poll(self) -> LLUPollSnapshot:
        """
        Poll LLU once.

        Strategy:
        - authenticate lazily
        - resolve the desired patient connection
        - fetch graph/history readings
        - fetch latest reading
        - normalize everything into local dataclasses
        - never leak remote library objects outside this adapter
        """
        polled_at_utc = datetime.now(UTC)

        try:
            if not self._authenticated:
                self._client.authenticate()
                self._authenticated = True

            patient_identifier = self._resolve_patient_identifier()
            if patient_identifier is None:
                return LLUPollSnapshot(
                    polled_at_utc=polled_at_utc,
                    ok=False,
                    latest_reading=None,
                    recent_readings=(),
                    message="No LibreLinkUp patient connection was available.",
                )

            graph_measurements = self._client.graph(patient_identifier=patient_identifier)
            latest_measurement = self._client.latest(patient_identifier=patient_identifier)

            recent_readings = tuple(
                self._normalize_graph_measurements(
                    graph_measurements=graph_measurements,
                    fetched_at_utc=polled_at_utc,
                )
            )

            latest_reading = self._normalize_single_measurement(
                measurement=latest_measurement,
                fetched_at_utc=polled_at_utc,
            )

            # If latest is not already present in graph history, append it.
            if latest_reading is not None and not self._contains_timestamp(recent_readings, latest_reading):
                recent_readings = tuple(sorted([*recent_readings, latest_reading], key=lambda r: r.device_timestamp_utc))

            return LLUPollSnapshot(
                polled_at_utc=polled_at_utc,
                ok=True,
                latest_reading=latest_reading,
                recent_readings=recent_readings,
                message=f"LLU poll ok for patient index {self.patient_index}",
            )

        except Exception as exc:
            # Reset auth state so the next poll can retry cleanly.
            self._authenticated = False
            return LLUPollSnapshot(
                polled_at_utc=polled_at_utc,
                ok=False,
                latest_reading=None,
                recent_readings=(),
                message=f"LLU poll exception: {type(exc).__name__}: {exc}",
            )

    def _resolve_patient_identifier(self) -> Optional[object]:
        patients = self._client.get_patients()
        if not patients:
            return None

        if self.patient_index < 0 or self.patient_index >= len(patients):
            raise RuntimeError(
                f"Patient index {self.patient_index} is out of range for {len(patients)} connection(s)."
            )

        return patients[self.patient_index]

    def _normalize_graph_measurements(
        self,
        graph_measurements: Sequence[object],
        fetched_at_utc: datetime,
    ) -> list[GlucoseReading]:
        readings: list[GlucoseReading] = []

        for measurement in graph_measurements:
            reading = self._normalize_single_measurement(
                measurement=measurement,
                fetched_at_utc=fetched_at_utc,
            )
            if reading is not None:
                readings.append(reading)

        readings.sort(key=lambda reading: reading.device_timestamp_utc)
        return readings

    def _normalize_single_measurement(
        self,
        measurement: object,
        fetched_at_utc: datetime,
    ) -> Optional[GlucoseReading]:
        timestamp = self._extract_timestamp(measurement)
        value = self._extract_value(measurement)
        trend_label = self._extract_trend_label(measurement)

        if timestamp is None or value is None:
            return None

        return GlucoseReading(
            device_timestamp_utc=timestamp,
            fetched_at_utc=fetched_at_utc,
            mgdl=float(value),
            trend_label=trend_label,
            source="llu",
        )

    @staticmethod
    def _contains_timestamp(
        readings: Sequence[GlucoseReading],
        candidate: GlucoseReading,
    ) -> bool:
        return any(reading.device_timestamp_utc == candidate.device_timestamp_utc for reading in readings)

    @staticmethod
    def _extract_value(measurement: object) -> Optional[float]:
        for attr in ("value", "glucose", "measurement"):
            if hasattr(measurement, attr):
                raw_value = getattr(measurement, attr)
                if raw_value is None:
                    continue
                try:
                    return float(raw_value)
                except (TypeError, ValueError):
                    return None
        return None

    @staticmethod
    def _extract_trend_label(measurement: object) -> Optional[str]:
        for attr in ("trend_arrow", "trend", "trend_label"):
            if hasattr(measurement, attr):
                raw_value = getattr(measurement, attr)
                if raw_value is None:
                    return None
                return str(raw_value)
        return None

    @staticmethod
    def _extract_timestamp(measurement: object) -> Optional[datetime]:
        candidates: list[object] = []

        for attr in (
            "timestamp",
            "factory_timestamp",
            "measurement_timestamp",
            "date",
            "datetime",
        ):
            if hasattr(measurement, attr):
                candidates.append(getattr(measurement, attr))

        for candidate in candidates:
            normalized = LibreLinkUpPoller._coerce_to_utc_datetime(candidate)
            if normalized is not None:
                return normalized

        return None

    @staticmethod
    def _coerce_to_utc_datetime(raw: object) -> Optional[datetime]:
        if raw is None:
            return None

        if isinstance(raw, datetime):
            if raw.tzinfo is None:
                return raw.replace(tzinfo=UTC)
            return raw.astimezone(UTC)

        if isinstance(raw, str):
            text = raw.strip()
            if text.endswith("Z"):
                text = text[:-1] + "+00:00"
            try:
                parsed = datetime.fromisoformat(text)
            except ValueError:
                return None

            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=UTC)
            return parsed.astimezone(UTC)

        return None



# =============================================================================
# LOCAL TEST HARNESS
# =============================================================================


def _print_reading(label: str, reading: Optional[GlucoseReading]) -> None:
    """Pretty-print one normalized reading for manual testing."""
    print(f"\n{label}")
    print("-" * len(label))

    if reading is None:
        print("None")
        return

    pprint(
        {
            "device_timestamp_utc": reading.device_timestamp_utc.isoformat(),
            "fetched_at_utc": reading.fetched_at_utc.isoformat(),
            "mgdl": reading.mgdl,
            "trend_label": reading.trend_label,
            "source": reading.source,
        }
    )


def _main() -> int:
    """
    Tiny smoke test.

    What this does:
    - builds the LLU poller
    - performs one real poll
    - prints a compact summary
    - prints the latest normalized reading
    - prints the first and last recent readings

    This is intentionally boring.
    We just want to know whether the polling boundary works.
    """
    poller = LibreLinkUpPoller()
    snapshot = poller.poll()

    print("\nLLU POLL SUMMARY")
    print("================")
    print(f"ok: {snapshot.ok}")
    print(f"message: {snapshot.message}")
    print(f"polled_at_utc: {snapshot.polled_at_utc.isoformat()}")
    print(f"recent_count: {len(snapshot.recent_readings)}")

    if snapshot.recent_readings:
        first = snapshot.recent_readings[0]
        last = snapshot.recent_readings[-1]
        print(f"recent_window_start: {first.device_timestamp_utc.isoformat()}")
        print(f"recent_window_end:   {last.device_timestamp_utc.isoformat()}")

    _print_reading("LATEST READING", snapshot.latest_reading)

    if snapshot.recent_readings:
        _print_reading("FIRST RECENT READING", snapshot.recent_readings[0])
        _print_reading("LAST RECENT READING", snapshot.recent_readings[-1])

    return 0 if snapshot.ok else 1


if __name__ == "__main__":
    raise SystemExit(_main())
