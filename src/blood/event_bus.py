"""事件總線 - 器官之間的通訊系統"""
class EventBus:
    def __init__(self):
        self._listeners = {}

    def on(self, event: str, callback):
        """訂閱事件"""
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(callback)

    def emit(self, event: str, data: dict = None) -> list:
        """發送事件到所有訂閱者"""
        results = []
        for cb in self._listeners.get(event, []):
            try:
                result = cb(data or {})
                if result:
                    results.append(result)
            except Exception as e:
                results.append(f"❌ {e}")
        return results
