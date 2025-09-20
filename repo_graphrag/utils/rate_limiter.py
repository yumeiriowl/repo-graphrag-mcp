import asyncio
import time
import logging
from ..config.settings import rate_limit_min_interval, llm_model_max_async


logger = logging.getLogger(__name__)

class RateLimiter:
    """Controls API request intervals and concurrency."""
    
    def __init__(self, min_interval: float = 1.0, max_concurrent: int = 3) -> None:
        """
        Args:
            min_interval: Minimum interval between requests in seconds
            max_concurrent: Maximum concurrent operations
        """
        self.min_interval = min_interval
        self.max_concurrent = max_concurrent
        self.last_request_time = 0
        self.request_lock = asyncio.Lock()
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
    async def __aenter__(self) -> 'RateLimiter':
        """Enter async context: enforce concurrency and pacing."""
        # Limit concurrency via semaphore
        await self.semaphore.acquire()
        
    # Enforce minimum interval between requests
        async with self.request_lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            
            if time_since_last < self.min_interval:
                wait_time = self.min_interval - time_since_last
                logger.info(f"Rate limit: waiting {wait_time:.2f} seconds...")
                await asyncio.sleep(wait_time)
            
            self.last_request_time = time.time()
        
        return self
    
    async def __aexit__(self, *exc_info) -> None:
        """Exit async context: release concurrency slot."""
        self.semaphore.release()

def get_rate_limiter() -> RateLimiter:
    """
    Create a new RateLimiter instance from settings.

    Returns:
        RateLimiter: Instance initialized with configured values
    """
    return RateLimiter(rate_limit_min_interval, llm_model_max_async)
