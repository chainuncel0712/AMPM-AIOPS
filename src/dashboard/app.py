"""
Dashboard + 網站聊天 API
"""
from flask import Flask, jsonify, request, abort
import os, sys, json
from pathlib import Path

try:
    from flask_cors import CORS
except ImportError:
    def CORS(app):
        return app

sys.path.insert(0, str(Path(__file__).parent.parent))

app = Flask(__name__)
CORS(app)

# 註冊官網書店 Blueprint
try:
    from frontend.store import store_bp
    app.register_blueprint(store_bp, url_prefix="/store")
except Exception as e:
    print(f"[Dashboard] 書店模組載入失敗: {e}")

# 註冊合作方 Blueprint
try:
    from frontend.collab import collab
    app.register_blueprint(collab)
except Exception as e:
    print(f"[Dashboard] 合作方模組載入失敗: {e}")

# 註冊後台管理 Blueprint
try:
    from frontend.admin import admin
    app.register_blueprint(admin)
except Exception as e:
    print(f"[Dashboard] 後台模組載入失敗: {e}")

# 也把 blog 掛在主路由下
try:
    from frontend.store import blog_list, blog_post
    app.add_url_rule("/blog", "blog_list", blog_list)
    app.add_url_rule("/blog/<name>", "blog_post_view", blog_post)
except:
    pass

DASHBOARD_TOKEN = os.environ.get("DASHBOARD_TOKEN", "")

@app.before_request
def check_auth():
    if not DASHBOARD_TOKEN:
        return
    token = request.args.get("token") or (request.form.get("token") if request.method == "POST" else None) or request.headers.get("Authorization", "").replace("Bearer ", "")
    if token == DASHBOARD_TOKEN:
        return
    if request.path in ("/health", "/login"):
        return
    if request.path == "/" and request.method == "GET":
        return f"""<html><head><meta http-equiv="refresh" content="0;url=/login"></head><body></body></html>"""
    # 公開頁面：書店、合作申請、部落格、靜態資源 → 不需登入
    if any(request.path.startswith(p) for p in ["/store", "/collab/apply", "/collab/login", "/blog", "/outputs/brand", "/outputs/covers", "/outputs/compiled", "/brand-logo"]):
        return
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
        comics = get_files("comics")
        novels = get_files("novels")
        short_stories = get_files("short_stories")

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
        comics_ok, comics_total = progress(comics)
        novels_ok, novels_total = progress(novels)
        stories_ok, stories_total = progress(short_stories)

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

        # ── 出版管線選題數據 ──
        from pipeline_data import store
        from pipeline_presets import PRODUCT_TYPES
        pipeline_books = []
        rejected_books = []
        for b in store.books:
            pt = PRODUCT_TYPES.get(b.get("product_type", "ebook"), {})
            title = b.get("stage_data", {}).get("1", {}).get("title", b["id"][:8])
            approved = b.get("stage_data", {}).get("1", {}).get("approved", False)
            info = {
                "id": b["id"], "title": title, "approved": approved,
                "type": f'{pt.get("icon","?")}{pt.get("label","?")}',
                "type_key": b.get("product_type", "ebook"),
                "stage": b.get("current_stage", 1)
            }
            if b.get("current_stage") == 0:
                rejected_books.append(info)
            elif b.get("current_stage") == 1:
                pipeline_books.append(info)

        # 电子书主题分类 (output 檔案)
        topic_map = {
            "intro": {"label": "📗 AI 入门导读", "cat": "AI入门"},
            "ai_introduction": {"label": "📗 AI 入门导读", "cat": "AI入门"},
            "test_chapter1": {"label": "📗 AI 入门导读", "cat": "AI入门"},
            "agent_era": {"label": "🤖 AI 代理时代", "cat": "AI代理"},
            "agent_as_employee": {"label": "🤖 AI 代理当做员工", "cat": "AI代理"},
            "multi_agent": {"label": "🤖 多代理协作", "cat": "AI代理"},
            "ai_agent_money": {"label": "💰 AI 变现", "cat": "变现"},
            "truth_about_ai_passive_income": {"label": "💰 AI 被动收入真相", "cat": "变现"},
            "monetize": {"label": "💰 AI 变现策略", "cat": "变现"},
            "prompt": {"label": "💬 AI 提示工程", "cat": "提示工程"},
            "prompt_skills": {"label": "💬 提示技巧实战", "cat": "提示工程"},
            "tools": {"label": "🔧 AI 工具介绍", "cat": "工具"},
            "mistakes": {"label": "⚠️ 常见错误避坑", "cat": "风险管理"},
            "you_are_written_by_rules": {"label": "⚠️ 规则陷阱", "cat": "风险管理"},
            "what_is_aiops": {"label": "⚙️ AIOps 入门", "cat": "AIOps"},
            "adler_philosophy": {"label": "🧠 哲学视角", "cat": "哲学"},
            "book_structure": {"label": "📐 书籍结构研究", "cat": "结构"},
            "ch04": {"label": "📝 第4章 暂未分类", "cat": "待分类"},
            "ch05": {"label": "📝 第5章 暂未分类", "cat": "待分类"},
        }
        def match_topic(name):
            n = name.lower().replace(".md", "")
            for key, info in topic_map.items():
                if key in n:
                    return info
            return {"label": "📝 " + n[:30], "cat": "待分类"}

        ebook_topics = []
        seen_cats = set()
        for f in ebooks:
            t = match_topic(f["name"])
            ebook_topics.append({**f, "label": t["label"], "cat": t["cat"]})
            seen_cats.add(t["cat"])
        ebook_topics.sort(key=lambda x: (list(topic_map.values()).index(next((v for k,v in topic_map.items() if k in x["name"].lower()), {"label":"zzz","cat":"待分类"})), x["name"]))
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
  <div style="display:flex;align-items:center;gap:12px">
    <img src="/brand-logo" style="height:32px" alt="AM&PM">
    <div><h1>AM&PM 出版社</h1><span>AI 自主出版系統 · {NOW}</span></div>
  </div>
  <div>
    <a href="/topics?token={request.args.get('token','')}" style="color:#58a6ff;text-decoration:none;font-size:13px;margin-right:12px">🎯 選題</a>
    <a href="/visual?token={request.args.get('token','')}" style="color:#58a6ff;text-decoration:none;font-size:13px;margin-right:12px">🎨 視覺</a>
    <a href="/ads?token={request.args.get('token','')}" style="color:#58a6ff;text-decoration:none;font-size:13px;margin-right:12px">📣 廣告</a>
    <a href="/publish-dashboard?token={request.args.get('token','')}" style="color:#58a6ff;text-decoration:none;font-size:13px;margin-right:16px">📤 上架</a>
    <span style="color:#3fb950">● 運行中</span>
  </div>
</div>

