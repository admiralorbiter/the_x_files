import sqlite3
import json
import hashlib
import os
from typing import List, Optional, Dict, Any
from emergence_lab.domain.events import Event, WorldState

class EventRepository:
    def __init__(self, db_path: str = "emergence_lab.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    scenario_name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    current_tick INTEGER DEFAULT 0
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT UNIQUE NOT NULL,
                    run_id TEXT NOT NULL,
                    tick INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    actor_id TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    previous_hash TEXT,
                    current_hash TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES runs(run_id)
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS snapshots (
                    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    tick INTEGER NOT NULL,
                    state_json TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(run_id) REFERENCES runs(run_id)
                );
            """)
            conn.commit()

    def create_run(self, run_id: str, scenario_name: str):
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO runs (run_id, scenario_name, current_tick) VALUES (?, ?, 0)",
                (run_id, scenario_name)
            )
            conn.commit()

    def get_latest_event_hash(self, run_id: str) -> Optional[str]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT current_hash FROM events WHERE run_id = ? ORDER BY id DESC LIMIT 1",
                (run_id,)
            )
            row = cursor.fetchone()
            return row["current_hash"] if row else "GENESIS"

    def append_event(self, event: Event) -> Event:
        previous_hash = self.get_latest_event_hash(event.run_id)
        event.previous_hash = previous_hash

        # Compute SHA-256 hash for hash chain integrity
        payload_str = json.dumps(event.payload, sort_keys=True)
        hash_input = f"{event.event_id}:{event.run_id}:{event.tick}:{event.event_type}:{event.actor_id}:{payload_str}:{previous_hash}"
        current_hash = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
        event.current_hash = current_hash

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO events (event_id, run_id, tick, event_type, actor_id, payload, timestamp, previous_hash, current_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    event.run_id,
                    event.tick,
                    event.event_type,
                    event.actor_id,
                    payload_str,
                    event.timestamp,
                    event.previous_hash,
                    event.current_hash
                )
            )
            conn.execute(
                "UPDATE runs SET current_tick = ? WHERE run_id = ?",
                (event.tick, event.run_id)
            )
            conn.commit()
        return event

    def save_snapshot(self, world_state: WorldState):
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO snapshots (run_id, tick, state_json) VALUES (?, ?, ?)",
                (world_state.run_id, world_state.tick, world_state.model_dump_json())
            )
            conn.commit()

    def get_events(self, run_id: str) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM events WHERE run_id = ? ORDER BY id ASC",
                (run_id,)
            )
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
