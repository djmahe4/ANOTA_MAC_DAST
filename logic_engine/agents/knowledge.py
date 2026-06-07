import os
import json
import re
from logic_engine.agent_config import AgentConfig

class KnowledgeAgent:
    """
    Synthesizes finding summaries and rationales for the Obsidian Vault.
    """
    def __init__(self):
        self.llm = AgentConfig.get_llm("reasoning")
        # Load prompt template
        prompt_path = os.path.join("agents", "prompts", "promote_finding.txt")
        with open(prompt_path, "r") as f:
            self.template = f.read()

    async def synthesize(self, hypothesis, trace, verdict):
        """
        Asks the LLM to generate a human-readable finding summary.
        """
        prompt = self.template.format(
            hypothesis=json.dumps(hypothesis, indent=2),
            trace=json.dumps(trace, indent=2),
            verdict=json.dumps(verdict, indent=2)
        )
        
        response = await self.llm.ainvoke(prompt)
        content = response.content
        
        # Robust JSON extraction
        json_match = re.search(r'(\{.*\})', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
                
        return {
            "title": "Unparsed Finding",
            "rationale": "Failed to synthesize rationale",
            "evidence_summary": str(content)
        }
