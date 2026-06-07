import unittest
import os
import subprocess
from logic_engine.agents.php_profiler import PHPProfiler

class TestPHPProfiler(unittest.TestCase):
    def setUp(self):
        self.profiler = PHPProfiler()
        self.test_dir = "tests/fixtures/php_project"
        os.makedirs(self.test_dir, exist_ok=True)

    def tearDown(self):
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_find_entry_points_composer(self):
        # Create a mock index.php requiring autoload
        index_path = os.path.join(self.test_dir, "index.php")
        with open(index_path, "w") as f:
            f.write("<?php require 'vendor/autoload.php'; ?>")
        
        entry_points = self.profiler.find_entry_points(self.test_dir)
        self.assertIn(os.path.abspath(index_path), entry_points)

    def test_profile_architecture_mvc(self):
        index_path = os.path.join(self.test_dir, "index.php")
        with open(index_path, "w") as f:
            f.write("<?php\nrequire_once 'vendor/autoload.php';\n$app = new App();")
            
        arch = self.profiler.profile_architecture(index_path)
        self.assertEqual(arch, "MVC")

    def test_strip_noise(self):
        noisy_php = os.path.join(self.test_dir, "noisy.php")
        with open(noisy_php, "w") as f:
            f.write("<?php\n// This is a comment\n/* Multi-line\n comment */\necho 'hello';\n?>")
            
        clean_code = self.profiler.strip_noise(noisy_php)
        self.assertNotIn("comment", clean_code)
        self.assertIn("echo 'hello';", clean_code)

if __name__ == "__main__":
    unittest.main()
