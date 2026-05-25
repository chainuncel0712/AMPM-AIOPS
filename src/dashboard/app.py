"""
Dashboard + 網站聊天 API
"""
from flask import Flask, jsonify, request, abort
import os, sys
from pathlib import Path

try:
    from flask_cors import CORS
except ImportError:
    def CORS(app):
        return app

sys.path.insert(0, str(Path(__file__).parent.parent))

app = Flask(__name__)
CORS(app)

DASHBOARD_TOKEN = os.environ.get("DASHBOARD_TOKEN", "")

@app.before_request
def check_auth():
    if not DASHBOARD_TOKEN:
        return
    token = request.args.get("token") or request.headers.get("Authorization", "").replace("Bearer ", "")
    if token == DASHBOARD_TOKEN:
        return
    if request.path in ("/health", "/login"):
        return
    if request.path == "/" and request.method == "GET":
        return f"""<html><head><meta http-equiv="refresh" content="0;url=/login"></head><body></body></html>"""
    return jsonify({"error": "unauthorized", "hint": "/login 登入或 ?token=密鑰"}), 401


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        token = (request.form.get("token") or "").strip()
        if token == DASHBOARD_TOKEN:
            return f"""<html><head><meta http-equiv="refresh" content="0;url=/?token={token}"></head><body>驗證成功，跳轉中...</body></html>"""
        return """<html><head><meta charset="utf-8"><style>body{{font-family:sans-serif;display:flex;justify-content:center;align-items:center;height:100vh;background:#0a0a0f;color:#e0e0e0}}form{{background:#1a1a2e;padding:2rem;border-radius:12px}}input{{width:100%;padding:10px;margin:8px 0;border:1px solid #333;border-radius:6px;background:#0d0d1a;color:#fff}}button{{width:100%;padding:10px;background:#e94560;color:#fff;border:none;border-radius:6px;cursor:pointer}}h2{{margin-top:0;color:#58a6ff}}</style></head><body><form method="post"><h2>黑曜 Dashboard</h2><input type="password" name="token" placeholder="請輸入密鑰" required><p style="color:#e94560;font-size:13px">密鑰錯誤</p><button type="submit">登入</button></form></body></html>"""
    return """<html><head><meta charset="utf-8"><style>body{{font-family:sans-serif;display:flex;justify-content:center;align-items:center;height:100vh;background:#0a0a0f;color:#e0e0e0}}form{{background:#1a1a2e;padding:2rem;border-radius:12px}}input{{width:100%;padding:10px;margin:8px 0;border:1px solid #333;border-radius:6px;background:#0d0d1a;color:#fff}}button{{width:100%;padding:10px;background:#e94560;color:#fff;border:none;border-radius:6px;cursor:pointer}}h2{{margin-top:0;color:#58a6ff}}</style></head><body><form method="post"><h2>黑曜 Dashboard</h2><input type="password" name="token" placeholder="請輸入密鑰" required><button type="submit">登入</button></form></body></html>"""

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
        import json, subprocess, time
        BASE = Path(__file__).parent.parent.parent
        NOW = time.strftime("%Y-%m-%d %H:%M:%S")

        # 系统资源
        cpu = subprocess.run("top -bn1 | grep 'Cpu(s)' | awk '{printf \"%.1f\",100-$8}'", shell=True, capture_output=True, text=True).stdout.strip() or "?"
        mem = subprocess.run("free -m | awk 'NR==2{printf \"%d/%dMB (%.0f%%)\",$3,$2,$3*100/$2}'", shell=True, capture_output=True, text=True).stdout.strip() or "?"
        disk = subprocess.run("df -h / | awk 'NR==2{print $5}'", shell=True, capture_output=True, text=True).stdout.strip() or "?"
        uptime_sec = 0
        bot_uptime = "?"
        try:
            pid = subprocess.run("pgrep -f 'python3.*main.py' | head -1", shell=True, capture_output=True, text=True).stdout.strip()
            if pid:
                bot_uptime = subprocess.run(f"ps -p {pid} -o etime=", shell=True, capture_output=True, text=True).stdout.strip()
        except: pass

        # 进化数据
        evo = {}
        evo_file = BASE / "data" / "evolution" / "cycle_state.json"
        if evo_file.exists():
            evo = json.loads(evo_file.read_text())

        # 客户数据
        customers = {}
        cf = BASE / "data" / "customers.json"
        if cf.exists():
            customers = json.loads(cf.read_text())

        # 产出文件及链接
        outputs_dir = BASE / "outputs"
        def get_files(subdir, ext="*.md"):
            p = outputs_dir / subdir
            if not p.exists(): return []
            return sorted([f.name for f in p.glob(ext)], key=lambda x: x.lower())

        ebooks = get_files("ebooks")
        children = get_files("children_book")
        research_files = get_files("research")
        websites = get_files("website", "*.html")
        website_css = get_files("website", "*.css")
        brand_files = get_files("brand_identity", "*")

        # 工具数
        tool_count = len(brain.tools.list_tools()) if hasattr(brain, 'tools') and brain.tools else 0
        tools_list = brain.tools.list_tools() if hasattr(brain, 'tools') and brain.tools else []

        return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>黑曜 Dashboard | AMPM-AIOPS</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Inter',-apple-system,sans-serif;background:#0a0a0f;color:#e0e0e0;min-height:100vh}}
