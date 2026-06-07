import os
import json
import asyncio
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
        self.codebase = CodebaseMemoryClient(project_name=project_name)
        self.codebase.root_path = self.repo_path
        
        self.db = BLMDatabase(db_path)
        self.memory = MemoryController(self.db, self.codebase)
        self.generator = BLMGenerator(db_path=db_path, memory_controller=self.memory)
        self.discovery_agent = DiscoveryAgent(self.memory)
        
        self.php_runner = PHPRunner()
        self.cpp_harness = CPPHarness()
        
        self.orchestrator = AgentOrchestrator(db_path=db_path)
        self.orchestrator.executor.php_runner = self.php_runner
        self.orchestrator.executor.cpp_harness = self.cpp_harness
        
        self.semaphore = asyncio.Semaphore(4)

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
            
            # 1. Gather autonomous discovery context
            base_trace_id = f"discovery-{info['type']}-{os.path.basename(rel_path)}-init"
            try:
                # Baseline run to feed the Discovery Agent
                init_telemetry = {
                    "trace_id": base_trace_id, "source": info['type'], "timestamp": "", 
                    "coverage": {rel_path: [1]}, "state": {}, "events": []
                }
                self.generator.ingest(init_telemetry, action_name=rel_path)
                
                # Ask Agent for suggested contexts based on code logic
                suggested_contexts = await self.discovery_agent.get_contexts(base_trace_id)
                print(f" [*] Discovery Agent suggested {len(suggested_contexts)} contexts")
                
                contexts = [{}] + suggested_contexts
                best_results = None
                
                for ctx in contexts:
                    try:
                        from datetime import datetime
                        trace_id = f"scan-{info['type']}-{os.path.basename(rel_path)}-{int(asyncio.get_event_loop().time())}"
                        
                        if info['type'] == 'php':
                            telemetry = self.php_runner.run(full_path, env=ctx)
                        else:
                            telemetry = self._generate_cpp_telemetry(rel_path)
                        
                        telemetry.update({
                            "trace_id": trace_id,
                            "timestamp": datetime.now().isoformat(),
                            "source": info['type']
                        })
                        
                        self.generator.ingest(telemetry, action_name=rel_path)
                        
                        state = {
                            "task": f"Analyze entry point {rel_path} with context {ctx}.",
                            "trace_id": trace_id, "context": {}, "attack_hypothesis": {},
                            "execution_result": {}, "verdict": {}, "repro_script": "",
                            "findings": [], "next_action": ""
                        }
                        
                        final_state = await self.orchestrator.app.ainvoke(state)
                        
                        if final_state.get("findings"):
                            best_results = {
                                "entry": rel_path,
                                "findings": final_state["findings"],
                                "verdict": final_state.get("verdict", {}).get("verdict", "Inconclusive")
                            }
                            break
                    except Exception as e:
                        print(f" [!] Error scanning {rel_path} with {ctx}: {e}")
                
                return best_results or {"entry": rel_path, "findings": [], "verdict": "Clean"}
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
        print(f"[*] Found {len(entries)} entry points. Starting parallel scan...")
        tasks = [self._scan_entry(rel_path, info) for rel_path, info in entries]
        return await asyncio.gather(*tasks)

class SecurityError(Exception): pass

async def main():
    import sys
    if len(sys.argv) < 4:
        print("Usage: python3 -m logic_engine.scanner <db_path> <project_name> <repo_path>")
        return
    scanner = FullScanner(sys.argv[1], sys.argv[2], sys.argv[3])
    results = await scanner.scan_all()
    print("\n" + "="*30 + "\n      SCAN SUMMARY\n" + "="*30)
    for res in results:
        status = "✅ CLEAN" if not res["findings"] else f"❌ VULNERABLE ({res['verdict']})"
        print(f"{res['entry']}: {status}")
        for f in res["findings"]: print(f"  - {f}")

if __name__ == "__main__":
    asyncio.run(main())
