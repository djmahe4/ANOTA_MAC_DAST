import unittest
import asyncio
from logic_engine.agents.concurrent_attacker import ConcurrentAttacker

class TestConcurrentAttacker(unittest.TestCase):
    def test_spawn_concurrent_requests(self):
        attacker = ConcurrentAttacker()
        
        # Mock request function
        results = []
        async def mock_request(payload):
            await asyncio.sleep(0.1) # Simulate network lag
            results.append(payload)
            return {"status": 200}

        payloads = [{"id": 1}, {"id": 2}, {"id": 3}]
        
        # Run 3 concurrent requests
        asyncio.run(attacker.spawn(mock_request, payloads))
        
        self.assertEqual(len(results), 3)
        # Check that they all finished (concurrency is harder to prove with purely synchronous tests, 
        # but we verify they all ran).

if __name__ == "__main__":
    unittest.main()
