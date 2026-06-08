import subprocess
import json
import os
from shutil import which

class CodebaseMemoryClient:
    """
    Python wrapper for codebase-memory-mcp CLI.
    Enables indexing and semantic search of the target repository.
    """
    def __init__(self, project_name="anota_target", root_path=None):
        self.project_name = project_name
        self.root_path = os.path.abspath(root_path) if root_path else None
        self.cli_bin = "codebase-memory-mcp"
        
        # Fallback to .venv/bin if not in global PATH
        venv_path = os.path.join(os.getcwd(), ".venv", "bin", self.cli_bin)
        if not self._is_in_path(self.cli_bin) and os.path.exists(venv_path):
            self.cli_bin = venv_path
            
        self._verify_cli()

    def _is_in_path(self, name):
        return which(name) is not None

    def _verify_cli(self):
        if not self._is_in_path(self.cli_bin) and not os.path.exists(self.cli_bin):
            print(f"Warning: {self.cli_bin} not found. CLI calls will fail.")

    def index_repository(self, repo_path, mode="full"):
        """
        Indices the repository and builds the knowledge graph.
        Updates self.project_name with the actual name returned by the CLI.
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
        result = self._run_command("index_repository", args)
        
        # Extract project name from result if successful
        if isinstance(result, dict) and ("project" in result or "name" in result):
            self.project_name = result.get("project") or result.get("name")
            # Store root path for reliable resolution
            self.root_path = abs_path
            
        return result

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
            data = json.loads(result.stdout)

            # If the response is wrapped in a 'results' field (standard for search_graph), unwrap it
            if isinstance(data, dict) and "results" in data:
                return data["results"]
            return data

        except subprocess.TimeoutExpired:
            return {"error": f"CLI command {cmd_name} timed out after 300s"}
        except subprocess.CalledProcessError as e:
            # Return error info in the same format
            return {"error": str(e), "stderr": e.stderr}
        except json.JSONDecodeError:
            # Try to handle case where stdout might be None or empty
            raw_output = result.stdout if 'result' in locals() else "N/A"
            return {"error": f"Failed to decode CLI output: {raw_output}"}

