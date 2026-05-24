"""
BrainComponent v2 — 支援資源治理的腦元件基底
"""
from abc import abstractmethod


class BrainComponent:
    def __init__(self, dna: dict | None = None):
        self._state: dict = {}
        self._dna: dict | None = dna
        self._asleep = False
        self._wake_count = 0
        self._sleep_count = 0

    def report_issue(self, issue_type: str, detail: str = ""):
        """器官自治投票：報告問題給 repair_engine。"""
        try:
            from core.repair_engine import report_issue as _ri
            _ri(self.__class__.__name__, issue_type, detail)
        except Exception:
            pass

    @abstractmethod
    def status(self) -> dict:
        ...

    def on_startup(self) -> None:
        pass

    def on_shutdown(self) -> None:
        pass

    def sleep(self):
        if not self._asleep:
            self._asleep = True
            self._sleep_count += 1
            self._on_sleep()

    def wake(self):
        if self._asleep:
            self._asleep = False
            self._wake_count += 1
            self._on_wake()

    def is_asleep(self) -> bool:
        return self._asleep

    def memory_estimate_mb(self) -> int:
        return 0

    def _on_sleep(self):
        pass

    def _on_wake(self):
        pass

    def resource_status(self) -> dict:
        return {
            "name": self.__class__.__name__,
            "asleep": self._asleep,
            "wake_count": self._wake_count,
            "sleep_count": self._sleep_count,
            "mem_mb": self.memory_estimate_mb(),
        }
