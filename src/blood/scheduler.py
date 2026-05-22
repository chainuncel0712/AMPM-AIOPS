"""心跳定時器 - 讓器官定時做自己的事"""
import threading
import time

class Scheduler:
    def __init__(self):
        self._tasks = []
        self._running = False

    def add(self, name: str, interval_seconds: int, callback, repeat: bool = True):
        """加入定時任務"""
        self._tasks.append({
            "name": name,
            "interval": interval_seconds,
            "callback": callback,
            "repeat": repeat,
            "last_run": 0,
        })

    def start(self):
        """開始心跳"""
        self._running = True
        t = threading.Thread(target=self._loop, daemon=True)
        t.start()

    def stop(self):
        self._running = False

    def _loop(self):
        while self._running:
            now = time.time()
            for task in self._tasks:
                if now - task["last_run"] >= task["interval"]:
                    try:
                        task["callback"]()
                    except:
                        pass
                    task["last_run"] = now
                    if not task["repeat"]:
                        self._tasks.remove(task)
            time.sleep(1)
