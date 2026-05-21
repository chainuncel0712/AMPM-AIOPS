"""
Organ Registry — 器官註冊表
"""


class OrganRegistry:
    def __init__(self):
        self._organs = {}

    def register(self, name: str, organ) -> object:
        self._organs[name] = organ
        return organ

    def get(self, name: str):
        return self._organs.get(name)

    def all(self) -> dict:
        return dict(self._organs)

    def health(self) -> list:
        results = []
        for name, organ in self._organs.items():
            status = "alive"
            try:
                if hasattr(organ, "status"):
                    st = organ.status()
                    status = st.get("alive", True) and "alive" or "dead"
            except Exception:
                status = "error"
            results.append({"name": name, "status": status})
        return results
