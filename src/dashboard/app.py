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
        review_file = BASE / "data" / "pipeline" / "reviews.json"
        reviews = {}
        if review_file.exists():
            reviews = json.loads(review_file.read_text())

        def get_files(subdir, ext="*.md"):
            p = outputs_dir / subdir
            if not p.exists(): return []
            result = []
            for f in sorted(p.glob(ext), key=lambda x: x.name.lower()):
                try:
                    size = f.stat().st_size
                    chars = len(f.read_text(encoding="utf-8"))
                except: size, chars = 0, 0
                key = f"{subdir}/{f.name}"
                review = reviews.get(key, "pending")
                if review == "approved": icon = "✅"
                elif review == "rejected": icon = "❌"
                elif chars > 2000: icon = "📝"
                elif chars > 500: icon = "🆕"
                else: icon = "⚠️"
                result.append({"name": f.name, "size": size, "chars": chars, "icon": icon, "review": review, "key": key})
            return result

        ebooks = get_files("ebooks")
        children = get_files("children_book")
        research_files = get_files("research")
        websites = get_files("website", "*.html")
        brand_files = get_files("brand_identity", "*")

        # 工具数
        tool_count = len(brain.tools.list_tools()) if hasattr(brain, 'tools') and brain.tools else 0
        tools_list = brain.tools.list_tools() if hasattr(brain, 'tools') and brain.tools else []

        # 计算完成度
        def progress(items):
            if not items: return 0, 0
            approved = sum(1 for i in items if i["review"] == "approved")
            return approved, len(items)

        ebook_ok, ebook_total = progress(ebooks)
        child_ok, child_total = progress(children)
        research_ok, research_total = progress(research_files)

        # IP 角色数据
        ip_files = []
        ip_dir = outputs_dir / "character_ip"
        if ip_dir.exists():
            for f in ip_dir.glob("*.md"):
                try: ip_files.append({"name": f.name, "preview": f.read_text(encoding="utf-8")[:200]})
                except: pass

        # 品牌素材
        brand_data = []
        brand_dir = outputs_dir / "brand_identity"
        if brand_dir.exists():
            for f in sorted(brand_dir.iterdir(), key=lambda x: x.name):
                if f.name.startswith("."): continue
                brand_data.append({"name": f.name, "size": f.stat().st_size})

        # 电子书选题 (从 ebook 文件名提取主题)
        ebook_topics = []
        topic_keywords = {"intro": "入门导览", "agent": "AI代理", "prompt": "提示技巧", "tools": "工具介绍",
                          "monetize": "变现策略", "mistakes": "常见错误", "truth": "真相揭露",
                          "passive": "被动收入", "aiops": "AIOps", "adler": "哲学视角",
                          "multi": "多代理协作", "structure": "结构研究"}
        for f in ebooks:
            name_lower = f["name"].lower()
            topic = "综合"
            for kw, label in topic_keywords.items():
                if kw in name_lower:
                    topic = label; break
            ebook_topics.append({**f, "topic": topic})
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
  <!-- 选題審閱 -->
  <div class="card" style="grid-column:span 2">
    <h3>🎯 電子書選題審閱</h3>
    <table>
    <tr><th>主题</th><th>章节</th><th>字数</th><th>審核</th><th>操作</th></tr>
    {''.join(f'<tr><td>{t["topic"]}</td><td>{t["name"][:35]}</td><td>{t["chars"]:,}</td><td>{t["icon"]}</td><td><a href="/view/ebooks/{t["name"]}?token=' + request.args.get("token","") + '" style="color:#58a6ff;font-size:11px">预览</a> <a href="/review/approved/{t["key"]}" style="color:#3fb950;font-size:11px;margin:0 4px">✓</a> <a href="/review/rejected/{t["key"]}" style="color:#e94560;font-size:11px">✗</a></td></tr>' for t in ebook_topics)}
    </table>
  </div>

  <!-- IP 角色 -->
  <div class="card" style="grid-column:span 2">
    <h3>🎭 IP 角色管理 (PANEY & MONEY)</h3>
    {''.join(f'<div class="stat-row"><span class="stat-label">📖 {f["name"]}</span><a href="/view/character_ip/{f["name"]}?token=' + request.args.get("token","") + '" style="color:#58a6ff;font-size:11px">查看</a></div><div style="color:#8b949e;font-size:11px;padding:4px 12px 8px">{f["preview"][:150]}...</div>' for f in ip_files) if ip_files else '<div style="color:#8b949e;font-size:12px;padding:8px 0">尚無 IP 設定檔</div>'}
    <div class="stat-row" style="margin-top:8px"><span class="stat-label">品牌素材</span><span class="stat-val">{len(brand_data)} 個檔案</span></div>
    {''.join(f'<div class="stat-row"><span class="stat-label">{b["name"][:30]}</span><span class="stat-val">{b["size"]:,}B</span></div>' for b in brand_data[:8])}
  </div>
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
    <h3>📝 電子書 ({ebook_ok}/{ebook_total} 已審核)</h3>
    <div style="background:#1a1a2e;border-radius:6px;height:6px;margin-bottom:12px"><div style="background:#3fb950;height:6px;border-radius:6px;width:{ebook_ok/max(ebook_total,1)*100:.0f}%"></div></div>
    {''.join(f'<div class="stat-row"><span class="stat-label">{f["icon"]} {f["name"][:30]}</span><span class="stat-val" style="font-size:10px">{f["chars"]:,}字</span><a href="/view/ebooks/{f["name"]}?token=' + request.args.get("token","") + '" style="color:#58a6ff;font-size:10px">查看</a><a href="/review/approved/{f["key"]}" style="color:#3fb950;font-size:10px;margin:0 4px">✓</a><a href="/review/rejected/{f["key"]}" style="color:#e94560;font-size:10px">✗</a></div>' for f in ebooks[:20])}
    {f'<div style="color:#8b949e;font-size:11px;padding:4px 0">...還有 {len(ebooks)-20} 章</div>' if len(ebooks)>20 else ''}
  </div>

  <div class="card">
    <h3>📚 童書 ({child_ok}/{child_total} 已審核)</h3>
    <div style="background:#1a1a2e;border-radius:6px;height:6px;margin-bottom:12px"><div style="background:#3fb950;height:6px;border-radius:6px;width:{child_ok/max(child_total,1)*100:.0f}%"></div></div>
    {''.join(f'<div class="stat-row"><span class="stat-label">{f["icon"]} {f["name"][:30]}</span><span class="stat-val" style="font-size:10px">{f["chars"]:,}字</span><a href="/view/children_book/{f["name"]}?token=' + request.args.get("token","") + '" style="color:#58a6ff;font-size:10px">查看</a><a href="/review/approved/{f["key"]}" style="color:#3fb950;font-size:10px;margin:0 4px">✓</a><a href="/review/rejected/{f["key"]}" style="color:#e94560;font-size:10px">✗</a></div>' for f in children[:20])}
  </div>

  <div class="card">
    <h3>🔬 研究報告 ({research_ok}/{research_total} 已審核)</h3>
    <div style="background:#1a1a2e;border-radius:6px;height:6px;margin-bottom:12px"><div style="background:#3fb950;height:6px;border-radius:6px;width:{research_ok/max(research_total,1)*100:.0f}%"></div></div>
    {''.join(f'<div class="stat-row"><span class="stat-label">{f["icon"]} {f["name"][:30]}</span><span class="stat-val" style="font-size:10px">{f["chars"]:,}字</span><a href="/view/research/{f["name"]}?token=' + request.args.get("token","") + '" style="color:#58a6ff;font-size:10px">查看</a><a href="/review/approved/{f["key"]}" style="color:#3fb950;font-size:10px;margin:0 4px">✓</a><a href="/review/rejected/{f["key"]}" style="color:#e94560;font-size:10px">✗</a></div>' for f in research_files[:20])}
  </div>

  <div class="card">
    <h3>🌐 品牌與網站</h3>
    <div class="stat-row"><span class="stat-label">網站頁面</span><span class="stat-val">{len(websites)} 個</span></div>
    {''.join(f'<div class="stat-row"><span class="stat-label">{f["name"][:30]}</span><a href="/view/website/{f["name"]}?token=' + request.args.get("token","") + '" style="color:#58a6ff;font-size:11px">查看</a></div>' for f in websites[:5])}
    <div class="stat-row"><span class="stat-label">品牌素材</span><span class="stat-val">{len(brand_files)} 個</span></div>
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


@app.route("/review/<status>/<path:subpath>")
def review_file(status, subpath):
    """人工審核：approved / rejected / pending"""
    if status not in ("approved", "rejected", "pending"):
        return "❌ 無效狀態", 400
    BASE = Path(__file__).parent.parent.parent
    review_file = BASE / "data" / "pipeline" / "reviews.json"
    review_file.parent.mkdir(parents=True, exist_ok=True)
    reviews = {}
    if review_file.exists():
        reviews = json.loads(review_file.read_text())
    reviews[subpath] = status
    review_file.write_text(json.dumps(reviews, ensure_ascii=False, indent=2))
    return f'<script>history.back()</script><p>{subpath} → {status}</p>', 200


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
