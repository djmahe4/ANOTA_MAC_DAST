import unittest
import uuid
from interface.aggregator import TelemetryAggregator

class TestTelemetryAggregator(unittest.TestCase):
    def test_aggregate_php_data(self):
        """
        Test that the aggregator correctly formats PHP telemetry.
        """
        aggregator = TelemetryAggregator()
        raw_php_data = {
            "type": "coverage", # From PHPRunner
            "files": {"index.php": [1, 2, 3]},
            "state": {"session": {"user": "admin"}}
        }
        
        aggregated = aggregator.aggregate("php", raw_php_data)
        
        self.assertEqual(aggregated["source"], "php")
        self.assertEqual(aggregated["coverage"], raw_php_data["files"])
        self.assertEqual(aggregated["state"], raw_php_data["state"])
        self.assertTrue(uuid.UUID(aggregated["trace_id"]))
        self.assertIn("timestamp", aggregated)

    def test_aggregate_cpp_data(self):
        """
        Test that the aggregator correctly formats C++ telemetry.
        """
        aggregator = TelemetryAggregator()
        raw_cpp_data = [
            {"type": "uprobe", "symbol": "target_func", "binary": "main"}
        ]
        
        aggregated = aggregator.aggregate("cpp", raw_cpp_data)
        
        self.assertEqual(aggregated["source"], "cpp")
        self.assertEqual(aggregated["events"], raw_cpp_data)
        self.assertTrue(uuid.UUID(aggregated["trace_id"]))

if __name__ == "__main__":
    unittest.main()
