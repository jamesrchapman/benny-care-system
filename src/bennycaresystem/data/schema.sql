PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS care_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp_utc TEXT NOT NULL,
    event_type TEXT NOT NULL,
    value REAL NOT NULL,
    unit TEXT NOT NULL,
    created_at_utc TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_care_events_timestamp_utc
    ON care_events(timestamp_utc);

CREATE INDEX IF NOT EXISTS idx_care_events_type_timestamp
    ON care_events(event_type, timestamp_utc);


CREATE TABLE IF NOT EXISTS glucose_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_timestamp_utc TEXT NOT NULL,
    mgdl REAL NOT NULL,
    trend_label TEXT,
    source TEXT NOT NULL,
    fetched_at_utc TEXT
);

CREATE INDEX IF NOT EXISTS idx_glucose_readings_device_timestamp_utc
    ON glucose_readings(device_timestamp_utc);

CREATE INDEX IF NOT EXISTS idx_glucose_readings_source_timestamp
    ON glucose_readings(source, device_timestamp_utc);

CREATE UNIQUE INDEX IF NOT EXISTS uq_glucose_readings_source_device_time
    ON glucose_readings(source, device_timestamp_utc);