"""Rollback System v1 — Snapshot, Restore, Diff Tracking"""
import json
import os
import sys
import time
import shutil
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))
from skeleton.base_organ import BaseOrgan


class RollbackSystem(BaseOrgan):
    def __init__(self, snapshot_dir="data/snapshots/", max_snapshots=20):
        super().__init__("rollback_system")
        self._snapshot_dir = Path(snapshot_dir)
        self._snapshot_dir.mkdir(parents=True, exist_ok=True)
        self._max_snapshots = max_snapshots
        self._snapshots = {}
        self._rollback_history = []
        self._current_snapshot_id = None

    def snapshot(self, data_source, label="", metadata=None):
        snapshot_id = f"snap_{int(time.time())}_{hashlib.md5(str(time.time()).encode()).hexdigest()[:6]}"
        try:
            serialized = json.dumps(_serialize(data_source), ensure_ascii=False, default=str)
        except Exception:
            serialized = str(data_source)
        checksum = hashlib.sha256(serialized.encode()).hexdigest()
        snap = {
            "id": snapshot_id, "label": label or f"snap_{len(self._snapshots)+1}",
            "timestamp": time.time(), "checksum": checksum,
            "data": data_source, "metadata": metadata or {},
        }
        filepath = self._snapshot_dir / f"{snapshot_id}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(serialized)
        self._snapshots[snapshot_id] = snap
        self._current_snapshot_id = snapshot_id
        self._cleanup()
        return snapshot_id

    def snapshot_file(self, filepath, label=""):
        path = Path(filepath)
        if not path.exists():
            return ""
        sid = f"file_{hashlib.md5(filepath.encode()).hexdigest()[:8]}_{int(time.time())}"
        backup = self._snapshot_dir / f"{sid}_{path.name}"
        shutil.copy2(path, backup)
        with open(path, "rb") as f:
            cs = hashlib.sha256(f.read()).hexdigest()
        self._snapshots[sid] = {"id": sid, "label": label or f"file:{filepath}", "timestamp": time.time(), "type": "file", "original_path": str(path), "checksum": cs, "backup_path": str(backup)}
        self._cleanup()
        return sid

    def snapshot_dir(self, dirpath, label=""):
        import tarfile
        path = Path(dirpath)
        if not path.exists() or not path.is_dir():
            return ""
        sid = f"dir_{hashlib.md5(dirpath.encode()).hexdigest()[:8]}_{int(time.time())}"
        tar = self._snapshot_dir / f"{sid}.tar.gz"
        with tarfile.open(tar, "w:gz") as tf:
            tf.add(path, arcname=path.name)
        self._snapshots[sid] = {"id": sid, "label": label or f"dir:{dirpath}", "timestamp": time.time(), "type": "directory", "original_path": str(path), "backup_path": str(tar)}
        self._cleanup()
        return sid

    def rollback(self, snapshot_id=None):
        tid = snapshot_id or self._current_snapshot_id
        if not tid or tid not in self._snapshots:
            avail = list(self._snapshots.keys())
            if avail:
                tid = sorted(avail, key=lambda x: self._snapshots[x]["timestamp"])[-1]
            else:
                return {"success": False, "error": "no snapshots"}
        snap = self._snapshots[tid]
        try:
            if snap.get("type") == "file":
                r = self._rb_file(snap)
            elif snap.get("type") == "directory":
                r = self._rb_dir(snap)
            else:
                r = {"success": True, "data": snap["data"], "snapshot_id": snap["id"], "checksum": snap["checksum"]}
            self._rollback_history.append({"snapshot_id": tid, "timestamp": time.time(), "success": r["success"], "label": snap.get("label", "")})
            return r
        except Exception as e:
            self._rollback_history.append({"snapshot_id": tid, "timestamp": time.time(), "success": False, "error": str(e)})
            return {"success": False, "error": str(e)}

    def _rb_file(self, snap):
        backup = Path(snap["backup_path"])
        orig = Path(snap["original_path"])
        if not backup.exists():
            return {"success": False, "error": "backup missing"}
        shutil.copy2(backup, orig)
        return {"success": True, "restored_file": str(orig), "snapshot_id": snap["id"]}

    def _rb_dir(self, snap):
        import tarfile
        tar = Path(snap["backup_path"])
        orig = Path(snap["original_path"])
        if not tar.exists():
            return {"success": False, "error": "backup missing"}
        if orig.exists():
            shutil.rmtree(orig)
        with tarfile.open(tar, "r:gz") as tf:
            tf.extractall(path=orig.parent)
        return {"success": True, "restored_dir": str(orig), "snapshot_id": snap["id"]}

    def diff(self, sid_a, sid_b=None):
        a = self._snapshots.get(sid_a)
        b = self._snapshots.get(sid_b or self._current_snapshot_id or "")
        if not a:
            return {"error": f"snapshot {sid_a} not found"}
        if b:
            da = a.get("data", {})
            db = b.get("data", {})
            changes = _compute_diff(da, db)
        else:
            changes = {"added": a.get("data", {}), "removed": {}, "modified": {}}
        return {"snapshot_a": sid_a, "snapshot_b": sid_b, "a_label": a.get("label", ""), "b_label": b.get("label", "") if b else "current", "changes": changes}

    def _cleanup(self):
        if len(self._snapshots) <= self._max_snapshots:
            return
        sorted_snaps = sorted(self._snapshots.items(), key=lambda x: x[1]["timestamp"])
        for sid, snap in sorted_snaps[:len(sorted_snaps) - self._max_snapshots]:
            if snap.get("type") in ("file", "directory"):
                bp = Path(snap.get("backup_path", ""))
                if bp.exists():
                    bp.unlink()
            else:
                fp = self._snapshot_dir / f"{sid}.json"
                if fp.exists():
                    fp.unlink()
            del self._snapshots[sid]

    def list_snapshots(self, limit=20):
        sorted_snaps = sorted(self._snapshots.values(), key=lambda x: x["timestamp"], reverse=True)[:limit]
        return [{"id": s["id"], "label": s["label"], "timestamp": s["timestamp"], "type": s.get("type", "data"), "checksum": s.get("checksum", "")[:12]} for s in sorted_snaps]

    def get_snapshot(self, sid):
        return self._snapshots.get(sid)

    def delete_snapshot(self, sid):
        if sid not in self._snapshots:
            return False
        snap = self._snapshots[sid]
        if snap.get("type") in ("file", "directory"):
            bp = Path(snap.get("backup_path", ""))
            if bp.exists():
                bp.unlink()
        else:
            fp = self._snapshot_dir / f"{sid}.json"
            if fp.exists():
                fp.unlink()
        del self._snapshots[sid]
        return True

    def get_rollback_history(self, limit=10):
        return self._rollback_history[-limit:]

    def status(self):
        return {"name": self.name, "alive": self.is_alive(), "snapshots": len(self._snapshots), "rollbacks": len(self._rollback_history), "current": self._current_snapshot_id, "max": self._max_snapshots, "dir": str(self._snapshot_dir)}


def _serialize(obj):
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple, set)):
        return [_serialize(x) for x in obj]
    elif hasattr(obj, "__dict__"):
        return _serialize(obj.__dict__)
    elif isinstance(obj, (int, float, str, bool, type(None))):
        return obj
    return str(obj)


def _compute_diff(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        added, removed, modified = {}, {}, {}
        for key in set(a.keys()) | set(b.keys()):
            if key not in a:
                added[key] = b[key]
            elif key not in b:
                removed[key] = a[key]
            elif a[key] != b[key]:
                modified[key] = {"old": a[key], "new": b[key]}
        return {"added": added, "removed": removed, "modified": modified}
    elif isinstance(a, list) and isinstance(b, list):
        return {"added": [x for x in b if x not in a], "removed": [x for x in a if x not in b], "modified": {}}
    return {"added": b, "removed": a, "modified": {}}
