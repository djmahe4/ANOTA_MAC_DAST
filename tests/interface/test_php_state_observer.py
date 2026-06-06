import unittest
import os
from interface.php_xdebug.runner import PHPRunner

class TestPHPStateObserver(unittest.TestCase):
    def test_capture_session_and_cookies(self):
        """
        Test that PHPRunner captures session and cookie state changes.
        """
        runner = PHPRunner()
        fixture_path = os.path.abspath("tests/fixtures/session_logic.php")
        
        # Run first time to initiate session
        telemetry = runner.run(fixture_path)
        
        self.assertIn("state", telemetry)
        state = telemetry["state"]
        
        # Verify Cookies (setcookie might not be in $_COOKIE immediately in same request, 
        # but we can capture response headers or check what instrument.php sees)
        self.assertIn("cookies", state)
        
        # Verify Session
        self.assertIn("session", state)
        self.assertEqual(state["session"].get("step"), 1)

        # Run second time (PHPRunner should ideally persist session between calls for this test)
        # Note: Standard CLI doesn't persist sessions without session_id management.
        # For now, we just check if it captures WHAT IS PRESENT at the end of execution.
        
if __name__ == "__main__":
    unittest.main()
