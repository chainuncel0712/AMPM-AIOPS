"""
AMPM 真實大腦 - 設定檔
"""

import os
from pathlib import Path

class Config:
    def __init__(self):
        self.base_dir = Path.home() / ".ampm_brain"
        
        # 新的 Telegram Token
        self.telegram_token = "8614933947:AAFGb3BDLNgDvrcGo7A_86jETV9QGjqWYlQ"
        self.your_chat_id = 5600355483
        
        # NVIDIA API
        self.nvidia_key = os.getenv("NVIDIA_API_KEY", "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")
        self.nvidia_endpoint = "https://integrate.api.nvidia.com/v1/chat/completions"
        self.model = "meta/llama-3.1-70b-instruct"
        
        # 限制
        self.max_agents = 50
        self.max_depth = 5
        self.max_api_calls_per_minute = 30
        self.honest_mode = True

config = Config()