<div class="grid">
  <!-- 选題審閱 -->
  <div class="card" style="grid-column:span 2">
    <h3>🎯 出版管線選題審核 (通過後才開始撰寫)</h3>
    <table>
    <tr><th>類型</th><th>選題</th><th>狀態</th><th>操作</th></tr>
    {''.join(f'<tr><td>{b["type"]}</td><td>{b["title"][:40]}</td><td>{"⏸️ 待審核" if not b["approved"] else "✅ 已通過"}</td><td>' + (f'<a href="/approve-topic/{b["type_key"]}/{b["id"]}?token=' + request.args.get("token","") + '" style="color:#3fb950;font-size:12px;font-weight:bold">✓</a> <a href="/reject-topic/{b["id"]}?token=' + request.args.get("token","") + '" style="color:#e94560;font-size:12px;font-weight:bold;margin-left:8px">✗淘汰</a>' if not b["approved"] else '等待循環') + '</td></tr>' for b in pipeline_books) if pipeline_books else '<tr><td colspan="4" style="color:#8b949e;padding:12px">尚無選題</td></tr>'}
    </table>
    <div style="font-size:11px;color:#8b949e;margin-top:8px">⚠️ 選題必須通過審核，才會開始撰寫內容。不通過就不生產。</div>
  </div>

  <div class="card" style="grid-column:span 2">
    <h3>🔄 淘汰區 — 敗部復活 (換個標題重新選題)</h3>
    {''.join(f'<div class="stat-row"><span class="stat-label">{b["type"]} {b["title"][:40]}</span><span><a href="/retry-topic/{b["id"]}?token=' + request.args.get("token","") + '" style="color:#d29922;font-size:11px;">🔄 敗部復活</a></span></div>' for b in rejected_books[:20]) if rejected_books else '<div style="color:#8b949e;padding:8px">無淘汰書籍</div>'}
  </div>

  <div class="card" style="grid-column:span 2">
    <h3>📋 輸出檔案審閱 (依分類)</h3>
    <table>
    <tr><th>分類</th><th>章節</th><th>字數</th><th>審核</th><th>操作</th></tr>
    {''.join(f'<tr><td>{t["cat"]}</td><td>{t["label"]}</td><td>{t["chars"]:,}</td><td>{t["icon"]}</td><td><a href="/view/ebooks/{t["name"]}?token=' + request.args.get("token","") + '" style="color:#58a6ff;font-size:11px">预览</a> <a href="/review/approved/{t["key"]}" style="color:#3fb950;font-size:11px;margin:0 4px">✓通過</a> <a href="/review/rejected/{t["key"]}" style="color:#e94560;font-size:11px">✗淘汰</a></td></tr>' for t in ebook_topics)}
    </table>
  </div>

  <!-- IP 角色 -->
  <div class="card" style="grid-column:span 2">
    <h3>🎨 美術素材 / 插畫</h3>
    <div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:12px">
    {''.join(f'<div style="text-align:center;font-size:10px;color:#8b949e"><img src="/asset/{img.name}?token=' + request.args.get("token","") + '" style="width:80px;height:80px;object-fit:cover;border-radius:6px;border:1px solid #1e1e3a"><br>{img.name[:20]}</div>' for img in sorted((BASE/"assets").glob("*"), key=lambda x: x.name) if img.suffix in ('.png','.jpg','.svg','.webp','.gif'))}
    {''.join(f'<div style="text-align:center;font-size:10px;color:#8b949e"><img src="/asset/brand_identity/{img.name}?token=' + request.args.get("token","") + '" style="width:80px;height:80px;object-fit:cover;border-radius:6px;border:1px solid #1e1e3a"><br>{img.name[:20]}</div>' for img in sorted((BASE/"outputs"/"brand_identity").glob("*"), key=lambda x: x.name) if img.suffix in ('.png','.jpg','.svg','.webp','.gif'))}
    </div>
    <div style="font-size:11px;color:#8b949e">上傳新插畫到 assets/ 目錄即可在此預覽</div>
  </div>

  <div class="card" style="grid-column:span 2">
    <h3>🎭 IP 角色設定 (PANEY & MONEY)</h3>
    {''.join(f'<div class="stat-row"><span class="stat-label">📖 {f["name"]}</span><a href="/view/character_ip/{f["name"]}?token=' + request.args.get("token","") + '" style="color:#58a6ff;font-size:11px">查看</a></div><div style="color:#8b949e;font-size:11px;padding:4px 12px 8px">{f["preview"][:150]}...</div>' for f in ip_files) if ip_files else '<div style="color:#8b949e;font-size:12px;padding:8px 0">尚無 IP 設定檔</div>'}
    <div class="stat-row" style="margin-top:8px"><span class="stat-label">品牌素材</span><span class="stat-val">{len(brand_data)} 個檔案</span></div>
    {''.join(f'<div class="stat-row"><span class="stat-label">{b["name"][:30]}</span><span class="stat-val">{b["size"]:,}B</span></div>' for b in brand_data[:8])}
  </div>

  <div class="card">
    <h3>🖥️ 系統資源</h3>    <div class="stat-row"><span class="stat-label">CPU</span><span class="stat-val">{cpu}%</span></div>
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
    <div style="margin-bottom:8px">
      <a href="/review/approved/ebooks" style="color:#3fb950;font-size:10px;text-decoration:none;margin-right:12px">✓ 全部通過</a>
      <a href="/review/pending/ebooks" style="color:#d29922;font-size:10px;text-decoration:none;margin-right:12px">↻ 全部重置</a>
      <a href="/compile-book/ebooks?token={request.args.get('token','')}" style="color:#58a6ff;font-size:10px;text-decoration:none;font-weight:bold">📖 編譯成書</a>
    </div>
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
    <h3>🎨 漫畫 ({comics_ok}/{comics_total} 已審核)</h3>
    <div style="background:#1a1a2e;border-radius:6px;height:6px;margin-bottom:12px"><div style="background:#3fb950;height:6px;border-radius:6px;width:{comics_ok/max(comics_total,1)*100:.0f}%"></div></div>
    {''.join(f'<div class="stat-row"><span class="stat-label">{f["icon"]} {f["name"][:30]}</span><span class="stat-val" style="font-size:10px">{f["chars"]:,}字</span><a href="/view/comics/{f["name"]}?token=' + request.args.get("token","") + '" style="color:#58a6ff;font-size:10px">查看</a><a href="/review/approved/{f["key"]}" style="color:#3fb950;font-size:10px;margin:0 4px">✓</a><a href="/review/rejected/{f["key"]}" style="color:#e94560;font-size:10px">✗</a></div>' for f in comics[:20])}
    {'<div style="color:#8b949e;font-size:12px;padding:8px 0">尚無漫畫內容</div>' if not comics else ''}
  </div>

  <div class="card">
    <h3>📖 長篇小說 ({novels_ok}/{novels_total})</h3>
    <div style="background:#1a1a2e;border-radius:6px;height:6px;margin-bottom:12px"><div style="background:#3fb950;height:6px;border-radius:6px;width:{novels_ok/max(novels_total,1)*100:.0f}%"></div></div>
    {''.join(f'<div class="stat-row"><span class="stat-label">{f["icon"]} {f["name"][:30]}</span><span class="stat-val" style="font-size:10px">{f["chars"]:,}字</span><a href="/view/novels/{f["name"]}?token=' + request.args.get("token","") + '" style="color:#58a6ff;font-size:10px">查看</a><a href="/review/approved/{f["key"]}" style="color:#3fb950;font-size:10px;margin:0 4px">✓</a><a href="/review/rejected/{f["key"]}" style="color:#e94560;font-size:10px">✗</a></div>' for f in novels[:20])}
    {'<div style="color:#8b949e;font-size:12px;padding:8px 0">尚無小說內容</div>' if not novels else ''}
  </div>

  <div class="card">
    <h3>📝 短篇小說 ({stories_ok}/{stories_total})</h3>
    <div style="background:#1a1a2e;border-radius:6px;height:6px;margin-bottom:12px"><div style="background:#3fb950;height:6px;border-radius:6px;width:{stories_ok/max(stories_total,1)*100:.0f}%"></div></div>
    {''.join(f'<div class="stat-row"><span class="stat-label">{f["icon"]} {f["name"][:30]}</span><span class="stat-val" style="font-size:10px">{f["chars"]:,}字</span><a href="/view/short_stories/{f["name"]}?token=' + request.args.get("token","") + '" style="color:#58a6ff;font-size:10px">查看</a><a href="/review/approved/{f["key"]}" style="color:#3fb950;font-size:10px;margin:0 4px">✓</a><a href="/review/rejected/{f["key"]}" style="color:#e94560;font-size:10px">✗</a></div>' for f in short_stories[:20])}
    {'<div style="color:#8b949e;font-size:12px;padding:8px 0">尚無短篇小說</div>' if not short_stories else ''}
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
    """人工審核：approved / rejected / pending (支援批次)"""
    if status not in ("approved", "rejected", "pending"):
        return "❌ 無效狀態", 400
    BASE = Path(__file__).parent.parent.parent
    review_file = BASE / "data" / "pipeline" / "reviews.json"
    review_file.parent.mkdir(parents=True, exist_ok=True)
    reviews = {}
    if review_file.exists():
        reviews = json.loads(review_file.read_text())

    batch_dirs = {"ebooks", "children_book", "research", "comics", "novels", "short_stories"}
    if subpath in batch_dirs:
        d = BASE / "outputs" / subpath
        if d.exists():
            for f in d.glob("*.md"):
                reviews[f"{subpath}/{f.name}"] = status
        review_file.write_text(json.dumps(reviews, ensure_ascii=False, indent=2))
        return f'<meta http-equiv="refresh" content="0;url=/?token={request.args.get("token","")}"><p>{subpath} → 全部 {status}</p>', 200

    reviews[subpath] = status
    review_file.write_text(json.dumps(reviews, ensure_ascii=False, indent=2))

    # 淘汰記錄：記住不要的主題
    if status == "rejected":
        rejected_file = BASE / "data" / "pipeline" / "rejected_topics.json"
        rejected_file.parent.mkdir(parents=True, exist_ok=True)
        rejected_topics = {}
        if rejected_file.exists():
            rejected_topics = json.loads(rejected_file.read_text())
        # 提取關鍵字
        name = Path(subpath).stem.replace("_", " ").lower()
        topic = "general"
        for kw, label in {"intro": "入门", "agent": "AI代理", "prompt": "提示", "tools": "工具",
                          "monetize": "变现", "mistakes": "错误", "truth": "真相",
                          "passive": "被动收入", "aiops": "AIOps", "adler": "哲学",
                          "multi": "多代理", "structure": "结构研究"}.items():
            if kw in name: topic = label; break
        rejected_topics[topic] = rejected_topics.get(topic, 0) + 1
        rejected_file.write_text(json.dumps(rejected_topics, ensure_ascii=False, indent=2))
        msg = f"{subpath} → 已淘汰，已記憶「{topic}」類將減少出現"
    else:
        msg = f"{subpath} → {status}"

    token = request.args.get("token", "")
    return f'<meta http-equiv="refresh" content="0;url=/?token={token}"><p>{msg}</p>', 200


@app.route("/approve-topic/<pipeline>/<book_id>")
def approve_topic(pipeline, book_id):
    from pipeline_engine import engine
    result = engine.approve_topic(pipeline, book_id)
    token = request.args.get("token", "")
    return f'<meta http-equiv="refresh" content="0;url=/?token={token}"><p>{result}</p>', 200


@app.route("/reject-topic/<book_id>")
def reject_topic(book_id):
    from pipeline_engine import engine
    result = engine.reject_topic(book_id)
    token = request.args.get("token", "")
    return f'<meta http-equiv="refresh" content="0;url=/?token={token}"><p>{result}</p>', 200


@app.route("/retry-topic/<book_id>")
def retry_topic(book_id):
    from pipeline_engine import engine
    new_title = request.args.get("title", "")
    result = engine.retry_topic(book_id, new_title)
    token = request.args.get("token", "")
    return f'<meta http-equiv="refresh" content="0;url=/?token={token}"><p>{result}</p>', 200


@app.route("/publishing")
def publishing_dashboard():
    """上架管理面板"""
    token = request.args.get("token", "")
    from publishing_system import publisher as pub_mgr, PLATFORM_SPECS
    items = pub_mgr.get_prepared_books()
    platforms = pub_mgr.get_platform_status()

    items_html = ""
    for item in items[:20]:
        plats = ", ".join(item.get("platforms", [])[:3])
        items_html += f"""<tr>
            <td>{item.get('title','?')[:30]}</td>
            <td>{item.get('status','?')}</td>
            <td>{plats}</td>
            <td>{item.get('metadata',{}).get('price',{}).get('ntd','?')}NTD</td>
        </tr>"""

    plat_html = ""
    for name, p in platforms.items():
        status = "✅" if p["status"] == "ready" else "🔧"
        plat_html += f"""<tr>
            <td>{p['icon']} {p['name']}</td>
            <td>{', '.join(p['formats'])}</td>
            <td>{p['royalty']}</td>
            <td>{status}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>上架系統 | 黑曜</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:system-ui,sans-serif;background:#0a0a0f;color:#e0e0e0;padding:20px;max-width:1000px;margin:0 auto}}
h1{{color:#58a6ff;font-size:20px;margin-bottom:16px}}
.card{{background:#111122;border:1px solid #1e1e3a;border-radius:12px;padding:20px;margin-bottom:16px}}
.card h3{{color:#8b949e;font-size:13px;text-transform:uppercase;margin-bottom:12px}}
a{{color:#58a6ff;text-decoration:none;font-size:12px}}
table{{width:100%;border-collapse:collapse;font-size:12px}}
th{{text-align:left;color:#8b949e;padding:8px;border-bottom:1px solid #1e1e3a}}
td{{padding:8px;border-bottom:1px solid #111122}}
.good{{color:#3fb950}}.warn{{color:#d29922}}</style></head>
<body>
<h1>📤 上架系統</h1>
<a href="/?token={token}">← Dashboard</a> | <a href="/pipeline?token={token}">管線看板</a>

<div class="card">
<h3>📚 待上架書籍 ({len(items)} 本)</h3>
<table>
<tr><th>書名</th><th>狀態</th><th>平台</th><th>建議售價</th></tr>
{items_html if items else '<tr><td colspan="4" style="color:#8b949e">尚無待上架書籍</td></tr>'}
</table>
</div>

<div class="card">
<h3>📡 上架平台 ({len(platforms)} 個)</h3>
<table>
<tr><th>平台</th><th>格式</th><th>版稅</th><th>狀態</th></tr>
{plat_html}
</table>
</div>
</body></html>"""


@app.route("/pipeline-kanban")
def pipeline_view():
    """管線看板：9 階段 Kanban"""
    token = request.args.get("token", "")
    BASE = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(BASE / "src"))
    from pipeline_presets import PRODUCT_TYPES, STAGE_LABELS, HUMAN_GATES

    all_books = []
    try:
        from pipeline_data import store
        all_books = store.books
    except: pass

    stages = {}
    for i in range(1, 11):
        stages[i] = {"label": STAGE_LABELS[i], "is_gate": i in HUMAN_GATES, "books": []}
    for b in all_books:
        s = b.get("current_stage", 1)
        if s in stages:
            pt = PRODUCT_TYPES.get(b.get("product_type", "ebook"), {})
            title = b.get("stage_data", {}).get("1", {}).get("title", b["id"][:8])
            stages[s]["books"].append({
                "id": b["id"], "title": title[:20],
                "icon": pt.get("icon", "?"), "type": pt.get("label", "?"),
                "stage": s
            })

    cards_html = ""
    for i in range(1, 11):
        s = stages[i]
        books_html = ""
        for b in s["books"]:
            gate_icon = "🔴" if s["is_gate"] and b["stage"] == 1 and not all_books else ""
            btn = ""
            if b["stage"] == 1:
                pt_key = next((k for k, v in PRODUCT_TYPES.items() if v["label"] == b["type"]), "ebook")
                btn = f'<a href="/approve-topic/{pt_key}/{b["id"]}?token={token}" class="btn btn-green" style="font-size:9px;padding:2px 6px">✓</a>'
            books_html += f'<div class="pipeline-card"><span>{b["icon"]}</span> <span title="{b["title"]}">{b["title"]}</span>{gate_icon} {btn}</div>'
        if not books_html:
            books_html = '<div class="pipeline-empty">—</div>'
        gate_label = " 🔴閘門" if s["is_gate"] else " ⏳自動"
        cards_html += f'<div class="pipe-col"><div class="pipe-header">{i}. {s["label"]}{gate_label}<span style="font-size:10px;color:#8b949e"> ({len(s["books"])})</span></div>{books_html}</div>'

    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>管線看板 | 黑曜</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:system-ui,sans-serif;background:#0a0a0f;color:#e0e0e0;padding:16px}}
