import unittest
import re
from interface.php_xdebug.routing import RoutingMapper

class TestRoutingMapper(unittest.TestCase):
    def test_basic_mapping(self):
        mapper = RoutingMapper()
        mapper.add_rule(r"^/user/login$", "auth/login.php")
        mapper.add_rule(r"^/user/profile/\d+$", "user/profile.php")
        
        self.assertEqual(mapper.resolve("/user/login"), "auth/login.php")
        self.assertEqual(mapper.resolve("/user/profile/123"), "user/profile.php")
        self.assertIsNone(mapper.resolve("/unknown"))

if __name__ == "__main__":
    unittest.main()
