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

# Define the shared state for the graph
class AgentState(TypedDict):
    task: str
    trace_id: str
    context: dict
    attack_hypothesis: dict
    findings: List[str]
    next_action: str

class AgentOrchestrator:
    """
    Supervisor that manages the MAC-DAST agent swarm using LangGraph.
    Integrated with iii-engine for durable execution.
    """
    def __init__(self, db_path="data/blm.db"):
        self.db = BLMDatabase(db_path)
        self.codebase = CodebaseMemoryClient()
        self.memory = MemoryController(self.db, self.codebase)
        self.attack_gen = AttackGenerator(self.memory)
        self.llm = AgentConfig.get_llm("reasoning")
        self._setup_graph()

    def _setup_graph(self):
        workflow = StateGraph(AgentState)

        # Define Nodes
        workflow.add_node("analyze_trace", self.analyze_trace)
        workflow.add_node("generate_attack", self.generate_attack)
        workflow.add_node("validate_attack", self.validate_attack)

        # Define Edges
        workflow.set_entry_point("analyze_trace")
        workflow.add_edge("analyze_trace", "generate_attack")
        workflow.add_edge("generate_attack", "validate_attack")
        workflow.add_edge("validate_attack", END)

        self.app = workflow.compile()

    def analyze_trace(self, state: AgentState):
        """
        Agent node: Examines a dynamic execution trace and static code hints.
        """
        trace_id = state["trace_id"]
        context = self.memory.get_context_for_trace(trace_id)
        return {
            "context": context,
            "next_action": "attack"
        }

    async def generate_attack(self, state: AgentState):
        """
        Agent node: Synthesizes a logic exploit based on the BLM.
        """
        trace_id = state["trace_id"]
        hypothesis = await self.attack_gen.generate(trace_id)
        return {
            "attack_hypothesis": hypothesis,
            "next_action": "validate"
        }

    def validate_attack(self, state: AgentState):
        """
        Agent node: Reality-checks the exploit against the instrumentation.
        """
        # Placeholder for Phase 5
        hypothesis = state.get("attack_hypothesis", {}).get("hypothesis", "unknown")
        return {"findings": [f"Exploit hypothesized: {hypothesis}"]}

# --- iii-engine Integration ---

async def process_new_trace(payload: dict) -> dict:
    """
    Durable iii-engine function triggered when a new trace is aggregated.
    """
    trace_id = payload.get("trace_id")
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
    return {"status": "complete", "findings": result["findings"]}

async def consolidate_memory(payload: dict) -> dict:
    """
    Background worker to consolidate memory tiers.
    """
    orchestrator = AgentOrchestrator()
    orchestrator.memory.consolidate()
    return {"status": "consolidated"}

def start_worker():
    """
    Starts the iii worker.
    """
    worker = register_worker(
        os.environ.get("III_URL", "ws://127.0.0.1:49134"),
        InitOptions(worker_name="mac-dast-orchestrator"),
    )
    
    worker.register_function("orchestrator::process_trace", process_new_trace)
    worker.register_function("orchestrator::consolidate", consolidate_memory)
    
    # Example trigger for process_trace (could be a queue or event)
    # worker.register_trigger({
    #     "type": "durable:subscriber", 
    #     "function_id": "orchestrator::process_trace", 
    #     "config": {"topic": "traces"}
    # })

    print("[*] MAC-DAST Orchestrator Worker started.")
    worker.wait()

if __name__ == "__main__":
    start_worker()
