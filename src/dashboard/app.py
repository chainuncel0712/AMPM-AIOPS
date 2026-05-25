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
  <div>
    <h1>⚙️ 黑曜 Dashboard</h1>
    <span>AMPM-AIOPS · 更新於 {NOW}</span>
  </div>
  <div>
    <a href="/publish?token={request.args.get('token','')}" style="color:#3fb950;text-decoration:none;font-size:13px;margin-right:16px">🚀 上架系統</a>
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


@app.route("/pipeline")
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
