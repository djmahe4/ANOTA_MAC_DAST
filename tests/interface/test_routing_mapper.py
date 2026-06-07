import unittest
from interface.php_xdebug.routing import RoutingMapper

class TestRoutingMapper(unittest.TestCase):
    def test_resolve_named_route(self):
        mapper = RoutingMapper()
        mapper.add_rule(r"^/user/(?P<id>\d+)$", "user.show", "controllers/UserController.php")
        
        resolved = mapper.resolve("/user/42")
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved["name"], "user.show")
        self.assertEqual(resolved["script"], "controllers/UserController.php")
        self.assertEqual(resolved["params"]["id"], "42")

    def test_resolve_no_match(self):
        mapper = RoutingMapper()
        mapper.add_rule(r"^/login$", "auth.login", "login.php")
        
        resolved = mapper.resolve("/unknown")
        self.assertIsNone(resolved)

if __name__ == "__main__":
    unittest.main()
