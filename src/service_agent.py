"""
業務 / 客服 / 安裝 / 售後 四個 AI 代理 + 調度器
有記憶、懂客戶、自動推進流程
"""
import json, os, threading, time, re, hashlib, random
from pathlib import Path
from datetime import datetime, timedelta

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"

class CustomerDB:
    def __init__(self):
        self.file = DATA / "customers.json"
        self.file.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._load()

    def _load(self):
        with self._lock:
            if self.file.exists():
                try:
                    self.data = json.loads(self.file.read_text())
                except:
                    self.data = {}
            else:
                self.data = {}

    def _save(self):
        with self._lock:
            self.file.write_text(json.dumps(self.data, ensure_ascii=False, indent=2))

    def _cid(self, cid):
        return str(cid).strip()

    def get(self, cid):
        return self.data.get(self._cid(cid))

    def get_or_create(self, cid):
        cid = self._cid(cid)
        with self._lock:
            if cid not in self.data:
                self.data[cid] = {
                    "name": f"客戶_{cid}", "contact": "", "plan": None, "status": "new",
                    "trial": False, "trial_expires": None, "license_key": None,
                    "payment": {}, "vps": {}, "conversation": [], "tickets": [],
                    "preferences": {"language": "zh", "contact_time": "", "notes": ""},
                    "usage": {"login_count": 0, "last_active": None, "features_used": [], "uptime": 100.0},
                    "created_at": datetime.now().isoformat(), "installed_at": None,
                    "assigned_agent": None
                }
                self._save()
            return self.data[cid]

    def save(self):
        self._save()

db = CustomerDB()

class SalesAgent:
    """業務代理 — 介紹方案、報價、成交"""
    def handle(self, cid, msg):
        c = db.get_or_create(cid)
        m = msg.lower()
        if any(k in m for k in ["方案", "價格", "多少錢", "月", "季", "年", "plan", "price", "pricing"]):
            return (
                "📋 黑曜有四種方案：\n\n"
                "自託管（自備 VPS）：\n"
                "  $15  / 30 天\n"
                "  $39  / 90 天（省 $6）\n"
                "  $120 / 365 天（省 $60）\n\n"
                "雲端版（我們代管，無需 VPS）：\n"
                "  $30  / 30 天\n"
                "  $80  / 90 天（省 $10）\n"
                "  $240 / 365 天（省 $120）\n\n"
                "全部方案功能全開，沒有分級。\n"
                "也有 3 天免費試用，歡迎體驗！\n"
                "👉 ampm-aiops.com"
            )
        if any(k in m for k in ["試用", "trial", "免費", "free"]):
            return "我們提供 3 天免費試用，功能全開。點擊網站上的「開始試用」按鈕，或告訴我您的名稱，我幫您啟用。"
        if any(k in m for k in ["特色", "功能", "能做", "feature", "capability"]):
            return (
                "黑曜不是一般的 AI 聊天機器人，它會：\n\n"
                "  ✅ AI 對話 — 自然聊天\n"
                "  ✅ 長期記憶 — 說過就記住\n"
                "  ✅ 自動跑任務 — 定時執行、回報\n"
                "  ✅ 讀檔案 — PDF、Word、Excel\n"
                "  ✅ 上網查資料 — 爬蟲、分析\n"
                "  ✅ 多子代理 — 同時處理多件事\n"
                "  ✅ AI 客服 + 安裝 — 幫客戶部署\n\n"
                "想像力，就是你的超能力。"
            )
        if c.get("status") == "new":
            c["name"] = msg.split()[0] if msg.split() else msg[:20]
            c["status"] = "chatting"
            db.save()
            return f"您好 {c['name']}，我是黑曜業務代表。\n\n您想先了解方案價格，還是直接體驗 3 天試用？"
        return (
            "我是黑曜業務代表，我可以為您介紹：\n"
            "  • 方案與價格\n"
            "  • 功能特色\n"
            "  • 免費試用\n\n"
            "您想了解哪個？"
        )

