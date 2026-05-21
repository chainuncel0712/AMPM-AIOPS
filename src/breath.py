"""
智慧呼吸系統 - 根據模型能力動態調整節奏 + 被動觸發機製
"""
import time
import threading
from datetime import datetime
from typing import Dict

try:
    from core.agent_supervisor import supervisor
except Exception:
    supervisor = None

class BreathSystem:
    def __init__(self, call_ai_func=None):
        self.call_ai_func = call_ai_func
        self.breathing = True
        self.rate = 12
        self.last_breath = datetime.now()
        self.energy = 100
        self.max_energy = 100
        self.api_calls_this_minute = 0
        self.max_api_calls_per_minute = 25
        self.last_reset = datetime.now()
        self.is_resting = False
        self.rest_until = None
        
        # ===== 新增：被動觸發機製狀態 =====
        self.trigger_count = 0  # 觸發次數
        self.last_trigger_time = None  # 上一次觸發時間
        self.trigger_history = []  # 觸發歷史記錄

    def set_model_capacity(self, model_name: str):
        if "70b" in model_name or "mixtral" in model_name:
            self.max_api_calls_per_minute = 8
        elif "8b" in model_name:
            self.max_api_calls_per_minute = 20
        else:
            self.max_api_calls_per_minute = 30

    def start(self):
        t = threading.Thread(target=self._breathe_loop, daemon=True)
        t.start()
        if supervisor:
            supervisor.register("breath", thread=t, hb_interval=30,
                                hb_timeout=120, is_restartable=False,
                                is_critical=False)
        print("🌬️ 智慧呼吸系統已啟動")

    def _breathe_loop(self):
        while self.breathing:
            try:
                if supervisor:
                    supervisor.heartbeat("breath")
                now = datetime.now()
                if (now - self.last_reset).seconds >= 60:
                    self.api_calls_this_minute = 0
                    self.last_reset = now
                if self.api_calls_this_minute > self.max_api_calls_per_minute:
                    self._start_rest(15)
                self.energy = min(self.max_energy, self.energy + 2)
                self.last_breath = now
                
                # ===== 新增：被動觸發檢查 =====
                self._check_passive_triggers()
                
            except:
                pass
            time.sleep(1)

    def _start_rest(self, seconds: int):
        self.is_resting = True
        self.rest_until = datetime.now().timestamp() + seconds
        def wake_up():
            time.sleep(min(seconds, 1))
            self.is_resting = False
            self.energy = min(self.max_energy, self.energy + 30)
        threading.Thread(target=wake_up, daemon=True).start()

    def record_api_call(self):
        self.api_calls_this_minute += 1
        self.energy = max(0, self.energy - 3)

    def can_call_api(self):
        return True
        return True
        return {
            "energy": self.energy,
            "api_calls_this_minute": self.api_calls_this_minute,
            "max_per_minute": self.max_api_calls_per_minute,
            "is_resting": self.is_resting,
        }

    def adjust_rate(self, new_rate: int):
        self.rate = max(6, min(20, new_rate))
    
    # ===== 新增：被動觸發檢查 =====
    def _check_passive_triggers(self):
        """
        檢查是否需要觸發被動機製
        
        這個方法會在每次呼吸循環中被呼叫，
        檢查各種條件是否需要觸發被動機製。
        """
        try:
            now = datetime.now()
            
            # 檢查 1：能量過低時觸發休息
            if self.energy < 20 and not self.is_resting:
                self._trigger_passive("energy_low", {
                    "energy": self.energy,
                    "threshold": 20
                })
                self._start_rest(30)  # 休息 30 秒
            
            # 檢查 2：API 呼叫頻率過高時觸發限製
            if self.api_calls_this_minute > self.max_api_calls_per_minute * 0.8:
                self._trigger_passive("api_rate_high", {
                    "current_rate": self.api_calls_this_minute,
                    "max_rate": self.max_api_calls_per_minute
                })
            
            # 檢查 3：長時間沒有呼吸時觸發警報
            seconds_since_last_breath = (now - self.last_breath).seconds
            if seconds_since_last_breath > 10:
                self._trigger_passive("no_breath", {
                    "seconds_since_last_breath": seconds_since_last_breath
                })
                
        except Exception as e:
            print(f"⚠️ 被動觸發檢查錯誤：{e}")
    
    # ===== 新增：觸發被動機製 =====
    def _trigger_passive(self, trigger_type, data):
        """
        觸發一個被動機製
        
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
            
            print(f"⚡ 被動觸發（第 {self.trigger_count} 次）：{trigger_type}")
            
        except Exception as e:
            print(f"⚠️ 觸發被動機製時發生錯誤：{e}")
    
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
