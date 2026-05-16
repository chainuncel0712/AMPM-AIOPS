"""
LLM 呼叫模組 - 處理所有 AI 模型呼叫
"""

import requests
from config import config

class LLMClient:
    def __init__(self, breath_system=None):
        self.breath = breath_system
    
    def call(self, messages, temperature=0.7) -> str:
        """呼叫 AI 模型"""
        if self.breath and not self.breath.can_call_api():
            return "🌬️ 系統正在休息，請稍後..."
        
        if self.breath:
            self.breath.record_api_call()
        
        headers = {"Authorization": f"Bearer {config.nvidia_key}", "Content-Type": "application/json"}
        payload = {
            "model": config.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 1000
        }
        
        try:
            r = requests.post(config.nvidia_endpoint, json=payload, headers=headers, timeout=60)
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
            return f"API錯誤: {r.status_code}"
        except Exception as e:
            return f"錯誤: {e}"
