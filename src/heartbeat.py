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
        r = requests.post("https://api.deepseek.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model":"deepseek-chat","messages":[{"role":"user","content":"ping"}],"max_tokens":2},
            timeout=10)
        return r.status_code == 200
    except:
        return False

def check_bot():
    result = subprocess.run(["pgrep", "-f", "python3.*main.py"], capture_output=True, text=True)
    return result.returncode == 0

def auto_heal():
    if not check_bot():
        print("[心跳] 黑曜離線，正在重啟...")
        key = os.environ.get("DEEPSEEK_API_KEY", "")
        env = os.environ.copy()
        if key:
            env["DEEPSEEK_API_KEY"] = key
        subprocess.Popen(["python3", "main.py"], cwd=str(BASE), env=env, stdout=open("/tmp/黑曜.log","a"), stderr=subprocess.STDOUT)
        return "重啟"
    return "正常"

def heartbeat_loop():
    while True:
        status = {
            "time": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "bot": check_bot(),
            "deepseek": check_deepseek(),
            "ollama": check_ollama(),
        }
        HEARTBEAT_FILE.parent.mkdir(parents=True, exist_ok=True)
        HEARTBEAT_FILE.write_text(json.dumps(status, indent=2))
        if not status["bot"]:
            auto_heal()
        time.sleep(30)

def start():
    t = threading.Thread(target=heartbeat_loop, daemon=True)
    t.start()
    print("[心跳] 監控已啟動，每30秒檢查一次")
