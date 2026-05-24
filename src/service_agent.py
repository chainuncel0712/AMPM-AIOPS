"""
多功能服務代理 — 業務/客服/安裝/售後 同一支 AI
有記憶、懂客戶、自動推進流程
"""
import json, os, threading, time, re, hashlib, random
from pathlib import Path
from datetime import datetime, timedelta, timezone

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"

MAX_HISTORY = 20  # keep last N turns


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
                now = datetime.now(timezone.utc).isoformat()
                self.data[cid] = {
                    "name": f"客戶_{cid}", "contact": "", "plan": None,
                    "status": "new",
                    "trial": False, "trial_expires": None, "license_key": None,
                    "payment": {}, "vps": {},
                    "conversation": [], "tickets": [],
                    "preferences": {"language": "zh", "contact_time": "", "notes": ""},
                    "usage": {"login_count": 0, "last_active": None, "features_used": [], "uptime": 100.0},
                    "created_at": now, "installed_at": None,
                    "assigned_agent": None,
                }
                self._save()
            return self.data[cid]

    def save(self):
        self._save()


db = CustomerDB()


class ServiceAgent:
    """多功能服務代理 — 業務/客服/安裝/售後，同一支"""

    def __init__(self, llm_client=None):
        self._llm = llm_client
        self._model = os.getenv("SERVICE_MODEL", "qwen2.5:7b")

    def set_llm(self, llm_client):
        self._llm = llm_client

    def _detect_vps(self, msg: str) -> dict | None:
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        ips = re.findall(ip_pattern, msg)
        if not ips:
            return None
        info = {"ip": ips[0], "user": "root", "port": 22}
        if "@" in msg:
            info["user"] = msg.split("@")[0].strip()
        port_m = re.search(r'port\s*[:：]?\s*(\d+)', msg, re.IGNORECASE)
        if port_m:
            info["port"] = int(port_m.group(1))
        return info

    def _build_prompt(self, cid: str, msg: str) -> str:
        from personality import SERVICE_PROMPT
        c = db.get_or_create(cid)
        status = c.get("status", "new")
        context = self._context_summary(c)
        history = self._history_text(c)
        return SERVICE_PROMPT.format(status=status, context=context, history=history)

    def _context_summary(self, c: dict) -> str:
        parts = [
            f"名稱: {c.get('name','?')}",
            f"狀態: {c.get('status','new')}",
            f"方案: {c.get('plan','無')}",
            f"主機: {c.get('vps',{}).get('ip','未部署')}",
            f"授權: {c.get('license_key','無')}",
            f"試用: {'是' if c.get('trial') else '否'}",
        ]
        prefs = c.get("preferences", {})
        if prefs.get("notes"):
            parts.append(f"備註: {prefs['notes']}")
        if prefs.get("contact_time"):
            parts.append(f"偏好聯絡時間: {prefs['contact_time']}")
        return " | ".join(parts)

    def _history_text(self, c: dict) -> str:
        conv = c.get("conversation", [])
        if not conv:
            return "(尚無對話記錄)"
        lines = []
        for entry in conv[-MAX_HISTORY:]:
            role = entry.get("role", "?")
            text = entry.get("text", "")[:120]
            lines.append(f"{role}: {text}")
        return "\n".join(lines)

    def _store(self, cid: str, role: str, text: str):
        c = db.get_or_create(cid)
        c.setdefault("conversation", []).append({
            "role": role, "text": text,
            "ts": datetime.now(timezone.utc).isoformat(),
        })
        if len(c["conversation"]) > MAX_HISTORY * 2:
            c["conversation"] = c["conversation"][-MAX_HISTORY:]
        db.save()

    def handle(self, cid: str, msg: str) -> str:
        c = db.get_or_create(cid)
        c["usage"]["login_count"] += 1
        c["usage"]["last_active"] = datetime.now(timezone.utc).isoformat()
        if c.get("status") == "new":
            c["status"] = "chatting"
            name_guess = msg.split()[0][:20] if msg.split() else msg[:20]
            c["name"] = name_guess
        db.save()

        self._store(cid, "客戶", msg)

        # Auto-detect VPS info → auto-generate install script
        vps_info = self._detect_vps(msg)
        if vps_info:
            c["vps"] = {**c.get("vps", {}), **vps_info, "collected_at": datetime.now(timezone.utc).isoformat()}
            c["status"] = "ready_for_install"
            db.save()
            script = self._generate(cid)
            reply = (
                f"✅ 已記錄主機資訊：{vps_info['ip']}:{vps_info['port']}（{vps_info['user']}）\n\n"
                f"{script}"
            )
            self._store(cid, "黑曜", reply)
            return reply

        prompt = self._build_prompt(cid, msg)

        if self._llm:
            try:
                resp = self._llm.chat.completions.create(
                    model=self._model,
                    messages=[{"role": "system", "content": prompt},
                              {"role": "user", "content": msg}],
                    max_tokens=512, temperature=0.7,
                )
                reply = resp.choices[0].message.content.strip()
            except Exception as e:
                reply = self._fallback(c, msg)
        else:
            reply = self._fallback(c, msg)

        self._store(cid, "黑曜", reply)
        return reply

    def _fallback(self, c: dict, msg: str) -> str:
        m = msg.lower()
        if any(k in m for k in ["方案", "價格", "多少錢", "plan", "price"]):
            return (
                "📋 方案：$15/月 · $39/季 · $120/年\n"
                "全部功能全開，沒有分級。也有 3 天試用。"
            )
        if any(k in m for k in ["付款", "怎麼買", "pay", "usdt", "購買"]):
            return (
                "💳 USDT BEP20 轉帳到：\n"
                "`0x7f3110c1314bD68Fdf8E32cD921E646912108587`\n"
                "付款後貼 TXID 自動開通。"
            )
        if re.search(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', m):
            ips = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', m)
            c["vps"]["ip"] = ips[0]
            c["vps"]["user"] = m.split("@")[0].strip() if "@" in m else "root"
            port_m = re.search(r'port\s*[:：]?\s*(\d+)', m, re.IGNORECASE)
            c["vps"]["port"] = int(port_m.group(1)) if port_m else 22
            c["vps"]["collected_at"] = datetime.now(timezone.utc).isoformat()
            c["status"] = "ready_for_install"
            db.save()
            return f"收到主機 {c['vps']['ip']}，準備安裝腳本..."
        if any(k in m for k in ["售後", "問題", "壞", "錯誤", "故障", "重啟", "慢"]):
            return "收到，幫您診斷中。請描述具體症狀（何時開始、發生什麼事）？"
        return "我是黑曜服務窗口，有什麼需要？方案介紹、付款問題、安裝部署、售後診斷，我都能處理。"

    def _generate(self, cid: str) -> str:
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
            f"  主機：{vps['ip']}:{vps['port']}\n"
            f"  使用者：{vps['user']}\n"
            f"  授權碼：{key}\n\n"
            f"  ssh {vps['user']}@{vps['ip']} -p {vps['port']} \\\n"
            f"    'curl -s https://raw.githubusercontent.com/chainuncel0712/AMPM-AIOPS/main/scripts/deploy.sh | bash'"
        )


