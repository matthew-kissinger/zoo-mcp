import time
import random
import logging
from typing import Optional, Callable, Any
from functools import wraps

logger = logging.getLogger(__name__)


class RateLimitError(Exception):
    pass


def exponential_backoff_with_jitter(
    func: Callable, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0
) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        retries = 0
        while retries <= max_retries:
            try:
                return func(*args, **kwargs)
            except RateLimitError as e:
                if retries == max_retries:
                    raise

                delay = min(base_delay * (2 ** retries), max_delay)
                jitter = random.uniform(0, delay * 0.1)
                total_delay = delay + jitter

                logger.warning(
                    f"Rate limit hit, retrying in {total_delay:.2f}s (attempt {retries + 1}/{max_retries})"
                )
                time.sleep(total_delay)
                retries += 1

        return func(*args, **kwargs)

    return wrapper


def handle_rate_limit_headers(response) -> Optional[int]:
    if response.status_code == 429 or response.status_code == 403:
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            return int(retry_after)

        reset_time = response.headers.get("X-RateLimit-Reset")
        if reset_time:
            wait_time = int(reset_time) - int(time.time())
            return max(wait_time, 0)

    return None


def parse_rate_limit(response) -> dict:
    return {
        "remaining": int(response.headers.get("X-RateLimit-Remaining", 0)),
        "reset": int(response.headers.get("X-RateLimit-Reset", 0)),
    }


def generate_time_windows(start_date: str, end_date: str, window_days: int = 30) -> list[str]:
    from datetime import datetime, timedelta

    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)

    windows = []
    current = start

    while current < end:
        window_end = min(current + timedelta(days=window_days), end)
        windows.append(f"{current.date()}..{window_end.date()}")
        current = window_end + timedelta(days=1)

    return windows


class PageCache:
    def __init__(self, max_size: int = 100):
        self._cache: dict[str, Any] = {}
        self._max_size = max_size
        self._access_order: list[str] = []

    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            self._access_order.remove(key)
            self._access_order.append(key)
            return self._cache[key]
        return None

    def set(self, key: str, value: Any) -> None:
        if key in self._cache:
            self._access_order.remove(key)
        elif len(self._cache) >= self._max_size:
            oldest = self._access_order.pop(0)
            del self._cache[oldest]

        self._cache[key] = value
        self._access_order.append(key)

    def clear(self) -> None:
        self._cache.clear()
        self._access_order.clear()


page_cache = PageCache()