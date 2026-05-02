import asyncio
import logging
import functools
from typing import Type, List, Callable

logger = logging.getLogger(__name__)


def retry(
    max_attempts: int = 3,
    base_delay: float = 2.0,
    max_delay: float = 30.0,
    exceptions: List[Type[Exception]] = [Exception],
):
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    if attempts >= max_attempts or not any(
                        isinstance(e, ex) for ex in exceptions
                    ):
                        logger.error(
                            f"Function {func.__name__} failed after {attempts} attempts: {str(e)}"
                        )
                        raise e

                    delay = min(base_delay * (2 ** (attempts - 1)), max_delay)
                    logger.warning(
                        f"Function {func.__name__} failed (attempt {attempts}/{max_attempts}). Retrying in {delay}s... Error: {str(e)}"
                    )
                    await asyncio.sleep(delay)
            return await func(*args, **kwargs)

        return wrapper

    return decorator
