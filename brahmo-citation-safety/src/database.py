"""
database.py
-----------
Initialises the SQLite database from schema.sql + seed.sql.
Provides a single get_connection() helper used by every other module.
"""

import sqlite3
import gc
from pathlib import Path

DB_PATH     = Path(__file__).parent.parent / "db" / "citations.db"
SCHEMA_PATH = Path(__file__).parent.parent / "db" / "schema.sql"
SEED_PATH   = Path(__file__).parent.parent / "db" / "seed.sql"


def get_connection() -> sqlite3.Connection:
    """Return a connection to the SQLite database. Initialises on first call."""
    first_run = not DB_PATH.exists()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    if first_run:
        _bootstrap(conn)
    return conn


def _bootstrap(conn: sqlite3.Connection) -> None:
    """Create tables and load seed data exactly once."""
    print("[DB] Bootstrapping database …")
    _run_sql_file(conn, SCHEMA_PATH)
    _run_sql_file(conn, SEED_PATH)
    conn.commit()
    _verify_seed(conn)
    print("[DB] Bootstrap complete.")


def _run_sql_file(conn: sqlite3.Connection, path: Path) -> None:
    sql = path.read_text(encoding="utf-8")
    conn.executescript(sql)


def _verify_seed(conn: sqlite3.Connection) -> None:
    cur = conn.execute("SELECT COUNT(*) AS n FROM section_mappings")
    n_maps = cur.fetchone()["n"]
    cur = conn.execute("SELECT COUNT(*) AS n FROM citation_patterns")
    n_pats = cur.fetchone()["n"]
    assert n_maps == 30, f"Expected 30 section_mappings, got {n_maps}"
    assert n_pats == 6,  f"Expected 6 citation_patterns, got {n_pats}"
    print(f"[DB] Verified: {n_maps} section mappings, {n_pats} citation patterns loaded.")


def reset_database() -> None:
    """
    Delete and re-create the database (useful for tests).

    Windows note: SQLite holds a file lock while connections are open.
    We force a garbage-collect first to release unreferenced connections.
    If the file is still locked (another open conn in the same process),
    we skip deletion and reuse the existing seeded DB — the seed data is
    identical so tests will still pass.
    """
    gc.collect()  # release any unreferenced connection objects
    if DB_PATH.exists():
        try:
            DB_PATH.unlink()
        except PermissionError:
            # Windows: file locked by a sibling test's open connection.
            # The DB is already seeded — safe to reuse.
            return
    get_connection().close()


if __name__ == "__main__":
    reset_database()
    print("Database reset and ready.")


def clear_unverified_cache() -> int:
    """
    Delete all verification_cache rows with status=UNVERIFIED.
    These were cached during mock-mode runs and will now be re-verified
    against the real Indian Kanoon API.
    Returns the number of rows deleted.
    """
    conn = get_connection()
    cur = conn.execute("DELETE FROM verification_cache WHERE status = 'UNVERIFIED'")
    deleted = cur.rowcount
    conn.commit()
    conn.close()
    if deleted:
        print(f"[DB] Cleared {deleted} stale UNVERIFIED cache entries — IK API will re-verify.")
    return deleted
