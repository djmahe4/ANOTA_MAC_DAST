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
        self._verify_cli()

    def _verify_cli(self):
        """
        Check if the MCP CLI binary exists in the PATH.
        """
        from shutil import which
        if which(self.cli_bin) is None:
            print(f"Warning: {self.cli_bin} not found in PATH. CLI calls will fail.")

    def index_repository(self, repo_path, mode="full"):
        """
        Indices the repository and builds the knowledge graph.
        """
        # Security: Normalize and validate path
        abs_path = os.path.abspath(repo_path)
        if not os.path.exists(abs_path):
            return {"error": f"Path does not exist: {abs_path}"}
            
        args = {
            "repo_path": abs_path,
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
        # Security: Whitelist command names
        if cmd_name not in ["index_repository", "search_graph"]:
            return {"error": f"Unauthorized command: {cmd_name}"}

        cmd = [
            self.cli_bin, "cli", cmd_name,
            json.dumps(args_dict)
        ]
        
        try:
            # Added 300s timeout for large indexing tasks
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=300)
            return json.loads(result.stdout)
        except subprocess.TimeoutExpired:
            return {"error": f"CLI command {cmd_name} timed out after 300s"}
        except subprocess.CalledProcessError as e:
            # Return error info in the same format
            return {"error": str(e), "stderr": e.stderr}
        except json.JSONDecodeError:
            return {"error": "Failed to decode CLI output", "raw": result.stdout}
