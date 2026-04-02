"""
Shared database module for claude-token-tracker.
Provides schema creation, migration, connection management, and cost calculation.
DB path: ~/.claude-tracker/tracker.db
"""
import contextlib
import pathlib
import sqlite3

DB_PATH = pathlib.Path.home() / ".claude-tracker" / "tracker.db"

# Pricing per million tokens (April 2026)
# Update these when Anthropic changes pricing.
MODEL_PRICING: dict = {
    "claude-opus-4-6": {
        "input": 15.00,
        "output": 75.00,
        "cache_creation": 18.75,
        "cache_read": 1.50,
    },
    "claude-sonnet-4-6": {
        "input": 3.00,
        "output": 15.00,
        "cache_creation": 3.75,
        "cache_read": 0.30,
    },
    "claude-haiku-4-5": {
        "input": 0.80,
        "output": 4.00,
        "cache_creation": 1.00,
        "cache_read": 0.08,
    },
    # Legacy model names
    "claude-opus-4": {
        "input": 15.00,
        "output": 75.00,
        "cache_creation": 18.75,
        "cache_read": 1.50,
    },
    "claude-sonnet-4": {
        "input": 3.00,
        "output": 15.00,
        "cache_creation": 3.75,
        "cache_read": 0.30,
    },
    "claude-3-5-sonnet-20241022": {
        "input": 3.00,
        "output": 15.00,
        "cache_creation": 3.75,
        "cache_read": 0.30,
    },
    "claude-3-5-haiku-20241022": {
        "input": 0.80,
        "output": 4.00,
        "cache_creation": 1.00,
        "cache_read": 0.08,
    },
    "claude-3-opus-20240229": {
        "input": 15.00,
        "output": 75.00,
        "cache_creation": 18.75,
        "cache_read": 1.50,
    },
    "_default": {
        "input": 3.00,
        "output": 15.00,
        "cache_creation": 3.75,
        "cache_read": 0.30,
    },
}

_CREATE_PROMPTS = """
CREATE TABLE IF NOT EXISTS prompts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp       TEXT    NOT NULL,
    session_id      TEXT    NOT NULL,
    prompt          TEXT    NOT NULL,
    char_count      INTEGER NOT NULL,
    cwd             TEXT,
    transcript_path TEXT
);
"""

_CREATE_RESPONSES = """
CREATE TABLE IF NOT EXISTS responses (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp             TEXT    NOT NULL,
    session_id            TEXT    NOT NULL,
    prompt_id             INTEGER,
    input_tokens          INTEGER,
    output_tokens         INTEGER,
    cache_creation_tokens INTEGER,
    cache_read_tokens     INTEGER,
    total_tokens          INTEGER,
    cost_usd              REAL,
    model                 TEXT,
    transcript_path       TEXT
);
"""

_CREATE_SESSIONS = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id          TEXT PRIMARY KEY,
    first_seen          TEXT NOT NULL,
    last_seen           TEXT NOT NULL,
    prompt_count        INTEGER NOT NULL DEFAULT 0,
    total_input_tokens  INTEGER NOT NULL DEFAULT 0,
    total_output_tokens INTEGER NOT NULL DEFAULT 0,
    total_cost_usd      REAL    NOT NULL DEFAULT 0.0
);
"""

_VIEW_DAILY_STATS = """
CREATE VIEW daily_stats AS
    SELECT
        date(r.timestamp)               AS day,
        COUNT(r.id)                     AS prompt_count,
        COALESCE(SUM(r.input_tokens), 0)         AS total_input_tokens,
        COALESCE(SUM(r.output_tokens), 0)        AS total_output_tokens,
        COALESCE(SUM(r.cache_read_tokens), 0)    AS total_cache_read_tokens,
        COALESCE(SUM(r.total_tokens), 0)         AS total_tokens,
        COALESCE(SUM(r.cost_usd), 0)             AS total_cost_usd,
        COUNT(DISTINCT r.session_id)    AS session_count
    FROM responses r
    GROUP BY date(r.timestamp)
    ORDER BY day DESC;
"""

_VIEW_HOURLY = """
CREATE VIEW hourly_distribution AS
    SELECT
        CAST(strftime('%H', timestamp) AS INTEGER) AS hour,
        COUNT(*)                                   AS prompt_count,
        COALESCE(SUM(total_tokens), 0)             AS total_tokens
    FROM responses
    GROUP BY hour
    ORDER BY hour;
