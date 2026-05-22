import hashlib, secrets, time
from pathlib import Path
from typing import Optional

class APIKey:
    def __init__(self, tenant_id: str, label: str = ""):
        self.key = f"am_{secrets.token_hex(24)}"
        self.key_hash = hashlib.sha256(self.key.encode()).hexdigest()
        self.tenant_id = tenant_id
        self.label = label
        self.created_at = time.time()
        self.active = True
        self.last_used: Optional[float] = None

    def to_dict(self):
        return {"key_hash": self.key_hash, "tenant_id": self.tenant_id,
                "label": self.label, "created_at": self.created_at,
                "active": self.active, "last_used": self.last_used}

    @staticmethod
    def from_dict(d):
        k = APIKey(d["tenant_id"], d.get("label", ""))
        k.key_hash = d["key_hash"]
        k.key = f"am_{'x' * 48}"
        k.created_at = d["created_at"]
        k.active = d.get("active", True)
        k.last_used = d.get("last_used")
        return k

class APIKeyManager:
    def __init__(self, data_dir: str = "data/studio"):
        self.data_dir = Path(data_dir)
        self.keys: dict[str, APIKey] = {}
        self._load()

    def _load(self):
        f = self.data_dir / "api_keys.json"
        if f.exists():
            import json
            for d in json.loads(f.read_text()):
                k = APIKey.from_dict(d)
                self.keys[k.key_hash] = k

    def _save(self):
        import json
        (self.data_dir / "api_keys.json").write_text(
            json.dumps([k.to_dict() for k in self.keys.values()],
                       ensure_ascii=False, indent=2))

    def create_key(self, tenant_id: str, label: str = "") -> APIKey:
        k = APIKey(tenant_id, label)
        self.keys[k.key_hash] = k
        self._save()
        return k

    def validate(self, raw_key: str) -> Optional[APIKey]:
        h = hashlib.sha256(raw_key.encode()).hexdigest()
        k = self.keys.get(h)
        if k and k.active:
            k.last_used = time.time()
            self._save()
            return k
        return None

    def revoke(self, key_hash: str) -> bool:
        k = self.keys.get(key_hash)
        if k:
            k.active = False
            self._save()
            return True
        return False
