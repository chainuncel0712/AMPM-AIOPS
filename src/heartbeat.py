"""
黑曜心跳監控 + 自動解卡
每30秒檢查一次，卡住就重啟
"""
import os, time, threading, subprocess, requests, json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
HEARTBEAT_FILE = BASE / "data" / "heartbeat.json"

def check_ollama():
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=5)
        return r.status_code == 200
    except:
        return False

def check_deepseek():
    key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not key:
        return False
    try:
        r = requests.get("https://api.deepseek.com/v1/models",
            headers={"Authorization": f"Bearer {key}"},
            timeout=5)
        return r.status_code == 200
    except:
        return False

def check_bot():
    result = subprocess.run(["pgrep", "-f", "python3.*main.py"], capture_output=True, text=True)
    return result.returncode == 0

def auto_heal():
    if not check_bot():
        print("[心跳] 黑曜離線，正在重啟...")
        env = os.environ.copy()
        env_file = BASE / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
        subprocess.Popen(["python3", "main.py"], cwd=str(BASE), env=env, stdout=open("/tmp/黑曜.log","a"), stderr=subprocess.STDOUT)
        return "重啟"
    return "正常"

def heartbeat_loop():
    tick = 0
    DS_CHECK_INTERVAL = 10   # 10 * 30s = 5 minutes
    _cached_ds = True
    while True:
        # DeepSeek ping 每 5 分钟一次，其余用缓存
        if tick % DS_CHECK_INTERVAL == 0:
            _cached_ds = check_deepseek()
        status = {
            "time": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "bot": check_bot(),
            "deepseek": _cached_ds,
            "ollama": check_ollama(),
        }
        HEARTBEAT_FILE.parent.mkdir(parents=True, exist_ok=True)
        HEARTBEAT_FILE.write_text(json.dumps(status, indent=2))
        if not status["bot"]:
            auto_heal()
        tick += 1
        time.sleep(30)

def start():
    t = threading.Thread(target=heartbeat_loop, daemon=True)
    t.start()
    print("[心跳] 監控已啟動，每30秒檢查一次")


def check() -> str:
    """執行一次健康檢查並回報狀態"""
    try:
        bot_alive = check_bot()
        ds_alive = check_deepseek()
        ollama_alive = check_ollama()
        lines = [
            "💓 黑曜心跳檢查",
            f"  Bot: {'✅ 運行中' if bot_alive else '❌ 離線'}",
            f"  DeepSeek: {'✅ 正常' if ds_alive else '❌ 異常'}",
            f"  Ollama: {'✅ 正常' if ollama_alive else '❌ 異常'}",
        ]
        if not bot_alive:
            lines.append(f"\n⚠️ Bot 離線，嘗試自動重啟...")
            result = auto_heal()
            lines.append(f"  重啟結果: {result}")
        else:
            lines.append(f"\n  系統狀態: 正常")
        return "\n".join(lines)
    except Exception as e:
        return f"❌ 心跳檢查失敗: {e}"


def register_tools(tool_system):
    """Register heartbeat tools with the tool system."""
    from tools import ToolSystem
    if not isinstance(tool_system, ToolSystem):
        return
    tool_system.register_tool("heartbeat", check, "執行心跳檢查：檢查 Bot、DeepSeek、Ollama 狀態")
