import os
import json

class AttackExecutor:
    """
    Executes logic attack hypotheses using the appropriate physical harness.
    """
    def __init__(self, php_runner=None, cpp_harness=None):
        self.php_runner = php_runner
        self.cpp_harness = cpp_harness

    def execute(self, hypothesis, env=None, session=None, repo_root=None):
        """
        Executes a logic attack hypothesis.
        Supports session persistence and path resolution.
        """
        source = hypothesis.get("source", "php")
        target = hypothesis.get("target_action")
        mutations = hypothesis.get("mutations", {})
        
        if not target:
            return {"error": "Attack hypothesis missing target_action"}, {}

        # Path Resolution: Ground logical URL to physical file
        if repo_root:
            # Strip leading slash/domain if present
            clean_target = target.lstrip("/").replace("http://localhost/", "")
            target_path = os.path.join(repo_root, clean_target)
            if not os.path.exists(target_path):
                # If target_path (filesystem path) doesn't exist, it means the target was probably already an HTTP path.
                # In HTTP mode, PHPRunner expects a URL path relative to the repo_root, not a filesystem path.
                # We need to ensure that the target is properly set to the clean_target for HTTP requests.
                target = clean_target # Use the URI path for HTTP execution
            else:
                target = target_path

        # Merge session cookies into mutations
        if session:
            if "COOKIE" not in mutations:
                mutations["COOKIE"] = {}
            mutations["COOKIE"].update(session)
            
        # Merge logical env context (ENV, GLOBALS) into mutations
        if env:
            for key, value in env.items():
                if key not in mutations:
                    mutations[key] = value
                elif isinstance(value, dict) and isinstance(mutations[key], dict):
                    mutations[key].update(value)

        if source == "php":
            if self.php_runner:
                # Use HTTP mode for more realistic business logic exploitation
                # Passing 'env' explicitly as None because it's now merged into mutations
                telemetry, new_session = self.php_runner.run(
                    target, 
                    params=mutations, 
                    env=None, 
                    session=session, 
                    use_http=True,
                    repo_root=repo_root
                )
                return telemetry, new_session
        return {"error": "Execution failed"}, {}

    def _extract_session(self, telemetry):
        cookies = {}
        headers = telemetry.get("state", {}).get("headers_out", [])
        for h in headers:
            if h.startswith("Set-Cookie:"):
                # Simple extraction
                parts = h.split(":")[1].strip().split(";")[0].split("=")
                if len(parts) == 2:
                    cookies[parts[0]] = parts[1]
        return cookies

