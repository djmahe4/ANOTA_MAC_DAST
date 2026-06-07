import unittest
from logic_engine.agents.mutator import RequestMutator

class TestRequestMutator(unittest.TestCase):
    def setUp(self):
        self.mutator = RequestMutator()

    def test_parameter_tampering(self):
        params = {"user_id": "123", "role": "user"}
        mutations = self.mutator.mutate_parameters(params)
        
        # Check that we have mutations for both keys
        target_keys = [m["target_key"] for m in mutations]
        self.assertIn("user_id", target_keys)
        self.assertIn("role", target_keys)
        
        # Verify a specific tampering case
        admin_mutations = [m for m in mutations if m["payload"].get("role") == "admin"]
        self.assertTrue(len(admin_mutations) > 0)

    def test_parameter_omission(self):
        params = {"auth_token": "secret", "action": "delete"}
        mutations = self.mutator.mutate_parameters(params)
        
        # Find omission strategies
        omissions = [m for m in mutations if m["strategy"] == "parameter_omission"]
        self.assertEqual(len(omissions), 2)
        
        # Verify specific omission
        token_omitted = [m for m in omissions if m["target_key"] == "auth_token"][0]
        self.assertNotIn("auth_token", token_omitted["payload"])
        self.assertEqual(token_omitted["payload"]["action"], "delete")

    def test_step_skipping(self):
        workflow = ["login", "add_item", "pay", "checkout"]
        mutations = self.mutator.mutate_sequence(workflow)
        
        # Should detect potential skip of 'add_item' and 'pay'
        skipped_steps = [m["skipped_step"] for m in mutations]
        self.assertIn("add_item", skipped_steps)
        self.assertIn("pay", skipped_steps)
        
        # Verify sequence integrity
        pay_skip = [m for m in mutations if m["skipped_step"] == "pay"][0]
        self.assertEqual(pay_skip["sequence"], ["login", "add_item", "checkout"])

if __name__ == "__main__":
    unittest.main()
