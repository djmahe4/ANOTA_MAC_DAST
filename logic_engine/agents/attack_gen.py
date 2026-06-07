import os
import json
from logic_engine.agent_config import AgentConfig

class AttackGenerator:
    """
    Synthesizes context-aware logic attacks using Qwen 2.5 Coder.
    """
    def __init__(self, memory_controller):
        self.memory = memory_controller
        self.llm = AgentConfig.get_llm("coder")
        
        # Load prompt template
        prompt_path = os.path.join("agents", "prompts", "logic_attack.txt")
        with open(prompt_path, "r") as f:
            self.template = f.read()

    async def generate(self, trace_id):
        """
        Retrieves context and generates an attack hypothesis.
        """
        # 1. Fetch multi-tier context
        context = self.memory.get_context_for_trace(trace_id)
        
        # 2. Extract state summary for prompt
        source = context["episodic"].get("source", "unknown")
        state_summary = json.dumps(context["episodic"].get("state_data", {}))
        semantic_context = json.dumps(context["semantic"])
        
        # 3. Construct Prompt
        prompt = self.template.format(
            source=source,
            state_summary=state_summary,
            semantic_context=semantic_context,
            blm_graph_fragment="[Querying BLM Transitions...]"
        )
        
        # 4. Invoke LLM
        response = await self.llm.ainvoke(prompt)
        
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            return {"error": "LLM failed to return JSON", "raw": response.content}
