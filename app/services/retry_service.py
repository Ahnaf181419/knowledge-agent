"""
Retry Service Module

Centralized retry handling for failed scraping operations.
Provides unified retry logic with configurable policies.
"""

import time
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from typing import TypeVar

from app.state import state

T = TypeVar("T")


@dataclass
class RetryPolicy:
    """Configuration for retry behavior."""

    max_attempts: int = 3
    initial_delay: float = 1.0
    backoff_multiplier: float = 2.0
    max_delay: float = 60.0


class RetryService:
    """
    Centralized retry handling service.

    Provides:
    - Configurable retry policies
    - Exponential backoff
    - Retry queue management
    """

    def __init__(self, policy: RetryPolicy | None = None):
        self.policy = policy or RetryPolicy()

    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for given attempt using exponential backoff.

        Args:
            attempt: Current attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        delay = self.policy.initial_delay * (self.policy.backoff_multiplier**attempt)
        return min(delay, self.policy.max_delay)

    def execute_with_retry(
        self,
        func: Callable[[], T],
        url: str,
        tags: list[str] | None = None,
        on_failure: Callable[[str, str], None] | None = None,
    ) -> tuple[T | None, bool]:
        """
        Execute a function with retry logic.

        Args:
            func: Function to execute
            url: URL being processed (for retry queue)
            tags: Tags associated with URL
            on_failure: Optional callback on final failure

        Returns:
            Tuple of (result, success)
        """
        last_error = None

        for attempt in range(self.policy.max_attempts):
            try:
                result = func()
                return result, True
            except Exception as e:
                last_error = str(e)

                if attempt < self.policy.max_attempts - 1:
                    delay = self.calculate_delay(attempt)
                    time.sleep(delay)

        # All attempts failed
        if on_failure:
            on_failure(url, last_error or "")

        return None, False

    def get_retry_items(self) -> list[dict]:
        """
        Get all items in the retry queue.

        Returns:
            List of retry items
        """
        return state.get_retry_normal()

    def clear_retry_item(self, url: str) -> None:
        """
        Remove an item from the retry queue.

        Args:
            url: URL to remove
        """
        state.remove_from_retry_normal(url)

    def get_retry_count(self, url: str) -> int:
        """
        Get number of times a URL has been retried.

        Args:
            url: URL to check

        Returns:
            Number of retry attempts
        """
        for item in state.get_retry_normal():
            if item.get("url") == url:
                return item.get("attempts", 1)  # type: ignore[no-any-return]
        return 0


retry_service = RetryService()


def with_retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_multiplier: float = 2.0,
    max_delay: float = 60.0,
):
    """
    Decorator for adding retry logic to functions.

    Args:
        max_attempts: Maximum number of attempts
        initial_delay: Initial delay in seconds
        backoff_multiplier: Multiplier for exponential backoff
        max_delay: Maximum delay between retries

    Returns:
        Decorated function
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            policy = RetryPolicy(
                max_attempts=max_attempts,
                initial_delay=initial_delay,
                backoff_multiplier=backoff_multiplier,
                max_delay=max_delay,
            )
            service = RetryService(policy)

            def execute():
                return func(*args, **kwargs)

            result, success = service.execute_with_retry(execute, "")
            if not success:
                raise RuntimeError(f"All {max_attempts} attempts failed")
            return result  # type: ignore[return-value]

        return wrapper

    return decorator
