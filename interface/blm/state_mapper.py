import hashlib
import json

class StateMapper:
    """
    Normalizes and hashes application states to identify unique logical nodes.
    """
    def __init__(self, volatile_keys=None):
        # Keys to ignore during hashing (e.g., timestamps, CSRF tokens, session IDs)
        self.volatile_keys = volatile_keys or ["PHPSESSID", "timestamp", "csrf_token"]

    def _normalize(self, state):
        """
        Removes volatile keys recursively and sorts dictionaries for stable hashing.
        """
        if not isinstance(state, dict):
            return state
        
        normalized = {}
        for k, v in sorted(state.items()):
            if k in self.volatile_keys:
                continue
            
            if isinstance(v, dict):
                normalized[k] = self._normalize(v)
            elif isinstance(v, list):
                normalized[k] = [self._normalize(item) for item in v]
            else:
                normalized[k] = v
                
        return normalized

    def compute_hash(self, state):
        """
        Generates a stable MD5 hash of the normalized state.
        """
        normalized = self._normalize(state)
        state_str = json.dumps(normalized, sort_keys=True)
        return hashlib.md5(state_str.encode("utf-8")).hexdigest()