h1{{color:#58a6ff;font-size:18px;margin-bottom:12px}}
a{{color:#58a6ff;text-decoration:none}}
.btn{{display:inline-block;border-radius:4px;text-decoration:none;cursor:pointer;border:none}}
.btn-green{{background:#238636;color:#fff}}
.pipeline-board{{display:flex;gap:10px;overflow-x:auto;padding-bottom:16px}}
.pipe-col{{min-width:150px;max-width:200px;flex-shrink:0}}
.pipe-header{{background:#111122;padding:8px 10px;border-radius:8px 8px 0 0;font-size:11px;color:#58a6ff;font-weight:600;border:1px solid #1e1e3a;border-bottom:none}}
.pipeline-card{{background:#111122;border:1px solid #1e1e3a;border-top:none;padding:8px 10px;font-size:10px;display:flex;align-items:center;gap:4px}}
.pipeline-card:last-child{{border-radius:0 0 8px 8px}}
.pipeline-empty{{color:#30363d;font-size:10px;padding:8px 10px;background:#111122;border:1px solid #1e1e3a;border-top:none;border-radius:0 0 8px 8px}}
</style></head>
<body>
<h1>🏭 出版管線看板</h1>
<a href="/?token={token}" style="font-size:11px">← Dashboard</a>
<div class="pipeline-board" style="margin-top:12px">{cards_html}</div>
</body></html>"""
def compile_book(book_type):
    """將已審核章節編譯為完整書籍"""
    BASE = Path(__file__).parent.parent.parent
    review_file = BASE / "data" / "pipeline" / "reviews.json"
    reviews = {}
    if review_file.exists():
        reviews = json.loads(review_file.read_text())

    book_dir = BASE / "outputs" / book_type
    if not book_dir.exists():
        return f"<script>history.back()</script><p>路徑不存在: {book_type}</p>", 404

    chapters = []
    for f in sorted(book_dir.glob("*.md")):
        key = f"{book_type}/{f.name}"
        if reviews.get(key) == "approved":
            try:
                content = f.read_text(encoding="utf-8")
                chapters.append({"name": f.stem, "content": content})
            except: pass

    if not chapters:
        return f"<script>history.back()</script><p>沒有已審核的章節可編譯</p>"

    book_name = {"ebooks": "AI入門指南", "children_book": "PANEY & MONEY 童書", "research": "研究報告合集",
                 "comics": "漫畫合集", "novels": "長篇小說", "short_stories": "短篇小說集"}.get(book_type, book_type)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")

    toc = f"# {book_name}\n\n> 自動編譯於 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n## 目錄\n\n"
    body = ""
    for i, ch in enumerate(chapters, 1):
        safe_name = ch["name"].replace("_", " ").replace("ch", "第").replace(" ", "")
        toc += f"{i}. [{safe_name}](#{ch['name']})\n"
        body += f"\n\n---\n\n# 第{i}章: {safe_name}\n\n{ch['content']}"

    full_book = toc + "\n" + body
    compile_dir = BASE / "outputs" / "compiled"
    compile_dir.mkdir(parents=True, exist_ok=True)
    out_path = compile_dir / f"{book_type}_{timestamp}.md"
    out_path.write_text(full_book, encoding="utf-8")

    total_chars = sum(len(c["content"]) for c in chapters)
    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>編譯完成 | 黑曜</title>
<style>
body{{font-family:system-ui,sans-serif;background:#0a0a0f;color:#e0e0e0;padding:30px;max-width:700px;margin:0 auto}}
h1{{color:#3fb950}}a{{color:#58a6ff}}.card{{background:#111122;border:1px solid #1e1e3a;border-radius:12px;padding:20px;margin:16px 0}}
.stat{{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #1a1a2e}}
</style>
</head>
<body>
<h1>✅ 書籍編譯完成</h1>
<div class="card">
<div class="stat"><span>書名</span><span>{book_name}</span></div>
<div class="stat"><span>章節數</span><span>{len(chapters)} 章</span></div>
<div class="stat"><span>總字數</span><span>{total_chars:,} 字</span></div>
<div class="stat"><span>檔案</span><span>{out_path.name}</span></div>
</div>
<div style="display:flex;gap:12px;margin-top:16px">
<a href="/view/compiled/{out_path.name}?token={request.args.get('token','')}" style="background:#1f6feb;color:#fff;padding:10px 20px;border-radius:8px;text-decoration:none">📖 預覽完整書籍</a>
<a href="/publish?token={request.args.get('token','')}" style="background:#238636;color:#fff;padding:10px 20px;border-radius:8px;text-decoration:none">🚀 前往上架</a>
<a href="javascript:history.back()" style="color:#8b949e;padding:10px 20px">← 返回</a>
</div>
</body></html>"""


@app.route("/publish")
def publish_page():
    """自動上架管理頁"""
    BASE = Path(__file__).parent.parent.parent
    review_file = BASE / "data" / "pipeline" / "reviews.json"
    reviews = {}
    if review_file.exists():
        reviews = json.loads(review_file.read_text())

    pub_log_file = BASE / "data" / "publisher_log.json"
    pub_logs = []
    if pub_log_file.exists():
        try: pub_logs = json.loads(pub_log_file.read_text())[-20:]
        except: pass

    approved_ebooks = []
    outputs_dir = BASE / "outputs"
    compiled_books = []
    compiled_dir = outputs_dir / "compiled"
    if compiled_dir.exists():
        for f in sorted(compiled_dir.glob("*.md"), reverse=True):
            try: compiled_books.append({"name": f.name, "chars": len(f.read_text(encoding="utf-8"))})
            except: pass

    for subdir, label in [("ebooks", "電子書"), ("children_book", "童書"),
                           ("comics", "漫畫"), ("novels", "長篇小說"), ("short_stories", "短篇小說")]:
        d = outputs_dir / subdir
        if d.exists():
            for f in sorted(d.glob("*.md")):
                key = f"{subdir}/{f.name}"
                if reviews.get(key) == "approved":
                    try: chars = len(f.read_text(encoding="utf-8"))
                    except: chars = 0
                    approved_ebooks.append({"key": key, "name": f.name, "chars": chars, "type": label})

    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>自動上架 | 黑曜</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:system-ui,sans-serif;background:#0a0a0f;color:#e0e0e0;padding:30px;max-width:900px;margin:0 auto}}
h1{{color:#58a6ff;font-size:20px;margin-bottom:20px}}
.card{{background:#111122;border:1px solid #1e1e3a;border-radius:12px;padding:20px;margin-bottom:16px}}
.card h3{{color:#8b949e;font-size:13px;text-transform:uppercase;margin-bottom:12px}}
.stat-row{{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #1a1a2e;font-size:13px}}
.stat-label{{color:#8b949e}}
.stat-val{{color:#e0e0e0}}
.btn{{display:inline-block;padding:8px 16px;border-radius:6px;text-decoration:none;font-size:12px;margin:4px;cursor:pointer;border:none}}
.btn-green{{background:#238636;color:#fff}}
.btn-blue{{background:#1f6feb;color:#fff}}
.btn-red{{background:#da3633;color:#fff}}
.btn-gray{{background:#30363d;color:#8b949e}}
.publish-log{{font-size:11px;color:#8b949e;max-height:300px;overflow-y:auto}}
a{{color:#58a6ff}}
</style>
</head>
<body>
<h1>🚀 自動上架系統</h1>
<a href="/?token={request.args.get('token','')}" style="color:#8b949e;font-size:12px">← 返回 Dashboard</a>

<div class="card">
<h3>✅ 已審核通過，待上架 ({len(approved_ebooks)} 章)</h3>
{''.join(f'<div class="stat-row"><span class="stat-label">{b["type"]}: {b["name"][:40]}</span><span class="stat-val">{b["chars"]:,}字</span><a href="/view/{b["key"]}?token=' + request.args.get("token","") + '" class="btn btn-blue">预览</a></div>' for b in approved_ebooks) if approved_ebooks else '<div style="color:#8b949e;padding:8px">尚無審核通過的章節。請先到 Dashboard 審核。</div>'}
<div style="margin-top:12px">
<a href="/compile-book/ebooks?token={request.args.get('token','')}" class="btn btn-green">📖 將已審核章節編譯成書</a>
</div>
</div>

<div class="card">
<h3>📚 已編譯書籍 ({len(compiled_books)} 本)</h3>
{''.join(f'<div class="stat-row"><span class="stat-label">📗 {b["name"]}</span><span class="stat-val">{b["chars"]:,}字</span><a href="/view/compiled/{b["name"]}?token=' + request.args.get("token","") + '" class="btn btn-blue">预览</a></div>' for b in compiled_books[:10]) if compiled_books else '<div style="color:#8b949e;padding:8px">尚未編譯完整書籍。審核章節後點「編譯成書」</div>'}
</div>

<div class="card">
<h3>⚙️ 上架平台狀態</h3>
<div class="stat-row"><span class="stat-label">Readmoo</span><span class="stat-val">{'✅ 已設定' if os.getenv('READMOO_EMAIL') else '❌ 未設定憑證'}</span></div>
<div class="stat-row"><span class="stat-label">Amazon KDP</span><span class="stat-val">{'✅ 已設定' if os.getenv('KDP_EMAIL') else '❌ 未設定憑證'}</span></div>
<div style="margin-top:12px;color:#8b949e;font-size:11px">
設定位於 .env：READMOO_EMAIL / READMOO_PASSWORD / KDP_EMAIL / KDP_PASSWORD
</div>
</div>

<div class="card">
<h3>📋 上架紀錄 (最近 {len(pub_logs)} 筆)</h3>
<div class="publish-log">
{''.join(f'<div style="padding:4px 0">{e.get("ts","")[:16]} | {"✅" if e.get("success") else "❌"} {e.get("platform","?")} | {e.get("title","?")}</div>' for e in reversed(pub_logs)) if pub_logs else '<div style="color:#8b949e">尚無上架紀錄</div>'}
</div>
</div>

<div class="card">
<h3>📖 上架指令 (Telegram)</h3>
<div style="font-size:12px;color:#8b949e;line-height:1.8">
/publish status — 管線狀態<br>
/publish ebook trend — 市場趨勢<br>
/publish ebook select &lt;主題&gt; — 選題<br>
/publish approve &lt;book_id&gt; — 批准<br>
/publish publish &lt;book_id&gt; — 上架<br>
/publish publisher status — 上架機械組件狀態
</div>
</div>

</body></html>"""


@app.route("/asset/<path:subpath>")
def serve_asset(subpath):
    """安全提供靜態素材"""
    BASE = Path(__file__).parent.parent.parent
    safe = (BASE / "assets" / subpath).resolve()
    if not str(safe).startswith(str((BASE / "assets").resolve())):
        safe = (BASE / "outputs" / "brand_identity" / subpath).resolve()
        if not str(safe).startswith(str((BASE / "outputs" / "brand_identity").resolve())):
            return "", 404
    if not safe.exists(): return "", 404
    from flask import send_file
    return send_file(str(safe))


@app.route("/view/<path:subpath>")
def view_file(subpath):
    """安全查看 + 編輯 outputs 目录下的文件（含 CodeMirror 編輯器）"""
    BASE = Path(__file__).parent.parent.parent
    safe_path = (BASE / "outputs" / subpath).resolve()
    if not str(safe_path).startswith(str((BASE / "outputs").resolve())):
        return "❌ 路徑不允許", 403
    if not safe_path.exists():
        return "❌ 檔案不存在", 404
    if safe_path.suffix == ".html":
        return safe_path.read_text(encoding="utf-8")

    content = safe_path.read_text(encoding="utf-8")
    token = request.args.get("token", "")
    edit_mode = request.args.get("edit", "0") == "1"
    relative = str(safe_path.relative_to(BASE))

    # Base64 content for safe JS embedding
    import base64
    content_b64 = base64.b64encode(content.encode("utf-8")).decode("ascii")

    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{safe_path.name} | 黑曜</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Inter',-apple-system,sans-serif;background:#0a0a0f;color:#e0e0e0;min-height:100vh}}
.toolbar{{background:#111122;border-bottom:1px solid #1e1e3a;padding:12px 20px;display:flex;justify-content:space-between;align-items:center;position:sticky;top:0;z-index:10}}
.toolbar h2{{font-size:15px;color:#58a6ff}}
.toolbar .actions{{display:flex;gap:8px}}
.btn{{padding:7px 14px;border-radius:6px;font-size:12px;border:none;cursor:pointer;text-decoration:none}}
.btn-primary{{background:#238636;color:#fff}}
.btn-secondary{{background:#1e1e3a;color:#8b949e;border:1px solid #333}}
.btn-warn{{background:#d29922;color:#000}}
.btn-danger{{background:#e94560;color:#fff}}
.view-content{{max-width:800px;margin:0 auto;padding:24px;line-height:1.7;white-space:pre-wrap;font-family:'Inter',system-ui,sans-serif;font-size:14px}}
.view-content h1,.view-content h2,.view-content h3{{color:#58a6ff;margin:16px 0 8px}}
.view-content p{{margin:8px 0}}
.view-content code{{background:#1a1a2e;padding:2px 6px;border-radius:4px}}
.view-content pre{{background:#111122;padding:16px;border-radius:8px;overflow-x:auto}}
.editor-container{{display:none;height:calc(100vh - 56px)}}
.editor-container.active{{display:block}}
#editor{{height:100%}}
.toast{{position:fixed;bottom:24px;right:24px;background:#238636;color:#fff;padding:12px 20px;border-radius:8px;font-size:13px;z-index:100;display:none}}
.cm-editor{{height:100%}} .cm-editor .cm-scroller{{font-family:'JetBrains Mono','IBM Plex Mono',monospace;font-size:14px}}
.stats{{font-size:11px;color:#8b949e;padding:4px 20px;background:#0d0d1a}}
</style>
</head>
<body>
<div class="toolbar">
  <div>
    <h2>📄 {safe_path.name}</h2>
    <span class="stats" id="stats">字數: {len(content):,} | 路徑: {subpath}</span>
  </div>
  <div class="actions">
    <a href="/?token={token}" class="btn btn-secondary">← 返回</a>
    <button class="btn btn-secondary" id="toggle-edit" onclick="toggleEdit()">✏️ 編輯</button>
    <button class="btn btn-primary" id="save-btn" style="display:none" onclick="saveFile()">💾 儲存</button>
  </div>
</div>
<div class="view-content" id="view-mode">{content}</div>
<div class="editor-container" id="edit-mode">
  <div id="editor"></div>
</div>
<div class="toast" id="toast"></div>

<script type="module">
import {{EditorView, basicSetup}} from "https://esm.sh/codemirror@6.0.1";
import {{markdown}} from "https://esm.sh/@codemirror/lang-markdown@6.2.4";
import {{oneDark}} from "https://esm.sh/@codemirror/theme-one-dark@6.1.2";

window.editorView = null;

window.toggleEdit = function() {{
  var viewEl = document.getElementById('view-mode');
  var editEl = document.getElementById('edit-mode');
  var saveBtn = document.getElementById('save-btn');
  var toggleBtn = document.getElementById('toggle-edit');

  if (editEl.classList.contains('active')) {{
    editEl.classList.remove('active');
    viewEl.style.display = 'block';
    saveBtn.style.display = 'none';
    toggleBtn.textContent = '✏️ 編輯';
  }} else {{
    viewEl.style.display = 'none';
    editEl.classList.add('active');
    saveBtn.style.display = 'inline-block';
    toggleBtn.textContent = '👁️ 預覽';

    if (!window.editorView) {{
      var contentB64 = "{content_b64}";
      var content = decodeURIComponent(escape(atob(contentB64)));
      window.editorView = new EditorView({{
        doc: content,
        extensions: [basicSetup, markdown(), oneDark],
        parent: document.getElementById('editor')
      }});
    }}
  }}
}};

window.saveFile = function() {{
  if (!window.editorView) return;
  var content = window.editorView.state.doc.toString();
  fetch('/api/save-file', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{filepath: '{relative}', content: content, token: '{token}'}})
  }})
  .then(function(r) {{ return r.json(); }})
  .then(function(d) {{
    var toast = document.getElementById('toast');
    if (d.ok) {{
      toast.style.background = '#238636';
      toast.textContent = '✅ 已儲存 (' + d.word_count.toLocaleString() + ' 字)';
      document.getElementById('stats').textContent = '字數: ' + d.word_count.toLocaleString() + ' | 路徑: {subpath}';
    }} else {{
      toast.style.background = '#e94560';
      toast.textContent = '❌ ' + (d.error || '儲存失敗');
    }}
    toast.style.display = 'block';
    setTimeout(function() {{ toast.style.display = 'none'; }}, 3000);
  }});
}};
</script>
</body>
</html>"""


@app.route("/api/save-file", methods=["POST"])
def api_save_file():
    """儲存編輯過的檔案內容 + 自動備份"""
    data = request.get_json(silent=True) or {}
    filepath = data.get("filepath", "")
    content = data.get("content", "")
    token = data.get("token", "")

    if DASHBOARD_TOKEN and token != DASHBOARD_TOKEN:
        return jsonify({"ok": False, "error": "未授權"})

    BASE_PATH = Path(__file__).parent.parent.parent
    safe_path = (BASE_PATH / filepath).resolve()
    if not str(safe_path).startswith(str(BASE_PATH.resolve())):
        return jsonify({"ok": False, "error": "路徑不允許"})

    try:
        import shutil
        backup_path = str(safe_path) + ".bak"
        if safe_path.exists():
            shutil.copy2(safe_path, backup_path)
        safe_path.write_text(content, encoding="utf-8")
        return jsonify({"ok": True, "word_count": len(content), "path": filepath})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


# ═══ 選題系統 Dashboard ═══

@app.route("/topics")
def topics_dashboard():
    """選題系統主頁"""
    from pipeline_engine import engine as topic_engine
    from pipeline_presets import PRODUCT_TYPES
    from sales_tracker import sales_tracker

    NOW = __import__("time").strftime("%Y-%m-%d %H:%M:%S")
    token = request.args.get("token", "")

    types = topic_engine.list_types(include_dormant=True)
    pending = topic_engine.get_pending_topics()
    approved = topic_engine.get_approved_topics()
    rejected = topic_engine.get_rejected_topics()
    sales_summary = sales_tracker.get_summary()
    series = sales_tracker.get_series_suggestions()
    eliminations = sales_tracker.get_elimination_candidates()

    type_opts = "\n".join(
        f'<option value="{t["key"]}">{t["icon"]} {t["label"]} ({t["priority"]}/10)</option>'
        for t in types
    )

    # pending rows
    pending_rows = ""
    for p in pending:
        pending_rows += (
            f'<tr><td>{p["type_icon"]} {p["type_label"]}</td>'
            f'<td>{p["title"][:40]}</td><td>⏸️ 待審</td>'
            f'<td><a href="/api/approve-topic/{p["id"]}?token={token}" style="color:#3fb950;font-size:11px">✓ 採用</a> '
            f'<a href="/api/reject-topic/{p["id"]}?token={token}&reason=品質" style="color:#e94560;font-size:11px">✗ 淘汰</a></td></tr>'
        )
    if not pending_rows:
        pending_rows = '<tr><td colspan="4" style="color:#8b949e;padding:12px">尚無選題</td></tr>'

    # approved rows
    approved_rows = ""
    for a in approved:
        approved_rows += f'<tr><td>{a["type_icon"]} {a["type_label"]}</td><td>{a["title"][:40]}</td><td style="color:#3fb950">✅ 已通過</td></tr>'
    if not approved_rows:
        approved_rows = '<tr><td colspan="3" style="color:#8b949e;padding:12px">尚無通過</td></tr>'

    # rejected rows
    rejected_rows = ""
    for r in rejected[:10]:
        rejected_rows += f'<tr><td>✗ {r["title"][:40]}</td><td>{r["count"]} 次</td></tr>'
    if not rejected_rows:
        rejected_rows = '<tr><td colspan="2" style="color:#8b949e;padding:12px">尚無淘汰</td></tr>'

    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>選題系統 | 黑曜</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Inter',-apple-system,sans-serif;background:#0a0a0f;color:#e0e0e0;min-height:100vh}}
.header{{background:#111122;border-bottom:1px solid #1e1e3a;padding:16px 24px;display:flex;justify-content:space-between;align-items:center}}
.header h1{{font-size:20px;color:#58a6ff}}
.header a{{color:#8b949e;text-decoration:none;font-size:13px;margin-left:12px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(400px,1fr));gap:16px;padding:20px 24px}}
.card{{background:#111122;border:1px solid #1e1e3a;border-radius:12px;padding:20px}}
.card h3{{font-size:13px;color:#8b949e;text-transform:uppercase;margin-bottom:12px}}
table{{width:100%;border-collapse:collapse;font-size:12px}}
th{{text-align:left;color:#8b949e;padding:6px 8px;border-bottom:1px solid #1e1e3a}}
td{{padding:6px 8px;border-bottom:1px solid #111122}}
.btn{{padding:8px 16px;background:#238636;color:#fff;border-radius:6px;font-size:13px;border:none;cursor:pointer}}
select,input{{padding:8px 12px;background:#0d0d1a;border:1px solid #1e1e3a;border-radius:6px;color:#e0e0e0;font-size:13px}}
select{{min-width:200px}}
.result-box{{background:#0d0d1a;border:1px solid #1e1e3a;border-radius:8px;padding:16px;margin-top:12px;min-height:100px;font-size:13px;line-height:1.6;white-space:pre-wrap;display:none}}
.spinner{{display:none;text-align:center;padding:20px;color:#58a6ff}}
</style>
</head>
<body>
<div class="header">
  <div><h1>🎯 黑曜選題系統</h1><span style="font-size:12px;color:#8b949e">28 種類型 · 銷售驅動 · {NOW}</span></div>
  <div>
    <a href="/sales?token={token}">📊 銷售</a>
    <a href="/visual?token={token}">🎨 視覺</a>
    <a href="/ads?token={token}">📣 廣告</a>
    <a href="/?token={token}">🏠 首頁</a>
  </div>
</div>

<div class="grid">
  <div class="card" style="grid-column:span 2">
    <h3>🤖 生成選題提案</h3>
    <div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap">
      <select id="topic-type">
        <option value="">🎯 智慧加權分配（推薦）</option>
        {type_opts}
      </select>
      <input type="number" id="topic-count" value="5" min="1" max="20" style="width:70px" title="提案數量">
      <button class="btn" onclick="gen()">生成提案</button>
    </div>
    <div class="spinner" id="spinner">⏳ 生成中...</div>
    <div class="result-box" id="result"></div>
  </div>

  <div class="card"><h3>⏸️ 待審核 ({len(pending)})</h3><table><tr><th>類型</th><th>選題</th><th>狀態</th><th>操作</th></tr>{pending_rows}</table></div>
  <div class="card"><h3>✅ 已通過 ({len(approved)})</h3><table><tr><th>類型</th><th>選題</th><th>狀態</th></tr>{approved_rows}</table></div>
  <div class="card"><h3>🗑️ 淘汰區 ({len(rejected)})</h3><table><tr><th>選題</th><th>狀態</th></tr>{rejected_rows}</table></div>
</div>

<script>
async function gen(){{
  var t=document.getElementById('topic-type').value;
  var c=document.getElementById('topic-count').value;
  var r=document.getElementById('result');
  var s=document.getElementById('spinner');
  s.style.display='block';r.style.display='none';
  try{{
    var resp=await fetch('/api/generate-proposals?token={token}&count='+c+(t?'&type='+t:''));
    var d=await resp.json(); s.style.display='none'; r.style.display='block';
    if(d.error){{r.innerHTML='<span style=color:#e94560>❌ '+d.error+'</span>';return;}}
    var h=d.sales_context?'<div style=color:#8b949e;font-size:11px;margin-bottom:12px>'+d.sales_context.replace(/\\n/g,'<br>')+'</div>':'';
    h+='<div style=margin-bottom:8px;color:#58a6ff>📋 '+d.proposals.length+' 提案：</div>';
    d.proposals.forEach(function(p){{
      h+='<div style=border:1px_solid_#1e1e3a;border-radius:8px;padding:12px;margin-bottom:8px>';
      h+='<div style=color:#58a6ff;font-weight:bold>'+p.title+'</div>';
      h+='<div style=font-size:11px;color:#8b949e>類型: '+(p.type_icon||'')+' '+(p.type_label||'')+'</div>';
      h+='<div style=font-size:12px;margin-top:4px>'+(p.description||'')+'</div>';
      h+='<div style=margin-top:8px><a href=/api/adopt-proposal?token={token}&type='+(p.product_type||'ebook')+'&title='+encodeURIComponent(p.title)+' class=btn style=font-size:10px;padding:4px_10px>✓ 採用</a></div>';
      h+='</div>';
    }});
    r.innerHTML=h;
  }}catch(e){{s.style.display='none';r.style.display='block';r.innerHTML='<span style=color:#e94560>❌ '+e.message+'</span>';}}
}}
</script>
</body>
</html>"""


@app.route("/sales")
def sales_dashboard():
    """銷售績效儀表板"""
    from pipeline_engine import engine as topic_engine
    from sales_tracker import sales_tracker
    NOW = __import__("time").strftime("%Y-%m-%d %H:%M:%S")
    token = request.args.get("token", "")
    types = topic_engine.list_types(include_dormant=True)
    summary = sales_tracker.get_summary()
    series = sales_tracker.get_series_suggestions()
    eliminations = sales_tracker.get_elimination_candidates()

    perf = ""
    for t in types:
        s = t["status"]; icon = {"active":"🟢","warning":"🟡","dormant":"🔴"}.get(s,"⚪")
        perf += f'<tr><td>{t["icon"]} {t["label"]}</td><td style="color:#3fb950">${t["avg_revenue"]:.0f}</td><td>{t["success_rate"]:.0%}</td><td>{t["total_published"]}</td><td>{icon} {s}</td><td style="font-size:10px;color:#8b949e">{t["priority"]}/10</td></tr>'

    series_html = "".join(
        '<tr><td>📚 '+s["source_book"]+'</td><td>'+", ".join(s.get("suggested_titles",[])[:2])+'</td><td style="font-size:10px">'+s.get("reason","")[:80]+'</td><td>'+'✅ 已採納' if s.get("adopted") else '<a href="/api/adopt-series/'+str(i)+'?token='+token+'" style="color:#3fb950">採用</a>'+'</td></tr>'
        for i,s in enumerate(series)
    ) or '<tr><td colspan="4" style="color:#8b949e">尚無系列建議</td></tr>'

    elim_html = "".join(
        '<tr><td>'+e.get("label","?")+'</td><td style="font-size:10px">'+e.get("reason","")[:80]+'</td><td>'+('✅' if e.get("human_confirmed") else '<a href="/api/confirm-eliminate/'+e["product_type"]+'?token='+token+'" style="color:#e94560;font-size:10px">確認淘汰</a>')+'</td></tr>'
        for e in eliminations
    ) or '<tr><td colspan="3" style="color:#8b949e">尚無淘汰建議</td></tr>'

    return f"""<!DOCTYPE html>
<html lang="zh-TW"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>銷售 | 黑曜</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Inter',-apple-system,sans-serif;background:#0a0a0f;color:#e0e0e0;min-height:100vh}}
.header{{background:#111122;border-bottom:1px solid #1e1e3a;padding:16px 24px;display:flex;justify-content:space-between;align-items:center}}
.header h1{{font-size:20px;color:#58a6ff}}
.header a{{color:#8b949e;text-decoration:none;font-size:13px;margin-left:12px}}
.card{{background:#111122;border:1px solid #1e1e3a;border-radius:12px;padding:20px;margin:16px 24px}}
.card h3{{font-size:13px;color:#8b949e;text-transform:uppercase;margin-bottom:12px}}
table{{width:100%;border-collapse:collapse;font-size:12px}}
th{{text-align:left;color:#8b949e;padding:6px 8px;border-bottom:1px solid #1e1e3a}}
td{{padding:6px 8px;border-bottom:1px solid #111122}}
.stats{{display:flex;gap:16px;margin-bottom:20px;flex-wrap:wrap}}
.stat{{background:#0d0d1a;border:1px solid #1e1e3a;border-radius:8px;padding:16px;flex:1;text-align:center;min-width:120px}}
.stat .val{{font-size:24px;font-weight:700;color:#58a6ff}}
.stat .label{{font-size:11px;color:#8b949e;margin-top:4px}}
</style></head><body>
<div class="header">
  <div><h1>📊 銷售績效</h1><span style="font-size:12px;color:#8b949e">總營收: ${summary.get("total_revenue", 0):.2f}</span></div>
  <div>
    <a href="/topics?token={token}">🎯 選題</a>
    <a href="/visual?token={token}">🎨 視覺</a>
    <a href="/ads?token={token}">📣 廣告</a>
    <a href="/?token={token}">🏠 首頁</a>
  </div>
</div>
<div style="padding:20px 24px"><div class="stats">
  <div class="stat"><div class="val">{summary["active"]}</div><div class="label">🟢 活躍</div></div>
  <div class="stat"><div class="val">{summary["warning"]}</div><div class="label">🟡 觀望</div></div>
  <div class="stat"><div class="val">{summary["dormant"]}</div><div class="label">🔴 休眠</div></div>
  <div class="stat"><div class="val">${summary.get("total_revenue",0):.0f}</div><div class="label">總營收</div></div>
</div></div>
<div class="card"><h3>28 種類型績效</h3><table><tr><th>類型</th><th>月均</th><th>成功率</th><th>出版</th><th>狀態</th><th>權重</th></tr>{perf}</table></div>
<div class="card"><h3>📚 系列建議</h3><table><tr><th>來源</th><th>建議</th><th>理由</th><th></th></tr>{series_html}</table></div>
<div class="card"><h3>⛔ 淘汰建議</h3><table><tr><th>類型</th><th>原因</th><th></th></tr>{elim_html}</table></div>
<div style="text-align:center;padding:20px;color:#484f58;font-size:11px">銷售數據 → 自動調整選題權重</div>
</body></html>"""


# ═══ 選題 API ═══

@app.route("/api/generate-proposals")
def api_generate_proposals():
    from pipeline_engine import engine as topic_engine
    pt = request.args.get("type", "").strip() or None
    count = int(request.args.get("count", 5))
    return jsonify(topic_engine.generate_proposals(pt, count))


@app.route("/api/approve-topic/<book_id>")
def api_approve_topic(book_id):
    from pipeline_engine import engine as topic_engine
    msg = topic_engine.approve_topic(book_id)
    token = request.args.get("token", "")
    return f"""<html><head><meta charset="utf-8"><meta http-equiv="refresh" content="1;url=/topics?token={token}"></head><body style="background:#0a0a0f;color:#e0e0e0;font-family:sans-serif;padding:40px;text-align:center"><h2>{msg}</h2></body></html>"""


@app.route("/api/reject-topic/<book_id>")
def api_reject_topic(book_id):
    from pipeline_engine import engine as topic_engine
    reason = request.args.get("reason", "品質未達標")
    msg = topic_engine.reject_topic(book_id, reason)
    token = request.args.get("token", "")
    return f"""<html><head><meta charset="utf-8"><meta http-equiv="refresh" content="1;url=/topics?token={token}"></head><body style="background:#0a0a0f;color:#e0e0e0;font-family:sans-serif;padding:40px;text-align:center"><h2>{msg}</h2></body></html>"""


@app.route("/api/adopt-proposal")
def api_adopt_proposal():
    from pipeline_engine import engine as topic_engine
    pt = request.args.get("type", "ebook")
    title = request.args.get("title", "未命名")
    msg = topic_engine.create_topic(pt, title)
    token = request.args.get("token", "")
    return f"""<html><head><meta charset="utf-8"><meta http-equiv="refresh" content="1;url=/topics?token={token}"></head><body style="background:#0a0a0f;color:#e0e0e0;font-family:sans-serif;padding:40px;text-align:center"><h2>{msg}</h2></body></html>"""


@app.route("/api/adopt-series/<int:index>")
def api_adopt_series(index):
    from sales_tracker import sales_tracker
    sales_tracker.adopt_series(index)
    token = request.args.get("token", "")
    return f"""<html><head><meta charset="utf-8"><meta http-equiv="refresh" content="1;url=/sales?token={token}"></head><body style="background:#0a0a0f;color:#e0e0e0;font-family:sans-serif;padding:40px;text-align:center"><h2>✅ 系列建議已採納</h2></body></html>"""


@app.route("/api/confirm-eliminate/<product_type>")
def api_confirm_eliminate(product_type):
    from sales_tracker import sales_tracker
    sales_tracker.human_confirm_eliminate(product_type)
    token = request.args.get("token", "")
    return f"""<html><head><meta charset="utf-8"><meta http-equiv="refresh" content="1;url=/sales?token={token}"></head><body style="background:#0a0a0f;color:#e0e0e0;font-family:sans-serif;padding:40px;text-align:center"><h2>✅ 已確認淘汰</h2></body></html>"""


@app.route("/api/revive-type/<product_type>")
def api_revive_type(product_type):
    from sales_tracker import sales_tracker
    sales_tracker.human_revive(product_type)
    token = request.args.get("token", "")
    return f"""<html><head><meta charset="utf-8"><meta http-equiv="refresh" content="1;url=/sales?token={token}"></head><body style="background:#0a0a0f;color:#e0e0e0;font-family:sans-serif;padding:40px;text-align:center"><h2>✅ {product_type} 已復活</h2></body></html>"""


@app.route("/visual")
def visual_dashboard():
    """視覺審查頁面"""
    from pipeline_engine import engine as topic_engine
    from pipeline_data import store
    import base64, os as _os
    NOW = __import__("time").strftime("%Y-%m-%d %H:%M:%S")
    token = request.args.get("token", "")

    approved = topic_engine.get_approved_topics()
    books = []
    for a in approved:
        b = store.get(a["id"])
        if b:
            books.append({"id": a["id"], "title": a["title"], "type": a["type"], "icon": a["type_icon"]})

    sel_id = request.args.get("book_id", "")
    cover_preview = palette_html = svg_preview = ""
    book_title = ""

    if sel_id and books:
        book = store.get(sel_id)
        if book:
            book_title = book.get("stage_data", {}).get("1", {}).get("title", "?")
            try:
                from visual.cover_generator import cover_gen
                cr = cover_gen.generate_cover(book)
                sp = cr.get("svg_path", "")
                if sp and _os.path.exists(sp):
                    raw = Path(sp).read_text(encoding="utf-8")
                    svg_b64 = base64.b64encode(raw.encode()).decode()
                    cover_preview = f'<img src="data:image/svg+xml;base64,{svg_b64}" style="max-width:100%;border-radius:8px;border:1px solid #1e1e3a">'
                    svg_preview = raw[:2000]
                for v in cr.get("palette", {}).values():
                    if isinstance(v, dict) and "hex" in v:
                        palette_html += f'<div style="display:flex;align-items:center;gap:8px;margin:4px 0"><div style="width:20px;height:20px;border-radius:4px;background:{v["hex"]};border:1px solid #333"></div><span style="font-size:11px;color:#8b949e">{v["name"]} {v["hex"]} - {v["role"]}</span></div>'
            except:
                palette_html = "封面生成失敗"

    book_opts = "\n".join(f'<option value="{b["id"]}">{b["icon"]} {b["title"][:40]}</option>' for b in books)

    return f"""<!DOCTYPE html>
<html lang="zh-TW"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>視覺 | 黑曜</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Inter',-apple-system,sans-serif;background:#0a0a0f;color:#e0e0e0;min-height:100vh}}
.header{{background:#111122;border-bottom:1px solid #1e1e3a;padding:16px 24px;display:flex;justify-content:space-between;align-items:center}}
.header h1{{font-size:20px;color:#58a6ff}}
.header a{{color:#8b949e;text-decoration:none;font-size:13px;margin-left:12px}}
.card{{background:#111122;border:1px solid #1e1e3a;border-radius:12px;padding:20px;margin:16px 24px}}
.card h3{{font-size:13px;color:#8b949e;text-transform:uppercase;margin-bottom:12px}}
select,button{{padding:8px 12px;background:#0d0d1a;border:1px solid #1e1e3a;border-radius:6px;color:#e0e0e0;font-size:13px}}
button{{background:#238636;cursor:pointer}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:16px;padding:0 24px}}
pre{{background:#0d0d1a;padding:12px;border-radius:6px;overflow-x:auto;font-size:11px}}
</style></head><body>
<div class="header">
  <div><h1>🎨 視覺審查</h1><span style="font-size:12px;color:#8b949e">{NOW}</span></div>
  <div>
    <a href="/topics?token={token}">🎯 選題</a>
    <a href="/ads?token={token}">📣 廣告</a>
    <a href="/publish-dashboard?token={token}">📤 上架</a>
    <a href="/?token={token}">🏠 首頁</a>
  </div>
</div>
<div class="card">
  <h3>選擇已通過選題</h3>
  <form method="get" style="display:flex;gap:12px;align-items:center">
    <input type="hidden" name="token" value="{token}">
    <select name="book_id">{book_opts}</select>
    <button type="submit">🎨 生成封面預覽</button>
  </form>
</div>
<div class="grid2">
  <div class="card"><h3>📔 封面: {book_title}</h3>{cover_preview if cover_preview else '<div style="color:#8b949e;padding:20px">選擇一本書預覽封面</div>'}</div>
  <div class="card"><h3>🎨 色彩</h3>{palette_html if palette_html else '<div style="color:#8b949e;padding:20px">選擇一本書</div>'}</div>
</div>
<div class="card"><h3>📐 SVG 預覽</h3><pre>{svg_preview if svg_preview else '尚無封面'}</pre></div>
<div style="text-align:center;padding:20px;color:#484f58;font-size:11px">AMPM 品牌引擎 · 5色/4場景/6封面模板</div>
</body></html>"""


@app.route("/ads")
def ads_dashboard():
    NOW = __import__("time").strftime("%Y-%m-%d %H:%M:%S")
    token = request.args.get("token", "")
    try:
        from visual.ad_campaign_manager import ad_campaign_mgr
        campaigns = ad_campaign_mgr.list_campaigns()
        summary = ad_campaign_mgr.summary()
    except:
        campaigns, summary = [], {"total_campaigns": 0, "active": 0, "total_spend": 0}

    camp_rows = ""
    for c in campaigns[-10:]:
        sc = {"active": "#3fb950", "paused": "#d29922"}.get(c.get("status", ""), "#8b949e")
        camp_rows += f'<tr><td style="font-size:10px">{c["id"][:10]}</td><td>{c["book_title"][:30]}</td><td style="color:{sc}">{c.get("status","?")}</td><td>${c.get("spent",0):.2f}</td></tr>'

    return f"""<!DOCTYPE html>
<html lang="zh-TW"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>廣告 | 黑曜</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Inter',-apple-system,sans-serif;background:#0a0a0f;color:#e0e0e0;min-height:100vh}}
.header{{background:#111122;border-bottom:1px solid #1e1e3a;padding:16px 24px;display:flex;justify-content:space-between;align-items:center}}
.header h1{{font-size:20px;color:#58a6ff}}
.header a{{color:#8b949e;text-decoration:none;font-size:13px;margin-left:12px}}
.card{{background:#111122;border:1px solid #1e1e3a;border-radius:12px;padding:20px;margin:16px 24px}}
.card h3{{font-size:13px;color:#8b949e;text-transform:uppercase;margin-bottom:12px}}
table{{width:100%;border-collapse:collapse;font-size:12px}}
th{{text-align:left;color:#8b949e;padding:6px 8px;border-bottom:1px solid #1e1e3a}}
td{{padding:6px 8px;border-bottom:1px solid #111122}}
</style></head><body>
<div class="header">
  <div><h1>📣 廣告管理</h1><span style="font-size:12px;color:#8b949e">活動:{summary["total_campaigns"]} 活躍:{summary["active"]} 花費:${summary["total_spend"]:.2f}</span></div>
  <div>
    <a href="/topics?token={token}">🎯 選題</a>
    <a href="/visual?token={token}">🎨 視覺</a>
    <a href="/publish-dashboard?token={token}">📤 上架</a>
    <a href="/?token={token}">🏠 首頁</a>
  </div>
</div>
<div class="card"><h3>廣告活動</h3><table><tr><th>ID</th><th>書名</th><th>狀態</th><th>花費</th></tr>{camp_rows if camp_rows else '<tr><td colspan="4" style="color:#8b949e">尚無活動</td></tr>'}</table></div>
<div style="text-align:center;padding:20px;color:#484f58;font-size:11px">AMPM 廣告 · 9平台素材自動生成</div>
</body></html>"""


@app.route("/publish-dashboard")
def publish_dashboard():
    NOW = __import__("time").strftime("%Y-%m-%d %H:%M:%S")
    token = request.args.get("token", "")
    try:
        from visual.publish_engine import publish_engine
        platforms = publish_engine.get_platform_status()
        log = publish_engine.recent_log(20)
    except:
        platforms, log = {}, []

    plat_rows = ""
    for k, p in platforms.items():
        ready = p.get("ready", False)
        color = "#3fb950" if ready else "#d29922" if p.get("creds_ok") else "#e94560"
        plat_rows += f'<tr><td>{p["icon"]} {p["name"]}</td><td style="color:{color}">{p["status"]}</td><td>{"✅" if ready else "🔧"}</td><td>{p.get("royalty","?")}</td></tr>'

    log_rows = ""
    for l in log[-15:]:
        ok = l.get("ok", False)
        log_rows += f'<tr><td style="font-size:10px">{(l.get("ts",""))[5:19]}</td><td>{l.get("title","?")[:30]}</td><td>{l.get("platform_name","?")}</td><td style="color:{"#3fb950" if ok else "#e94560"}">{"✅" if ok else "❌"}</td></tr>'
    if not log_rows:
        log_rows = '<tr><td colspan="4" style="color:#8b949e">尚無上架紀錄</td></tr>'

    return f"""<!DOCTYPE html>
<html lang="zh-TW"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>上架 | 黑曜</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Inter',-apple-system,sans-serif;background:#0a0a0f;color:#e0e0e0;min-height:100vh}}
.header{{background:#111122;border-bottom:1px solid #1e1e3a;padding:16px 24px;display:flex;justify-content:space-between;align-items:center}}
.header h1{{font-size:20px;color:#58a6ff}}
.header a{{color:#8b949e;text-decoration:none;font-size:13px;margin-left:12px}}
.card{{background:#111122;border:1px solid #1e1e3a;border-radius:12px;padding:20px;margin:16px 24px}}
.card h3{{font-size:13px;color:#8b949e;text-transform:uppercase;margin-bottom:12px}}
table{{width:100%;border-collapse:collapse;font-size:12px}}
th{{text-align:left;color:#8b949e;padding:6px 8px;border-bottom:1px solid #1e1e3a}}
td{{padding:6px 8px;border-bottom:1px solid #111122}}
</style></head><body>
<div class="header">
  <div><h1>📤 上架管理</h1><span style="font-size:12px;color:#8b949e">10 書商 · {NOW}</span></div>
  <div>
    <a href="/topics?token={token}">🎯 選題</a>
    <a href="/visual?token={token}">🎨 視覺</a>
    <a href="/ads?token={token}">📣 廣告</a>
    <a href="/?token={token}">🏠 首頁</a>
  </div>
</div>
<div class="card"><h3>📡 Top 10 書商狀態</h3><table><tr><th>平台</th><th>狀態</th><th>自動化</th><th>版稅</th></tr>{plat_rows}</table></div>
<div class="card"><h3>📋 上架紀錄</h3><table><tr><th>時間</th><th>書名</th><th>平台</th><th>結果</th></tr>{log_rows}</table></div>
<div style="text-align:center;padding:20px;color:#484f58;font-size:11px">AMPM · Playwright自動化</div>
</body></html>"""


# ═══ Kanban 看板 + 批次採用 + 校稿頁 ═══

@app.route("/pipeline")
def pipeline_kanban():
    """10 欄 Kanban 看板 — 每本書所在階段和器官"""
    from pipeline_data import store
    from pipeline_presets import PRODUCT_TYPES, STAGE_LABELS
    token = request.args.get("token", "")
    NOW = __import__("time").strftime("%Y-%m-%d %H:%M")

    books = store.books

    stage_map = {i: [] for i in [1, 2, 3, 4, 5, 6, 7, 7.5, 8, 9, 10]}
    organ_icons = {1: "🎯", 2: "🧠", 3: "📋", 4: "✍️", 5: "🔍", 6: "🎨", 7: "📐", 7.5: "🔬", 8: "⏸️", 9: "📤", 10: "📣"}
    organ_names = {1: "選題", 2: "研究", 3: "大綱", 4: "撰寫", 5: "編輯", 6: "美術", 7: "排版", 7.5: "校稿", 8: "審核", 9: "上架", 10: "行銷"}
    for b in books:
        s = b.get("current_stage", 1)
        pt = PRODUCT_TYPES.get(b.get("product_type", "ebook"), {})
        title = b["stage_data"].get("1", {}).get("title", "?")[:20]
        approved = b["stage_data"].get("1", {}).get("approved", False)
        rejected = b["stage_data"].get("8", {}).get("rejected", False)
        status = "⏸️" if (s == 1 and not approved) else ("↩️駁回" if rejected else "🔄")
        if s not in stage_map:
            stage_map[s] = []
        stage_map[s].append({
            "id": b["id"], "title": title, "status": status,
            "icon": pt.get("icon", "📚"),
        })

    columns = ""
    for s in [1, 2, 3, 4, 5, 6, 7, 7.5, 8, 9, 10]:
        cards = stage_map.get(s, [])
        col_color = "#3fb950" if s in (1, 8) else "#1e1e3a"
        cards_html = ""
        for c in cards:
            review_link = f'/review/{c["id"]}?token={token}' if s == 8 else ''
            review_tag = (' <a href="' + review_link + '" style="color:#58a6ff;font-size:10px">審核</a>') if review_link else ''
            cards_html += (
                '<div style="background:#1a1a2e;border:1px solid #333;border-radius:6px;padding:8px;margin:4px 0;font-size:11px">'
                + c["icon"] + ' ' + c["title"] + '<br>'
                + '<span style="color:#8b949e">' + c["status"] + '</span>'
                + review_tag
                + '</div>'
            )
        empty_div = '<div style="color:#8b949e;font-size:10px;padding:8px">—</div>'
        cards_display = cards_html if cards_html else empty_div
        columns += (
            '<div style="flex:1;min-width:120px;background:#111122;border:1px solid ' + col_color + ';border-radius:8px;padding:10px;margin:4px">'
            + '<div style="font-size:11px;color:#58a6ff;font-weight:bold;margin-bottom:6px">' + str(organ_icons[s]) + ' Stage ' + str(s) + '<br>' + str(organ_names[s]) + '</div>'
            + cards_display
            + '</div>'
        )

    return f"""<!DOCTYPE html>
<html lang="zh-TW"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>管線 Kanban | 黑曜</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Inter',system-ui,sans-serif;background:#0a0a0f;color:#e0e0e0;min-height:100vh}}
.header{{background:#111122;border-bottom:1px solid #1e1e3a;padding:12px 20px;display:flex;justify-content:space-between;align-items:center}}
.header h1{{font-size:18px;color:#58a6ff}}
.header a{{color:#8b949e;text-decoration:none;font-size:12px;margin-left:12px}}
.kanban{{display:flex;gap:4px;padding:12px;overflow-x:auto}}
</style></head><body>
<div class="header"><div><h1>📊 出版管線 Kanban</h1><span style="font-size:11px;color:#8b949e">{NOW}</span></div>
<div><a href="/topics?token={token}">🎯選題</a><a href="/?token={token}">🏠首頁</a></div></div>
<div class="kanban">{columns}</div>
<div style="text-align:center;padding:16px;color:#484f58;font-size:10px">10.5 Stage · 即時同步 · 每5秒自動更新</div>
{LIVESYNC_JS}
<script>
function updateLive(d){{
  if(!d.books) return;
  d.books.forEach(function(b){{
    var el = document.getElementById('card-'+b.id);
    if(el){{
      el.querySelector('.stage-badge').textContent = 'S'+b.stage;
      el.querySelector('.progress-bar').style.width = b.progress_pct+'%';
    }}
  }});
}}
</script>
</body></html>"""


@app.route("/review/<book_id>")
def review_page(book_id):
    """人工校稿頁面：完整內容 + 駁回原因輸入 + 通過/駁回按鈕"""
    from pipeline_data import store
    from pipeline_presets import PRODUCT_TYPES
    token = request.args.get("token", "")

    book = store.get(book_id)
    if not book:
        return "❌ 找不到書籍", 404

    title = book["stage_data"].get("1", {}).get("title", "?")
    pt = PRODUCT_TYPES.get(book.get("product_type", "ebook"), {})
    content = book["stage_data"].get("4", {}).get("content", "尚無內容")
    outline = book["stage_data"].get("3", {}).get("outline", "")
    editing = book["stage_data"].get("5", {})
    art = book["stage_data"].get("6", {})
    layout = book["stage_data"].get("7", {})
    proof = book["stage_data"].get("7_5", {}) or book["stage_data"].get("7.5", {})
    review_data = book["stage_data"].get("8", {})
    rejected = review_data.get("rejected", False)
    prev_reason = review_data.get("rejection_reason", "")
    stage = book.get("current_stage", 1)
    issues = editing.get("issues", [])
    score = editing.get("quality_score", 0)
    retry_key = proof.get("retry_key", "")

    # 校稿報告區塊
    proof_html = ""
    if proof and proof.get("checks"):
        grade_colors = {"pass": "#3fb950", "suggest": "#d29922", "minor_fix": "#e94f20", "major_fix": "#e94560", "human_decision": "#e94560"}
        gc = grade_colors.get(proof.get("grade", ""), "#8b949e")
        proof_html = (
            '<div class="card"><h3>🔬 專業校稿報告 '
            f'(<span style="color:{gc};font-weight:bold">{proof.get("grade_label","")} {proof.get("overall",0)}/100</span>)</h3>'
            + '<table style="margin-top:8px"><tr><th>檢查項</th><th>分數</th><th>問題</th></tr>'
            + "".join(
                f'<tr><td>{c["name"]}</td><td style="color:{"#3fb950" if c["score"]>=80 else "#d29922" if c["score"]>=60 else "#e94560"}">{c["score"]}</td>'
                f'<td style="font-size:10px;color:#8b949e">{"; ".join(c.get("issues",[])[:3]) or "—"}</td></tr>'
                for c in proof.get("checks", [])
            )
            + "</table>"
        )
        if retry_key:
            retry_st = proof.get("return_to_stage", "?")
            proof_html += f'<div style="font-size:10px;color:#e94560;margin-top:4px">⚠️ 駁回建議：退回 Stage {retry_st} 重跑（{retry_key}）</div>'
        if proof.get("retry_count", 0) > 0:
            proof_html += f'<div style="font-size:10px;color:#8b949e;margin-top:4px">重試次數: {proof["retry_count"]}</div>'
        proof_html += '</div>'

    # 駁回歷程
    retry_history = ""
    try:
        from proofreader import proofreader
        rs = proofreader.get_retry_status(book_id)
        if rs["retries"]:
            retry_history = (
                '<div class="card"><h3>📋 駁回歷程</h3><table style="margin-top:8px">'
                + "".join(
                    f'<tr><td>{k}</td><td>{v} 次</td><td>上限 {rs["limits"].get(k, "?")}</td></tr>'
                    for k, v in rs["retries"].items()
                )
                + f'<tr><td colspan="3" style="font-size:10px;color:#8b949e">總計 {rs["total"]} 次駁回</td></tr></table></div>'
            )
    except:
        pass

    return f"""<!DOCTYPE html>
<html lang="zh-TW"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>校稿: {title[:20]} | 黑曜</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Inter',system-ui,sans-serif;background:#0a0a0f;color:#e0e0e0;min-height:100vh}}
.header{{background:#111122;border-bottom:1px solid #1e1e3a;padding:14px 20px;display:flex;justify-content:space-between;align-items:center}}
.header h1{{font-size:16px;color:#58a6ff}}
.btn{{padding:8px 16px;border-radius:6px;font-size:12px;border:none;cursor:pointer;text-decoration:none}}
.btn-ok{{background:#238636;color:#fff}}
.btn-reject{{background:#e94560;color:#fff}}
.card{{background:#111122;border:1px solid #1e1e3a;border-radius:10px;padding:16px;margin:12px 16px}}
.card h3{{font-size:12px;color:#8b949e;text-transform:uppercase;margin-bottom:8px}}
.content{{background:#0d0d1a;padding:16px;border-radius:8px;white-space:pre-wrap;font-size:13px;line-height:1.7;max-height:500px;overflow-y:auto}}
textarea{{width:100%;background:#0d0d1a;border:1px solid #333;border-radius:6px;color:#e0e0e0;padding:10px;font-size:12px;resize:vertical;margin:8px 0}}
.info{{display:flex;gap:16px;flex-wrap:wrap;font-size:11px;color:#8b949e;margin-bottom:12px}}
</style></head><body>
<div class="header">
  <div><h1>📖 校稿: {title[:30]}</h1><span style="font-size:11px;color:#8b949e">{pt.get('icon','')} {pt.get('label','')} | Stage {stage}/10</span></div>
  <div><a href="/pipeline?token={token}" style="color:#8b949e;font-size:12px">← Kanban</a></div>
</div>

<div class="card">
  <div class="info">
    <span>品質分: {score}</span>
    <span>問題: {'; '.join(issues) if issues else '無'}</span>
    <span>美術: {'✅' if art else '❌'}</span>
    <span>排版: {'✅' if layout.get('output') else '❌'}</span>
    {"<span style='color:#e94560'>⚠️ 曾駁回: "+prev_reason[:60]+"</span>" if rejected else ""}
  </div>
  <h3>目錄</h3>
  <div class="content">{outline[:2000] if outline else "（無目錄）"}</div>
</div>

{proof_html}
{retry_history}

<div class="card">
  <h3>內文預覽</h3>
  <div class="content">{content[:3000] if content else "（尚無內容）"}</div>
</div>

<div class="card">
  <h3>審核決定</h3>
  <form method="get" action="/api/review-action/{book_id}" style="display:flex;flex-direction:column;gap:8px">
    <input type="hidden" name="token" value="{token}">
    <textarea name="reason" rows="2" placeholder="駁回原因（通過則留空）">{prev_reason}</textarea>
    <div style="display:flex;gap:12px">
      <button type="submit" name="action" value="approve" class="btn btn-ok">✅ 通過 → 上架</button>
      <button type="submit" name="action" value="reject_write" class="btn btn-reject">✗ 駁回 → 重寫 (Stage 4)</button>
      <button type="submit" name="action" value="reject_art" class="btn btn-reject">✗ 駁回 → 重做美術 (Stage 6)</button>
    </div>
  </form>
  {"<div style='font-size:11px;color:#8b949e;margin-top:8px'>上一次駁回：" + prev_reason[:200] + "</div>" if rejected else ""}
</div>
</body></html>"""


@app.route("/api/review-action/<book_id>")
def api_review_action(book_id):
    from pipeline_engine import engine
    from pipeline_data import store
    action = request.args.get("action", "approve")
    reason = request.args.get("reason", "")
    token = request.args.get("token", "")

    if action == "approve":
        engine.advance_to_published(book_id)
        msg = f"✅ 審核通過，已自動上架官網+外部平台"
    elif action == "reject_write":
        msg = engine.retry_from_stage(book_id, 4, reason)
    elif action == "reject_art":
        msg = engine.retry_from_stage(book_id, 6, reason)
    else:
        msg = "未知操作"

    return f"""<html><head><meta charset="utf-8"><meta http-equiv="refresh" content="1;url=/pipeline?token={token}"></head>
<body style="background:#0a0a0f;color:#e0e0e0;font-family:sans-serif;padding:40px;text-align:center">
<h2>{msg}</h2></body></html>"""


@app.route("/api/batch-approve", methods=["POST"])
def api_batch_approve():
    from pipeline_engine import engine
    data = request.get_json(silent=True) or {}
    ids = data.get("ids", [])
    results = []
    for bid in ids:
        results.append(engine.approve_topic(bid, auto_advance=True))
    return jsonify({"ok": True, "results": results})


@app.route("/brand-logo")
def brand_logo():
    from flask import send_file
    logo = Path(__file__).resolve().parent.parent.parent / "assets" / "logo_main.png"
    if logo.exists():
        return send_file(logo, mimetype="image/png")
    return "no logo", 404


@app.route("/outputs/brand/<path:filename>")
def serve_brand_file(filename):
    brand_dir = Path(__file__).resolve().parent.parent.parent / "assets"
    safe = (brand_dir / filename).resolve()
    if not str(safe).startswith(str(brand_dir.resolve())):
        return "", 404
    if not safe.exists():
        return "", 404
    from flask import send_file
    return send_file(str(safe))


@app.route("/outputs/covers/<path:filename>")
def serve_cover_file(filename):
    covers_dir = Path(__file__).resolve().parent.parent.parent / "outputs" / "covers"
    safe = (covers_dir / filename).resolve()
    if not str(safe).startswith(str(covers_dir.resolve())):
        return "", 404
    if not safe.exists():
        return "", 404
    from flask import send_file
    return send_file(str(safe))


@app.route("/outputs/compiled/<path:filename>")
def serve_compiled_file(filename):
    compiled_dir = Path(__file__).resolve().parent.parent.parent / "outputs" / "compiled"
    safe = (compiled_dir / filename).resolve()
    if not str(safe).startswith(str(compiled_dir.resolve())):
        return "", 404
    if not safe.exists():
        return "", 404
    from flask import send_file
    return send_file(str(safe), as_attachment=(filename.endswith('.epub')))


# ═══ LiveSync — 即時同步層 ═══

@app.route("/api/pipeline-live")
def api_pipeline_live():
    """單一 API — 回傳所有書+器官+事件的即時狀態（強制讀取最新 books.json）"""
    from pipeline_data import BookStore
    store = BookStore()  # 強制重新讀取
    from pipeline_presets import PRODUCT_TYPES, STAGE_LABELS
    books_data = []
    for b in store.books:
        pt = PRODUCT_TYPES.get(b.get("product_type", "ebook"), {})
        s = b.get("current_stage", 1)
        proof = b["stage_data"].get("7.5", {}) or b["stage_data"].get("7_5", {})
        books_data.append({
            "id": b["id"][:12],
            "title": b["stage_data"].get("1", {}).get("title", "?")[:30],
            "icon": pt.get("icon", "📚"),
            "type": pt.get("label", ""),
            "stage": s,
            "stage_label": STAGE_LABELS.get(int(s) if isinstance(s, (int,float)) and s == int(s) else s, "?"),
            "approved": b["stage_data"].get("1", {}).get("approved", False),
            "published": b.get("status") == "published",
            "grade": proof.get("grade_label", ""),
            "overall": proof.get("overall", 0),
            "progress_pct": min(100, int(s * 10)),
        })

    org_data = {}
    try:
        from pipeline_orchestrator import orchestrator
        st = orchestrator.get_organ_status()
        org_data = st
    except: pass

    return jsonify({
        "books": books_data,
        "organs": org_data,
        "updated_at": __import__("time").strftime("%H:%M:%S"),
    })


LIVESYNC_JS = """
<script>
(function(){
  var token = new URLSearchParams(location.search).get('token') || '';
  function fetchLive(){
    fetch('/api/pipeline-live').then(r=>r.json()).then(d=>{
      if(window.updateLive) updateLive(d);
    }).catch(()=>{});
  }
  fetchLive();
  setInterval(fetchLive, 5000);
})();
</script>"""


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=False)


# ═══ CRM / 客戶關係路由 ═══

@app.route("/account")
def account_page():
    token = request.args.get("token", "")
    logo_path = Path(__file__).resolve().parent.parent.parent / "assets" / "logo_main.png"
    return f"""<!DOCTYPE html><html lang="zh-TW"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>我的帳戶 | AM&PM</title><style>body{{font-family:'Inter',sans-serif;background:#F5F0E8;color:#000;min-height:100vh;max-width:600px;margin:0 auto;padding:32px}}h2{{font-family:'Oswald',sans-serif}}input{{width:100%;padding:10px;margin:8px 0;border:1px solid #ddd;border-radius:6px;font-size:14px}}button{{padding:10px 24px;background:#000;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:14px}}.card{{background:#fff;border-radius:10px;padding:20px;margin:16px 0;box-shadow:0 2px 8px rgba(0,0,0,0.06)}}.shelf-item{{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #eee;font-size:13px}}</style></head><body>
<h2>📚 我的帳戶</h2>
<div class="card"><h3>註冊 / 登入</h3><form onsubmit="login(event)"><input type="email" id="email" placeholder="你的 Email" required><input type="text" id="name" placeholder="名稱 (選填)"><button type="submit">進入</button></form></div>
<div class="card" id="shelf-card" style="display:none"><h3>📖 我的書架</h3><div id="shelf"></div></div>
<div class="card"><h3>⭐ 寫書評賺點數</h3><form onsubmit="submitReview(event)"><input type="text" id="book-id" placeholder="書籍 ID"><input type="number" id="rating" placeholder="評分 1-5" min="1" max="5"><textarea id="comment" placeholder="簡短評論" rows="2" style="width:100%;margin:8px 0;padding:8px;border:1px solid #ddd;border-radius:4px"></textarea><button type="submit">送出 (賺 $3)</button></form></div>
<div class="card"><h3>🔗 推薦好友</h3><p id="ref-code" style="font-family:monospace;font-size:14px"></p><p style="font-size:11px;color:#666">雙方獲 $5 折扣點數</p></div>
<script>
function login(e){{e.preventDefault();var email=document.getElementById('email').value;fetch('/api/crm/register',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{email:email,name:document.getElementById('name').value}})}}).then(r=>r.json()).then(d=>{{if(d.ok){{document.getElementById('ref-code').textContent='你的推薦碼: '+d.referral_code;loadShelf(email)}}else{{alert(d.error)}}}})}}
function loadShelf(email){{fetch('/api/crm/bookshelf?email='+email).then(r=>r.json()).then(d=>{{var s='';d.books.forEach(function(b){{s+='<div class=shelf-item><span>'+b.book_id.substr(0,12)+'...</span><span>'+b.purchased_at.substr(0,10)+'</span><a href=/store/download/'+b.delivery_token+'?id='+b.book_id+'>⬇下載</a></div>'}});document.getElementById('shelf').innerHTML=s||'尚無購買';document.getElementById('shelf-card').style.display='block'}})}}
function submitReview(e){{e.preventDefault();var email=document.getElementById('email').value;fetch('/api/crm/review',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{email:email,book_id:document.getElementById('book-id').value,rating:parseInt(document.getElementById('rating').value),comment:document.getElementById('comment').value}})}}).then(r=>r.json()).then(d=>{{alert(d.ok?'✅ 獲得 $'+d.credits_earned+' 點數！':'❌ 失敗')}})}}
</script></body></html>"""


@app.route("/api/crm/register", methods=["POST"])
def api_crm_register():
    from crm_engine import crm
    data = request.get_json(silent=True) or {}
    email = data.get("email", "")
    name = data.get("name", "")
    if not email:
        return jsonify({"ok": False})
    result = crm.register(email, name)
    return jsonify(result)


@app.route("/api/crm/bookshelf")
def api_crm_bookshelf():
    from crm_engine import crm
    email = request.args.get("email", "")
    if not email:
        return jsonify({"books": []})
    return jsonify({"books": crm.get_bookshelf(email)})


@app.route("/api/crm/review", methods=["POST"])
def api_crm_review():
    from crm_engine import crm
    data = request.get_json(silent=True) or {}
    email = data.get("email", "")
    book_id = data.get("book_id", "")
    rating = int(data.get("rating", 3))
    comment = data.get("comment", "")
    result = crm.submit_review(email, book_id, rating, comment)
    return jsonify(result)


# ═══ 器官健康 + 平台設定 ═══

@app.route("/organs")
def organs_dashboard():
    token = request.args.get("token", "")
    NOW = __import__("time").strftime("%Y-%m-%d %H:%M")
    rows = ""
    try:
        from pipeline_orchestrator import orchestrator
        st = orchestrator.get_organ_status()
        for org, info in st.get("by_organ", {}).items():
            rows += f'<tr><td>🧬 {org}</td><td>{info.get("last_action","—")}</td><td>{info.get("count",0)}</td><td>S{info.get("last_stage",0)}</td></tr>'
    except:
        rows = '<tr><td colspan="4">尚未有器官活動</td></tr>'
    return f"""<!DOCTYPE html><html lang="zh-TW"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>器官狀態 | AMPM</title><style>
*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:'Inter',sans-serif;background:#0a0a0f;color:#e0e0e0;min-height:100vh}}
.header{{background:#111122;padding:16px 24px;display:flex;justify-content:space-between}}
.header h1{{font-size:18px;color:#58a6ff}}.card{{background:#111122;border:1px solid #1e1e3a;border-radius:12px;padding:20px;margin:16px 24px}}
table{{width:100%;border-collapse:collapse;font-size:12px}}th{{text-align:left;color:#8b949e;padding:6px 8px;border-bottom:1px solid #1e1e3a}}td{{padding:6px 8px;border-bottom:1px solid #111122}}
</style></head><body>
<div class="header"><h1>🧬 器官健康儀表板</h1><a href="/?token={token}" style="color:#8b949e;font-size:13px;text-decoration:none">← 返回</a></div>
<div class="card"><h3>{st.get('organs_loaded',0)}/{st.get('organs_total',0)} 活躍器官</h3><table><tr><th>器官</th><th>最後操作</th><th>次數</th><th>Stage</th></tr>{rows}</table></div>
<div style="text-align:center;padding:20px;color:#484f58;font-size:10px">{NOW} · AMPM 器官系統</div></body></html>"""


@app.route("/setup-platforms")
def setup_platforms():
    token = request.args.get("token", "")
    from platform_onboarding import onboarding
    platforms = onboarding.get_all_status()
    rows = ""
    for p in platforms:
        icon = {"ready": "🟢", "need_setup": "🔴"}.get(p["status"], "⚫")
        rows += f'<tr><td>{p["icon"]} {p["name"]}</td><td>{icon} {p["status"]}</td><td>{p["royalty"]}</td><td><a href="/api/setup-guide/{p["key"]}?token={token}" style="color:#58a6ff;font-size:10px">申請導引</a></td></tr>'
    return f"""<!DOCTYPE html><html lang="zh-TW"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>平台設定 | AMPM</title><style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:'Inter',sans-serif;background:#0a0a0f;color:#e0e0e0}} .header{{background:#111122;padding:16px 24px}}h1{{font-size:18px;color:#58a6ff}}.card{{background:#111122;border:1px solid #1e1e3a;border-radius:12px;padding:20px;margin:16px 24px}}table{{width:100%;border-collapse:collapse;font-size:12px}}th{{text-align:left;color:#8b949e;padding:6px 8px;border-bottom:1px solid #1e1e3a}}td{{padding:6px 8px}}</style></head><body>
<div class="header"><h1>📡 平台上架設定</h1><a href="/?token={token}" style="color:#8b949e;font-size:13px;text-decoration:none">← 返回</a></div>
<div class="card"><table><tr><th>平台</th><th>狀態</th><th>版稅</th><th></th></tr>{rows}</table></div>
<div style="text-align:center;padding:20px;color:#484f58;font-size:10px">完成驗證後 Telegram 回 /verify &lt;平台&gt; 儲存憑證</div></body></html>"""


@app.route("/api/setup-guide/<platform_key>")
def api_setup_guide(platform_key):
    from platform_onboarding import onboarding
    guide = onboarding.get_setup_guide(platform_key)
    token = request.args.get("token", "")
    return f"""<!DOCTYPE html><html lang="zh-TW"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>申請導引 | AMPM</title><style>body{{font-family:'Inter',sans-serif;background:#0a0a0f;color:#e0e0e0;max-width:600px;margin:40px auto;padding:20px;line-height:1.8}}pre{{background:#111122;padding:16px;border-radius:8px;white-space:pre-wrap}}a{{color:#58a6ff}}</style></head><body>
<a href="/setup-platforms?token={token}" style="color:#8b949e">← 返回</a>
<pre>{guide}</pre></body></html>"""

