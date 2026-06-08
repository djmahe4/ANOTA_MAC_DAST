import os
import json
import asyncio
from datetime import datetime
from interface.blm.db import BLMDatabase
from interface.blm.generator import BLMGenerator
from interface.php_xdebug.runner import PHPRunner
from interface.cpp_ebpf.harness import CPPHarness
from logic_engine.orchestrator import AgentOrchestrator
from interface.memory.controller import MemoryController
from interface.memory.codebase import CodebaseMemoryClient
from logic_engine.agents.discovery import DiscoveryAgent

class FullScanner:
    """
    Automates the scanning of all identified entry points in a target repository.
    Includes path validation (jail) and autonomous context discovery via Agent.
    """
    def __init__(self, db_path, project_name, repo_path):
        self.db_path = db_path
        self.repo_path = os.path.abspath(repo_path)
        # Fix: correctly initialize with root_path
        self.codebase = CodebaseMemoryClient(project_name=project_name, root_path=self.repo_path)
        
        self.db = BLMDatabase(db_path)
        self.memory = MemoryController(self.db, self.codebase)
        self.generator = BLMGenerator(db_path=db_path, memory_controller=self.memory)
        self.discovery_agent = DiscoveryAgent(self.memory)
        
        self.php_runner = PHPRunner()
        self.cpp_harness = CPPHarness()
        
        self.orchestrator = AgentOrchestrator(db_path=db_path, project_name=project_name)
        # Ensure consistency
        self.orchestrator.memory.codebase.root_path = self.repo_path
        self.orchestrator.executor.php_runner = self.php_runner
        self.orchestrator.executor.cpp_harness = self.cpp_harness
        
        # Concurrency: Limit to 2 for local LLM stability
        self.semaphore = asyncio.Semaphore(2)

    def get_entry_points(self):
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT key, value FROM static_hints WHERE type = 'entry_point'")
        return [(row[0], json.loads(row[1])) for row in cursor.fetchall()]

    def _validate_path(self, path):
        abs_path = os.path.abspath(path)
        if not abs_path.startswith(self.repo_path):
            raise SecurityError(f"Path traversal attempt blocked: {abs_path}")
        return abs_path

    async def _scan_entry(self, rel_path, info):
        async with self.semaphore:
            full_path = self._validate_path(os.path.join(self.repo_path, rel_path))
            print(f"\n[>] Scanning {info['type'].upper()} entry point: {rel_path}")
            
            # 1. Baseline run (Clean state)
            base_trace_id = f"baseline-{info['type']}-{os.path.basename(rel_path)}-{int(asyncio.get_event_loop().time())}"
            try:
                if info['type'] == 'php':
                    telemetry, _ = self.php_runner.run(full_path, repo_root=self.repo_path, use_http=True)
                else:
                    telemetry = self._generate_cpp_telemetry(rel_path)
                
                telemetry.update({
                    "trace_id": base_trace_id,
                    "timestamp": datetime.now().isoformat(),
                    "source": info['type']
                })
                await self.generator.ingest(telemetry, action_name=rel_path)
                
                # Logic: If coverage is high, we might not need immediate discovery
                # Logic: We no longer do the manual setup loop here. The Orchestrator's discovery node handles it autonomously!
                total_cov = sum(len(lines) for lines in telemetry.get("coverage", {}).values())
                
                # We can just start the orchestrator directly, the discovery node will handle everything.
                trace_id = base_trace_id
                
                state = {
                    "task": f"Analyze entry point {rel_path} for logic flaws.",
                    "trace_id": trace_id, 
                    "target_script": full_path,
                    "context": {
                        "active_env": {},
                        "session": {}
                    },
                    "attack_hypothesis": {},
                    "execution_result": {}, "verdict": {}, "repro_script": "",
                    "findings": [], "next_action": ""
                }

                final_state = await self.orchestrator.app.ainvoke(state)

                if final_state.get("findings"):
                    return {
                        "entry": rel_path,
                        "findings": final_state["findings"],
                        "verdict": final_state.get("verdict", {}).get("verdict", "Inconclusive")
                    }
                
                return {"entry": rel_path, "findings": [], "verdict": "Clean"}
            except Exception as e:
                print(f" [!] Discovery failure for {rel_path}: {e}")
                return {"entry": rel_path, "findings": [], "verdict": "Discovery Error"}

    def _generate_cpp_telemetry(self, rel_path):
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT value FROM static_hints WHERE type = 'code_structure'")
        symbols = []
        for row in cursor.fetchall():
            hint = json.loads(row[0])
            if hint.get("file_path", "").startswith(rel_path.split('/')[0]):
                 symbols.append(hint.get("name"))
        return {"coverage": {}, "state": {}, "events": [{"type": "static_analysis", "symbols_found": symbols}]}

    async def scan_all(self):
        entries = self.get_entry_points()
        print(f"[*] Found {len(entries)} entry points. Starting optimized scan...")
        tasks = [self._scan_entry(rel_path, info) for rel_path, info in entries]
        return await asyncio.gather(*tasks)

class SecurityError(Exception): pass

async def main():
    import sys
    if len(sys.argv) < 4:
        print("Usage: python3 -m logic_engine.scanner <db_path> <project_name> <repo_path>")
        return
    scanner = FullScanner(sys.argv[1], sys.argv[2], sys.argv[3])
    try:
        results = await scanner.scan_all()
    finally:
        scanner.php_runner.stop_server()
    
    print("\n" + "="*30 + "\n      SCAN SUMMARY\n" + "="*30)
    for res in results:
        status = "✅ CLEAN" if not res["findings"] else f"❌ VULNERABLE ({res['verdict']})"
        print(f"{res['entry']}: {status}")
        for f in res["findings"]: print(f"  - {f}")

if __name__ == "__main__":
    asyncio.run(main())
