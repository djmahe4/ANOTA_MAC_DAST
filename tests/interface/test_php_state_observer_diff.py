import unittest
from interface.php_xdebug.state_observer import PHPStateObserver

class TestPHPStateObserver(unittest.TestCase):
    def test_detect_state_transitions(self):
        observer = PHPStateObserver()
        
        state1 = {"session": {"user_id": 0, "role": "guest"}}
        state2 = {"session": {"user_id": 42, "role": "admin"}}
        
        transitions = observer.diff(state1, state2)
        
        self.assertIn("session", transitions)
        self.assertEqual(transitions["session"]["user_id"], {"from": 0, "to": 42})
        self.assertEqual(transitions["session"]["role"], {"from": "guest", "to": "admin"})

    def test_interesting_transitions(self):
        observer = PHPStateObserver(interesting_keys=["role"])
        
        state1 = {"session": {"user_id": 42, "role": "guest"}}
        state2 = {"session": {"user_id": 42, "role": "admin"}}
        
        is_interesting = observer.is_interesting(state1, state2)
        self.assertTrue(is_interesting)

if __name__ == "__main__":
    unittest.main()
