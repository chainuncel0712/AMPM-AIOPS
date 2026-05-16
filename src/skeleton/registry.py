"""器官注册表 - 兼容新旧器官"""
class Registry:
    def __init__(self):
        self._organs = {}

    def add(self, organ):
        # 如果器官没有 name 属性，用类名作为名字
        name = getattr(organ, 'name', None)
        if not name:
            name = type(organ).__name__.lower()
            # 如果仍然重名，加上数字后缀
            while name in self._organs:
                name = type(organ).__name__.lower() + "_" + str(id(organ))[-4:]
        self._organs[name] = organ
        return organ

    def get(self, name: str):
        return self._organs.get(name)

    def all(self) -> dict:
        return self._organs

    def status_all(self) -> dict:
        """检查所有器官状态，安全处理无 status 方法的器官"""
        result = {}
        for name, organ in self._organs.items():
            try:
                if hasattr(organ, 'is_alive') and not organ.is_alive():
                    result[name] = "dead"
                    continue
                if hasattr(organ, 'status'):
                    result[name] = organ.status()
                else:
                    result[name] = {"name": name, "alive": True}
            except Exception as e:
                result[name] = {"error": str(e)}
        return result

    def list_organs(self) -> list:
        return list(self._organs.keys())
