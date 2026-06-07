import json
import os
from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from iii import register_worker, InitOptions
from logic_engine.agent_config import AgentConfig
from interface.blm.db import BLMDatabase
from interface.memory.codebase import CodebaseMemoryClient

from interface.memory.controller import MemoryController

from logic_engine.agents.attack_gen import AttackGenerator
from logic_engine.agents.validator import ValidatorAgent
from logic_engine.agents.executor import AttackExecutor
from logic_engine.agents.repro_gen import ReproGenerator
from logic_engine.agents.knowledge import KnowledgeAgent
from interface.memory.projector import KnowledgeProjector

# Define the shared state for the graph
class AgentState(TypedDict):
    task: str
    trace_id: str
    context: dict
    attack_hypothesis: dict
    execution_result: dict
    verdict: dict
    repro_script: str
    findings: List[str]
    next_action: str

class AgentOrchestrator:
    """
    Supervisor that manages the MAC-DAST agent swarm using LangGraph.
    Integrated with iii-engine for durable execution.
    """
    def __init__(self, db_path="data/blm.db", project_name="anota_target"):
        self.db = BLMDatabase(db_path)
        self.project_name = project_name
        self.codebase = CodebaseMemoryClient(project_name=project_name)
        # Ensure codebase client knows the root path if it can be inferred
        self.memory = MemoryController(self.db, self.codebase)
        self.attack_gen = AttackGenerator(self.memory)
        self.validator = ValidatorAgent()
        self.repro_gen = ReproGenerator()
        self.knowledge_agent = KnowledgeAgent()
        self.projector = KnowledgeProjector()
        self.executor = AttackExecutor() # Real runners would be injected here
        self.llm = AgentConfig.get_llm("reasoning")
        self._setup_graph()

    def _setup_graph(self):
        workflow = StateGraph(AgentState)

        # Define Nodes
        workflow.add_node("analyze_trace", self.analyze_trace)
        workflow.add_node("generate_attack", self.generate_attack)
        workflow.add_node("validate_attack", self.validate_attack)
        workflow.add_node("promote_knowledge", self.promote_knowledge)

        # Define Edges
        workflow.set_entry_point("analyze_trace")
        workflow.add_edge("analyze_trace", "generate_attack")
        workflow.add_edge("generate_attack", "validate_attack")
        workflow.add_edge("validate_attack", "promote_knowledge")
        workflow.add_edge("promote_knowledge", END)

        self.app = workflow.compile()

    def _log_agent_turn(self, node_name, state, output):
        """
        Logs raw agent interaction to Vault/SessionLog.md for transparency.
        """
        log_path = os.path.join(self.projector.vault_root, "SessionLog.md")
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Scrub large context to keep log readable
        clean_state = {k: v for k, v in state.items() if k != "context"}
        
        log_entry = f"""
### [{timestamp}] Node: {node_name}
**State (Scrubbed):**
```json
{json.dumps(clean_state, indent=2)}
```

**Output/Decision:**
```json
{json.dumps(output, indent=2)}
```
---
"""
        with open(log_path, "a") as f:
            f.write(log_entry)

    def analyze_trace(self, state: AgentState):
        """
        Agent node: Examines a dynamic execution trace and static code hints.
        """
        trace_id = state["trace_id"]
        context = self.memory.get_context_for_trace(trace_id)
        res = {
            "context": context,
            "next_action": "attack"
        }
        self._log_agent_turn("analyze_trace", state, res)
        return res

    async def generate_attack(self, state: AgentState):
        """
        Agent node: Synthesizes a logic exploit based on the BLM.
        """
        trace_id = state["trace_id"]
        hypothesis = await self.attack_gen.generate(trace_id)
        res = {
            "attack_hypothesis": hypothesis,
            "next_action": "validate"
        }
        self._log_agent_turn("generate_attack", state, res)
        return res

    async def validate_attack(self, state: AgentState):
        """
        Agent node: Executes the attack and reality-checks the result.
        """
        hypothesis = state["attack_hypothesis"]
        
        # Carry over context from baseline trace (e.g., security level)
        baseline_cookies = state["context"].get("episodic", {}).get("state_data", {}).get("cookies", {})
        env_context = {}
        if "security" in baseline_cookies:
            env_context["security"] = baseline_cookies["security"]

        # 1. Execute attack
        execution_trace = self.executor.execute(hypothesis, env=env_context)
        
        # 2. Validate result
        verdict = await self.validator.validate(hypothesis, execution_trace)
        
        repro_script = ""
        findings = state.get("findings", [])
        if verdict.get("verdict") == "Valid":
            findings.append(f"CRITICAL: {verdict.get('reasoning')}")
            # 3. Generate reproduction script
            repro_script = await self.repro_gen.generate(hypothesis, execution_trace, verdict)
            
        res = {
            "execution_result": execution_trace,
            "verdict": verdict,
            "repro_script": repro_script,
            "findings": findings
        }
        self._log_agent_turn("validate_attack", state, res)
        return res

    async def promote_knowledge(self, state: AgentState):
        """
        Agent node: Curates confirmed finding into the Obsidian Vault.
        """
        verdict = state.get("verdict", {})
        if verdict.get("verdict") == "Valid":
            # 1. Synthesize human-readable rationale
            summary = await self.knowledge_agent.synthesize(
                state["attack_hypothesis"],
                state["execution_result"],
                verdict
            )
            
            # 2. Project into Vault
            promotion_data = {
                "id": state["trace_id"],
                "title": summary.get("title", "Confirmed Logic Flaw"),
                "target": state["attack_hypothesis"].get("target_action"),
                "confidence": verdict.get("confidence"),
                "model": AgentConfig.REASONING_MODEL,
                "rationale": summary.get("rationale"),
                "evidence": summary.get("evidence_summary")
            }
            self.projector.materialize_finding(promotion_data)
            
        return {}

