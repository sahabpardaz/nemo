from datetime import datetime
from typing import Optional
import uuid


class ElapsedTimeTracer:
    def __init__(self, logger, tag: Optional[str] = None):
        self._logger = logger
        self.start_time = None
        self.last_log_time = None
        self._tag = tag or f"TimeTracer-{str(uuid.uuid4())[:5]}"
        self.reset()

    def reset(self, description_message: Optional[str] = None):
        self.start_time = datetime.now()
        self.last_log_time = self.start_time
        self._logger.info(
            f"Elapsed time tracer started. {description_message if description_message is not None else ''}")

    @staticmethod
    def _get_diff_in_milliseconds(t1: datetime, t2: datetime) -> int:
        return int((t2 - t1).microseconds / 1000)

    def log(self, message: str):
        """
        Logs the elapsed time (from start and from previous lap) alongside the given message.
        :param message:
        """
        now = datetime.now()
        self._logger.info(f"{message}\n"
                          f"Elapsed time from last log: {self._get_diff_in_milliseconds(self.last_log_time, now)}ms\t"
                          f"Total elapsed time: {self._get_diff_in_milliseconds(self.start_time, now)}ms")
        self.last_log_time = now
