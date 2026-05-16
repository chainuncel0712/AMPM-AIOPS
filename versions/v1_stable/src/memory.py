"""
記憶系統 - 主動成長版
會自己整理、壓縮、遺忘、連結相關記憶
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

class Memory:
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        
        # 三層記憶結構（會自己流動）
        self.working_file = self.base_dir / "memory" / "working.json"      # 工作記憶（短期）
        self.episodic_file = self.base_dir / "memory" / "episodic.json"    # 情節記憶（中期）
        self.semantic_file = self.base_dir / "memory" / "semantic.json"    # 語義記憶（長期）
        
        # 確保目錄存在
        self.working_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.working = self._load(self.working_file, [])     # 最多 50 條
        self.episodic = self._load(self.episodic_file, [])   # 最多 500 條
        self.semantic = self._load(self.semantic_file, [])   # 永久，但會優化
        
        # 最後整理時間
        self.last_organize = datetime.now()
    
    def _load(self, filepath, default):
        if filepath.exists():
            try:
                return json.loads(filepath.read_text())
            except:
                return default
        return default
    
    def _save(self, filepath, data):
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    
    def remember_conversation(self, user_msg: str, assistant_msg: str, importance: float = 0.5):
        """記住對話（自動放入工作記憶）"""
        entry = {
            "user": user_msg[:500],
            "assistant": assistant_msg[:500],
            "time": datetime.now().isoformat(),
            "importance": importance
        }
        self.working.append(entry)
        
        # 工作記憶超過 50 條，自動壓縮
        if len(self.working) > 50:
            self._compress_working()
        
        self._save(self.working_file, self.working)
        self._check_if_need_organize()
    
    def remember_fact(self, fact: str, importance: float = 0.5):
        """記住重要事實（直接放入語義記憶）"""
        # 檢查是否已存在相似事實
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
    
    def clear_working(self):
        """清空工作記憶（開始新話題）"""
        self.working = []
        self._save(self.working_file, self.working)
    
    def get_stats(self) -> Dict:
        """記憶統計"""
        return {
            "working_count": len(self.working),
            "episodic_count": len(self.episodic),
            "semantic_count": len(self.semantic),
            "avg_importance": sum(f["importance"] for f in self.semantic) / max(1, len(self.semantic))
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
