"""
Dashboard + 網站聊天 API
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

app = Flask(__name__)
CORS(app)

brain = None
_dispatcher = None


def set_brain(obsidian_instance, dispatcher=None):
    global brain, _dispatcher
    brain = obsidian_instance
    if dispatcher:
        _dispatcher = dispatcher


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


@app.route("/api/chat", methods=["POST"])
def chat():
    """網站對話窗口 API"""
    data = request.get_json(silent=True) or {}
    msg = (data.get("message") or "").strip()
    cid = data.get("cid") or f"web_{request.remote_addr}"
    if not msg:
        return jsonify({"reply": "請輸入訊息。"})
    if _dispatcher:
        try:
            reply = _dispatcher.route(cid, msg)
            return jsonify({"reply": reply, "cid": cid})
        except Exception as e:
            return jsonify({"reply": f"⚠️ {e}"})
    return jsonify({"reply": "服務代理尚未就緒，請稍後再試。"})


@app.route("/api/service-info", methods=["GET"])
def service_info():
    """前端取得方案與付款資訊"""
    return jsonify({
        "plans": [
            {"name": "月方案", "price": 15, "days": 30, "type": "self-hosted"},
            {"name": "季方案", "price": 39, "days": 90, "type": "self-hosted"},
            {"name": "年方案", "price": 120, "days": 365, "type": "self-hosted"},
            {"name": "月方案(雲端)", "price": 30, "days": 30, "type": "cloud"},
            {"name": "季方案(雲端)", "price": 80, "days": 90, "type": "cloud"},
            {"name": "年方案(雲端)", "price": 240, "days": 365, "type": "cloud"},
        ],
        "wallet": "0x7f3110c1314bD68Fdf8E32cD921E646912108587",
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=False)
