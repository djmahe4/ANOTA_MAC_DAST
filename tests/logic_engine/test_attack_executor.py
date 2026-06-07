import unittest
from unittest.mock import MagicMock, patch
from logic_engine.agents.executor import AttackExecutor

class TestAttackExecutor(unittest.TestCase):
    def setUp(self):
        self.php_runner = MagicMock()
        self.cpp_harness = MagicMock()
        self.executor = AttackExecutor(php_runner=self.php_runner, cpp_harness=self.cpp_harness)

    def test_execute_php_attack(self):
        hypothesis = {
            "source": "php",
            "target_action": "/login.php",
            "mutations": {"user_id": "admin"}
        }
        
        self.executor.execute(hypothesis)
        
        # Verify php_runner was called
        self.php_runner.run.assert_called_once()
        args, kwargs = self.php_runner.run.call_args
        self.assertEqual(args[0], "/login.php")

if __name__ == "__main__":
    unittest.main()
