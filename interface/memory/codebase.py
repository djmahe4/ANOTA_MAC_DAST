import subprocess
import json
import os

class CodebaseMemoryClient:
    """
    Python wrapper for codebase-memory-mcp CLI.
    Enables indexing and semantic search of the target repository.
    """
    def __init__(self, project_name="anota_target"):
        self.project_name = project_name
        self.cli_bin = "codebase-memory-mcp" # Assumes it's in PATH

    def index_repository(self, repo_path, mode="full"):
        """
        Indices the repository and builds the knowledge graph.
        """
        args = {
            "repo_path": os.path.abspath(repo_path),
            "mode": mode,
            "persistence": True
        }
        return self._run_command("index_repository", args)

    def search_graph(self, query=None, name_pattern=None, label=None, min_degree=None, limit=50):
        """
        Searches the indexed knowledge graph for code patterns.
        """
        args = {
            "project": self.project_name,
            "limit": limit
        }
        if query:
            args["query"] = query
        if name_pattern:
            args["name_pattern"] = name_pattern
        if label:
            args["label"] = label
        if min_degree:
            args["min_degree"] = min_degree
            
        return self._run_command("search_graph", args)

    def get_core_logic(self):
        """
        Helper to find core business logic (high in-degree functions).
        """
        return self.search_graph(min_degree=3, label="Function", limit=100)

    def _run_command(self, cmd_name, args_dict):
        """
        Executes the MCP CLI command and returns the parsed JSON result.
        """
        cmd = [
            self.cli_bin, "cli", cmd_name,
            json.dumps(args_dict)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            # Return error info in the same format
            return {"error": str(e), "stderr": e.stderr}
        except json.JSONDecodeError:
            return {"error": "Failed to decode CLI output", "raw": result.stdout}
