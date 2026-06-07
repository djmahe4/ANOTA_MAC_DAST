import sys
import os
from interface.memory.codebase import CodebaseMemoryClient
from interface.blm.generator import BLMGenerator

def sync_codebase_hints(repo_path, db_path="data/blm.db", project_name="anota_target"):
    """
    Indexes the repo and extracts core logic hints for the BLM database.
    """
    client = CodebaseMemoryClient(project_name=project_name)
    generator = BLMGenerator(db_path=db_path)
    
    print(f"[*] Indexing repository: {repo_path}")
    client.index_repository(repo_path)
    
    print("[*] Extracting core business logic hints...")
    core_logic = client.get_core_logic()
    
    if "error" in core_logic:
        print(f"Error extracting hints: {core_logic['error']}")
        return

    count = 0
    for item in core_logic:
        name = item.get("name")
        # Store as a static hint in the BLM database
        # This helps agents know that this function is an 'anchor' for business logic.
        generator.db.save_static_hint(
            hint_type="code_structure",
            key=item.get("qualified_name", name),
            value_dict=item
        )
        count += 1
        
    print(f"[+] Successfully synced {count} core logic hints to BLM database.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 sync_hints.py <repo_path> [db_path]")
        sys.exit(1)
        
    repo = sys.argv[1]
    db = sys.argv[2] if len(sys.argv) > 2 else "data/blm.db"
    sync_codebase_hints(repo, db)