class ServiceDispatcher:
    def __init__(self, llm_client=None):
        self.agent = ServiceAgent(llm_client)

    def set_llm(self, llm_client):
        self.agent.set_llm(llm_client)

    def train(self, cid, topic, content):
        c = db.get_or_create(cid)
        c.setdefault("knowledge", {})[topic] = {"content": content, "trained_at": datetime.now(timezone.utc).isoformat()}
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
            f"方案: {plan} | 狀態: {status} | {trial} | "
            f"主機: {vps} | 授權: {license_k}"
        )

    def log_usage(self, cid, feature):
        c = db.get_or_create(cid)
        if feature and feature not in c["usage"]["features_used"]:
            c["usage"]["features_used"].append(feature)
        c["usage"]["login_count"] += 1
        c["usage"]["last_active"] = datetime.now(timezone.utc).isoformat()
        db.save()

    def route(self, cid, msg):
        return self.agent.handle(cid, msg)

    def start_trial(self, cid, days=3):
        c = db.get_or_create(cid)
        if c.get("trial") and c.get("trial_expires"):
            remaining = (datetime.fromisoformat(c["trial_expires"]) - datetime.now(timezone.utc)).total_seconds()
            if remaining > 0:
                return f"您已在試用期內，還剩 {int(remaining/86400)} 天。"
        expires = (datetime.now(timezone.utc).replace(microsecond=0) + timedelta(days=days)).isoformat()
        key = hashlib.md5(f"TRIAL-{cid}-{int(time.time())}".encode()).hexdigest()[:16].upper()
        c["trial"] = True
        c["trial_expires"] = expires
        c["status"] = "trial"
        c["plan"] = "trial"
        c["license_key"] = key
        db.save()
        return (f"🚀 試用 {days} 天已啟用！\n🔑 授權碼：{key}")

    def get_customers_summary(self):
        return {k: {"name": v.get("name"), "plan": v.get("plan"), "status": v.get("status")}
                for k, v in db.data.items()}

    def get_customer_detail(self, cid):
        c = db.get(cid)
        if not c:
            return "找不到客戶"
        return (
            f"  姓名: {c.get('name','?')}\n"
            f"  方案: {c.get('plan','無')}\n"
            f"  狀態: {c.get('status','new')}\n"
            f"  主機: {c.get('vps',{}).get('ip','無')}\n"
            f"  授權: {c.get('license_key','無')}\n"
            f"  登入: {c['usage']['login_count']} 次\n"
            f"  工單: {len([t for t in c.get('tickets',[]) if t['status']=='open'])} 張"
        )


dispatcher = ServiceDispatcher()
