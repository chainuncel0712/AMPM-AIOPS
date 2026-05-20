"""丘腦 — 訊息路由器 + 模型調度 + 閾值控制
取代盲目 fallback，一條訊息只打一個模型。
"""
import threading
import time
from skeleton.base_organ import BaseOrgan


class Thalamus(BaseOrgan):
    """訊息路由中樞：分類 → 指派模型 → 一條直通"""

    def __init__(self, llm_client=None):
        super().__init__("thalamus")
        self.llm = llm_client
        self._lock = threading.Lock()
        self._last_call = 0.0
        self._call_count = 0
        self._min_interval = 0.5  # 兩次 LLM 呼叫最小間隔（秒）

    # ── 訊息分類表 ──
    CATEGORY_RULES = [
        # (關鍵字, 類別, 推薦模型名)
        (["看圖", "圖片", "這張圖", "照片", "截圖"], "vision", "OR-Gemini"),
        (["寫程式", "code", "python", "bug", "錯誤", "修復", "改", "做", "寫"], "task", "DeepSeek"),
        (["搜", "查", "找", "價格", "新聞", "天氣"], "search", "DeepSeek"),
        (["模型", "切換", "換模型"], "system", "DeepSeek"),
        (["硬碟", "磁碟", "記憶體", "cpu", "系統"], "system", "DeepSeek"),
        (["翻譯", "英文", "日文"], "translate", "DeepSeek"),
    ]

    @classmethod
    def classify(cls, user_msg: str) -> str:
        """根據訊息內容回傳類別標籤"""
        for keywords, category, _ in cls.CATEGORY_RULES:
            if any(kw in user_msg for kw in keywords):
                return category
        return "chat"

    @classmethod
    def pick_model(cls, category: str, providers: list) -> dict:
        """根據類別從可用模型清單中挑一個最適合的。
        找不到就回傳第一個。
        """
        target_map = {
            "vision": ["OR-Gemini", "Gemini"],
            "chat":    ["DeepSeek", "OR-DeepSeek"],
            "task":    ["DeepSeek", "OR-DeepSeek"],
            "search":  ["DeepSeek", "OR-DeepSeek"],
            "system":  ["DeepSeek", "Ollama"],
            "translate": ["DeepSeek", "OR-DeepSeek"],
        }
        preferred_names = target_map.get(category, ["DeepSeek"])
        for name in preferred_names:
            for p in providers:
                if name.lower() in p.get("name", "").lower():
                    return p
        return providers[0] if providers else None

    def acquire(self, timeout: float = 10.0) -> bool:
        """取得 LLM 呼叫權（防自治任務搶使用者訊息）"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self._lock.acquire(blocking=False):
                # 速率保護：最小間隔
                elapsed = time.time() - self._last_call
                if elapsed < self._min_interval:
                    time.sleep(self._min_interval - elapsed)
                self._call_count += 1
                return True
            time.sleep(0.05)
        return False

    def release(self):
        """釋放 LLM 呼叫權"""
        self._last_call = time.time()
        try:
            self._lock.release()
        except RuntimeError:
            pass

    def route(self, user_msg: str, providers: list) -> dict:
        """完整路由：分類 + 選模型，回傳 {provider, category}"""
        category = self.classify(user_msg)
        provider = self.pick_model(category, providers)
        return {"category": category, "provider": provider}

    def should_skip_review(self, category: str, confidence: float = 1.0) -> bool:
        """閾值控制：簡單對話不需要自我審查"""
        if category in ("chat", "system"):
            return True
        return confidence > 0.9

    @property
    def stats(self) -> dict:
        return {
            "call_count": self._call_count,
            "last_call": self._last_call,
            "locked": self._lock.locked(),
        }

    def status(self) -> dict:
        return {"name": self.name, "alive": self.is_alive(), **self.stats}