"""

_VIEW_MODEL = """
CREATE VIEW model_usage AS
    SELECT
        COALESCE(model, 'unknown')   AS model,
        COUNT(*)                     AS response_count,
        COALESCE(SUM(input_tokens), 0) + COALESCE(SUM(cache_creation_tokens), 0) + COALESCE(SUM(cache_read_tokens), 0)
                                        AS total_input_tokens,
        COALESCE(SUM(output_tokens), 0) AS total_output_tokens,
        COALESCE(SUM(cost_usd), 0)      AS total_cost_usd
    FROM responses
    GROUP BY model
    ORDER BY total_cost_usd DESC;
"""


def calculate_cost(
    model,
    input_tokens: int,
    output_tokens: int,
    cache_creation: int,
    cache_read: int,
) -> float:
    pricing = MODEL_PRICING.get(model or "", MODEL_PRICING["_default"])
    cost = (
        input_tokens * pricing["input"] / 1_000_000
        + output_tokens * pricing["output"] / 1_000_000
        + cache_creation * pricing["cache_creation"] / 1_000_000
        + cache_read * pricing["cache_read"] / 1_000_000
    )
    return round(cost, 8)


def _create_schema(conn: sqlite3.Connection) -> None:
    conn.execute(_CREATE_PROMPTS)
    conn.execute(_CREATE_RESPONSES)
    conn.execute(_CREATE_SESSIONS)


def _migrate(conn: sqlite3.Connection) -> None:
    """Non-destructive migration: add missing columns to existing tables."""
    cursor = conn.cursor()

    # prompts table: old schema has `estimated_tokens INTEGER NOT NULL` which breaks
    # new INSERTs that don't provide it. Rebuild the table to make it nullable.
    cursor.execute("PRAGMA table_info(prompts)")
    prompt_col_info = cursor.fetchall()
    prompt_cols = {row[1]: row for row in prompt_col_info}
    if "estimated_tokens" in prompt_cols:
        # notnull=1 means NOT NULL constraint — needs rebuild
        notnull = prompt_col_info[[r[1] for r in prompt_col_info].index("estimated_tokens")][3]
        if notnull:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS prompts_v2 (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp       TEXT    NOT NULL,
                    session_id      TEXT    NOT NULL,
                    prompt          TEXT    NOT NULL,
                    char_count      INTEGER NOT NULL,
                    cwd             TEXT,
                    transcript_path TEXT
                )
            """)
            conn.execute("""
                INSERT OR IGNORE INTO prompts_v2
                    (id, timestamp, session_id, prompt, char_count, cwd, transcript_path)
                SELECT id, timestamp, session_id, prompt, char_count, cwd, transcript_path
                FROM prompts
            """)
            conn.execute("DROP TABLE prompts")
            conn.execute("ALTER TABLE prompts_v2 RENAME TO prompts")

    # responses table
    cursor.execute("PRAGMA table_info(responses)")
    resp_cols = {row[1] for row in cursor.fetchall()}
    for col, defn in [
        ("prompt_id", "INTEGER"),
        ("total_tokens", "INTEGER"),
        ("model", "TEXT"),
        ("cache_creation_tokens", "INTEGER"),
        ("cache_read_tokens", "INTEGER"),
    ]:
        if col not in resp_cols:
            conn.execute(f"ALTER TABLE responses ADD COLUMN {col} {defn}")

    # sessions table
    cursor.execute("PRAGMA table_info(sessions)")
    sess_cols = {row[1] for row in cursor.fetchall()}
    for col, defn in [
        ("total_input_tokens", "INTEGER NOT NULL DEFAULT 0"),
        ("total_output_tokens", "INTEGER NOT NULL DEFAULT 0"),
        ("total_cost_usd", "REAL NOT NULL DEFAULT 0.0"),
    ]:
        if col not in sess_cols:
            conn.execute(f"ALTER TABLE sessions ADD COLUMN {col} {defn}")

    # Recreate views (DROP + CREATE to pick up schema changes)
    for view in ("daily_stats", "hourly_distribution", "model_usage"):
        conn.execute(f"DROP VIEW IF EXISTS {view}")
    conn.execute(_VIEW_DAILY_STATS)
    conn.execute(_VIEW_HOURLY)
    conn.execute(_VIEW_MODEL)


def ensure_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    _create_schema(conn)
    _migrate(conn)
    conn.commit()
    return conn


@contextlib.contextmanager
def get_conn():
    conn = ensure_db()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    conn = ensure_db()
    cursor = conn.cursor()
    cursor.execute("SELECT sql FROM sqlite_master WHERE type IN ('table', 'view') ORDER BY type, name")
    for row in cursor.fetchall():
        print(row[0])
        print()
    conn.close()
    print(f"DB ready at {DB_PATH}")
