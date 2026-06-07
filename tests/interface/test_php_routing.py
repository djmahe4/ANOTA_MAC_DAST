import unittest
import re
from interface.php_xdebug.routing import RoutingMapper

class TestRoutingMapper(unittest.TestCase):
    def test_basic_mapping(self):
        mapper = RoutingMapper()
        mapper.add_rule(r"^/user/login$", "user.login", "auth/login.php")
        mapper.add_rule(r"^/user/profile/(?P<id>\d+)$", "user.profile", "user/profile.php")
        
        res1 = mapper.resolve("/user/login")
        self.assertEqual(res1["name"], "user.login")
        self.assertEqual(res1["script"], "auth/login.php")
        
        res2 = mapper.resolve("/user/profile/123")
        self.assertEqual(res2["name"], "user.profile")
        self.assertEqual(res2["script"], "user/profile.php")
        self.assertEqual(res2["params"]["id"], "123")
        
        self.assertIsNone(mapper.resolve("/unknown"))

if __name__ == "__main__":
    unittest.main()
