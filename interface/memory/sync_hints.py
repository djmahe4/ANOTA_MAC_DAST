import sys
import os
from interface.memory.codebase import CodebaseMemoryClient
from interface.blm.generator import BLMGenerator
from logic_engine.agents.php_profiler import PHPProfiler
from logic_engine.agents.cpp_profiler import CPPProfiler

def sync_codebase_hints(repo_path, db_path="data/blm.db", project_name="anota_target"):
    """
    Indexes the repo and extracts core logic hints for the BLM database.
    """
    client = CodebaseMemoryClient(project_name=project_name)
    generator = BLMGenerator(db_path=db_path)
    php_prof = PHPProfiler()
    cpp_prof = CPPProfiler()
    
    print(f"[*] Indexing repository: {repo_path}")
    client.index_repository(repo_path)
    
    # 1. Automated Entry Point Discovery
    print("[*] Profiling application architecture and entry points...")
    php_entries = php_prof.find_entry_points(repo_path)
    for entry in php_entries:
        arch = php_prof.profile_architecture(entry)
        rel_entry = os.path.relpath(entry, repo_path)
        generator.db.save_static_hint(
            "entry_point", 
            rel_entry, 
            {"type": "php", "architecture": arch}
        )
        
        # Discover internal dependencies for this entry point
        deps = php_prof.get_dependencies(entry)
        for dep in deps:
            if dep.startswith(os.path.abspath(repo_path)):
                rel_dep = os.path.relpath(dep, repo_path)
                if rel_dep != rel_entry:
                    generator.db.save_static_hint(
                        "code_dependency",
                        f"{rel_entry}->{rel_dep}",
                        {"from": rel_entry, "to": rel_dep}
                    )
        
    cpp_entries = cpp_prof.find_entry_points(repo_path)
    for entry in cpp_entries:
        is_daemon = cpp_prof.is_daemon(entry)
        generator.db.save_static_hint(
            "entry_point", 
            os.path.relpath(entry, repo_path), 
            {"type": "cpp", "is_daemon": is_daemon}
        )
    
    # 2. Sync Codebase Graph Hints
    print("[*] Extracting core business logic hints from code graph...")
    core_logic = client.get_core_logic()
    
    if isinstance(core_logic, dict) and "error" in core_logic:
        print(f"Error extracting hints: {core_logic['error']}")
        return

    count = 0
    for item in core_logic:
        name = item.get("name")
        generator.db.save_static_hint(
            hint_type="code_structure",
            key=item.get("qualified_name", name),
            value_dict=item
        )
        count += 1
        
    print(f"[+] Successfully synced {count} core logic hints and entry points to BLM database.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 sync_hints.py <repo_path> [db_path]")
        sys.exit(1)
        
    repo = sys.argv[1]
    db = sys.argv[2] if len(sys.argv) > 2 else "data/blm.db"
    sync_codebase_hints(repo, db)
