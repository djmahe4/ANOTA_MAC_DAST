import unittest
import os
import json
import sqlite3
from unittest.mock import MagicMock, patch
from interface.memory.controller import MemoryController
from interface.blm.db import BLMDatabase

class TestAgenticMemoryIndexing(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.db_path = "tests/fixtures/test_indexing.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.db = BLMDatabase(self.db_path)
        self.memory = MemoryController(self.db, MagicMock())

    def tearDown(self):
        self.db.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    @patch("logic_engine.agent_config.AgentConfig.get_embedding")
    @patch("logic_engine.agent_config.AgentConfig.get_llm")
    async def test_agentic_compression(self, mock_get_llm, mock_get_embedding):
        # 1. Create a large trace (> 4000 but < 12000)
        critical_finding = "CRITICAL_SECURITY_VULNERABILITY_CONFIRMED_HERE"
        large_trace = "dummy_data " * 450 + critical_finding
        self.assertTrue(len(large_trace) > 4000)
        self.assertTrue(len(large_trace) < 12000)

        # 2. Mock LLM (Async)
        from unittest.mock import AsyncMock
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = MagicMock(content=f"Summary: {critical_finding}")
        mock_get_llm.return_value = mock_llm
        
        # 3. Mock Embedding
        mock_get_embedding.return_value = [0.1] * 1024

        # 4. Call add_vector_index (Agentic version)
        await self.memory.add_vector_index_agentic("trace-large", large_trace)

        # 5. Verify the LLM was called to compress the logic
        mock_llm.ainvoke.assert_called()
        
        # 6. Verify the embedding was generated for the summary
        call_args = mock_get_embedding.call_args[0][0]
        self.assertIn(critical_finding, call_args)

    @patch("logic_engine.agent_config.AgentConfig.get_embedding")
    @patch("logic_engine.agent_config.AgentConfig.get_llm")
    async def test_tiered_reassessment(self, mock_get_llm, mock_get_embedding):
        # 1. Create a massive trace (> 12000 chars)
        massive_trace = "massive_data " * 2000 
        self.assertTrue(len(massive_trace) > 12000)

        # 2. Mock LLM (Async)
        from unittest.mock import AsyncMock
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = MagicMock(content="Segment/Final Summary")
        mock_get_llm.return_value = mock_llm
        
        # 3. Mock Embedding
        mock_get_embedding.return_value = [0.1] * 1024

        # 4. Call add_vector_index (Agentic version)
        await self.memory.add_vector_index_agentic("trace-massive", massive_trace)

        # 5. Verify tiered processing:
        # For ~26k chars, limit 12k -> 3 chunks + 1 final synthesis = 4 calls
        self.assertEqual(mock_llm.ainvoke.call_count, 4)

if __name__ == "__main__":
    unittest.main()
