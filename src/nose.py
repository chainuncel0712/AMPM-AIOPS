"""
嗅覺系統 - 偵測機會和異常 + 被動觸發機制
讓黑曜主動「聞」哪裡有賺錢機會、哪裡有異常趨勢
"""

import time
import threading
import json
from pathlib import Path
from datetime import datetime
from runtime.context.persona_builder import RUNTIME_IDENTITY, RUNTIME_RULES
from typing import Dict, List, Optional


try:
    from core.agent_supervisor import supervisor
except Exception:
    supervisor = None

class NoseSystem:
    def __init__(self, base_dir: Path, call_ai_func=None, memory=None):
        self.base_dir = Path(base_dir)
        self.call_ai_func = call_ai_func
        self.memory = memory
        self.sniffing = True
        
        # 嗅覺記錄
        self.smells_file = self.base_dir / "data" / "nose" / "smells.json"
        self.smells_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 歷史嗅覺
        self.smell_history = self._load_history()
        
        # 嗅覺靈敏度（0-1）
        self.sensitivity = 0.7
        
        # ===== 新增：被動觸發機制狀態 =====
        self.trigger_count = 0  # 觸發次數
        self.last_trigger_time = None  # 上一次觸發時間
        self.trigger_history = []  # 觸發歷史記錄
    
    def _load_history(self) -> List:
        if self.smells_file.exists():
            return json.loads(self.smells_file.read_text())
        return []
    
    def _save_history(self):
        self.smells_file.write_text(json.dumps(self.smell_history[-100:], ensure_ascii=False, indent=2))
    
    def start(self):
        """啟動嗅覺循環"""
        t = threading.Thread(target=self._sniff_loop, daemon=True)
        t.start()
        if supervisor:
            supervisor.register("nose", thread=t, hb_interval=120,
                                hb_timeout=300, is_restartable=False,
                                is_critical=False)
        print("👃 嗅覺系統已啟動")
    
    def _sniff_loop(self):
        """嗅覺循環 - 持續偵測"""
        while self.sniffing:
            try:
                if supervisor:
                    supervisor.heartbeat("nose")
                # 每 5 分鐘偵測一次
                time.sleep(60)
                
                # 1. 嗅市場機會
                opportunities = self._sniff_opportunities()
                if opportunities:
                    self._report_findings("機會", opportunities)
                    # ===== 新增：檢測到機會時觸發被動機制 =====
                    self._trigger_passive("opportunity", opportunities)
                
                # 2. 嗅異常趨勢
                anomalies = self._sniff_anomalies()
                if anomalies:
                    self._report_findings("異常", anomalies)
                    # ===== 新增：檢測到異常時觸發被動機制 =====
                    self._trigger_passive("anomaly", anomalies)
                
                # 3. 嗅記憶中的模式
                patterns = self._sniff_patterns()
                if patterns:
                    self._report_findings("模式", patterns)
                    # ===== 新增：檢測到模式時觸發被動機制 =====
                    self._trigger_passive("pattern", patterns)
                
            except Exception as e:
                print(f"嗅覺錯誤: {e}")
    
    def _sniff_opportunities(self) -> List[str]:
        """嗅出賺錢機會"""
        if not self.call_ai_func:
            return []
        
        # 從記憶中提取近期對話關鍵字
        recent_facts = []
        if self.memory:
            raw = self.memory.get_all_facts()
            recent_facts = list(raw.values())[-10:] if hasattr(raw, 'values') else list(raw)[-10:]
        
        prompt = f"""根據以下資訊，嗅出可能的賺錢機會：

近期記憶：{recent_facts}

輸出 JSON 列表（最多 3 個）：
[{{"opportunity": "機會描述", "confidence": 0.0-1.0, "suggested_action": "建議行動"}}]
"""
        try:
            system_identity = f"{RUNTIME_IDENTITY}\n\n{RUNTIME_RULES}\n\n你正在執行系統嗅覺任務：尋找機會。"
            response = self.call_ai_func([
                {"role": "system", "content": system_identity},
                {"role": "user", "content": prompt}
            ])
            import re
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                opportunities = json.loads(json_match.group())
                return [f"{o['opportunity']}（信心度 {o['confidence']:.0%}）" 
                        for o in opportunities[:3] if o.get('confidence', 0) > self.sensitivity]
        except:
            pass
        return []
    
    def _sniff_anomalies(self) -> List[str]:
        """嗅出異常趨勢"""
        # 檢查系統狀態異常
        anomalies = []
        
        # 檢查記憶過多
        if self.memory:
            facts_count = len(self.memory.get_all_facts())
            if facts_count > 500:
                anomalies.append(f"記憶超過 500 條（{facts_count}），可能需要壓縮")
        
        return anomalies
    
    def _sniff_patterns(self) -> List[str]:
        """嗅出重複模式"""
        if not self.memory or not self.call_ai_func:
            return []
        
        raw = self.memory.get_all_facts()
        facts = list(raw.values())[-30:] if hasattr(raw, 'values') else list(raw)[-30:]
        if len(facts) < 10:
            return []
        
        prompt = f"""分析以下記憶，找出重複出現的模式或趨勢：

{json.dumps(facts, ensure_ascii=False)[:1000]}

輸出 JSON 列表（最多 2 個）：
[{{"pattern": "模式描述", "frequency": "頻率"}}]
"""
        try:
            system_identity = f"{RUNTIME_IDENTITY}\n\n{RUNTIME_RULES}\n\n你正在執行系統嗅覺任務：尋找模式。"
            response = self.call_ai_func([
                {"role": "system", "content": system_identity},
                {"role": "user", "content": prompt}
            ])
            import re
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                patterns = json.loads(json_match.group())
                return [f"{p['pattern']}（出現頻率: {p.get('frequency', '未知')}）" 
                        for p in patterns[:2]]
        except:
            pass
        return []
    
    def _report_findings(self, category: str, findings: List[str]):
        """報告嗅到的發現"""
        if not findings:
            return
        
        timestamp = datetime.now().strftime("%H:%M")
        print(f"👃 嗅到 {category}: {findings[0][:50]}...")
        
        # 記錄到嗅覺歷史
        self.smell_history.append({
            "time": datetime.now().isoformat(),
            "category": category,
            "findings": findings
        })
        self._save_history()
        
        # 如果有重要發現，可以觸發主動回應
        if category == "機會" and self.sensitivity > 0.6:
            # 這裡可以觸發主動通知
            pass
    
    # ===== 新增：觸發被動機制 =====
    def _trigger_passive(self, trigger_type, data):
        """
        觸發一個被動機制
        
        參數：
            trigger_type: 觸發類型（opportunity, anomaly, pattern）
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
            
            print(f"👃 被動觸發（第 {self.trigger_count} 次）：{trigger_type}")
            
            # 如果記憶系統可用，記錄觸發事件
            if self.memory:
                self.memory.remember_fact(
                    f"嗅覺觸發：{trigger_type} - {str(data)[:100]}",
                    importance=0.7
                )
                
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
    
    def get_status(self) -> Dict:
        """取得嗅覺狀態"""
        recent = self.smell_history[-5:] if self.smell_history else []
        return {
            "sensitivity": self.sensitivity,
            "smells_detected": len(self.smell_history),
            "recent_findings": recent,
            "trigger_stats": self.get_trigger_stats()
        }
    
    def set_sensitivity(self, value: float):
        """調整嗅覺靈敏度"""
        self.sensitivity = max(0.1, min(1.0, value))
        print(f"👃 嗅覺靈敏度調整為 {self.sensitivity}")
    
    def sniff_now(self) -> str:
        """立即嗅一次（手動觸發）"""
        opportunities = self._sniff_opportunities()
        anomalies = self._sniff_anomalies()
        patterns = self._sniff_patterns()
        
        result = []
        if opportunities:
            result.append(f"💰 機會：{', '.join(opportunities[:3])}")
        if anomalies:
            result.append(f"⚠️ 異常：{', '.join(anomalies[:3])}")
        if patterns:
            result.append(f"📊 模式：{', '.join(patterns[:3])}")
        
        if result:
            return "\n".join(result)
        return "👃 沒有嗅到特別的東西"

if __name__ == "__main__":
    print("👃 嗅覺系統模組")
