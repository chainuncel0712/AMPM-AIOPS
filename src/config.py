"""
AM&PM 控制台 2.0 - 全功能配置檔 (安全版)
所有金鑰從 .env 讀取，不寫死在程式碼中
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 載入 .env 檔案（位於專案根目錄）
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

class Config:
    def __init__(self):
        self.base_dir = Path.home() / ".ampm_brain"
        
        # ========== Telegram Bot 配置（只保留商業用代號） ==========
        self.bots = {
            "黑曜": os.getenv("TELEGRAM_TOKEN_OBSIDIAN", ""),
            "業務": os.getenv("TELEGRAM_TOKEN_BUSINESS", ""),
            "客服": os.getenv("TELEGRAM_TOKEN_SUPPORT", ""),
            "財務": os.getenv("TELEGRAM_TOKEN_FINANCE", ""),
            "執行": os.getenv("TELEGRAM_TOKEN_EXECUTE", ""),
        }
        
        self.default_bot_name = os.getenv("TELEGRAM_DEFAULT_BOT", "黑曜")
        self.telegram_token = self.bots.get(self.default_bot_name, "")
        
        # 安全地轉換 YOUR_CHAT_ID，如果無法轉換則使用 0
        chat_id_str = os.getenv("YOUR_CHAT_ID", "0")
        try:
            self.your_chat_id = int(chat_id_str)
        except ValueError:
            print(f"  [⚠️] YOUR_CHAT_ID 設定無效: '{chat_id_str}'，使用預設值 0")
            self.your_chat_id = 0
        
        # ========== 大模型 API 金鑰 ==========
        self.openai_key = os.getenv("OPENAI_API_KEY", "")
        self.deepseek_key = os.getenv("DEEPSEEK_API_KEY", "")
        self.alibaba_key = os.getenv("ALIBABA_API_KEY", "")
        self.nvidia_key = os.getenv("NVIDIA_API_KEY", "")
        self.huggingface_token = os.getenv("HUGGINGFACE_TOKEN", "")
        
        # ========== NVIDIA NIM 設定 ==========
        self.nvidia_endpoint = os.getenv("NVIDIA_ENDPOINT", "https://integrate.api.nvidia.com/v1/chat/completions")
        self.model = os.getenv("NVIDIA_MODEL", "meta/llama-3.1-8b-instruct")
        
        # ========== Cloudflare 設定 ==========
        self.cf_api_token = os.getenv("CLOUDFLARE_API_TOKEN", "")
        self.cf_global_key = os.getenv("CLOUDFLARE_GLOBAL_KEY", "")
        self.cf_dnskey = os.getenv("CLOUDFLARE_DNSKEY", "")
        self.cf_account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
        self.cf_zone_id = os.getenv("CLOUDFLARE_ZONE_ID", "")
        
        # ========== 自訂金鑰 ==========
        self.lianshu_key = os.getenv("LIANSHU_KEY", "")
        
        # ========== 系統限制 ==========
        self.max_agents = int(os.getenv("MAX_AGENTS", "50"))
        self.max_depth = int(os.getenv("MAX_DEPTH", "5"))
        self.max_api_calls_per_minute = int(os.getenv("MAX_API_CALLS_PER_MINUTE", "30"))
        self.honest_mode = os.getenv("HONEST_MODE", "true").lower() == "true"
    
    def get_bot_token(self, bot_name: str) -> str:
        return self.bots.get(bot_name, "")
    
    def list_bots(self) -> dict:
        return {name: "已設定" if token else "未設定" for name, token in self.bots.items()}

config = Config()

# ========== 指揮官/管理員設定 ==========
def get_authorized_users():
    """取得授權的使用者 ID 列表"""
    ids_str = os.getenv("AUTHORIZED_USER_IDS", "")
    if ids_str:
        result = []
        for x in ids_str.split(","):
            x = x.strip()
            if x:
                try:
                    result.append(int(x))
                except ValueError:
                    print(f"  [⚠️] AUTHORIZED_USER_IDS 包含無效值: '{x}'，已跳過")
        return result
    return []

def is_authorized(user_id: int) -> bool:
    """檢查是否為授權使用者"""
    return user_id in get_authorized_users()

# 加入到 Config 類別
if not hasattr(config, 'authorized_users'):
    config.authorized_users = get_authorized_users()
if not hasattr(config, 'admin_username'):
    config.admin_username = os.getenv("ADMIN_USERNAME", "")
