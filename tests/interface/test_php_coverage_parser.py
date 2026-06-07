import unittest
import os
from interface.php_xdebug.coverage_parser import PHPXdebugParser
from interface.php_xdebug.runner import PHPRunner

class TestPHPXdebugParser(unittest.TestCase):
    def test_parse_raw_coverage(self):
        """
        Test that the parser correctly converts raw Xdebug coverage data (dict)
        into the unified MAC-DAST JSON telemetry format.
        """
        raw_data = {
            "/var/www/html/index.php": {
                "5": 1,
                "6": 1,
                "7": -1,
                "10": 1
            }
        }
        parser = PHPXdebugParser()
        telemetry = parser.parse_raw_data(raw_data)
        
        # Expected unified format (Phase 1 output)
        expected = {
            "type": "coverage",
            "coverage": {
                "/var/www/html/index.php": [5, 6, 10]
            }
        }
        self.assertEqual(telemetry, expected)

class TestPHPRunner(unittest.TestCase):
    def test_run_php_script(self):
        """
        Test that PHPRunner can execute a simple PHP script and extract coverage.
        Requires php and xdebug to be installed.
        """
        runner = PHPRunner()
        fixture_path = os.path.abspath("tests/fixtures/simple.php")
        telemetry = runner.run(fixture_path)
        
        if "error" in telemetry:
            print(f"\nPHPRunner Error: {telemetry['error']}")
            
        self.assertEqual(telemetry["type"], "coverage", f"Telemetry: {telemetry}")
        self.assertIn(fixture_path, telemetry["coverage"], f"Telemetry: {telemetry}")
        # simple.php: line 11 calls greet("World")
        self.assertIn(11, telemetry["coverage"][fixture_path], f"Telemetry: {telemetry}")

if __name__ == "__main__":
    unittest.main()
