import unittest
import os
import subprocess
from unittest.mock import patch, MagicMock
from logic_engine.agents.cpp_profiler import CPPProfiler

class TestCPPProfiler(unittest.TestCase):
    def setUp(self):
        self.profiler = CPPProfiler()
        self.test_dir = "tests/fixtures/cpp_project"
        os.makedirs(self.test_dir, exist_ok=True)

    def tearDown(self):
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_find_entry_points_main(self):
        # Compile a simple main.c
        main_c = os.path.join(self.test_dir, "main.c")
        with open(main_c, "w") as f:
            f.write("int main() { return 0; }")
            
        binary_path = os.path.join(self.test_dir, "app")
        # Compile to real ELF binary for readelf to work
        subprocess.run(["gcc", main_c, "-o", binary_path], check=True)
        
        entry_points = self.profiler.find_entry_points(self.test_dir)
        self.assertIn(os.path.abspath(binary_path), entry_points)

    def test_profile_architecture_daemon(self):
        # Mock 'strings' output instead of 'proftpd --version'
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(stdout="... listen ... socket ... server ...")
            # The path just needs to exist for the check
            with open(os.path.join(self.test_dir, "mock_binary"), "w") as f:
                f.write("dummy")
            
            self.assertTrue(self.profiler.is_daemon(os.path.join(self.test_dir, "mock_binary")))

if __name__ == "__main__":
    unittest.main()
