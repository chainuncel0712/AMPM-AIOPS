"""
簡單儀表板 - 網頁介面查看黑曜狀態
"""
from flask import Flask, jsonify
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

app = Flask(__name__)

# 不自己啟動 Obsidian，由外部傳入
brain = None

def set_brain(obsidian_instance):
    """由 main.py 傳入已初始化的 Obsidian"""
    global brain
    brain = obsidian_instance

@app.route("/")
def index():
    if brain is None:
        return "⚠️ 黑曜尚未初始化"
    try:
        status = brain.cortex.status()
        return jsonify({
            "name": brain.name,
            "cortex": status,
            "organs": {
                "memory": str(brain.memory.is_alive()),
                "tools": str(brain.tools.list_tools()),
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/health")
def health():
    if brain is None:
        return jsonify({"status": "not ready"})
    try:
        return jsonify({"status": "alive", "cortex": brain.cortex.status()})
    except:
        return jsonify({"status": "error"})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
