import json, time, uuid
from pathlib import Path
from typing import Optional

class Workspace:
    def __init__(self, tenant_id: str, name: str):
        self.id = str(uuid.uuid4())[:12]
        self.tenant_id = tenant_id
        self.name = name
        self.brain_ref: Optional[object] = None
        self.created_at = time.time()
        self.config: dict = {}

    def to_dict(self):
        return {"id": self.id, "tenant_id": self.tenant_id, "name": self.name,
                "created_at": self.created_at, "config": self.config}

    @staticmethod
    def from_dict(d):
        w = Workspace(d["tenant_id"], d["name"])
        w.id = d["id"]
        w.created_at = d.get("created_at", time.time())
        w.config = d.get("config", {})
        return w

class WorkspaceManager:
    def __init__(self, data_dir: str = "data/studio"):
        self.data_dir = Path(data_dir)
        self.workspaces: dict[str, Workspace] = {}
        self._load()

    def _load(self):
        f = self.data_dir / "workspaces.json"
        if f.exists():
            for d in json.loads(f.read_text()):
                w = Workspace.from_dict(d)
                self.workspaces[w.id] = w

    def _save(self):
        (self.data_dir / "workspaces.json").write_text(
            json.dumps([w.to_dict() for w in self.workspaces.values()],
                       ensure_ascii=False, indent=2))

    def create_workspace(self, tenant_id: str, name: str) -> Workspace:
        w = Workspace(tenant_id, name)
        self.workspaces[w.id] = w
        self._save()
        return w

    def get_workspace(self, ws_id: str) -> Optional[Workspace]:
        return self.workspaces.get(ws_id)

    def list_by_tenant(self, tenant_id: str) -> list[Workspace]:
        return [w for w in self.workspaces.values() if w.tenant_id == tenant_id]
