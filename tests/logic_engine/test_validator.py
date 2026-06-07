import unittest
from unittest.mock import MagicMock, AsyncMock
from logic_engine.agents.validator import ValidatorAgent

class TestValidatorAgent(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.validator = ValidatorAgent()

    async def test_validate_successful_exploit(self):
        hypothesis = {
            "expected_outcome": "User role changes to admin without login"
        }
        trace = {
            "state_data": {"session": {"role": "admin"}},
            "events_data": [{"type": "uprobe", "symbol": "bypass_check"}]
        }
        
        # Mock LLM to return 'Valid'
        self.validator.llm = AsyncMock()
        self.validator.llm.ainvoke.return_value = MagicMock(content='{"verdict": "Valid", "reasoning": "Role is admin"}')
        
        result = await self.validator.validate(hypothesis, trace)
        
        self.assertEqual(result["verdict"], "Valid")

if __name__ == "__main__":
    unittest.main()
