"""包包 - 外挂工具载入器"""
from skeleton.base_organ import BaseOrgan

class PluginLoader(BaseOrgan):
    def __init__(self):
        super().__init__("plugin_loader")
        self._plugins = {}

    def load(self, name: str, executor, config: dict = None):
        """装入一個外挂工具"""
        self._plugins[name] = {
            "executor": executor,
            "config": config or {},
        }

    def unload(self, name: str):
        self._plugins.pop(name, None)

    def get(self, name: str):
        return self._plugins.get(name)

    def list_plugins(self) -> list:
        return list(self._plugins.keys())

    def status(self) -> dict:
        return {"name": self.name, "alive": self.is_alive(), "plugins": self.list_plugins()}
