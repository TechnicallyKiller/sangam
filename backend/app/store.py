"""Small durable run/artifact store; SQLite locally, Postgres when configured."""
import json
import os
import sqlite3
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class Store:
    def __init__(self):
        self.lock = threading.RLock()
        self.url = os.getenv("DATABASE_URL", "")
        if self.url:
            import psycopg
            self.db = psycopg.connect(self.url, connect_timeout=12, autocommit=True, sslmode="require")
            self.mark = "%s"
        else:
            root = Path(os.getenv("SANGAM_DATA_DIR", str(ROOT / ".data")))
            root.mkdir(parents=True, exist_ok=True)
            self.db = sqlite3.connect(root / "sangam.sqlite", check_same_thread=False)
            self.mark = "?"
        with self.lock:
            self.db.execute("CREATE TABLE IF NOT EXISTS sangam_runs (id TEXT PRIMARY KEY, payload TEXT NOT NULL)")
            self.db.execute("CREATE TABLE IF NOT EXISTS sangam_models (cid TEXT PRIMARY KEY, content TEXT NOT NULL)")
            self.db.commit()

    def save(self, state):
        with self.lock:
            m = self.mark
            self.db.execute(f"INSERT INTO sangam_runs(id,payload) VALUES({m},{m}) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload", (state["runId"], json.dumps(state, allow_nan=False)))
            self.db.commit()

    def runs(self):
        with self.lock:
            rows = self.db.execute("SELECT payload FROM sangam_runs").fetchall()
        return sorted((json.loads(r[0]) for r in rows), key=lambda r: r["createdAt"], reverse=True)

    def model(self, cid, data=None):
        import base64
        with self.lock:
            if data is not None:
                m = self.mark
                self.db.execute(f"INSERT INTO sangam_models(cid,content) VALUES({m},{m}) ON CONFLICT(cid) DO NOTHING", (cid, base64.b64encode(data).decode()))
                self.db.commit()
            row = self.db.execute(f"SELECT content FROM sangam_models WHERE cid={self.mark}", (cid,)).fetchone()
            return base64.b64decode(row[0]) if row else None
