import sqlite3
import json
import os

class BLMDatabase:
    """
    Handles SQLite persistence for raw observations and the synthesized state graph.
    """
    def __init__(self, db_path="data/blm.db"):
        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self._create_schema()

    def _create_schema(self):
        cursor = self.conn.cursor()
        
        # 1. Observations: Raw telemetry logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trace_id TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                source TEXT NOT NULL,
                coverage_data TEXT,
                state_data TEXT,
                events_data TEXT
            )
        """)

        # 2. States: Unique logical states (Nodes)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                state_hash TEXT UNIQUE NOT NULL,
                raw_state TEXT NOT NULL
            )
        """)

        # 3. Transitions: Edges in the state graph
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_state_id INTEGER,
                to_state_id INTEGER,
                action_identifier TEXT NOT NULL,
                coverage_signature TEXT NOT NULL,
                trace_id TEXT,
                FOREIGN KEY(from_state_id) REFERENCES states(id),
                FOREIGN KEY(to_state_id) REFERENCES states(id)
            )
        """)
        
        self.conn.commit()

    def save_observation(self, observation):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO observations (trace_id, timestamp, source, coverage_data, state_data, events_data)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            observation["trace_id"],
            observation["timestamp"],
            observation["source"],
            json.dumps(observation.get("coverage", {})),
            json.dumps(observation.get("state", {})),
            json.dumps(observation.get("events", []))
        ))
        self.conn.commit()
        return cursor.lastrowid

    def close(self):
        self.conn.close()
