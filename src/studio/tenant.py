import json, uuid, time
from pathlib import Path
from typing import Optional

class Tenant:
    def __init__(self, name: str, owner_id: str, tier: str = "basic"):
        self.id = str(uuid.uuid4())[:12]
        self.name = name
        self.owner_id = owner_id
        self.tier = tier
        self.created_at = time.time()
        self.active = True
        self.members: list[str] = [owner_id]
        self.settings: dict = {}

    def to_dict(self):
        return {"id": self.id, "name": self.name, "owner_id": self.owner_id,
                "tier": self.tier, "created_at": self.created_at,
                "active": self.active, "members": self.members,
                "settings": self.settings}

    @staticmethod
    def from_dict(d):
        t = Tenant(d["name"], d["owner_id"], d.get("tier", "basic"))
        t.id = d["id"]
        t.created_at = d.get("created_at", time.time())
        t.active = d.get("active", True)
        t.members = d.get("members", [d["owner_id"]])
        t.settings = d.get("settings", {})
        return t

class TenantManager:
    def __init__(self, data_dir: str = "data/studio"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.tenants: dict[str, Tenant] = {}
        self._load()

    def _load(self):
        f = self.data_dir / "tenants.json"
        if f.exists():
            for d in json.loads(f.read_text()):
                t = Tenant.from_dict(d)
                self.tenants[t.id] = t

    def _save(self):
        (self.data_dir / "tenants.json").write_text(
            json.dumps([t.to_dict() for t in self.tenants.values()],
                       ensure_ascii=False, indent=2))

    def create_tenant(self, name: str, owner_id: str, tier: str = "basic") -> Tenant:
        t = Tenant(name, owner_id, tier)
        self.tenants[t.id] = t
        self._save()
        return t

    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        return self.tenants.get(tenant_id)

    def list_tenants(self) -> list[Tenant]:
        return list(self.tenants.values())

    def add_member(self, tenant_id: str, user_id: str) -> bool:
        t = self.tenants.get(tenant_id)
        if t and user_id not in t.members:
            t.members.append(user_id)
            self._save()
            return True
        return False

    def remove_member(self, tenant_id: str, user_id: str) -> bool:
        t = self.tenants.get(tenant_id)
        if t and user_id in t.members and user_id != t.owner_id:
            t.members.remove(user_id)
            self._save()
            return True
        return False