.header{{background:#111122;border-bottom:1px solid #1e1e3a;padding:20px 30px;display:flex;justify-content:space-between;align-items:center}}
.header h1{{font-size:22px;color:#58a6ff}}
.header span{{font-size:12px;color:#8b949e}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px;padding:20px 30px}}
.card{{background:#111122;border:1px solid #1e1e3a;border-radius:12px;padding:20px}}
.card h3{{font-size:13px;color:#8b949e;text-transform:uppercase;letter-spacing:1px;margin-bottom:12px}}
.card .value{{font-size:28px;font-weight:700;color:#58a6ff}}
.card .sub{{font-size:12px;color:#8b949e;margin-top:4px}}
.stat-row{{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #1a1a2e;font-size:13px}}
.stat-row:last-child{{border:none}}
.stat-label{{color:#8b949e}}
.stat-val{{color:#e0e0e0;font-weight:600}}
.good{{color:#3fb950}}
.warn{{color:#d29922}}
.bad{{color:#e94560}}
table{{width:100%;border-collapse:collapse;font-size:12px}}
th{{text-align:left;color:#8b949e;padding:6px 8px;border-bottom:1px solid #1e1e3a}}
td{{padding:6px 8px;border-bottom:1px solid #111122}}
.footer{{text-align:center;padding:20px;color:#484f58;font-size:11px}}
</style>
</head>
<body>
<div class="header">
  <div>
    <h1>⚙️ 黑曜 Dashboard</h1>
    <span>AMPM-AIOPS · 更新於 {NOW}</span>
  </div>
  <span style="color:#3fb950">● 運行中</span>
</div>

<div class="grid">
  <div class="card">
    <h3>🖥️ 系統資源</h3>
    <div class="stat-row"><span class="stat-label">CPU</span><span class="stat-val">{cpu}%</span></div>
    <div class="stat-row"><span class="stat-label">記憶體</span><span class="stat-val">{mem}</span></div>
    <div class="stat-row"><span class="stat-label">磁碟</span><span class="stat-val">{disk}</span></div>
    <div class="stat-row"><span class="stat-label">Bot 運行</span><span class="stat-val">{bot_uptime}</span></div>
  </div>

  <div class="card">
    <h3>🤖 黑曜核心</h3>
    <div class="stat-row"><span class="stat-label">狀態</span><span class="stat-val good">✅ alive</span></div>
    <div class="stat-row"><span class="stat-label">記憶模組</span><span class="stat-val good">✅</span></div>
    <div class="stat-row"><span class="stat-label">工具系統</span><span class="stat-val">{tool_count} 個工具</span></div>
    <div class="stat-row"><span class="stat-label">思考引擎</span><span class="stat-val good">✅</span></div>
  </div>

  <div class="card">
    <h3>🧬 進化循環</h3>
    <div class="stat-row"><span class="stat-label">循環次數</span><span class="stat-val">{evo.get('cycle_count', evo.get('cycles','?'))}</span></div>
    <div class="stat-row"><span class="stat-label">進化分數</span><span class="stat-val">{evo.get('evolution_score','?')}</span></div>
    <div class="stat-row"><span class="stat-label">吸收資訊</span><span class="stat-val">{evo.get('total_absorbed','?')}</span></div>
    <div class="stat-row"><span class="stat-label">學習次數</span><span class="stat-val">{evo.get('total_learned','?')}</span></div>
  </div>

  <div class="card">
    <h3>👤 客戶 ({len(customers)})</h3>
    {''.join(f'<div class="stat-row"><span class="stat-label">#{cid[:8]}</span><span class="stat-val">{c.get("name","?")} · {c.get("status","?")}</span></div>' for cid, c in list(customers.items())[:5])}
    {f'<div class="stat-row"><span class="stat-label" style="color:#8b949e">...還有 {len(customers)-5} 位</span></div>' if len(customers)>5 else ''}
    {'<div style="color:#8b949e;font-size:12px;padding:8px 0">尚無客戶</div>' if not customers else ''}
  </div>

  <div class="card">
    <h3>📝 電子書 ({len(ebooks)} 章)</h3>
    {''.join(f'<div class="stat-row"><span class="stat-label">{f[:50]}</span><a href="/view/ebooks/{f}?token={request.args.get("token","")}" style="color:#58a6ff;font-size:11px">查看</a></div>' for f in ebooks[:10])}
    {f'<div style="color:#8b949e;font-size:11px;padding:4px 0">...還有 {len(ebooks)-10} 章</div>' if len(ebooks)>10 else ''}
    {'<div style="color:#8b949e;font-size:12px;padding:8px 0">尚無電子書</div>' if not ebooks else ''}
  </div>

  <div class="card">
    <h3>📚 童書 ({len(children)} 篇)</h3>
    {''.join(f'<div class="stat-row"><span class="stat-label">{f[:50]}</span><a href="/view/children_book/{f}?token={request.args.get("token","")}" style="color:#58a6ff;font-size:11px">查看</a></div>' for f in children[:10])}
    {f'<div style="color:#8b949e;font-size:11px;padding:4px 0">...還有 {len(children)-10} 篇</div>' if len(children)>10 else ''}
    {'<div style="color:#8b949e;font-size:12px;padding:8px 0">尚無童書</div>' if not children else ''}
  </div>

  <div class="card">
    <h3>🔬 研究報告 ({len(research_files)} 篇)</h3>
    {''.join(f'<div class="stat-row"><span class="stat-label">{f[:45]}</span><a href="/view/research/{f}?token={request.args.get("token","")}" style="color:#58a6ff;font-size:11px">查看</a></div>' for f in research_files[:10])}
    {f'<div style="color:#8b949e;font-size:11px;padding:4px 0">...還有 {len(research_files)-10} 篇</div>' if len(research_files)>10 else ''}
    {'<div style="color:#8b949e;font-size:12px;padding:8px 0">尚無研究報告</div>' if not research_files else ''}
  </div>

  <div class="card">
    <h3>🌐 網站</h3>
    <div class="stat-row"><span class="stat-label">HTML 頁面</span><span class="stat-val">{len(websites)} 個</span></div>
    {''.join(f'<div class="stat-row"><span class="stat-label">{f[:50]}</span><a href="/view/website/{f}?token={request.args.get("token","")}" style="color:#58a6ff;font-size:11px">查看</a></div>' for f in websites[:5])}
    <div class="stat-row"><span class="stat-label">CSS 樣式</span><span class="stat-val">{len(website_css)} 個</span></div>
  </div>

  <div class="card">
    <h3>🔧 工具清單 ({tool_count})</h3>
    <div style="max-height:200px;overflow-y:auto;font-size:11px;color:#8b949e;line-height:1.8">
      {', '.join(brain.tools.list_tools() if hasattr(brain,'tools') and brain.tools else [])}
    </div>
  </div>
</div>

<div class="footer">AMPM-AIOPS 黑曜 · Dashboard v1.0</div>
</body>
</html>"""
    except Exception as e:
        return f"<h1>錯誤</h1><pre>{e}</pre>"


@app.route("/view/<path:subpath>")
def view_file(subpath):
    """安全查看 outputs 目录下的文件"""
    if brain is None:
        return "⚠️ 黑曜尚未初始化", 503
    BASE = Path(__file__).parent.parent.parent
    safe_path = (BASE / "outputs" / subpath).resolve()
    if not str(safe_path).startswith(str((BASE / "outputs").resolve())):
        return "❌ 路徑不允許", 403
    if not safe_path.exists():
        return "❌ 檔案不存在", 404
    if safe_path.suffix == ".html":
        return safe_path.read_text(encoding="utf-8")
    content = safe_path.read_text(encoding="utf-8")
    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{safe_path.name} | 黑曜</title>
<style>
body{{font-family:'Inter',-apple-system,sans-serif;background:#0a0a0f;color:#e0e0e0;max-width:800px;margin:0 auto;padding:20px;line-height:1.7}}
a{{color:#58a6ff}}
pre{{background:#111122;padding:16px;border-radius:8px;overflow-x:auto;white-space:pre-wrap}}
h1,h2,h3{{color:#58a6ff}}
code{{background:#1a1a2e;padding:2px 6px;border-radius:4px}}
.back{{display:inline-block;margin-bottom:16px;color:#8b949e;text-decoration:none}}
</style>
</head>
<body>
<a href="/?token={request.args.get('token','')}" class="back">← 返回 Dashboard</a>
<div style="white-space:pre-wrap">{content}</div>
</body>
</html>"""
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
