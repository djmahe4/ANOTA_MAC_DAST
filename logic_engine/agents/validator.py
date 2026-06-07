import json
import re
import os
from logic_engine.agent_config import AgentConfig

class ValidatorAgent:
    """
    Evaluates execution traces against attack hypotheses to confirm vulnerabilities.
    Acts as a 'Critic' to eliminate false positives.
    """
    def __init__(self):
        # Use reasoning model for critical judgement
        self.llm = AgentConfig.get_llm("reasoning")
        # Load prompt template
        prompt_path = os.path.join("agents", "prompts", "validate_attack.txt")
        with open(prompt_path, "r") as f:
            self.prompt_template = f.read()

    async def validate(self, hypothesis, trace):
        """
        Invokes the LLM to judge the execution trace and computes an objective confidence score.
        """
        prompt = self.prompt_template.format(
            hypothesis=json.dumps(hypothesis, indent=2),
            trace=json.dumps(trace, indent=2)
        )
        
        response = await self.llm.ainvoke(prompt)
        content = response.content
        
        # 1. Robust JSON extraction
        verdict_data = {"verdict": "Inconclusive", "confidence": 0.0, "reasoning": "Parse failure"}
        json_match = re.search(r'(\{.*\})', content, re.DOTALL)
        if json_match:
            try:
                verdict_data = json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # 2. Objective Telemetry Match Score
        # We check if the 'expected_outcome' string keywords appear in the trace events/state
        telemetry_score = self._compute_telemetry_match(hypothesis.get("expected_outcome", ""), trace)
        
        # 3. Final Weighted Confidence
        # 60% LLM judgment, 40% objective telemetry match
        llm_conf = float(verdict_data.get("confidence", 0.5))
        final_confidence = (llm_conf * 0.6) + (telemetry_score * 0.4)
        
        verdict_data["confidence"] = round(final_confidence, 2)
        verdict_data["telemetry_match"] = round(telemetry_score, 2)
        
        return verdict_data

    def _compute_telemetry_match(self, expected_outcome, trace):
        """
        Calculates a score [0.0 - 1.0] based on keyword overlap between 
        the expected outcome and the observed trace data.
        """
        if not expected_outcome:
            return 0.5
            
        keywords = set(re.findall(r'\w+', expected_outcome.lower()))
        trace_str = json.dumps(trace).lower()
        
        matches = 0
        for word in keywords:
            if word in trace_str:
                matches += 1
                
        return matches / len(keywords) if keywords else 1.0
