import os
import json
from logic_engine.agent_config import AgentConfig

class ReproGenerator:
    """
    Generates standalone Python/Bash reproduction scripts for confirmed vulnerabilities.
    """
    def __init__(self):
        self.llm = AgentConfig.get_llm("coder")
        prompt_path = os.path.join("agents", "prompts", "repro_attack.txt")
        with open(prompt_path, "r") as f:
            self.prompt_template = f.read()

    async def generate(self, hypothesis, trace, verdict):
        """
        Synthesizes the reproduction script.
        """
        prompt = self.prompt_template.format(
            hypothesis=json.dumps(hypothesis, indent=2),
            trace=json.dumps(trace, indent=2),
            verdict=json.dumps(verdict, indent=2)
        )
        
        response = await self.llm.ainvoke(prompt)
        return response.content
