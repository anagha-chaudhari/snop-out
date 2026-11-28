import json
import sqlite3

conn = sqlite3.connect(":memory:")

COLUMNS = "id INTEGER PRIMARY KEY, connector TEXT NOT NULL, external_id TEXT NOT NULL, payload TEXT NOT NULL"
conn.execute(f"CREATE TABLE naive ({COLUMNS})")
conn.execute(f"CREATE TABLE safe ({COLUMNS}, UNIQUE (connector, external_id))")

ROW = ("github", "1234567", json.dumps({"stars": 100}))

# no protection. Simulate running a sync twice.
for run in (1, 2):
    conn.execute("INSERT INTO naive (connector, external_id, payload) VALUES (?, ?, ?)", ROW)
    print(f"naive after run {run}:", conn.execute("SELECT COUNT(*) FROM naive").fetchone()[0], "rows")

# the UNIQUE rule refuses the second copy.
conn.execute("INSERT INTO safe (connector, external_id, payload) VALUES (?, ?, ?)", ROW)
print("safe after run 1:", conn.execute("SELECT COUNT(*) FROM safe").fetchone()[0], "rows")
try:
    conn.execute("INSERT INTO safe (connector, external_id, payload) VALUES (?, ?, ?)", ROW)
except sqlite3.IntegrityError as exc:
    print("safe run 2 rejected:", exc)

# read the payload back.
text = conn.execute("SELECT payload FROM safe").fetchone()[0]
print(type(text).__name__, text, "->", json.loads(text)["stars"])

# placeholders matter.
evil = "nobody' OR '1'='1"
unsafe_sql = f"SELECT COUNT(*) FROM safe WHERE connector = '{evil}'"
print("unsafe query matched:", conn.execute(unsafe_sql).fetchone()[0])
print("placeholder query matched:", conn.execute("SELECT COUNT(*) FROM safe WHERE connector = ?", (evil,)).fetchone()[0])