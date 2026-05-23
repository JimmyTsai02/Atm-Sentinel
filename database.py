from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class EventRecord:
    risk_level: int
    reason: str
    event_type: str
    screenshot_path: str
    actions: str


class EventDatabase:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    risk_level INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    screenshot_path TEXT NOT NULL,
                    actions TEXT NOT NULL
                )
                """
            )

    def log_event(self, record: EventRecord) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO events (
                    created_at,
                    risk_level,
                    reason,
                    event_type,
                    screenshot_path,
                    actions
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.now().isoformat(timespec="seconds"),
                    record.risk_level,
                    record.reason,
                    record.event_type,
                    record.screenshot_path,
                    record.actions,
                ),
            )
            return int(cursor.lastrowid)
