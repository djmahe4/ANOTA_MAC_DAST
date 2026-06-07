import json

class MermaidExporter:
    """
    Exports the BLM state graph from SQLite to Mermaid.js format for visualization.
    """
    def __init__(self, db):
        self.db = db

    def export(self):
        """
        Generates a Mermaid state diagram string.
        """
        cursor = self.db.conn.cursor()
        
        # 1. Fetch all states
        cursor.execute("SELECT id, raw_state FROM states")
        states = cursor.fetchall()
        
        # 2. Fetch all transitions
        cursor.execute("""
            SELECT from_state_id, to_state_id, action_identifier 
            FROM transitions
        """)
        transitions = cursor.fetchall()
        
        mermaid = ["stateDiagram-v2"]
        
        # Map state IDs to short labels
        for state_id, raw_state_json in states:
            state_dict = json.loads(raw_state_json)
            # Try to find a meaningful label (e.g., user role)
            label = f"State_{state_id}"
            if "session" in state_dict and "role" in state_dict["session"]:
                label = f"{state_dict['session']['role']}_{state_id}"
            
            mermaid.append(f"    state {label} {{")
            # Add some state detail as a comment/sub-label if needed
            # for k, v in state_dict.items():
            #     mermaid.append(f"        {k}: {v}")
            mermaid.append(f"    }}")

        # Create transitions
        for from_id, to_id, action in transitions:
            # Find labels again (inefficient but simple for now)
            from_label = self._get_label(from_id)
            to_label = self._get_label(to_id)
            mermaid.append(f"    {from_label} --> {to_label}: {action}")
            
        return "\n".join(mermaid)

    def _get_label(self, state_id):
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT raw_state FROM states WHERE id = ?", (state_id,))
        row = cursor.fetchone()
        if not row:
            return f"Unknown_{state_id}"
        
        state_dict = json.loads(row[0])
        if "session" in state_dict and "role" in state_dict["session"]:
            return f"{state_dict['session']['role']}_{state_id}"
        return f"State_{state_id}"
