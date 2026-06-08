import hashlib
import json
from interface.blm.db import BLMDatabase
from interface.blm.state_mapper import StateMapper

class BLMGenerator:
    """
    Parses telemetry and constructs/updates the Business Logic Model (State Graph).
    """
    def __init__(self, db_path="data/blm.db", memory_controller=None):
        self.db = BLMDatabase(db_path)
        self.mapper = StateMapper()
        self.memory = memory_controller
        self.last_state_id = None

    def _get_or_create_state(self, state_dict):
        """
        Hashes the state and uses the database to find/create it thread-safely.
        """
        state_hash = self.mapper.compute_hash(state_dict)
        return self.db.get_or_create_state(state_hash, state_dict)

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

    async def ingest(self, telemetry_item, action_name=None):
        """
        Processes a telemetry item and updates the state graph.
        Returns the ID of the current state.
        """
        try:
            # Ensure mandatory metadata is present
            from datetime import datetime
            if "timestamp" not in telemetry_item or not telemetry_item["timestamp"]:
                telemetry_item["timestamp"] = datetime.now().isoformat()
            if "source" not in telemetry_item:
                telemetry_item["source"] = "unknown"

            # 1. Save raw observation
            self.db.save_observation(telemetry_item)

            # 2. Update Vector Index (Agentic & Async)
            content_to_index = f"{json.dumps(telemetry_item.get('state', {}))} {json.dumps(telemetry_item.get('events', []))}"
            try:
                await self.memory.add_vector_index_agentic(telemetry_item["trace_id"], content_to_index)
            except Exception as e:
                print(f" [!] Failed to trigger agentic indexing: {e}")

            # 3. Get current state ID
            current_state_dict = telemetry_item.get("state", {})

            current_state_id = self._get_or_create_state(current_state_dict)
            
            # 3. Record transition if we have a previous state
            if self.last_state_id is not None:
                coverage = telemetry_item.get("coverage", {})
                cov_sig = self._compute_coverage_signature(coverage)
                
                self.db.record_transition(
                    self.last_state_id, 
                    current_state_id, 
                    action_name, 
                    cov_sig, 
                    telemetry_item["trace_id"]
                )
            
            # Update tracker
            self.last_state_id = current_state_id
            return current_state_id
        except Exception as e:
            print(f"Error during ingestion: {e}")
            return None
