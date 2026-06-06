import re

class RoutingMapper:
    """
    Maps URLs to local PHP entry points based on regex rules.
    """
    def __init__(self):
        self.rules = []

    def add_rule(self, pattern, script_path):
        """
        Adds a new routing rule.
        """
        self.rules.append((re.compile(pattern), script_path))

    def resolve(self, url):
        """
        Resolves a URL to a script path. Returns None if no match.
        """
        for pattern, script_path in self.rules:
            if pattern.match(url):
                return script_path
        return None
