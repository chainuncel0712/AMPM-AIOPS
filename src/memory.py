"""
記憶系統 - 線程安全版
"""
import json
import threading
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

class Memory:
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self._lock = threading.Lock()

        self.working_file = self.base_dir / "memory" / "working.json"
        self.episodic_file = self.base_dir / "memory" / "episodic.json"
        self.semantic_file = self.base_dir / "memory" / "semantic.json"

        self.working_file.parent.mkdir(parents=True, exist_ok=True)

        self.working = self._load(self.working_file, [])
        self.episodic = self._load(self.episodic_file, [])
        self.semantic = self._load(self.semantic_file, [])
        
        # 最後整理時間
        self.last_organize = datetime.now()
        
        # ===== 新增：被動觸發機制狀態 =====
        self.trigger_count = 0  # 觸發次數
        self.last_trigger_time = None  # 上一次觸發時間
        self.trigger_history = []  # 觸發歷史記錄
    
    def _load(self, filepath, default):
        if filepath.exists():
            try:
                return json.loads(filepath.read_text())
            except:
                return default
        return default
    
    def _save(self, filepath, data):
        """線程安全寫入"""
        with self._lock:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            filepath.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def remember_conversation(self, user_msg: str, assistant_msg: str, importance: float = 0.5):
        """記住對話（線程安全）"""
        entry = {
            "user": user_msg[:500],
            "assistant": assistant_msg[:500],
            "time": datetime.now().isoformat(),
            "importance": importance
        }
        with self._lock:
            self.working.append(entry)
            if len(self.working) > 50:
                self._compress_working()
            self._save(self.working_file, self.working)
        self._check_if_need_organize()
        
        # ===== 新增：根據重要性觸發被動機制 =====
        if importance > 0.8:
            self._trigger_passive("high_importance_memory", {
                "importance": importance,
                "user_msg": user_msg[:50],
                "assistant_msg": assistant_msg[:50]
            })
    
    def remember_fact(self, fact: str, importance: float = 0.5):
        """記住重要事實（線程安全）"""
        with self._lock:
            for existing in self.semantic:
                if existing["fact"] == fact:
                    existing["importance"] = max(existing["importance"], importance)
                    existing["last_recalled"] = datetime.now().isoformat()
                    self._save(self.semantic_file, self.semantic)
                return
        
        self.semantic.append({
            "fact": fact,
            "importance": importance,
            "created_at": datetime.now().isoformat(),
            "last_recalled": datetime.now().isoformat()
        })
        
        # 按重要性排序，保留最重要的
        self.semantic.sort(key=lambda x: x["importance"], reverse=True)
        self.semantic = self.semantic[:500]  # 最多 500 條
        self._save(self.semantic_file, self.semantic)
        
        # ===== 新增：根據重要性觸發被動機制 =====
        if importance > 0.8:
            self._trigger_passive("high_importance_fact", {
                "importance": importance,
                "fact": fact[:50]
            })
    
    def _compress_working(self):
        """壓縮工作記憶到情節記憶"""
        # 取出最舊的 20 條
        to_compress = self.working[:20]
        self.working = self.working[20:]
        
        # 壓縮成一條摘要
        if to_compress:
            summary = {
                "summary": f"對話片段（{len(to_compress)} 條）",
                "time_range": f"{to_compress[0]['time']} ~ {to_compress[-1]['time']}",
                "original_count": len(to_compress),
                "compressed_at": datetime.now().isoformat()
            }
            self.episodic.append(summary)
            
            # 情節記憶最多 500 條
            if len(self.episodic) > 500:
                self.episodic = self.episodic[-500:]
            self._save(self.episodic_file, self.episodic)
            
            # ===== 新增：壓縮時觸發被動機制 =====
            self._trigger_passive("memory_compressed", {
                "compressed_count": len(to_compress),
                "remaining_working": len(self.working)
            })
    
    def _check_if_need_organize(self):
        """檢查是否需要整理記憶"""
        now = datetime.now()
        # 每 1 小時整理一次
        if (now - self.last_organize).seconds > 3600:
            self.organize()
            self.last_organize = now
    
    def organize(self):
        """主動整理記憶 - 成長核心"""
        # 1. 降低很久沒 recall 的事實的重要性
        now = datetime.now()
        for fact in self.semantic:
            last = datetime.fromisoformat(fact.get("last_recalled", fact["created_at"]))
            days_since = (now - last).days
            if days_since > 7:
                # 每週沒 recall，重要性降 10%
                fact["importance"] *= 0.9
                if fact["importance"] < 0.1:
                    fact["importance"] = 0.1
        
        # 2. 移除重要性過低的事實
        before = len(self.semantic)
        self.semantic = [f for f in self.semantic if f["importance"] >= 0.15]
        
        # 3. 重新排序
        self.semantic.sort(key=lambda x: x["importance"], reverse=True)
        
        # 4. 儲存
        self._save(self.semantic_file, self.semantic)
        
        print(f"🧠 記憶整理完成：{before} -> {len(self.semantic)} 條事實")
        
        # ===== 新增：整理時觸發被動機制 =====
        self._trigger_passive("memory_organized", {
            "before": before,
            "after": len(self.semantic),
            "removed": before - len(self.semantic)
        })
    
    def recall(self, query: str, limit: int = 5, threshold: float = 0.3) -> List[str]:
        """回憶相關內容（同時更新 recall 時間）"""
        results = []
        query_lower = query.lower()
        
        for fact in self.semantic:
            if fact["importance"] < threshold:
                continue
            if query_lower in fact["fact"].lower():
                results.append(fact["fact"])
                # 更新 recall 時間
                fact["last_recalled"] = datetime.now().isoformat()
                if len(results) >= limit:
                    break
        
        # 如果有 recall，儲存更新
        if results:
            self._save(self.semantic_file, self.semantic)
        
        return results
    
    def search_semantic(self, keyword: str) -> List[Dict]:
        """搜尋語義記憶"""
        results = []
        for fact in self.semantic:
            if keyword in fact["fact"]:
                results.append(fact)
        return results
    
    def get_recent_conversations(self, limit: int = 10) -> List[Dict]:
        """取得最近對話（從工作記憶）"""
        return self.working[-limit:]
    
    def get_all_facts(self) -> List[str]:
        """取得所有記住的事實"""
        return [f["fact"] for f in self.semantic]
    
    def get_important_facts(self, min_importance: float = 0.7) -> List[str]:
        """取得重要事實"""
        return [f["fact"] for f in self.semantic if f["importance"] >= min_importance]
    
    def forget(self, keyword: str = None, min_importance: float = 0.1):
        """遺忘（主動）"""
        if keyword:
            # 遺忘包含關鍵字的記憶
            before = len(self.semantic)
            self.semantic = [f for f in self.semantic if keyword not in f["fact"]]
            print(f"🧠 遺忘 {before - len(self.semantic)} 條關於 '{keyword}' 的記憶")
        else:
            # 遺忘重要性過低的記憶
            before = len(self.semantic)
            self.semantic = [f for f in self.semantic if f["importance"] >= min_importance]
            print(f"🧠 遺忘 {before - len(self.semantic)} 條低重要性記憶")
        
        self._save(self.semantic_file, self.semantic)
        
        # ===== 新增：遺忘時觸發被動機制 =====
        self._trigger_passive("memory_forgotten", {
            "keyword": keyword,
            "before": before,
            "after": len(self.semantic)
        })
    
    def clear_working(self):
        """清空工作記憶（開始新話題）"""
        self.working = []
        self._save(self.working_file, self.working)
        
        # ===== 新增：清空時觸發被動機制 =====
        self._trigger_passive("working_memory_cleared", {})
    
    def get_stats(self) -> Dict:
        """記憶統計"""
        return {
            "working_count": len(self.working),
            "episodic_count": len(self.episodic),
            "semantic_count": len(self.semantic),
            "avg_importance": sum(f["importance"] for f in self.semantic) / max(1, len(self.semantic)),
            "trigger_stats": self.get_trigger_stats()
        }
    
    # ===== 新增：觸發被動機制 =====
    def _trigger_passive(self, trigger_type, data):
        """
        觸發一個被動機制
        
        參數：
            trigger_type: 觸發類型
            data: 觸發數據
        """
        try:
            self.trigger_count += 1
            self.last_trigger_time = datetime.now()
            
            trigger_record = {
                "trigger_number": self.trigger_count,
                "type": trigger_type,
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
            
            self.trigger_history.append(trigger_record)
            # 最多保留 100 條歷史記錄
            if len(self.trigger_history) > 100:
                self.trigger_history = self.trigger_history[-100:]
            
            print(f"🧠 被動觸發（第 {self.trigger_count} 次）：{trigger_type}")
            
        except Exception as e:
            print(f"⚠️ 觸發被動機制時發生錯誤：{e}")
    
    # ===== 新增：取得觸發統計 =====
    def get_trigger_stats(self) -> Dict:
        """
        取得被動觸發統計資訊
        
        回傳：
            包含觸發統計的字典
        """
        trigger_types = {}
        for record in self.trigger_history:
            t = record.get("type", "unknown")
            trigger_types[t] = trigger_types.get(t, 0) + 1
        
        return {
            "total_triggers": self.trigger_count,
            "last_trigger_time": self.last_trigger_time.isoformat() if self.last_trigger_time else None,
            "trigger_types": trigger_types,
            "recent_triggers": self.trigger_history[-5:] if self.trigger_history else []
        }
    
    def suggest_what_to_remember(self, call_ai_func) -> str:
        """建議應該記住什麼（主動學習）"""
        recent = self.get_recent_conversations(10)
        prompt = f"""根據最近的對話，我應該記住哪些重要的事？

最近對話：
{json.dumps(recent, ensure_ascii=False, indent=2)[:1000]}

輸出 JSON 列表：["重要事實1", "重要事實2", ...]
"""
        try:
            response = call_ai_func(prompt)
            import re
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                suggestions = json.loads(json_match.group())
                for s in suggestions[:5]:
                    self.remember_fact(s, importance=0.6)
                return f"📝 已記住 {len(suggestions[:5])} 項新事實"
        except:
            pass
        return "沒有新建議"


if __name__ == "__main__":
    mem = Memory(Path.home() / ".ampm_brain")
    print("記憶統計：", mem.get_stats())