# --- iii-engine Integration ---

async def process_new_trace(payload: dict) -> dict:
    """
    Durable iii-engine function triggered when a new trace is aggregated.
    """
    try:
        trace_id = payload.get("trace_id")
        if not trace_id:
            return {"status": "error", "message": "Missing trace_id"}
            
        orchestrator = AgentOrchestrator()
        
        # Run the LangGraph workflow
        initial_state = {
            "task": "Find logic flaws",
            "trace_id": trace_id,
            "context": {},
            "attack_hypothesis": {},
            "findings": [],
            "next_action": ""
        }
        
        result = await orchestrator.app.ainvoke(initial_state)
        return {"status": "complete", "findings": result.get("findings", [])}
    except Exception as e:
        print(f"[!] Orchestrator error (process_trace): {e}")
        return {"status": "error", "message": str(e)}

async def consolidate_memory(payload: dict) -> dict:
    """
    Background worker to consolidate memory tiers.
    """
    try:
        orchestrator = AgentOrchestrator()
        orchestrator.memory.consolidate()
        return {"status": "consolidated"}
    except Exception as e:
        print(f"[!] Orchestrator error (consolidate): {e}")
        return {"status": "error", "message": str(e)}

def start_worker():
    """
    Starts the iii worker.
    """
    import signal
    import time
    
    worker = register_worker(
        os.environ.get("III_URL", "ws://127.0.0.1:49134"),
        InitOptions(worker_name="mac-dast-orchestrator"),
    )
    
    worker.register_function("orchestrator::process_trace", process_new_trace)
    worker.register_function("orchestrator::consolidate", consolidate_memory)
    
    # Set up graceful shutdown
    def _on_term(*_):
        print("\n[*] Shutting down MAC-DAST Orchestrator Worker...")
        worker.shutdown()
        os._exit(0)
    
    signal.signal(signal.SIGTERM, _on_term)
    signal.signal(signal.SIGINT, _on_term)

    print("[*] MAC-DAST Orchestrator Worker started.")
    
    # Keep the worker running indefinitely
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        _on_term()

if __name__ == "__main__":
    start_worker()
