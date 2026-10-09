"""Durable local MVP media queue. Private data is never served as static files.

One backend process owns this SQLite queue. Live lesson cards are published to
the primary PostgreSQL database; local demo files stay in the ignored media dir.
"""
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Any

from app.config import get_settings


def root() -> Path:
    path = get_settings().media_dir
    path.mkdir(parents=True, exist_ok=True)
    return path


@contextmanager
def connection() -> Iterator[sqlite3.Connection]:
    with sqlite3.connect(root() / "queue.sqlite", timeout=15) as db:
        db.row_factory = sqlite3.Row
        db.execute('''CREATE TABLE IF NOT EXISTS recordings (
            id TEXT PRIMARY KEY, lesson_id INTEGER NOT NULL, scope TEXT NOT NULL,
            status TEXT NOT NULL, stage TEXT NOT NULL, error TEXT, filename TEXT NOT NULL,
            created_at TEXT NOT NULL, duration REAL, card TEXT, transcript TEXT,
            attempts INTEGER NOT NULL DEFAULT 0)''')
        db.execute("CREATE UNIQUE INDEX IF NOT EXISTS one_live_recording ON recordings(lesson_id) WHERE scope='live'")
        yield db


def get(recording_id: str) -> dict[str, Any] | None:
    with connection() as db:
        row = db.execute("SELECT * FROM recordings WHERE id=?", (recording_id,)).fetchone()
    return dict(row) if row else None


def insert(recording_id: str, lesson_id: int, scope: str, filename: str) -> None:
    with connection() as db:
        db.execute("INSERT INTO recordings(id,lesson_id,scope,status,stage,filename,created_at) VALUES(?,?,?,'queued','queued',?,?)",
                   (recording_id, lesson_id, scope, filename, datetime.now(timezone.utc).isoformat()))


def update(recording_id: str, **values: Any) -> None:
    allowed = {"status", "stage", "error", "duration", "card", "transcript"}
    if not values or not values.keys() <= allowed:
        raise ValueError("Invalid update fields")
    with connection() as db:
        db.execute("UPDATE recordings SET " + ",".join(f"{key}=?" for key in values) + " WHERE id=?", (*values.values(), recording_id))


def public(row: dict[str, Any]) -> dict[str, Any]:
    return {**{k: row[k] for k in ("id", "lesson_id", "status", "stage", "error", "filename", "created_at", "duration", "transcript")},
            "card": json.loads(row["card"]) if row["card"] else None}


def recover() -> None:
    with connection() as db:
        db.execute("UPDATE recordings SET status='queued',stage='queued' WHERE status='processing'")


def claim() -> dict[str, Any] | None:
    with connection() as db:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("SELECT * FROM recordings WHERE status='queued' ORDER BY created_at LIMIT 1").fetchone()
        if row:
            db.execute("UPDATE recordings SET status='processing',attempts=attempts+1,error=NULL WHERE id=?", (row["id"],))
        return dict(row) if row else None
