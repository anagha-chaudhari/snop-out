import sqlite3

DEFAULT_DB_PATH = "snopout.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS records (
    id INTEGER PRIMARY KEY,
    connector TEXT NOT NULL,
    external_id TEXT NOT NULL,
    payload TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (connector, external_id)
);

CREATE TABLE IF NOT EXISTS sync_state (
    connector TEXT PRIMARY KEY,
    cursor TEXT,
    last_success_at TEXT
);

CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY,
    connector TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL CHECK (status IN ('running', 'success', 'failed')),
    rows_loaded INTEGER NOT NULL DEFAULT 0,
    error TEXT
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'viewer'))
);
"""


def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    # Open the database. Rows can be read by column name
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    # Create all tables if they do not exist yet. Safe to call repeatedly
    conn.executescript(SCHEMA)


if __name__ == "__main__":
    conn = get_connection()
    init_db(conn)
    init_db(conn)  # a second call - harmless

    names = "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    tables = [row["name"] for row in conn.execute(names)]
    print("tables:", tables)
    print("journal mode:", conn.execute("PRAGMA journal_mode").fetchone()[0])
    for table in tables:  # PRAGMA cannot take ? parameters; names come from our own schema
        print(f"{table}:", [col["name"] for col in conn.execute(f"PRAGMA table_info({table})")])

    for column in ("connector", "updated_at"):
        plan = conn.execute(f"EXPLAIN QUERY PLAN SELECT * FROM records WHERE {column} = ?", ("x",)).fetchone()
        print(f"search by {column}:", plan["detail"])

    try:
        conn.execute("INSERT INTO runs (connector, started_at, status) VALUES ('github', 'now', 'banana')")
    except sqlite3.IntegrityError as exc:
        print("rejected:", exc)