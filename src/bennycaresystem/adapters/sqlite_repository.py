from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

from bennycaresystem.domain.care_events import CareEvent
from bennycaresystem.domain.glucose_readings import GlucoseReading


# -----------------------------------------------------------------------------
# Small row DTOs for read operations.
#
# I am keeping these separate from the domain objects so the domain objects stay
# focused on validated business data, while reads can optionally include DB ids.
# -----------------------------------------------------------------------------
@dataclass(frozen=True)
class CareEventRow:
    id: int
    timestamp_utc: datetime
    event_type: str
    value: float
    unit: str
    created_at_utc: datetime


@dataclass(frozen=True)
class GlucoseReadingRow:
    id: int
    device_timestamp_utc: datetime
    mgdl: float
    trend_label: Optional[str]
    source: str
    fetched_at_utc: Optional[datetime]


class SQLiteRepository:
    """
    Very small SQLite repository for BCS care events + glucose readings.

    Responsibilities:
    - initialize the database schema
    - insert validated CareEvent objects
    - insert validated GlucoseReading objects
    - provide a few tiny read helpers

    Non-goals for this first pass:
    - migrations
    - fancy query language
    - connection pooling
    - write batching
    """

    def __init__(self, db_path: str | Path, schema_path: str | Path) -> None:
        self._db_path = Path(db_path)
        self._schema_path = Path(schema_path)

    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------
    def init_db(self) -> None:
        """
        Initialize the SQLite DB using schema.sql.

        Preconditions:
        - schema_path exists and contains valid SQL

        Postconditions:
        - DB file exists
        - schema has been applied
        """
        self._db_path.parent.mkdir(parents=True, exist_ok=True)

        schema_sql = self._schema_path.read_text(encoding="utf-8")

        with self._connect() as connection:
            connection.executescript(schema_sql)
            connection.commit()

    # -------------------------------------------------------------------------
    # Inserts
    # -------------------------------------------------------------------------
    def insert_care_event(self, event: CareEvent) -> int:
        """
        Insert one validated care event.

        Returns:
        - inserted row id
        """
        sql = """
        INSERT INTO care_events (
            timestamp_utc,
            event_type,
            value,
            unit,
            created_at_utc
        )
        VALUES (?, ?, ?, ?, ?)
        """

        params = (
            _to_iso_utc(event.timestamp_utc),
            event.event_type,
            event.value,
            event.unit,
            _to_iso_utc(event.created_at_utc),
        )

        with self._connect() as connection:
            cursor = connection.execute(sql, params)
            connection.commit()
            return int(cursor.lastrowid)

    def insert_glucose_reading(self, reading: GlucoseReading) -> int | None:
        """
        Insert one validated glucose reading.

        Because the schema has a uniqueness constraint on:
            (source, device_timestamp_utc)

        repeated imports of the same reading are ignored.

        Returns:
        - inserted row id if a new row was inserted
        - None if the reading already existed
        """
        sql = """
        INSERT OR IGNORE INTO glucose_readings (
            device_timestamp_utc,
            mgdl,
            trend_label,
            source,
            fetched_at_utc
        )
        VALUES (?, ?, ?, ?, ?)
        """

        params = (
            _to_iso_utc(reading.device_timestamp_utc),
            reading.mgdl,
            reading.trend_label,
            reading.source,
            (
                _to_iso_utc(reading.fetched_at_utc)
                if reading.fetched_at_utc is not None
                else None
            ),
        )

        with self._connect() as connection:
            cursor = connection.execute(sql, params)
            connection.commit()

            if cursor.rowcount == 0:
                return None

            return int(cursor.lastrowid)

    def insert_glucose_readings(
        self,
        readings: Iterable[GlucoseReading],
    ) -> int:
        """
        Insert many glucose readings.

        Duplicate readings are ignored by the unique index.

        Returns:
        - number of newly inserted rows
        """
        sql = """
        INSERT OR IGNORE INTO glucose_readings (
            device_timestamp_utc,
            mgdl,
            trend_label,
            source,
            fetched_at_utc
        )
        VALUES (?, ?, ?, ?, ?)
        """

        rows = [
            (
                _to_iso_utc(reading.device_timestamp_utc),
                reading.mgdl,
                reading.trend_label,
                reading.source,
                (
                    _to_iso_utc(reading.fetched_at_utc)
                    if reading.fetched_at_utc is not None
                    else None
                ),
            )
            for reading in readings
        ]

        if not rows:
            return 0

        with self._connect() as connection:
            before_changes = connection.total_changes
            connection.executemany(sql, rows)
            connection.commit()
            after_changes = connection.total_changes
            return int(after_changes - before_changes)

    # -------------------------------------------------------------------------
    # Simple reads
    # -------------------------------------------------------------------------
    def list_recent_care_events(self, limit: int = 20) -> list[CareEventRow]:
        """
        Return recent care events in descending timestamp order.
        """
        if limit <= 0:
            raise ValueError("limit must be positive.")

        sql = """
        SELECT
            id,
            timestamp_utc,
            event_type,
            value,
            unit,
            created_at_utc
        FROM care_events
        ORDER BY timestamp_utc DESC, id DESC
        LIMIT ?
        """

        with self._connect() as connection:
            cursor = connection.execute(sql, (limit,))
            rows = cursor.fetchall()

        return [
            CareEventRow(
                id=int(row["id"]),
                timestamp_utc=_from_iso_utc(row["timestamp_utc"]),
                event_type=str(row["event_type"]),
                value=float(row["value"]),
                unit=str(row["unit"]),
                created_at_utc=_from_iso_utc(row["created_at_utc"]),
            )
            for row in rows
        ]

    def list_recent_glucose_readings(
        self,
        limit: int = 50,
    ) -> list[GlucoseReadingRow]:
        """
        Return recent glucose readings in descending device timestamp order.
        """
        if limit <= 0:
            raise ValueError("limit must be positive.")

        sql = """
        SELECT
            id,
            device_timestamp_utc,
            mgdl,
            trend_label,
            source,
            fetched_at_utc
        FROM glucose_readings
        ORDER BY device_timestamp_utc DESC, id DESC
        LIMIT ?
        """

        with self._connect() as connection:
            cursor = connection.execute(sql, (limit,))
            rows = cursor.fetchall()

        return [
            GlucoseReadingRow(
                id=int(row["id"]),
                device_timestamp_utc=_from_iso_utc(row["device_timestamp_utc"]),
                mgdl=float(row["mgdl"]),
                trend_label=(
                    str(row["trend_label"])
                    if row["trend_label"] is not None
                    else None
                ),
                source=str(row["source"]),
                fetched_at_utc=(
                    _from_iso_utc(row["fetched_at_utc"])
                    if row["fetched_at_utc"] is not None
                    else None
                ),
            )
            for row in rows
        ]

    def get_care_events_between(
        self,
        *,
        start_utc: datetime,
        end_utc: datetime,
    ) -> list[CareEventRow]:
        """
        Return care events in [start_utc, end_utc], ordered ascending.

        Preconditions:
        - start_utc and end_utc are timezone-aware
        - start_utc <= end_utc
        """
        start_utc = _normalize_to_utc(start_utc)
        end_utc = _normalize_to_utc(end_utc)

        if start_utc > end_utc:
            raise ValueError("start_utc must be <= end_utc.")

        sql = """
        SELECT
            id,
            timestamp_utc,
            event_type,
            value,
            unit,
            created_at_utc
        FROM care_events
        WHERE timestamp_utc >= ?
          AND timestamp_utc <= ?
        ORDER BY timestamp_utc ASC, id ASC
        """

        params = (
            _to_iso_utc(start_utc),
            _to_iso_utc(end_utc),
        )

        with self._connect() as connection:
            cursor = connection.execute(sql, params)
            rows = cursor.fetchall()

        return [
            CareEventRow(
                id=int(row["id"]),
                timestamp_utc=_from_iso_utc(row["timestamp_utc"]),
                event_type=str(row["event_type"]),
                value=float(row["value"]),
                unit=str(row["unit"]),
                created_at_utc=_from_iso_utc(row["created_at_utc"]),
            )
            for row in rows
        ]

    def get_glucose_readings_between(
        self,
        *,
        start_utc: datetime,
        end_utc: datetime,
    ) -> list[GlucoseReadingRow]:
        """
        Return glucose readings in [start_utc, end_utc], ordered ascending.

        Preconditions:
        - start_utc and end_utc are timezone-aware
        - start_utc <= end_utc
        """
        start_utc = _normalize_to_utc(start_utc)
        end_utc = _normalize_to_utc(end_utc)

        if start_utc > end_utc:
            raise ValueError("start_utc must be <= end_utc.")

        sql = """
        SELECT
            id,
            device_timestamp_utc,
            mgdl,
            trend_label,
            source,
            fetched_at_utc
        FROM glucose_readings
        WHERE device_timestamp_utc >= ?
          AND device_timestamp_utc <= ?
        ORDER BY device_timestamp_utc ASC, id ASC
        """

        params = (
            _to_iso_utc(start_utc),
            _to_iso_utc(end_utc),
        )

        with self._connect() as connection:
            cursor = connection.execute(sql, params)
            rows = cursor.fetchall()

        return [
            GlucoseReadingRow(
                id=int(row["id"]),
                device_timestamp_utc=_from_iso_utc(row["device_timestamp_utc"]),
                mgdl=float(row["mgdl"]),
                trend_label=(
                    str(row["trend_label"])
                    if row["trend_label"] is not None
                    else None
                ),
                source=str(row["source"]),
                fetched_at_utc=(
                    _from_iso_utc(row["fetched_at_utc"])
                    if row["fetched_at_utc"] is not None
                    else None
                ),
            )
            for row in rows
        ]

    # -------------------------------------------------------------------------
    # Internal connection helper
    # -------------------------------------------------------------------------
    def _connect(self) -> sqlite3.Connection:
        """
        Open a SQLite connection configured for simple app use.

        Notes:
        - row_factory lets us access columns by name
        - foreign_keys is turned on defensively
        """
        connection = sqlite3.connect(self._db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON;")
        return connection


def _to_iso_utc(value: datetime) -> str:
    """
    Serialize a UTC-aware datetime to ISO-8601 text.

    We store text because:
    - it's simple
    - SQLite handles it fine
    - it's easy to inspect manually
    """
    value = _normalize_to_utc(value)
    return value.isoformat()


def _from_iso_utc(value: str) -> datetime:
    """
    Parse an ISO-8601 datetime string back into a datetime.

    Postcondition:
    - returned datetime is normalized to UTC
    """
    parsed = datetime.fromisoformat(value)
    return _normalize_to_utc(parsed)


def _normalize_to_utc(value: datetime) -> datetime:
    """
    Normalize a timezone-aware datetime to UTC.

    Raises for naive datetimes to avoid silent timezone bugs.
    """
    if value.tzinfo is None:
        raise ValueError("Datetime must be timezone-aware.")
    return value.astimezone(timezone.utc)