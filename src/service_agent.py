"""
客服 / 安裝 / 售後 一條龍 AI 代理
有記憶、懂客戶、自動推進流程
"""
import json, os, threading, time, re
from pathlib import Path
from datetime import datetime, timedelta

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"

class ServiceAgent:
    def __init__(self):
        self.customers_file = DATA / "customers.json"
        self.log_file = DATA / "service_agent_log.json"
        self.customers_file.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._load()

    def _load(self):
        with self._lock:
            if self.customers_file.exists():
                try:
                    self.customers = json.loads(self.customers_file.read_text())
                except:
                    self.customers = {}
            else:
                self.customers = {}
            if self.log_file.exists():
                try:
                    self.log = json.loads(self.log_file.read_text())
                except:
                    self.log = []
            else:
                self.log = []

    def _save(self):
        with self._lock:
            self.customers_file.write_text(json.dumps(self.customers, ensure_ascii=False, indent=2))
            self.log_file.write_text(json.dumps(self.log, ensure_ascii=False, indent=2))

    def _log(self, customer_id, action, detail):
        self.log.append({
            "customer_id": customer_id,
            "action": action,
            "detail": detail,
            "time": datetime.now().isoformat()
        })
        self._save()

    def _cid(self, cid):
        return str(cid).strip()

    def get_or_create(self, customer_id, name=None, contact=None):
        cid = self._cid(customer_id)
        with self._lock:
            if cid not in self.customers:
                self.customers[cid] = {
                    "name": name or f"客戶_{cid}",
                    "contact": contact or "",
                    "plan": None,
                    "status": "new",
                    "trial": False,
                    "trial_expires": None,
                    "conversation": [],
                    "payment": {},
                    "vps": {},
                    "license_key": None,
                    "notes": [],
                    "preferences": {
                        "language": "zh",
                        "contact_time": "",
                        "preferred_model": "",
                        "notes": ""
                    },
                    "usage": {
                        "login_count": 0,
                        "last_active": None,
                        "features_used": [],
                        "reports_requested": 0,
                        "uptime_percentage": 100.0
                    },
                    "tickets": [],
                    "created_at": datetime.now().isoformat(),
                    "installed_at": None
                }
                self._save()
                self._log(cid, "new_customer", f"新客戶建立: {self.customers[cid]['name']}")
            return self.customers[cid]

    def get(self, customer_id):
        cid = self._cid(customer_id)
        return self.customers.get(cid)

    def set_name(self, customer_id, name):
        cid = self._cid(customer_id)
        self.get_or_create(cid)
        self.customers[cid]["name"] = name
        self._save()
        self._log(cid, "set_name", name)

    def set_contact(self, customer_id, contact):
        cid = self._cid(customer_id)
        self.get_or_create(cid)
        self.customers[cid]["contact"] = contact
        self._save()
        self._log(cid, "set_contact", contact)

    def set_plan(self, customer_id, plan):
        cid = self._cid(customer_id)
        self.get_or_create(cid)
        self.customers[cid]["plan"] = plan
        self.customers[cid]["status"] = "plan_selected"
        self._save()
        self._log(cid, "plan_selected", plan)

    def confirm_payment(self, customer_id, method, amount, txid=""):
        cid = self._cid(customer_id)
        customer = self.get(cid)
        if not customer:
            return "找不到這個客戶，請先建立基本資料。"
        customer["payment"] = {"method": method, "amount": amount, "txid": txid, "paid_at": datetime.now().isoformat()}
        customer["status"] = "paid"
        self._save()
        self._log(cid, "payment_confirmed", f"{method} {amount}")
        return f"付款確認完成，接下來請提供您的主機 IP 和 SSH 登入資訊，我來幫您部署。"

    def start_trial(self, customer_id, days=3):
        cid = self._cid(customer_id)
        customer = self.get_or_create(cid)
        if customer.get("trial") and customer.get("trial_expires"):
            remaining = (datetime.fromisoformat(customer["trial_expires"]) - datetime.now()).total_seconds()
            if remaining > 0:
                return f"您已在試用期內，還剩下 {int(remaining/86400)} 天。"
        customer["trial"] = True
        customer["trial_expires"] = (datetime.now().replace(microsecond=0) + timedelta(days=days)).isoformat()
        customer["status"] = "trial"
        customer["plan"] = "trial"
        license_key = self._generate_license(cid)
        customer["license_key"] = license_key
        self._save()
        self._log(cid, "trial_started", f"{days} 天試用")
        return f"✅ 您已啟用 {days} 天試用版（功能全開）！\n授權碼: {license_key}\n到期日: {customer['trial_expires']}\n試用期滿後如需繼續使用，請選擇方案付款。\n\n👉 前往 ampm-aiops.com 查看方案"

    def check_trial(self, customer_id):
        cid = self._cid(customer_id)
        customer = self.get(cid)
        if not customer or not customer.get("trial"):
            return False, "無試用記錄"
        expires = customer.get("trial_expires")
        if not expires:
            return False, "無到期日"
        remaining = (datetime.fromisoformat(expires) - datetime.now()).total_seconds()
        if remaining <= 0:
            customer["trial"] = False
            customer["status"] = "trial_expired"
            self._save()
            return False, "試用已到期，請選擇方案付款續用"
        return True, f"試用中，剩餘 {int(remaining/86400)} 天 {int((remaining%86400)/3600)} 小時"

    def set_vps(self, customer_id, ip, user, port=22):
        cid = self._cid(customer_id)
        customer = self.get(cid)
        if not customer:
            return "找不到這個客戶。"
        customer["vps"] = {"ip": ip, "user": user, "port": port, "collected_at": datetime.now().isoformat()}
        customer["status"] = "ready_for_install"
        self._save()
        self._log(cid, "vps_collected", f"{ip}:{port}")
        return f"收到，目標主機 {ip}:{port}，使用者 {user}。正在準備安裝腳本……"

    def generate_script(self, customer_id):
        cid = self._cid(customer_id)
        customer = self.get(cid)
        if not customer:
            return None
        vps = customer.get("vps", {})
        if not vps.get("ip"):
            return None
        license_key = self._generate_license(cid)
        script_path = DATA / f"deploy_{cid}.sh"
        script = self._build_script(customer.get("name", "客戶"), vps["ip"], vps["user"], vps.get("port", 22), license_key)
        script_path.write_text(script)
        script_path.chmod(0o755)
        customer["license_key"] = license_key
        customer["status"] = "script_ready"
        self._save()
        self._log(cid, "script_generated", license_key)
        return str(script_path)

    def _build_script(self, name, ip, user, port, key):
        return f"""#!/bin/bash
# AMPM-AIOPS 自動部署 — {name} ({ip})
set -e
echo ">>> 開始部署黑曜到 {name} 的主機 {ip}"
ssh -o StrictHostKeyChecking=no -p {port} {user}@{ip} bash -s << 'SSHEOF'
  cd /opt
  git clone https://github.com/chainuncel0712/AMPM-AIOPS.git 2>/dev/null || (cd AMPM-AIOPS && git pull)
  cd AMPM-AIOPS
  python3 -m venv venv 2>/dev/null || true
  source venv/bin/activate
  pip install -q -r requirements.txt
  echo "{key}" > data/license.key
  tmux new-session -d -s obsidian 'python3 main.py' 2>/dev/null || screen -dmS obsidian python3 main.py
  echo "黑曜已啟動，授權碼: {key}"
SSHEOF
echo ">>> 部署完成！"
"""

    def _generate_license(self, cid):
        import hashlib, random
        raw = f"AMPM-{cid}-{random.randint(10000,99999)}-{int(time.time())}"
        return hashlib.md5(raw.encode()).hexdigest()[:16].upper()

    def mark_installed(self, customer_id):
        cid = self._cid(customer_id)
        customer = self.get(cid)
        if not customer:
            return
        customer["status"] = "installed"
        customer["installed_at"] = datetime.now().isoformat()
        self._save()
        self._log(cid, "installed", "部署完成")

    def set_preference(self, customer_id, key, value):
        allowed = ["language", "contact_time", "preferred_model", "notes"]
        if key not in allowed:
            return
        cid = self._cid(customer_id)
        customer = self.get_or_create(cid)
        customer["preferences"][key] = value
        self._save()
        self._log(cid, "preference_set", f"{key}={value}")

    def log_usage(self, customer_id, feature=None):
        cid = self._cid(customer_id)
        customer = self.get_or_create(cid)
        customer["usage"]["login_count"] += 1
        customer["usage"]["last_active"] = datetime.now().isoformat()
        if feature and feature not in customer["usage"]["features_used"]:
            customer["usage"]["features_used"].append(feature)
        self._save()

    def add_ticket(self, customer_id, subject, description):
        cid = self._cid(customer_id)
        customer = self.get_or_create(cid)
        ticket = {
            "id": len(customer["tickets"]) + 1,
            "subject": subject,
            "description": description,
            "status": "open",
            "created_at": datetime.now().isoformat(),
            "resolved_at": None
        }
        customer["tickets"].append(ticket)
        self._save()
        self._log(cid, "ticket_created", f"#{ticket['id']} {subject}")
        return ticket

    def resolve_ticket(self, customer_id, ticket_id):
        cid = self._cid(customer_id)
        customer = self.get(cid)
        if not customer:
            return
        for t in customer["tickets"]:
            if t["id"] == ticket_id:
                t["status"] = "resolved"
                t["resolved_at"] = datetime.now().isoformat()
                break
        self._save()
        self._log(cid, "ticket_resolved", f"#{ticket_id}")

    def get_customer_summary(self, customer_id):
        cid = self._cid(customer_id)
        customer = self.get(cid)
        if not customer:
            return "找不到客戶"
        c = customer
        lines = [
            f"姓名: {c.get('name', '未知')}",
            f"聯絡: {c.get('contact', '無')}",
            f"方案: {c.get('plan', '未選擇')}",
            f"狀態: {c.get('status', 'new')}",
            f"付款: {c.get('payment', {}).get('method', '未付款')} {c.get('payment', {}).get('amount', '')}",
            f"主機: {c.get('vps', {}).get('ip', '未部署')}",
            f"授權: {c.get('license_key', '無')}",
            f"使用次數: {c['usage']['login_count']} 次",
            f"最後上線: {c['usage']['last_active'] or '從未'}",
            f"使用功能: {', '.join(c['usage']['features_used']) if c['usage']['features_used'] else '無'}",
            f"工單: {len([t for t in c['tickets'] if t['status']=='open'])} 張開啟",
            f"偏好語言: {c['preferences'].get('language', 'zh')}",
            f"偏好模型: {c['preferences'].get('preferred_model', '未設定')}",
            f"備註: {c['preferences'].get('notes', '無')}",
        ]
        return "\n".join(lines)

    def add_note(self, customer_id, note):
        cid = self._cid(customer_id)
        customer = self.get_or_create(cid)
        customer["notes"].append({"note": note, "time": datetime.now().isoformat()})
        self._save()
        self._log(cid, "note_added", note[:100])

    def add_conversation(self, customer_id, role, text):
        cid = self._cid(customer_id)
        customer = self.get_or_create(cid)
        customer["conversation"].append({
            "role": role,
            "text": text,
            "time": datetime.now().isoformat()
        })
        if len(customer["conversation"]) > 2000:
            customer["conversation"] = customer["conversation"][-2000:]
        self._save()

    def get_context(self, customer_id):
        cid = self._cid(customer_id)
        customer = self.get(cid)
        if not customer:
            return ""
        ctx = [
            f"客戶: {customer.get('name', '未知')}",
            f"狀態: {customer.get('status', 'new')}",
            f"方案: {customer.get('plan', '未選擇')}",
            f"付款: {customer.get('payment', {}).get('method', '未付款')}",
            f"主機: {customer.get('vps', {}).get('ip', '未提供')}",
            f"授權: {customer.get('license_key', '無')}",
        ]
        convs = customer.get("conversation", [])[-6:]
        for c in convs:
            who = "客戶" if c["role"] == "user" else "客服"
            ctx.append(f"{who}: {c['text'][:100]}")
        return "\n".join(ctx)

    def handle_chat(self, customer_id, message, llm_call=None):
        cid = self._cid(customer_id)
        customer = self.get_or_create(cid)
        self.add_conversation(cid, "user", message)
        self.log_usage(cid)

        m = message.lower()
        if "偏好" in m or "語言" in m or "習慣" in m:
            if "英文" in m or "en" in m:
                self.set_preference(cid, "language", "en")
                return "已記錄您的語言偏好：英文。"
            if "中文" in m or "zh" in m:
                self.set_preference(cid, "language", "zh")
                return "已記錄您的語言偏好：中文。"
            if "模型" in m:
                for model in ["ollama", "deepseek", "openai", "qwen", "llama", "gpt"]:
                    if model in m:
                        self.set_preference(cid, "preferred_model", model)
                        return f"已記錄您的偏好模型：{model}"
            return "您可以告訴我您的偏好，例如「我习惯用英文」或「偏好 deepseek 模型」"

        if "工單" in m or "ticket" in m or "報修" in m or "問題回報" in m:
            subject = "客戶回報問題"
            desc = message
            ticket = self.add_ticket(cid, subject, desc)
            return f"已建立工單 #{ticket['id']}，我們會盡快處理。工單狀態：{ticket['status']}"

        if "摘要" in m or "summary" in m or "我的資料" in m or "查看" in m:
            return f"📋 您的客戶資料：\n\n{self.get_customer_summary(cid)}"

        if llm_call:
            context = self.get_context(cid)
            prompt = f"""你是黑曜的客服 AI 代理，負責銷售、安裝部署與售後支援。
語氣自然、不強迫推銷，像朋友一樣協助客戶。

當前客戶狀態：
{context}

客戶最新訊息: {message}

根據客戶狀態和對話歷史回應。不要主動推銷，客戶問什麼就答什麼。
如果是新客戶，簡單介紹即可，不要一直催。
如果是已付費客戶，引導提供主機資訊。
如果是已安裝客戶，提供售後支援。
"""
            reply = llm_call(prompt)
            self.add_conversation(cid, "assistant", reply)
            return reply

        m = message.lower()
        status = customer.get("status", "new")

        if status == "new":
            self.customers[cid]["name"] = message.split()[0] if message.split() else message[:10]
            self.customers[cid]["status"] = "chatting"
            self._save()
            return (
                f"您好 {customer.get('name','')}，我是黑曜的 AI 客服。\n\n"
                "我可以幫您：\n"
                "1. 了解方案與價格\n"
                "2. 完成付款\n"
                "3. 安排安裝部署\n"
                "4. 售後技術支援\n\n"
                "請問您想了解什麼？"
            )

        if any(k in m for k in ["方案", "價格", "多少錢", "月", "季", "年", "plan", "price"]):
            return (
                "📋 我們有三種方案：\n\n"
                "▸ 月方案  $15／30 天\n"
                "▸ 季方案  $39／90 天（省 $6）\n"
                "▸ 年方案  $120／365 天（省 $60）\n\n"
                "全部方案都解鎖完整功能，沒有分級。\n"
                "您想選擇哪個方案？"
            )

        if any(k in m for k in ["月", "季", "年", "15", "39", "120", "選"]):
            plan_map = {"月": "monthly", "15": "monthly", "季": "quarterly", "39": "quarterly", "年": "yearly", "120": "yearly"}
            for k, v in plan_map.items():
                if k in m:
                    self.set_plan(cid, v)
                    break
            return (
                f"好的，已為您選擇 {customer.get('plan','')} 方案。\n\n"
                "付款方式：\n"
                "1. USDT BEP20 — 掃 QR Code 轉帳\n"
                "2. PayPal — 點擊網站上的按鈕\n\n"
                "付款完成後請告知，我會立即為您安排安裝。"
            )

        if any(k in m for k in ["付", "pay", "usdt", "txid", "轉帳", "匯款"]):
            return (
                "付款完成後，請提供：\n"
                "1. 付款方式（USDT / PayPal）\n"
                "2. 金額\n"
                "3. TXID 或交易截圖\n\n"
                "我會確認後立刻為您安排安裝。"
            )

        if status in ("paid", "plan_selected") or any(k in m for k in ["主機", "ip", "ssh", "vps", "安裝", "部署", "裝"]):
            if status in ("paid", "plan_selected") and not customer.get("vps", {}).get("ip"):
                return (
                    "要為您部署黑曜，請提供以下主機資訊：\n\n"
                    "• IP 地址\n"
                    "• SSH 使用者名稱（通常是 root）\n"
                    "• SSH 連接埠（預設 22）\n\n"
                    "收到後我會自動產生安裝腳本並部署。"
                )

        if any(k in m for k in ["問題", "故障", "錯誤", "不能", "壞", "error", "bug", "當機", "連不上"]):
            return (
                "請描述您遇到的問題，我會嘗試遠端診斷。\n\n"
                "常見問題：\n"
                "• Bot 無回應 → 檢查是否在運行\n"
                "• 記憶不見了 → 檢查 memory/ 目錄\n"
                "• 模型無法載入 → 確認 Ollama 狀態\n\n"
                "詳細描述後我會給您具體解法。"
            )

        reply = (
            f"了解。我已經記錄您的訊息。\n\n"
            f"目前您的狀態：方案 {customer.get('plan','未選擇')}，"
            f"付款 {customer.get('payment',{}).get('method','未付款')}。\n\n"
            "請問還有什麼需要幫助的嗎？"
        )
        self.add_conversation(cid, "assistant", reply)
        return reply

service_agent = ServiceAgent()
