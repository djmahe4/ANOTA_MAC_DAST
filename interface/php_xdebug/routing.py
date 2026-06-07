import re

class RoutingMapper:
    """
    Maps URLs to logical route names and entry points based on regex rules.
    """
    def __init__(self):
        self.rules = []

    def add_rule(self, pattern, route_name, script_path):
        """
        Adds a new routing rule with a logical name.
        """
        self.rules.append({
            "pattern": re.compile(pattern),
            "name": route_name,
            "script": script_path
        })

    def resolve(self, url):
        """
        Resolves a URL to a route name and script path. Returns None if no match.
        """
        for rule in self.rules:
            match = rule["pattern"].match(url)
            if match:
                # Extract parameters if any
                params = match.groupdict()
                return {
                    "name": rule["name"],
                    "script": rule["script"],
                    "params": params
                }
        return None

    def get_route_from_coverage(self, coverage):
        """
        Infers the route based on the files present in the coverage data.
        Useful when the URL is unknown or ambiguous.
        """
        # This is a heuristic. If we see a specific controller, we might know the route.
        # For now, we return a generic string if no specific mapping is found.
        # In a real implementation, this would look at a map of {file: route_name}
        return "inferred_route"
