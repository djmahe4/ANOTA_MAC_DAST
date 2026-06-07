import hashlib
import json
from interface.blm.db import BLMDatabase
from interface.blm.state_mapper import StateMapper

class BLMGenerator:
    """
    Parses telemetry and constructs/updates the Business Logic Model (State Graph).
    """
    def __init__(self, db_path="data/blm.db"):
        self.db = BLMDatabase(db_path)
        self.mapper = StateMapper()
        self.last_state_id = None

    def _get_or_create_state(self, state_dict):
        """
        Hashes the state and returns its ID in the 'states' table.
        """
        state_hash = self.mapper.compute_hash(state_dict)
        cursor = self.db.conn.cursor()
        
        # Check if state exists
        cursor.execute("SELECT id FROM states WHERE state_hash = ?", (state_hash,))
        row = cursor.fetchone()
        if row:
            return row[0]
        
        # Create new state
        cursor.execute("""
            INSERT INTO states (state_hash, raw_state)
            VALUES (?, ?)
        """, (state_hash, json.dumps(state_dict)))
        self.db.conn.commit()
        return cursor.lastrowid

    def _compute_coverage_signature(self, coverage):
        """
        Creates a deterministic signature of the code path.
        """
        cov_str = json.dumps(coverage, sort_keys=True)
        return hashlib.sha1(cov_str.encode("utf-8")).hexdigest()

    def add_static_routing_hint(self, route_name, pattern, script_path):
        """
        Records a routing rule as a static hint.
        """
        hint_value = {
            "pattern": pattern,
            "script": script_path
        }
        self.db.save_static_hint("routing", route_name, hint_value)

    def add_openapi_hint(self, path, method, details):
        """
        Records an API endpoint from an OpenAPI spec.
        """
        key = f"{method.upper()} {path}"
        self.db.save_static_hint("openapi", key, details)

    def ingest(self, telemetry_item, action_name="unknown"):
        """
        Processes a single telemetry item, recording the observation and updating transitions.
        """
        # 1. Save raw observation
        self.db.save_observation(telemetry_item)
        
        # 2. Get current state ID
        current_state_dict = telemetry_item.get("state", {})
        current_state_id = self._get_or_create_state(current_state_dict)
        
        # 3. Record transition if we have a previous state
        if self.last_state_id is not None:
            coverage = telemetry_item.get("coverage", {})
            cov_sig = self._compute_coverage_signature(coverage)
            
            cursor = self.db.conn.cursor()
            # Check if this transition (action + path) already exists
            cursor.execute("""
                SELECT id FROM transitions 
                WHERE from_state_id = ? AND to_state_id = ? 
                AND action_identifier = ? AND coverage_signature = ?
            """, (self.last_state_id, current_state_id, action_name, cov_sig))
            
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO transitions (from_state_id, to_state_id, action_identifier, coverage_signature, trace_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (self.last_state_id, current_state_id, action_name, cov_sig, telemetry_item["trace_id"]))
                self.db.conn.commit()
        
        # Update tracker
        self.last_state_id = current_state_id
        return current_state_id