class SupportAgent:
    """客服代理 — 回答問題、處理客訴、引導流程"""
    def handle(self, cid, msg):
        c = db.get_or_create(cid)
        m = msg.lower()
        if any(k in m for k in ["付款", "怎麼買", "購買", "pay", "usdt", "paypal"]):
            return (
                "💳 付款方式：\n\n"
                "1. USDT BEP20 — 掃 QR Code 或複製錢包地址轉帳\n"
                "2. PayPal / 信用卡 — 點擊網站上的 PayPal 按鈕\n\n"
                "付款後請告知，客服會立即確認。"
            )
        if any(k in m for k in ["安裝", "部署", "怎麼裝", "主機", "vps"]):
            return (
                "🔧 安裝流程：\n\n"
                "1. 付款完成後告訴我\n"
                "2. 提供您的主機 IP 和 SSH 帳號\n"
                "3. 黑曜 AI 安裝代理人會自動遠端部署\n"
                "4. 約 30 分鐘內完成\n\n"
                "您不用懂技術，我們幫您處理。"
            )
        if any(k in m for k in ["售後", "問題", "故障", "錯誤", "不能", "壞", "error"]):
            return (
                "🛠️ 請描述您遇到的問題，我會幫您診斷。\n\n"
                "常見問題：\n"
                "  • Bot 無回應 → 檢查 tmux session\n"
                "  • 記憶不見了 → 檢查 memory/ 目錄\n"
                "  • 模型載入失敗 → 確認 Ollama 狀態\n\n"
                "如果急需處理，也可以開工單，會有技術人員跟進。"
            )
        if "工單" in m or "ticket" in m or "報修" in m:
            ticket = {"id": len(c.get("tickets", [])) + 1, "subject": "客戶回報", "description": msg,
                      "status": "open", "created_at": datetime.now().isoformat(), "resolved_at": None}
            c.setdefault("tickets", []).append(ticket)
            db.save()
            return f"✅ 已建立工單 #{ticket['id']}，技術人員會儘快處理。"
        if "摘要" in m or "summary" in m or "我的資料" in m:
            return f"📋 您的資料：\n{self._summary(cid)}"
        if c.get("status") == "new":
            c["name"] = msg.split()[0] if msg.split() else msg[:20]
            c["status"] = "chatting"
            db.save()
            return f"您好 {c['name']}，我是黑曜客服。有什麼可以幫您的？"
        return "您好，我是黑曜客服。有什麼可以幫您的？"

    def _summary(self, cid):
        c = db.get(cid)
        if not c:
            return "找不到資料"
        return (
            f"  姓名: {c.get('name','?')}\n"
            f"  方案: {c.get('plan','未選擇')}\n"
            f"  狀態: {c.get('status','new')}\n"
            f"  主機: {c.get('vps',{}).get('ip','未部署')}\n"
            f"  使用次數: {c['usage']['login_count']} 次"
        )

class InstallAgent:
    """安裝代理 — 收集主機資訊、產生部署腳本"""
    def handle(self, cid, msg):
        c = db.get_or_create(cid)
        m = msg.lower()

        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        ips = re.findall(ip_pattern, m)

        if ips:
            ip = ips[0]
            user = "root"
            if "@" in m:
                parts = m.split("@")
                user = parts[0].strip()
            port = 22
            port_match = re.search(r'port\s*[:：]?\s*(\d+)', m, re.IGNORECASE)
            if port_match:
                port = int(port_match.group(1))
            c["vps"] = {"ip": ip, "user": user, "port": port, "collected_at": datetime.now().isoformat()}
            c["status"] = "ready_for_install"
            db.save()
            return f"收到！主機 {ip}:{port}，使用者 {user}。正在準備安裝腳本，請稍候……"

        if c.get("vps", {}).get("ip"):
            if any(k in m for k in ["裝", "開始", "go", "deploy", "run"]):
                return self._generate(cid)
            return (
                f"已記錄您的主機 {c['vps']['ip']}。\n"
                "要現在開始安裝嗎？回覆「開始安裝」即可。"
            )

        return (
            "🔧 要為您部署黑曜，請提供以下資訊：\n\n"
            "  • 主機 IP 地址\n"
            "  • SSH 使用者名稱（預設 root）\n"
            "  • SSH 連接埠（預設 22）\n\n"
            "範例：root@192.168.1.1 port 22\n\n"
            "收到後我會自動產生安裝腳本。"
        )

    def _generate(self, cid):
        c = db.get(cid)
        if not c or not c.get("vps", {}).get("ip"):
            return "請先提供主機資訊。"
        vps = c["vps"]
        key = hashlib.md5(f"AMPM-{cid}-{random.randint(10000,99999)}-{int(time.time())}".encode()).hexdigest()[:16].upper()
        c["license_key"] = key
        c["status"] = "script_ready"
        db.save()
        return (
            f"✅ 安裝腳本已產生！\n\n"
            f"  目標主機：{vps['ip']}:{vps['port']}\n"
            f"  使用者：{vps['user']}\n"
            f"  授權碼：{key}\n\n"
            f"請在目標主機上執行以下命令：\n\n"
            f"  ssh {vps['user']}@{vps['ip']} -p {vps['port']} \\\n"
            f"    'curl -s https://raw.githubusercontent.com/chainuncel0712/AMPM-AIOPS/main/scripts/deploy.sh | bash'\n\n"
            f"部署完成後黑曜會自動啟動。"
        )

