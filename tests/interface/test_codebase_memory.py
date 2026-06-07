import unittest
from unittest.mock import patch, MagicMock
import json
from interface.memory.codebase import CodebaseMemoryClient

class TestCodebaseMemoryClient(unittest.TestCase):
    def setUp(self):
        self.client = CodebaseMemoryClient(project_name="test_proj")

    @patch("subprocess.run")
    def test_search_graph(self, mock_run):
        # Mock successful CLI output
        mock_output = [
            {"name": "processPayment", "in_degree": 5}
        ]
        mock_run.return_value = MagicMock(stdout=json.dumps(mock_output))
        
        results = self.client.search_graph(query="payment")
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "processPayment")
        
        # Verify CLI args
        called_args = mock_run.call_args[0][0]
        self.assertIn("search_graph", called_args)
        payload = json.loads(called_args[-1])
        self.assertEqual(payload["query"], "payment")
        self.assertEqual(payload["project"], "test_proj")

if __name__ == "__main__":
    unittest.main()
