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
            "files": {
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
        self.assertIn(fixture_path, telemetry["files"], f"Telemetry: {telemetry}")
        # In simple.php, line 10 calls greet("World"), which should be executed.
        # Wait, in simple.php line 10 is actually greet("World")? Let's check the file.
        # Line 1: <?php
        # Line 2: // tests/fixtures/simple.php
        # Line 3: function greet($name) {
        # Line 4:     if ($name) {
        # Line 5:         echo "Hello, " . $name;
        # Line 6:     } else {
        # Line 7:         echo "Hello, Guest";
        # Line 8:     }
        # Line 9: }
        # Line 10: 
        # Line 11: greet("World");
        # Line 12: ?>
        # My previous test expected 10, but it might be 11.
        self.assertIn(11, telemetry["files"][fixture_path], f"Telemetry: {telemetry}")

if __name__ == "__main__":
    unittest.main()
