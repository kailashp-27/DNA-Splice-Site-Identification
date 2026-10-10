"""Local, transactional history. Each completed run is an immutable JSON snapshot."""
from contextlib import contextmanager
import json
from pathlib import Path
import sqlite3


class RunStore:
    def __init__(self, path):
        self.path = Path(path)

    @contextmanager
    def connection(self):
        # A separate connection per operation supports FastAPI's worker threads.
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def initialize(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as connection:
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 1):
                raise ValueError("Unsupported history database version; use the matching EcoSplice release.")
            connection.execute("""CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY, name TEXT NOT NULL,
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                summary TEXT NOT NULL, snapshot TEXT NOT NULL
            )""")
            connection.execute("PRAGMA user_version = 1")

    def save(self, run):
        analysis = run["analysis"]
        summary = {"input": analysis["input"], "method": analysis["method"],
                   "model_id": analysis["model_id"], "work": analysis["work"],
                   "timing_ms": analysis["timing_ms"], "energy": run["energy"]}
        with self.connection() as connection:
            connection.execute("INSERT INTO runs VALUES (?, ?, ?, ?, ?, ?)",
                               (run["id"], run["name"], run["created_at"], run["updated_at"],
                                json.dumps(summary, allow_nan=False), json.dumps(run, allow_nan=False)))

    def list(self, limit=50, offset=0):
        with self.connection() as connection:
            total = connection.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
            rows = connection.execute("SELECT id, name, created_at, updated_at, summary FROM runs "
                                      "ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?", (limit, offset)).fetchall()
        return {"total": total, "limit": limit, "offset": offset,
                "runs": [{"id": row["id"], "name": row["name"], "created_at": row["created_at"],
                          "updated_at": row["updated_at"], **json.loads(row["summary"])} for row in rows]}

    def get(self, run_id):
        with self.connection() as connection:
            row = connection.execute("SELECT name, updated_at, snapshot FROM runs WHERE id = ?", (run_id,)).fetchone()
        if row is None:
            raise KeyError(run_id)
        run = json.loads(row["snapshot"])
        # Rename changes presentation metadata, never the scientific snapshot.
        run.update(name=row["name"], updated_at=row["updated_at"])
        return run

    def rename(self, run_id, name, updated_at):
        with self.connection() as connection:
            cursor = connection.execute("UPDATE runs SET name = ?, updated_at = ? WHERE id = ?",
                                        (name, updated_at, run_id))
            if cursor.rowcount == 0:
                raise KeyError(run_id)
        return self.get(run_id)

    def delete(self, run_id):
        with self.connection() as connection:
            cursor = connection.execute("DELETE FROM runs WHERE id = ?", (run_id,))
            if cursor.rowcount == 0:
                raise KeyError(run_id)

    def attach_comparison(self, run_id, comparison, updated_at):
        with self.connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT snapshot FROM runs WHERE id = ?", (run_id,)).fetchone()
            if row is None:
                raise KeyError(run_id)
            snapshot = json.loads(row["snapshot"])
            snapshot["comparison"] = comparison
            connection.execute("UPDATE runs SET snapshot = ?, updated_at = ? WHERE id = ?",
                               (json.dumps(snapshot, allow_nan=False), updated_at, run_id))
        return self.get(run_id)
