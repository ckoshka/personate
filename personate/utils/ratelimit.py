from threading import Thread
from threading import Lock
from typing import Callable, Any
import time
from personate.utils.logger import logger


class RateLimiter:
    def __init__(self, duration: float, maximum_count: int) -> None:
        self.duration: float = duration
        self.maximum_count: int = maximum_count
        self.current_count: int = 0
        self.last_time: float = 0.0
        self.lock: Lock = Lock()

    def ratelimit_decorator(self, func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            with self.lock:
                if self.current_count >= self.maximum_count:
                    time_since_last_call = time.time() - self.last_time
                    if time_since_last_call < self.duration:
                        time_to_wait = self.duration - time_since_last_call
                        logger.debug(
                            f"Ratelimiting {func.__name__} for {time_to_wait} seconds."
                        )
                        time.sleep(time_to_wait)
                    self.current_count = 0
                self.current_count += 1
                self.last_time = time.time()
            return func(*args, **kwargs)

        return wrapper
