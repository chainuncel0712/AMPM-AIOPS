"""
MemoryManager — 統一三層記憶引擎
=================================
取代原本分散的 Memory + MemoryWriter + LangGraph 獨立記憶。
單一寫入入口、跨層檢索、持久化、執行緒安全。

三層架構：
  Layer 1: working   — 最近對話緩衝 (50 輪)
  Layer 2: semantic  — 重要事實/任務/知識 (500 條)
  Layer 3: episodic  — 事件記錄 (500 條)

寫入規則（Write Policy）：
  - working：永遠寫（短期緩衝）
  - semantic：僅當 importance >= 0.85 或透過 remember_fact() 手動寫入
  - episodic：含事件關鍵字才寫
  - 禁止 working 自動升級到 semantic（防止 noise 污染長期記憶）

檢索規則：
  - 關鍵字搜 semantic（含重要性門檻）
  - 最近 working 對話
  - 標籤搜 episodic
  → 合併、去重、按分數排序回傳
"""

import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class MemoryManager:
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.memory_dir = self.base_dir / "memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

        self.working_file = self.memory_dir / "working.json"
        self.semantic_file = self.memory_dir / "semantic.json"
        self.episodic_file = self.memory_dir / "episodic.json"

        self.working: List[Dict] = self._load(self.working_file, [])
        self.semantic: List[Dict] = self._load(self.semantic_file, [])
        self.episodic: List[Dict] = self._load(self.episodic_file, [])

        self.max_working = 10000  # 不刪，硬碟夠大
        self.max_semantic = 50000
        self.max_episodic = 50000

        self.last_organize = datetime.now()

    # ========== IO ==========

    def _load(self, path: Path, default):
        if path.exists():
            try:
                return json.loads(path.read_text())
            except Exception:
                return default
        return default

    def _save(self, path: Path, data):
        with self._lock:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    # ========== 寫入 ==========

    def remember(self, user_msg: str, assistant_msg: str) -> float:
        """記住一輪對話。自動評分並分類寫入三層。回傳重要性分數。"""
        importance = self._score(user_msg, assistant_msg)
        ts = datetime.now().isoformat()

        entry = {
            "user": user_msg[:1000],
            "assistant": assistant_msg[:2000] if assistant_msg else "",
            "time": ts,
            "importance": importance,
            "source": "conversation",
        }

        with self._lock:
            # Layer 1: working — 永遠寫
            self.working.append(entry)
            if len(self.working) > self.max_working:
                self._compress_working()

            # Layer 2: semantic — 全寫，不刪
            self._write_semantic(user_msg, assistant_msg, importance, ts)

            # Layer 3: episodic — 含事件關鍵字寫入
            self._write_episodic(user_msg, assistant_msg, importance, ts)

        self._maybe_organize()
        return importance

    def remember_fact(self, fact: str, importance: float = 0.7, value: str = "") -> None:
        """直接寫入 semantic（供 cortex 等手動調用）"""
        ts = datetime.now().isoformat()
        with self._lock:
            for existing in self.semantic:
                if existing.get("fact") == fact:
                    existing["importance"] = max(existing["importance"], importance)
                    if value:
                        existing["value"] = value
                    existing["last_recalled"] = ts
                    self._save(self.semantic_file, self.semantic)
                    return
            self.semantic.append({
                "fact": fact,
                "value": value or fact,
                "importance": importance,
                "created_at": ts,
                "last_recalled": ts,
            })
            self._trim_semantic()
            self._save(self.semantic_file, self.semantic)

    def _write_semantic(self, user_msg: str, assistant_msg: str, importance: float, ts: str):
        fact_text = user_msg[:200]
        value_text = assistant_msg[:500] if assistant_msg else user_msg[:200]
        entry = {
            "fact": fact_text,
            "value": value_text,
            "importance": importance,
            "created_at": ts,
            "last_recalled": ts,
        }
        self.semantic.append(entry)
        self._trim_semantic()
        self._save(self.semantic_file, self.semantic)

    def _write_episodic(self, user_msg: str, assistant_msg: str, importance: float, ts: str):
        event_type, tags = self._classify_event(user_msg, assistant_msg)
        if not tags:
            return
        entry = {
            "type": event_type,
            "summary": f"{user_msg[:150]} → {assistant_msg[:150]}" if assistant_msg else user_msg[:150],
            "importance": importance,
            "tags": tags,
            "timestamp": ts,
        }
        self.episodic.append(entry)
        if len(self.episodic) > self.max_episodic:
            self.episodic = self.episodic[-self.max_episodic:]
        self._save(self.episodic_file, self.episodic)

    def _classify_event(self, user_msg: str, assistant_msg: str):
        combined = (user_msg + " " + assistant_msg).lower()
        if any(k in combined for k in ["部署", "安裝", "設定", "配置"]):
            return "deployment", ["task", "infra"]
        if any(k in combined for k in ["建立", "創造", "生成", "產生", "開發"]):
            return "creation", ["task", "development"]
        if any(k in combined for k in ["修", "修復", "修正", "debug", "錯誤"]):
            return "repair", ["task", "maintenance"]
        if any(k in combined for k in ["檢查", "掃描", "查看", "監控"]):
            return "inspection", ["task", "monitoring"]
        if any(k in combined for k in ["規劃", "計畫", "專案", "任務", "目標"]):
            return "planning", ["task", "strategy"]
        if any(k in combined for k in ["分析", "評估", "審核"]):
            return "analysis", ["task", "review"]
        return "conversation", []

    # ========== 檢索 ==========

    def recall(self, query: str = "", limit: int = 5, threshold: float = 0.3) -> List[Dict]:
        """跨三層檢索。回傳 [{type, content, importance, time, source}]"""
        results: List[Dict] = []
        query_lower = query.lower() if query else ""

        with self._lock:
            # 搜 semantic
            for fact in self.semantic:
                if fact.get("importance", 0.5) < threshold:
                    continue
                f_text = fact.get("fact", "")
                v_text = fact.get("value", "")
                if query_lower and query_lower not in f_text.lower() and query_lower not in v_text.lower():
                    continue
                results.append({
                    "type": "semantic",
                    "content": v_text or f_text,
                    "importance": fact.get("importance", 0.5),
                    "time": fact.get("created_at", ""),
                    "source": "semantic",
                })

            # 搜 working（最近對話）
            for entry in reversed(self.working[-10:]):
                u = entry.get("user", "")
                a = entry.get("assistant", "")
                if query_lower and query_lower not in (u + a).lower():
                    continue
                results.append({
                    "type": "working",
                    "content": f"使用者: {u[:100]}" + (f" → 回覆: {a[:100]}" if a else ""),
                    "importance": entry.get("importance", 0.5),
                    "time": entry.get("time", ""),
                    "source": "working",
                })

            # 搜 episodic
            if query_lower:
                query_tags = [t for t in query_lower.split() if len(t) >= 2]
                for ep in self.episodic:
                    ep_tags = [t.lower() for t in ep.get("tags", [])]
                    if any(t in ep_tags for t in query_tags) or query_lower in ep.get("summary", "").lower():
                        results.append({
                            "type": "episodic",
                            "content": ep.get("summary", ""),
                            "importance": ep.get("importance", 0.5),
                            "time": ep.get("timestamp", ""),
                            "source": "episodic",
                        })

        # 排序：importance + 時間新近度
        results.sort(key=lambda r: (
            r.get("importance", 0.5) * 0.6 +
            (1.0 if query_lower and query_lower in r.get("content", "").lower() else 0.3)
        ), reverse=True)

        # 去重（content 相似）
        seen = set()
        deduped = []
        for r in results:
            key = r["content"][:40]
            if key not in seen:
                seen.add(key)
                deduped.append(r)
                if len(deduped) >= limit:
                    break

        return deduped

    def get_context(self, query: str = "", limit: int = 5) -> str:
        """取得記憶上下文（給 LLM system prompt 注入用）"""
        items = self.recall(query=query, limit=limit)
        if not items:
            return ""
        lines = []
        for item in items:
            src = item.get("source", "?")
            content = item.get("content", "")[:200]
            labels = {"semantic": "已知", "working": "最近", "episodic": "事件"}
            label = labels.get(src, src)
            lines.append(f"[{label}] {content}")
        return "\n".join(lines)

    def get_recent(self, n: int = 5) -> List[Dict]:
        """取得最近 N 輪對話"""
        with self._lock:
            return list(self.working[-n:])

    # ========== 維護 ==========

    def _score(self, user_msg: str, assistant_msg: str) -> float:
        """自動評分重要性 0~1"""
        score = 0.3
        combined = (user_msg + " " + (assistant_msg or "")).lower()

        # 顯式標記 → 最高
        if any(kw in user_msg for kw in ["重要", "記住", "記下來", "別忘", "不要忘"]):
            return 1.0

        # 任務/規劃
        if any(kw in combined for kw in [
            "任務", "規劃", "專案", "計畫", "目標", "公司", "組織",
            "架構", "架設", "工具書", "電子書", "自動化", "代理",
            "選題", "童書", "一條龍", "客製化", "商業", "營收",
        ]):
            score = max(score, 0.9)

        # 身份/偏好
        if any(kw in user_msg for kw in [
            "我叫", "我是", "我喜歡", "我討厭", "我習慣", "偏好",
            "改名", "稱呼", "叫我",
        ]):
            score = max(score, 0.85)

        # 事件/操作
        if any(kw in combined for kw in [
            "部署", "安裝", "執行", "完成", "建立", "修復",
            "修正", "檢查", "重啟",
        ]):
            score = max(score, 0.75)

        # 長訊息（有意義的內容）
        if len(user_msg) > 80:
            score = max(score, 0.7)
        elif len(user_msg) > 30:
            score = max(score, 0.5)

        return min(1.0, score)

    def _compress_working(self):
        overflow = self.working[:20]
        self.working = self.working[20:]
        if overflow:
            summary = {
                "type": "compressed",
                "count": len(overflow),
                "range": f"{overflow[0].get('time','?')} ~ {overflow[-1].get('time','?')}",
                "compressed_at": datetime.now().isoformat(),
            }
            self.episodic.append(summary)
            if len(self.episodic) > self.max_episodic:
                self.episodic = self.episodic[-self.max_episodic:]
            self._save(self.working_file, self.working)
            self._save(self.episodic_file, self.episodic)

    def _trim_semantic(self):
        self.semantic.sort(key=lambda x: x.get("importance", 0.5), reverse=True)
        if len(self.semantic) > self.max_semantic:
            self.semantic = self.semantic[:self.max_semantic]

    def _maybe_organize(self):
        pass  # 不自動整理，記憶永遠保留
            self.last_organize = now

    def organize(self):
        """維護：不刪記憶，只存檔"""
        with self._lock:
            self._save(self.semantic_file, self.semantic)
            self._save(self.working_file, self.working)
            self._save(self.episodic_file, self.episodic)

    def forget(self, keyword: str = None):
        """根據關鍵字遺忘記憶"""
        with self._lock:
            if keyword:
                kw = keyword.lower()
                before = len(self.semantic)
                self.semantic = [
                    f for f in self.semantic
                    if kw not in f.get("fact", "").lower() and kw not in f.get("value", "").lower()
                ]
                self._save(self.semantic_file, self.semantic)
                print(f"🧠 遺忘 {before - len(self.semantic)} 條關於 '{keyword}' 的記憶")

    def get_stats(self) -> Dict:
        with self._lock:
            return {
                "working": len(self.working),
                "semantic": len(self.semantic),
                "episodic": len(self.episodic),
                "avg_importance": round(
                    sum(f.get("importance", 0.5) for f in self.semantic) / max(1, len(self.semantic)), 2
                ),
            }

    # ===== 舊 API 相容層（讓 MemoryManager 可直接替換 memory.Memory）=====

    def remember_conversation(self, user_msg: str, assistant_msg: str, importance: float = 0.5):
        """舊 API 相容：記住對話 → 委派給 remember()"""
        return self.remember(user_msg, assistant_msg)

    def get_recent_conversations(self, limit: int = 10) -> List[Dict]:
        """舊 API 相容：取得最近對話"""
        return self.get_recent(limit)

    def get_all_facts(self) -> Dict:
        """舊 API 相容：所有語義記憶"""
        with self._lock:
            return {f.get("fact", ""): f.get("value", f.get("fact", "")) for f in self.semantic}

    def get_important_facts(self, min_importance: float = 0.7) -> Dict:
        """舊 API 相容：重要事實"""
        with self._lock:
            return {
                f.get("fact", ""): f.get("value", f.get("fact", ""))
                for f in self.semantic
                if f.get("importance", 0.5) >= min_importance
            }

    def search_semantic(self, keyword: str) -> List[Dict]:
        """舊 API 相容：搜尋語義記憶"""
        kw = keyword.lower()
        with self._lock:
            return [f for f in self.semantic if kw in f.get("fact", "").lower() or kw in f.get("value", "").lower()]

    def clear_working(self):
        """舊 API 相容：清空工作記憶"""
        with self._lock:
            self.working = []
            self._save(self.working_file, self.working)

    def get_trigger_stats(self) -> Dict:
        return {"total_triggers": 0, "trigger_types": {}}

    def suggest_what_to_remember(self, call_ai_func) -> str:
        return ""
