import os
import json
import re
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
        Retrieves context and generates an attack hypothesis with a 3-pass retry loop for JSON robustness.
        """
        # 1. Fetch multi-tier context
        context = self.memory.get_context_for_trace(trace_id)
        
        # 2. Extract state summary for prompt
        source = context["episodic"].get("source", "unknown")
        state_summary = json.dumps(context["episodic"].get("state_data", {}))
        semantic_context = json.dumps(context["semantic"])
        
        # 3. Construct Prompt
        base_prompt = self.template.format(
            source=source,
            state_summary=state_summary,
            semantic_context=semantic_context,
            blm_graph_fragment="[Querying BLM Transitions...]"
        )
        
        # 4. Retry loop for LLM JSON robustness
        for attempt in range(3):
            prompt = base_prompt
            if attempt > 0:
                prompt += "\n\nCRITICAL: Your previous response was not valid JSON. Return ONLY a valid JSON object."
                
            response = await self.llm.ainvoke(prompt)
            content = response.content
            
            # 5. Robust JSON extraction
            json_match = re.search(r'(\{.*\})', content, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass
                    
        return {
            "error": "LLM failed to return valid JSON after 3 attempts",
            "hypothesis": "FAILED_TO_PARSE",
            "raw": content
        }
