from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = Path(os.getenv("SALESOPS_DB_PATH", PROJECT_ROOT / "database" / "salesops.db"))

@contextmanager
def connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback(); raise
    finally:
        conn.close()

def query(sql: str, params: tuple = ()) -> list[dict]:
    if not sql.lstrip().upper().startswith(("SELECT", "WITH", "PRAGMA")):
        raise ValueError("Only read-only SQL is allowed through query()")
    with connection() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]

def execute(sql: str, params: tuple = ()) -> int:
    with connection() as conn:
        cursor = conn.execute(sql, params)
        return cursor.lastrowid

def table_exists(name: str) -> bool:
    return bool(query("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)))

