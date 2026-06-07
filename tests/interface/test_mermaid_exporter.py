import unittest
import os
import uuid
from interface.blm.generator import BLMGenerator
from interface.blm.exporter import MermaidExporter

class TestMermaidExporter(unittest.TestCase):
    def setUp(self):
        self.db_path = "data/test_exporter.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.generator = BLMGenerator(db_path=self.db_path)
        self.exporter = MermaidExporter(self.generator.db)

    def test_export_basic_graph(self):
        # Create a simple Guest -> Admin transition
        self.generator.ingest({
            "trace_id": "t1",
            "timestamp": "2026-06-07T00:00:00Z",
            "source": "php",
            "state": {"session": {"user_id": 0, "role": "guest"}},
            "coverage": {}
        }, action_name="/index.php")
        
        self.generator.ingest({
            "trace_id": "t2",
            "timestamp": "2026-06-07T00:00:05Z",
            "source": "php",
            "state": {"session": {"user_id": 42, "role": "admin"}},
            "coverage": {}
        }, action_name="/login.php")
        
        output = self.exporter.export()
        
        # Verify Mermaid syntax
        self.assertIn("stateDiagram-v2", output)
        self.assertIn("guest_1", output)
        self.assertIn("admin_2", output)
        self.assertIn("guest_1 --> admin_2: /login.php", output)

if __name__ == "__main__":
    unittest.main()
