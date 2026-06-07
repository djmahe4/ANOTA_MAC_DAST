import asyncio

class ConcurrentAttacker:
    """
    Spawns multiple concurrent requests to target race conditions.
    """
    async def spawn(self, request_fn, payloads):
        """
        Executes request_fn concurrently for each payload in payloads.
        """
        tasks = []
        for payload in payloads:
            tasks.append(asyncio.create_task(request_fn(payload)))
        
        return await asyncio.gather(*tasks)
