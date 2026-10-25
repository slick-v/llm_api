import time
from collections import defaultdict,deque
from threading import Lock



class RateLimiter:
    """Allow at most 'limit' calls per 'window' seconds for each key """

    def __init__(self, limit:int, window: int):
        self.limit = limit
        self.window = window
        self.calls: dict[str, deque] = defaultdict(deque)
        self.lock = Lock()   #fastapi runs sync rooutes in several threads


    def allow(self, key:str) -> bool:
        now = time.monotonic()
        with self.lock:
            calls= self.calls[key]
            # forget callks older than the windows
            while calls and now - calls[0] > self.window:
                calls.popleft()
            if len(calls) >= self.limit:
                return False
            calls.append(now)
            return True