class AfterSalesAgent:
    """售後代理 — 診斷問題、自動修復、開工單"""
    def handle(self, cid, msg):
        c = db.get_or_create(cid)
        m = msg.lower()

        if not c.get("vps", {}).get("ip"):
            return "您目前還沒有安裝黑曜。要先購買或試用嗎？"

        if any(k in m for k in ["ping", "活著", "在嗎", "status", "狀態"]):
            return "✅ 系統運行中。如需詳細狀態，請輸入 /status。"

        if any(k in m for k in ["重啟", "restart", "reboot"]):
            return "🔄 正在嘗試重新啟動黑曜服務……\n請稍候，約 30 秒後會恢復。"

        if any(k in m for k in ["慢", "lag", "卡", "頓"]):
            return (
                "⚡ 效能診斷：\n\n"
                "可能原因：\n"
                "  1. CPU 使用率過高 — 檢查有無其他程式佔用\n"
                "  2. 記憶體不足 — 建議關閉不必要的服務\n"
                "  3. 模型回應慢 — 試用較小的模型如 qwen2.5:7b\n\n"
                "需要我幫您進一步檢查嗎？"
            )

        if any(k in m for k in ["更新", "update", "upgrade"]):
            return (
                "🔄 正在檢查更新……\n\n"
                "可執行的更新：\n"
                "  • 黑曜核心 — git pull 即可更新\n"
                "  • Ollama 模型 — ollama pull qwen2.5:14b\n\n"
                "要現在更新嗎？"
            )

        if any(k in m for k in ["資料", "記憶", "memory", "不見", "丟"]):
            return (
                "🧠 記憶系統檢查：\n\n"
                "1. 檢查 ~/.ampm_brain/memory/ 目錄\n"
                "2. 確認 semantic.json / working.json 存在\n"
                "3. 重啟黑曜記憶會自動恢復\n\n"
                "如果還是找不到，我可以幫您復原。"
            )

        return (
            "我是黑曜售後技術支援。\n\n"
            "我可以幫您：\n"
            "  • 檢查系統狀態\n"
            "  • 診斷效能問題\n"
            "  • 重啟服務\n"
            "  • 檢查更新\n"
            "  • 記憶恢復\n\n"
            "請描述您遇到的問題。"
        )

