import time
import uuid

class TraceContext:
    def __init__(self) -> None:
        self.trace_id = str(uuid.uuid4())
        self.started_at = time.perf_counter()

    def elapsed_ms(self) -> float:
        elapsed = time.perf_counter() - self.started_at
        return round(elapsed * 1000, 2)