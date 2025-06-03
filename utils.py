import asyncio
import functools
import logging
import time

logger = logging.getLogger(__name__)

def log_timing(func):
    if asyncio.iscoroutinefunction(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = await func(*args, **kwargs)
            duration = time.perf_counter() - start
            logger.info(f"{func.__name__} took {duration:.2f}s")
            return result
        return async_wrapper
    else:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = func(*args, **kwargs)
            duration = time.perf_counter() - start
            logger.info(f"{func.__name__} took {duration:.2f}s")
            return result
        return sync_wrapper