class ServiceDispatcher:
    """調度器 — 根據客戶狀態和訊息分派到對應代理"""
    def __init__(self):
        self.sales = SalesAgent()
        self.support = SupportAgent()
        self.install = InstallAgent()
        self.after = AfterSalesAgent()

    def train(self, cid, topic, content):
        """訓練黑曜 — 記錄特定知識"""
        c = db.get_or_create(cid)
        if "knowledge" not in c:
            c["knowledge"] = {}
        c["knowledge"][topic] = {"content": content, "trained_at": datetime.now().isoformat()}
        db.save()
        return f"✅ 已學習：{topic}"

    def get_knowledge(self, cid, topic=None):
        c = db.get(cid)
        if not c or "knowledge" not in c:
            return ""
        if topic:
            return c["knowledge"].get(topic, {}).get("content", "")
        return c["knowledge"]

    def get_context_for_obsidian(self, cid):
        """黑曜呼叫用 — 回傳客戶摘要文字"""
        c = db.get(cid)
        if not c:
            return "新客戶，尚無資料"
        plan = c.get("plan") or "未選擇"
        status = c.get("status") or "new"
        trial = f"試用中（到期 {c.get('trial_expires','?')}）" if c.get("trial") else "正式版"
        vps = c.get("vps", {}).get("ip") or "未部署"
        license_k = c.get("license_key") or "無"
        return (
            f"客戶: {c.get('name','?')} | "
            f"方案: {plan} | "
            f"狀態: {status} | "
            f"{trial} | "
            f"主機: {vps} | "
            f"授權: {license_k}"
        )

    def log_usage(self, cid, feature):
        """黑曜呼叫用 — 記錄客戶使用的功能"""
        c = db.get_or_create(cid)
        if feature and feature not in c["usage"]["features_used"]:
            c["usage"]["features_used"].append(feature)
        c["usage"]["login_count"] += 1
        c["usage"]["last_active"] = datetime.now().isoformat()
        db.save()

    def route(self, cid, msg):
        c = db.get_or_create(cid)
        m = msg.lower()

        c["usage"]["login_count"] += 1
        c["usage"]["last_active"] = datetime.now().isoformat()
        db.save()

        if c.get("status") in ("ready_for_install", "script_ready"):
            return self.install.handle(cid, msg)

        if c.get("status") == "installed":
            return self.after.handle(cid, msg)

        if any(k in m for k in ["方案", "價格", "多少錢", "特色", "功能", "能做", "trial", "試用", "免費"]):
            return self.sales.handle(cid, msg)

        if any(k in m for k in ["付款", "怎麼買", "購買", "pay", "usdt", "paypal", "主機", "vps", "安裝", "部署"]):
            return self.support.handle(cid, msg)

        if any(k in m for k in ["售後", "問題", "故障", "錯誤", "壞", "重啟", "慢", "更新", "記憶"]):
            return self.after.handle(cid, msg)

        if c.get("status") in ("new", "chatting"):
            return self.sales.handle(cid, msg)

        return self.support.handle(cid, msg)

    def start_trial(self, cid, days=3):
        c = db.get_or_create(cid)
        if c.get("trial") and c.get("trial_expires"):
            remaining = (datetime.fromisoformat(c["trial_expires"]) - datetime.now()).total_seconds()
            if remaining > 0:
                return f"您已在試用期內，還剩 {int(remaining/86400)} 天。"
        expires = (datetime.now().replace(microsecond=0) + timedelta(days=days)).isoformat()
        key = hashlib.md5(f"TRIAL-{cid}-{int(time.time())}".encode()).hexdigest()[:16].upper()
        c["trial"] = True
        c["trial_expires"] = expires
        c["status"] = "trial"
        c["plan"] = "trial"
        c["license_key"] = key
        db.save()
        return (
            f"🚀 試用版已啟用！\n\n"
            f"⏱ 時效：{days} 天（到期 {expires}）\n"
            f"🔑 授權碼：{key}\n\n"
            f"✅ 試用版包含：\n"
            f"  • AI 對話（無限制）\n"
            f"  • 長期記憶\n"
            f"  • 任務執行\n"
            f"  • 檔案分析\n"
            f"  • 網路搜尋\n\n"
            f"⭐ 完整版額外功能（試用版未含）：\n"
            f"  • 多子代理分工\n"
            f"  • 自動排程定時回報\n"
            f"  • 銷售追蹤\n"
            f"  • AI 安裝代理人\n"
            f"  • 商業變現提案\n\n"
            f"試用期滿後選擇方案付款即可解鎖全部功能。\n"
            f"👉 ampm-aiops.com"
        )

    def get_customers_summary(self):
        return {k: {"name": v.get("name"), "plan": v.get("plan"), "status": v.get("status")}
                for k, v in db.data.items()}

    def get_customer_detail(self, cid):
        c = db.get(cid)
        if not c:
            return "找不到客戶"
        return (
            f"  姓名: {c.get('name','?')}\n"
            f"  聯絡: {c.get('contact','無')}\n"
            f"  方案: {c.get('plan','無')}\n"
            f"  狀態: {c.get('status','new')}\n"
            f"  試用: {'是' if c.get('trial') else '否'}\n"
            f"  到期: {c.get('trial_expires','無')}\n"
            f"  付款: {c.get('payment',{}).get('method','無')}\n"
            f"  主機: {c.get('vps',{}).get('ip','無')}\n"
            f"  授權: {c.get('license_key','無')}\n"
            f"  登入: {c['usage']['login_count']} 次\n"
            f"  最後: {c['usage']['last_active'] or '從未'}\n"
            f"  功能: {', '.join(c['usage']['features_used']) if c['usage']['features_used'] else '無'}\n"
            f"  工單: {len([t for t in c.get('tickets',[]) if t['status']=='open'])} 張開啟"
        )

dispatcher = ServiceDispatcher()
