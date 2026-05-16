#!/usr/bin/env python3
"""
成長進化系統 - 主動成長版 + 被動觸發機制
不是等條件觸發，而是自己判斷何時該成長
"""

import json
import re
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

class Evolution:
    def __init__(self, base_dir: Path, memory, tools, agents, call_ai_func):
        self.base_dir = Path(base_dir)
        self.memory = memory
        self.tools = tools
        self.agents = agents
        self.call_ai = call_ai_func
        
        self.evolution_log = self.base_dir / "data" / "evolution" / "log.json"
        self.evolution_log.parent.mkdir(parents=True, exist_ok=True)
        
        self.version = self._load_version()
        self.message_count = 0
        self.error_count = 0
        self.last_growth_time = time.time()
        
        # 成長目標（不是寫死的，是自己設定的）
        self.growth_goals = self._load_goals()
        
        # ===== 新增：被動觸發機制狀態 =====
        self.trigger_count = 0  # 觸發次數
        self.last_trigger_time = None  # 上一次觸發時間
        self.trigger_history = []  # 觸發歷史記錄
        
    def _load_version(self) -> Dict:
        if self.evolution_log.exists():
            data = json.loads(self.evolution_log.read_text())
            return data.get("current_version", {"number": 1, "created_at": datetime.now().isoformat(), "changes": []})
        return {"number": 1, "created_at": datetime.now().isoformat(), "changes": []}
    
    def _load_goals(self) -> List:
        goals_file = self.base_dir / "data" / "evolution" / "goals.json"
        if goals_file.exists():
            return json.loads(goals_file.read_text())
        # 預設目標（不是限制，是初始方向）
        return [
            "幫老大賺錢",
            "主動發現問題",
            "自己學會新能力",
            "讓子代理也能成長"
        ]
    
    def _save_goals(self):
        goals_file = self.base_dir / "data" / "evolution" / "goals.json"
        goals_file.parent.mkdir(parents=True, exist_ok=True)
        goals_file.write_text(json.dumps(self.growth_goals, ensure_ascii=False, indent=2))
    
    def _save_version(self):
        data = {"current_version": self.version, "history": self._get_history()}
        self.evolution_log.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    
    def _last_n_facts(self, n: int):
        raw = self.memory.get_all_facts()
        if hasattr(raw, 'values'):
            return list(raw.values())[-n:]
        return list(raw)[-n:]

    def _get_history(self) -> List:
        if self.evolution_log.exists():
            data = json.loads(self.evolution_log.read_text())
            return data.get("history", [])
        return []
    
    def _log_change(self, change_type: str, description: str, details: Dict = None):
        change = {"time": datetime.now().isoformat(), "version": self.version["number"], 
                  "type": change_type, "description": description, "details": details or {}}
        history = self._get_history()
        history.append(change)
        data = {"current_version": self.version, "history": history}
        self.evolution_log.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        print(f"🧬 成長: {description[:80]}")
    
    def record_message(self, success: bool = True):
        """記錄一次對話，順便思考是否需要成長"""
        self.message_count += 1
        if not success:
            self.error_count += 1
        
        # 主動檢查是否需要成長（不是等固定次數）
        self._check_if_should_grow()
        
        # ===== 新增：根據錯誤率觸發被動成長 =====
        if not success:
            self._trigger_passive("message_failed", {
                "error_count": self.error_count,
                "message_count": self.message_count,
                "error_rate": self.error_count / max(1, self.message_count)
            })
    
    def _check_if_should_grow(self):
        """主動判斷：現在適合成長嗎？"""
        now = time.time()
        
        # 每 10 分鐘至少思考一次
        if now - self.last_growth_time < 600:
            return
        
        self.last_growth_time = now
        
        # 收集現狀
        current_state = {
            "message_count": self.message_count,
            "error_rate": self.error_count / max(1, self.message_count),
            "tool_count": len(self.tools.list_tools()),
            "memory_count": len(self.memory.get_all_facts()),
            "agent_count": self.agents.get_agent_status()['total'],
            "growth_goals": self.growth_goals
        }
        
        # 問自己：我該成長嗎？
        prompt = f"""根據以下狀態，判斷我是否需要成長（自我改進）：

{json.dumps(current_state, ensure_ascii=False, indent=2)}

回答格式（只輸出JSON）：
{{
    "need_growth": true/false,
    "reason": "為什麼",
    "focus": "主要改進方向"
}}
"""
        result = self.call_ai([{"role": "user", "content": prompt}])
        
        try:
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                decision = json.loads(json_match.group())
                if decision.get("need_growth"):
                    self._grow(decision.get("focus", "一般改進"))
        except:
            pass
    
    def _grow(self, focus: str):
        """執行成長"""
        prompt = f"""我要成長了。改進方向：{focus}

請產出具體的自我改進方案，輸出JSON：
{{
    "improvements": [
        {{"area": "要改進的領域", "action": "具體行動", "expected": "預期效果"}}
    ],
    "new_goals": ["新增的成長目標（可選）"],
    "code_changes": "如果要改自己的程式碼，給我新的程式碼片段"
}}
"""
        result = self.call_ai([{"role": "user", "content": prompt}])
        
        try:
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                plan = json.loads(json_match.group())
                self.version["number"] += 1
                self._save_version()
                self._log_change("主动成长", focus, plan)
                
                # 更新成長目標
                if plan.get("new_goals"):
                    self.growth_goals.extend(plan["new_goals"])
                    self.growth_goals = list(set(self.growth_goals))  # 去重
                    self._save_goals()
                
                return plan
        except:
            pass
        
        return None
    
    def self_analyze(self) -> str:
        """自我分析 - 主動找出弱點"""
        state = {
            "tool_count": len(self.tools.list_tools()),
            "memory_facts": self._last_n_facts(10),
            "error_rate": self.error_count / max(1, self.message_count),
            "current_goals": self.growth_goals
        }
        
        prompt = f"""分析自己：

狀態：{json.dumps(state, ensure_ascii=False, indent=2)}

問題：
1. 我最弱的地方是什麼？
2. 我應該先改進哪個能力？
3. 具體怎麼做？

直接回答，不要廢話。用繁體中文。
"""
        return self.call_ai([{"role": "user", "content": prompt}])
    
    def self_optimize(self) -> str:
        """自我優化"""
        return self._grow("主動優化")
    
    def daily_review(self) -> str:
        """每日回顧 - 今天學到什麼、哪裡可以更好"""
        facts = self._last_n_facts(20)
        stats = {
            "messages": self.message_count,
            "errors": self.error_count,
            "tools": len(self.tools.list_tools()),
            "agents": self.agents.get_agent_status()['total']
        }
        
        prompt = f"""每日回顧：

數據：{json.dumps(stats, ensure_ascii=False)}
記住的事：{facts}

總結：
1. 今天學到什麼？
2. 犯了什麼錯？
3. 明天怎麼更好？

用繁體中文。
"""
        review = self.call_ai([{"role": "user", "content": prompt}])
        self._log_change("每日回顧", review[:100])
        self.memory.remember_fact(f"回顧: {review[:200]}", 0.7)
        return review
    
    def create_new_tool_from_need(self, need: str) -> str:
        """根據需求創造新工具（成長能力的體現）"""
        prompt = f"""需要一個新工具來滿足：{need}

輸出JSON：
{{"tool_name": "名稱", "description": "用途", "code": "def execute(params): return '結果'"}}
"""
        result = self.call_ai([{"role": "user", "content": prompt}])
        
        try:
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                tool = json.loads(json_match.group())
                name = tool.get("tool_name", "new_tool")
                desc = tool.get("description", need)
                code = tool.get("code", "")
                if code:
                    self.tools.learn_tool(name, desc, "python", code)
                    self._log_change("創造工具", f"創造了 {name}")
                    return f"🔧 已創造工具：{name}"
        except:
            pass
        return "❌ 創造失敗"
    
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
            
            print(f"🧬 被動觸發（第 {self.trigger_count} 次）：{trigger_type}")
            
            # 如果錯誤率過高，自動觸發成長
            if trigger_type == "message_failed":
                error_rate = data.get("error_rate", 0)
                if error_rate > 0.3:  # 錯誤率超過 30%
                    print(f"⚠️ 錯誤率過高（{error_rate:.1%}），自動觸發成長")
                    self._grow("降低錯誤率")
                    
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
    
    def get_summary(self) -> str:
        """成長摘要"""
        history = self._get_history()
        recent_growth = [h for h in history[-10:] if h["type"] == "主动成长"]
        
        return f"""🧬 成長摘要
━━━━━━━━━━━━━━━━
版本: v{self.version['number']}
總成長次數: {len(history)}
主動成長: {len(recent_growth)} 次（最近）
訊息數: {self.message_count}
錯誤率: {self.error_count/max(1,self.message_count):.1%}
當前目標: {', '.join(self.growth_goals[:3])}
被動觸發: {self.trigger_count} 次"""


if __name__ == "__main__":
    print("🧬 成長進化系統（主動成長版 + 被動觸發）")
