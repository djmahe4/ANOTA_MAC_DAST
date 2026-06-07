import json
import re
from logic_engine.agent_config import AgentConfig

class DiscoveryAgent:
    """
    Analyzes codebase context to discover environment variables, headers, or 
    session keys that control the application's flow.
    """
    def __init__(self, memory_controller):
        self.memory = memory_controller
        self.llm = AgentConfig.get_llm("reasoning")
        self.prompt_template = """
You are the MAC-DAST Discovery Agent.
Your goal is to identify environment variables, configuration constants, or session keys that control the target application's security level or business logic flow.

CODE CONTEXT:
{semantic_context}

CODE DEPENDENCIES (Internal Files):
{dependencies}

INSTRUCTIONS:
1. Search for `getenv()`, `defined()`, `$_SESSION`, `$_COOKIE`, or `header()` checks.
2. Identify values that change logic (e.g., 'low', 'dev', 'admin').
3. Propose a list of potential "execution contexts" (dictionaries of env vars) to test.

OUTPUT FORMAT:
Return a JSON object with:
- "contexts": A list of dictionaries (e.g., [[{{"security": "low"}}, {{"DEBUG": "1"}}]]).
- "rationale": Brief explanation of why these were chosen based on the code.
"""

    async def get_contexts(self, trace_id):
        """
        Retrieves context and asks the LLM to suggest probes.
        """
        context = self.memory.get_context_for_trace(trace_id)
        
        # Include dynamic coverage and static structural hints
        semantic_context = json.dumps(context.get("semantic", []))
        
        # Pull static dependencies from DB for this trace's entry point
        cursor = self.memory.blm_db.conn.cursor()
        cursor.execute("SELECT value FROM static_hints WHERE type = 'code_dependency'")
        dependencies = [json.loads(row[0]) for row in cursor.fetchall()]
        
        prompt = self.prompt_template.format(
            semantic_context=semantic_context,
            dependencies=json.dumps(dependencies)
        )
        
        response = await self.llm.ainvoke(prompt)
        content = response.content
        
        # Robust JSON extraction
        json_match = re.search(r'(\{.*\})', content, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                return data.get("contexts", [{}])
            except json.JSONDecodeError:
                pass
                
        return [{}] # Default empty context
