import unittest
import os
import shutil
import json
from interface.memory.projector import KnowledgeProjector

class TestKnowledgeProjector(unittest.TestCase):
    def setUp(self):
        self.vault_root = "tests/fixtures/test_vault"
        if os.path.exists(self.vault_root):
            shutil.rmtree(self.vault_root)
        os.makedirs(self.vault_root)
        self.projector = KnowledgeProjector(vault_root=self.vault_root)

    def tearDown(self):
        if os.path.exists(self.vault_root):
            shutil.rmtree(self.vault_root)

    def test_materialize_new_finding(self):
        finding_data = {
            "id": "trace-123",
            "type": "vulnerability_finding",
            "title": "CSRF in Login",
            "target": "/login.php",
            "confidence": 0.85,
            "model": "mistral-nemo",
            "rationale": "Detected state change without CSRF token validation.",
            "evidence": "Observed trace shows bypass of check_token() in source/low.php."
        }
        
        filepath = self.projector.materialize_finding(finding_data)
        
        self.assertTrue(os.path.exists(filepath))
        with open(filepath, "r") as f:
            content = f.read()
            self.assertIn("id: trace-123", content)
            self.assertIn("# CSRF in Login", content)
            self.assertIn("## Agent Rationale", content)
            self.assertIn(finding_data["rationale"], content)

    def test_preserve_human_rationale(self):
        finding_data = {
            "id": "trace-123",
            "title": "Finding",
            "rationale": "Old rationale"
        }
        filepath = self.projector.materialize_finding(finding_data)
        
        # Manually add a human rationale
        with open(filepath, "a") as f:
            f.write("\n## Human Rationale\nThis was manually confirmed as valid.")
            
        # Update with new finding data
        new_data = finding_data.copy()
        new_data["rationale"] = "Updated rationale"
        self.projector.materialize_finding(new_data)
        
        with open(filepath, "r") as f:
            content = f.read()
            self.assertIn("Updated rationale", content)
            self.assertIn("## Human Rationale", content)
            self.assertIn("This was manually confirmed as valid.", content)

if __name__ == "__main__":
    unittest.main()
