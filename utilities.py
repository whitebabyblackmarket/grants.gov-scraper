"""
Utility functions for logging and error handling.
"""
import logging
import time
from functools import wraps

def setup_logger(name: str, level=logging.INFO) -> logging.Logger:
    """
    Set up a logger with consistent formatting.

    Args:
        name: Logger name (usually __name__ from the calling module)
        level: Logging level (default: INFO)

    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

logger = setup_logger(__name__)

def retry_request(max_retries: int = 3, delay: float = 2.0):
    """
    Retry a function if it fails, with a fixed delay.

    Args:
        max_retries: Maximum number of retry attempts.
        delay: Seconds to wait between retries.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    logger.warning(f"Retry {retries}/{max_retries} for {func.__name__} after error: {e}")
                    time.sleep(delay)
                    if retries == max_retries:
                        logger.error(f"Max retries reached for {func.__name__}")
                        raise
        return wrapper
    return decorator

def rate_limit(min_delay: float = 1.0):
    """
    Enforce a minimum delay between function calls.

    Args:
        min_delay: Minimum delay in seconds between calls.
    """
    last_called = {}

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            elapsed = now - last_called.get(func.__name__, 0)
            if elapsed < min_delay:
                time.sleep(min_delay - elapsed)
            result = func(*args, **kwargs)
            last_called[func.__name__] = time.time()
            return result
        return wrapper
    return decorator
