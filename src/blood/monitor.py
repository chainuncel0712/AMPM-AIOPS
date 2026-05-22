"""生命跡象監控 - 定時檢查所有器官"""
from skeleton.registry import Registry

class VitalMonitor:
    def __init__(self, registry: Registry):
        self.registry = registry
        self.alerts = []

    def check_all(self) -> dict:
        """檢查所有器官"""
        result = {"healthy": [], "warning": [], "dead": []}
        for name, organ in self.registry.all().items():
            try:
                # 先检查是否活着
                if hasattr(organ, 'is_alive') and not organ.is_alive():
                    result["dead"].append(name)
                    continue
                # 尝试获取状态
                if hasattr(organ, 'status'):
                    stat = organ.status()
                    result["healthy"].append(name)
                else:
                    result["healthy"].append(name)  # 无 status 也视为健康
            except Exception as e:
                result["warning"].append(f"{name}: {e}")
        return result

    def alert(self, msg: str):
        self.alerts.append(msg)
