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
        rows = cursor.fetchall()
        dependencies = [json.loads(row[0]) for row in rows] if rows else []
        
        # Using a raw string and manual replacement to avoid brace/format hell
        prompt = """
        You are the MAC-DAST Discovery Agent.
        Your goal is to identify environment variables, configuration constants, or session keys that control the target application's security level or business logic flow.

        CODE CONTEXT:
        {{SEMANTIC_CONTEXT}}

        CODE DEPENDENCIES (Internal Files):
        {{DEPENDENCIES}}

        INSTRUCTIONS:
        1. Search for getenv(), defined(), $_SESSION, $_COOKIE, header(), or $GLOBALS checks in the snippets above.
        2. Identify values that change logic (e.g., 'low', 'dev', 'admin').
        3. **CREDENTIAL DISCOVERY**: Look for hardcoded test users, passwords, or configuration defaults in comments or code.
        4. **CRITICAL: CONFIGURATION OVERRIDES**: If the application requires a database or configuration to boot (e.g. $DBMS, $_DVWA), suggest overriding these to prevent crashes. If the code uses `getenv()`, put the override in the "ENV" dictionary. Otherwise, put it in "GLOBALS".
           - ALWAYS set any `DISABLE_AUTHENTICATION` or similar environment variables to `true` (boolean) to bypass login screens!
        5. **CRITICAL: SETUP ACTIONS**: 
           - Check for `file_exists` or `die()` statements indicating missing configuration files. If found, suggest "copy [src] [dst]".
           - If the application strictly requires a MySQL/MariaDB database to be running locally, suggest "start_db [dbname] [user] [pass] [port]" (e.g., "start_db dvwa dvwa p@ssw0rd 3306").
           - If there's an initialization endpoint (e.g., `setup.php`), suggest "http_post setup.php create_db=1".
        6. Propose a list of potential "execution contexts" (dictionaries containing "ENV" or "GLOBALS") to test.
        7. **STRICT GROUNDING**: ONLY use parameter keys and environment variable names found in the provided CODE CONTEXT.

        OUTPUT FORMAT:
        Return a JSON object with:
        - "contexts": A list of dictionaries (e.g., [{"ENV": {"security": "low", "DBMS": "SQLite"}, "GLOBALS": {"_DVWA": {"disable_authentication": true}}}]).
        - "setup_actions": A list of strings for required setup steps (e.g., ["copy config/config.inc.php.dist config/config.inc.php", "start_db dvwa dvwa p@ssw0rd 3306"]).
        - "rationale": Brief explanation of why these were chosen based on the code.
        """

        prompt = prompt.replace("{{SEMANTIC_CONTEXT}}", semantic_context)
        prompt = prompt.replace("{{DEPENDENCIES}}", json.dumps(dependencies))
        
        response = await self.llm.ainvoke(prompt)
        content = response.content
        print(f" [DEBUG] Discovery LLM Output: {content}")
        
        # Robust JSON extraction
        json_match = re.search(r'(\{.*\})', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
                
        return {"contexts": [{}], "setup_actions": []}
