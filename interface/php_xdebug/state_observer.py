class PHPStateObserver:
    """
    Analyzes PHP application state changes (sessions, cookies) between requests.
    """
    def __init__(self, interesting_keys=None):
        self.interesting_keys = interesting_keys or []

    def diff(self, old_state, new_state):
        """
        Computes the difference between two state snapshots.
        """
        changes = {}
        
        for category in ["session", "cookies"]:
            old_cat = old_state.get(category, {})
            new_cat = new_state.get(category, {})
            
            cat_changes = {}
            # Check all keys in both old and new
            all_keys = set(old_cat.keys()) | set(new_cat.keys())
            
            for key in all_keys:
                old_val = old_cat.get(key)
                new_val = new_cat.get(key)
                
                if old_val != new_val:
                    cat_changes[key] = {"from": old_val, "to": new_val}
            
            if cat_changes:
                changes[category] = cat_changes
                
        return changes

    def is_interesting(self, old_state, new_state):
        """
        Returns True if any 'interesting' key changed.
        Used to signal logic-heavy transitions to the agents.
        """
        changes = self.diff(old_state, new_state)
        
        for category in changes.values():
            for key in category.keys():
                if key in self.interesting_keys:
                    return True
                    
        return False
