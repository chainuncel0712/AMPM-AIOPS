"""
Dashboard + 網站聊天 API
"""
from flask import Flask, jsonify, request
import sys
from pathlib import Path

try:
    from flask_cors import CORS
except ImportError:
    def CORS(app):
        return app

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


@app.route("/api/preferences", methods=["POST"])
def save_preferences():
    """儲存客戶偏好"""
    data = request.get_json(silent=True) or {}
    cid = data.get("cid") or f"web_{request.remote_addr}"
    if _dispatcher:
        from service_agent import db
        c = db.get_or_create(cid)
        prefs = c.setdefault("preferences", {})
        for key in ("language", "contact_time", "notes", "name"):
            if key in data:
                prefs[key] = data[key]
                if key == "name":
                    c["name"] = data[key]
        db.save()
        return jsonify({"ok": True, "cid": cid})
    return jsonify({"ok": False, "error": "服務尚未就緒"})


@app.route("/api/ticket", methods=["POST"])
def create_ticket():
    """建立售後工單"""
    data = request.get_json(silent=True) or {}
    cid = data.get("cid") or f"web_{request.remote_addr}"
    subject = (data.get("subject") or "客戶回報").strip()
    description = (data.get("description") or "").strip()
    if not description:
        return jsonify({"ok": False, "error": "請描述問題"})
    if _dispatcher:
        from service_agent import db
        from datetime import datetime, timezone
        c = db.get_or_create(cid)
        ticket = {
            "id": len(c.get("tickets", [])) + 1,
            "subject": subject,
            "description": description,
            "status": "open",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "resolved_at": None,
        }
        c.setdefault("tickets", []).append(ticket)
        db.save()
        return jsonify({"ok": True, "ticket_id": ticket["id"]})
    return jsonify({"ok": False, "error": "服務尚未就緒"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=False)
