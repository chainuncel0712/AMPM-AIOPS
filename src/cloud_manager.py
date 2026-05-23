#!/usr/bin/env python3
"""Cloud Bot Manager — 多租戶 Bot 啟動器"""

import os, sys, subprocess, json, signal, time
from pathlib import Path

INSTANCES_DIR = Path(__file__).parent / "cloud_instances"
INSTANCES_FILE = Path(__file__).parent / "data" / "cloud_instances.json"


def _load():
    if INSTANCES_FILE.exists():
        try:
            return json.loads(INSTANCES_FILE.read_text())
        except Exception:
            return {}
    return {}


def _save(data: dict):
    INSTANCES_FILE.parent.mkdir(parents=True, exist_ok=True)
    INSTANCES_FILE.write_text(json.dumps(data, indent=2))


def create_instance(user_id: int, token: str) -> str:
    """Create a cloud bot instance for a user."""
    instances = _load()
    if str(user_id) in instances:
        return f"❌ 用戶 {user_id} 已有雲端實例。"

    # Create a run script for this instance
    INSTANCES_DIR.mkdir(parents=True, exist_ok=True)
    script = INSTANCES_DIR / f"bot_{user_id}.py"
    script.write_text(f"""#!/usr/bin/env python3
import os, sys
from pathlib import Path
sys.path.insert(0, r"{Path(__file__).parent}")
os.environ["TELEGRAM_TOKEN_OBSIDIAN"] = "{token}"
from main import main
main()
""")
    script.chmod(0o755)

    instances[str(user_id)] = {
        "token": token[:10] + "...",
        "pid": None,
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "stopped",
    }
    _save(instances)
    return f"✅ 雲端實例已建立（用戶 {user_id}）。"


def start_instance(user_id: int) -> str:
    """Start a cloud bot instance."""
    instances = _load()
    uid = str(user_id)
    if uid not in instances:
        return "❌ 該用戶無雲端實例。"

    proc = subprocess.Popen(
        [sys.executable, str(INSTANCES_DIR / f"bot_{user_id}.py")],
        stdout=open(f"/tmp/cloud_bot_{user_id}.log", "a"),
        stderr=subprocess.STDOUT,
    )
    instances[uid]["pid"] = proc.pid
    instances[uid]["status"] = "running"
    _save(instances)
    return f"✅ 雲端 Bot 已啟動（PID {proc.pid}）。"


def stop_instance(user_id: int) -> str:
    """Stop a cloud bot instance."""
    instances = _load()
    uid = str(user_id)
    if uid not in instances:
        return "❌ 該用戶無雲端實例。"
    pid = instances[uid].get("pid")
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    instances[uid]["pid"] = None
    instances[uid]["status"] = "stopped"
    _save(instances)
    return f"✅ 雲端 Bot 已停止。"


def list_instances() -> str:
    """List all cloud instances."""
    instances = _load()
    if not instances:
        return "📋 尚無雲端實例。"
    lines = ["📋 雲端實例列表:"]
    for uid, info in instances.items():
        lines.append(f"  🆔 {uid} | {info['status']} | 建立: {info['created']}")
    return "\n".join(lines)
