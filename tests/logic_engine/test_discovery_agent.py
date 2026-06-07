import unittest
from unittest.mock import MagicMock, AsyncMock
from logic_engine.agents.discovery import DiscoveryAgent

class TestDiscoveryAgent(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.memory = MagicMock()
        self.agent = DiscoveryAgent(self.memory)

    async def test_discover_security_context(self):
        # Mock semantic context showing a getenv('security') call
        self.memory.get_context_for_trace.return_value = {
            "semantic": [
                [{"type": "code_summary", "content": "if (getenv('security') == 'low') { ... }"}]
            ]
        }
        
        # Mock LLM response
        self.agent.llm = AsyncMock()
        self.agent.llm.ainvoke.return_value = MagicMock(
            content='{"contexts": [{"security": "low"}, {"security": "medium"}]}'
        )
        
        contexts = await self.agent.get_contexts("dummy-trace")
        
        self.assertEqual(len(contexts), 2)
        self.assertEqual(contexts[0]["security"], "low")

if __name__ == "__main__":
    unittest.main()
