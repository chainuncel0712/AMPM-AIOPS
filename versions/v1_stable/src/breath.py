"""
呼吸系統 - 節奏控制
讓黑曜知道要休息、冷卻、不要過度運作
"""

import time
import threading
from datetime import datetime
from typing import Dict, Optional

class BreathSystem:
    def __init__(self, call_ai_func=None):
        self.call_ai_func = call_ai_func
        self.breathing = True
        
        # 呼吸節奏（每分鐘幾次）
        self.rate = 12  # 正常 12 次/分鐘
        self.last_breath = datetime.now()
        
        # 能量管理
        self.energy = 100
        self.max_energy = 100
        self.energy_drain_rate = 1  # 每分鐘消耗
        
        # 冷卻機制
        self.api_calls_this_minute = 0
        self.max_api_calls_per_minute = 30
        self.last_reset = datetime.now()
        
        # 休息狀態
        self.is_resting = False
        self.rest_until = None
    
    def start(self):
        """啟動呼吸循環"""
        threading.Thread(target=self._breathe_loop, daemon=True).start()
        print("🌬️ 呼吸系統已啟動")
    
    def _breathe_loop(self):
        """呼吸循環 - 持續調節節奏"""
        while self.breathing:
            try:
                now = datetime.now()
                
                # 1. 重置每分鐘計數
                if (now - self.last_reset).seconds >= 60:
                    self.api_calls_this_minute = 0
                    self.last_reset = now
                
                # 2. 檢查是否需要休息
                if self.api_calls_this_minute > self.max_api_calls_per_minute:
                    self._start_rest(30)  # 休息 30 秒
                
                # 3. 消耗能量
                self.energy -= self.energy_drain_rate
                if self.energy < 20:
                    self._low_energy_alert()
                
                # 4. 自然恢復
                if self.energy < self.max_energy and not self.is_resting:
                    self.energy = min(self.max_energy, self.energy + 2)
                
                # 5. 呼吸記錄（每 5 秒一次）
                self.last_breath = now
                
            except Exception as e:
                print(f"呼吸錯誤: {e}")
            
            time.sleep(5)  # 每 5 秒呼吸一次
    
    def _start_rest(self, seconds: int):
        """開始休息"""
        self.is_resting = True
        self.rest_until = datetime.now().timestamp() + seconds
        print(f"😴 進入休息模式 {seconds} 秒（API 呼叫過多）")
        
        def wake_up():
            time.sleep(seconds)
            self.is_resting = False
            self.energy = min(self.max_energy, self.energy + 20)
            print(f"🌅 休息結束，能量恢復到 {self.energy}")
        
        threading.Thread(target=wake_up, daemon=True).start()
    
    def _low_energy_alert(self):
        """能量過低警告"""
        print(f"⚠️ 能量過低: {self.energy}%")
        if self.call_ai_func:
            self.call_ai_func([{"role": "system", "content": f"能量 {self.energy}%，建議降低活動頻率"}])
    
    def record_api_call(self):
        """記錄一次 API 呼叫"""
        self.api_calls_this_minute += 1
        self.energy = max(0, self.energy - 5)
    
    def can_call_api(self) -> bool:
        """是否允許呼叫 API"""
        if self.is_resting:
            return False
        if self.api_calls_this_minute >= self.max_api_calls_per_minute:
            return False
        if self.energy < 10:
            return False
        return True
    
    def get_status(self) -> Dict:
        """取得呼吸狀態"""
        return {
            "energy": self.energy,
            "api_calls_this_minute": self.api_calls_this_minute,
            "is_resting": self.is_resting,
            "rate": self.rate
        }
    
    def adjust_rate(self, new_rate: int):
        """調整呼吸節奏（主動調節）"""
        self.rate = max(6, min(20, new_rate))
        print(f"🌬️ 呼吸節奏調整為 {self.rate} 次/分鐘")

if __name__ == "__main__":
    print("🌬️ 呼吸系統模組")
