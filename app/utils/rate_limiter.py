import asyncio
import time
import logging

logger = logging.getLogger(__name__)

class TokenBucket:
    def __init__(self, rate: float, capacity: int):
        self.rate = rate
        self.capacity = capacity
        self.tokens = float(capacity)
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self, timeout: float = 30.0) -> bool:
        start_time = time.monotonic()
        while True:
            async with self._lock:
                now = time.monotonic()
                elapsed = now - self.last_update
                self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
                self.last_update = now

                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    return True

            if time.monotonic() - start_time > timeout:
                return False
            
            await asyncio.sleep(0.1)

    def available_tokens(self) -> int:
        return int(self.tokens)

from app.config import settings
cnas_rate_limiter = TokenBucket(rate=1.0/settings.CNAS_RATE_LIMIT_SECONDS, capacity=1)
