from .tenant import TenantManager
from .workspace import WorkspaceManager
from .api_key import APIKeyManager

class StudioOrgan:
    def __init__(self, data_dir: str = "data/studio"):
        self.tenants = TenantManager(data_dir)
        self.workspaces = WorkspaceManager(data_dir)
        self.api_keys = APIKeyManager(data_dir)
        self.name = "studio"

    def is_alive(self):
        return True

    def onboard_tenant(self, name: str, owner_id: str, tier: str = "basic"):
        tenant = self.tenants.create_tenant(name, owner_id, tier)
        ws = self.workspaces.create_workspace(tenant.id, f"{name}-default")
        api_key = self.api_keys.create_key(tenant.id, "default")
        return {"tenant": tenant.to_dict(), "workspace": ws.to_dict(),
                "api_key": api_key.key}
