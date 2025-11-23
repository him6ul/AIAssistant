"""
Middleware for connectors - retry logic, error handling, logging, throttling.
"""

import asyncio
import time
from typing import Callable, Any, Optional, TypeVar, Awaitable
from functools import wraps
from app.utils.logger import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        retryable_exceptions: tuple = (Exception,),
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.retryable_exceptions = retryable_exceptions


def with_retry(
    config: Optional[RetryConfig] = None,
) -> Callable:
    """
    Decorator to add retry logic to async functions.
    
    Args:
        config: Retry configuration (uses defaults if None)
    
    Example:
        @with_retry(RetryConfig(max_retries=5))
        async def fetch_data():
            ...
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None
            delay = config.initial_delay
            
            for attempt in range(config.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except config.retryable_exceptions as e:
                    last_exception = e
                    if attempt < config.max_retries:
                        logger.warning(
                            f"Attempt {attempt + 1}/{config.max_retries + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        await asyncio.sleep(delay)
                        delay = min(delay * config.exponential_base, config.max_delay)
                    else:
                        logger.error(f"All {config.max_retries + 1} attempts failed for {func.__name__}: {e}")
                except Exception as e:
                    # Non-retryable exception - re-raise immediately
                    logger.error(f"Non-retryable error in {func.__name__}: {e}")
                    raise
            
            # If we get here, all retries failed
            raise last_exception
        
        return wrapper
    return decorator


class RateLimiter:
    """Rate limiter for API calls."""
    
    def __init__(self, max_calls: int, time_window: float):
        """
        Initialize rate limiter.
        
        Args:
            max_calls: Maximum number of calls allowed
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls: list[float] = []
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> None:
        """Acquire permission to make a call (blocks if rate limit exceeded)."""
        async with self._lock:
            now = time.time()
            # Remove old calls outside the time window
            self.calls = [call_time for call_time in self.calls if now - call_time < self.time_window]
            
            if len(self.calls) >= self.max_calls:
                # Calculate wait time
                oldest_call = min(self.calls)
                wait_time = self.time_window - (now - oldest_call) + 0.1
                logger.debug(f"Rate limit reached. Waiting {wait_time:.2f}s...")
                await asyncio.sleep(wait_time)
                # Clean up again after waiting
                now = time.time()
                self.calls = [call_time for call_time in self.calls if now - call_time < self.time_window]
            
            self.calls.append(time.time())


def with_rate_limit(
    rate_limiter: RateLimiter,
) -> Callable:
    """
    Decorator to add rate limiting to async functions.
    
    Args:
        rate_limiter: RateLimiter instance
    
    Example:
        limiter = RateLimiter(max_calls=10, time_window=60.0)
        
        @with_rate_limit(limiter)
        async def api_call():
            ...
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            await rate_limiter.acquire()
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def with_error_boundary(
    error_message: Optional[str] = None,
    return_on_error: Any = None,
) -> Callable:
    """
    Decorator to catch and log errors without breaking the system.
    
    Args:
        error_message: Custom error message prefix
        return_on_error: Value to return if error occurs (None = re-raise)
    
    Example:
        @with_error_boundary("Failed to fetch messages", return_on_error=[])
        async def fetch_messages():
            ...
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                msg = error_message or f"Error in {func.__name__}"
                logger.error(f"{msg}: {e}", exc_info=True)
                if return_on_error is not None:
                    return return_on_error
                raise
        return wrapper
    return decorator


def with_logging(
    log_args: bool = False,
    log_result: bool = False,
) -> Callable:
    """
    Decorator to add logging to async functions.
    
    Args:
        log_args: Whether to log function arguments
        log_result: Whether to log function result
    
    Example:
        @with_logging(log_args=True, log_result=False)
        async def process_data(data):
            ...
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            if log_args:
                logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
            else:
                logger.debug(f"Calling {func.__name__}")
            
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                elapsed = time.time() - start_time
                logger.debug(f"{func.__name__} completed in {elapsed:.2f}s")
                if log_result:
                    logger.debug(f"{func.__name__} returned: {result}")
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"{func.__name__} failed after {elapsed:.2f}s: {e}")
                raise
        return wrapper
    return decorator

