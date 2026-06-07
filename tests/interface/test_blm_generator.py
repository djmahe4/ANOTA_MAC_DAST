import unittest
import os
import uuid
from interface.blm.generator import BLMGenerator

class TestBLMGenerator(unittest.TestCase):
    def setUp(self):
        self.db_path = "data/test_blm.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.generator = BLMGenerator(db_path=self.db_path)

    def test_ingest_state_transition(self):
        # 1. First event (Initial state: Guest)
        event1 = {
            "trace_id": str(uuid.uuid4()),
            "timestamp": "2026-06-07T00:00:00Z",
            "source": "php",
            "state": {"session": {"user_id": 0, "role": "guest"}},
            "coverage": {"index.php": [1, 2]}
        }
        self.generator.ingest(event1, action_name="/index.php")
        
        # 2. Second event (Action: Login -> State: Admin)
        event2 = {
            "trace_id": str(uuid.uuid4()),
            "timestamp": "2026-06-07T00:00:05Z",
            "source": "php",
            "state": {"session": {"user_id": 42, "role": "admin"}},
            "coverage": {"login.php": [10, 11, 12]}
        }
        self.generator.ingest(event2, action_name="/login.php")
        
        # 3. Verify Database
        cursor = self.generator.db.conn.cursor()
        
        # Should have 2 states
        cursor.execute("SELECT count(*) FROM states")
        self.assertEqual(cursor.fetchone()[0], 2)
        
        # Should have 1 transition
        cursor.execute("SELECT from_state_id, to_state_id, action_identifier FROM transitions")
        transition = cursor.fetchone()
        self.assertIsNotNone(transition)
        self.assertEqual(transition[2], "/login.php")
        
        # Transitions should link the correct states
        self.assertEqual(transition[0], 1) # Guest
        self.assertEqual(transition[1], 2) # Admin

    def test_state_normalization(self):
        """
        Verify that volatile keys (like timestamps) don't create new states.
        """
        event1 = {
            "trace_id": "trace-1",
            "timestamp": "2026-06-07T00:00:00Z",
            "source": "php",
            "state": {"session": {"user_id": 42}, "timestamp": 1000},
            "coverage": {}
        }
        id1 = self.generator.ingest(event1)
        
        event2 = {
            "trace_id": "trace-2",
            "timestamp": "2026-06-07T00:00:01Z",
            "source": "php",
            "state": {"session": {"user_id": 42}, "timestamp": 1001},
            "coverage": {}
        }
        id2 = self.generator.ingest(event2)
        
        self.assertEqual(id1, id2) # Should be the same logical state

if __name__ == "__main__":
    unittest.main()
