"""
對話管理器 — 多輪上下文管理 + 自動摘要壓縮
防止 LLM context window 溢出，自動壓縮歷史對話。
"""
import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from skeleton.base_organ import BaseOrgan


class ConversationManager(BaseOrgan):
    """
    對話管理器

    功能：
    1. 管理多輪對話歷史
    2. 自動摘要 — 超過 N 輪後自動壓縮
    3. 上下文視窗 — 限制 token 上限
    4. 重要訊息標記 — 不會被摘要掉的關鍵訊息
    """

    DEFAULT_SYSTEM_PROMPT = """你是黑曜，一個專業的 AI 商業夥伴。
務必用繁體中文回覆，簡短有力。不知道就說不知道，然後去找答案。"""

    def __init__(self, base_dir: Path, max_history: int = 20, max_tokens: int = 8000):
        super().__init__("conversation")
        self.base_dir = base_dir
        self.max_history = max_history
        self.max_tokens = max_tokens
        self._lock = threading.Lock()

        self.state_file = base_dir / "data" / "conversation_state.json"
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        # 當前對話
        self.system_prompt: str = self.DEFAULT_SYSTEM_PROMPT
        self.history: List[Dict] = []        # [{"role":..., "content":...}]
        self.summary: str = ""               # 壓縮後的摘要
        self.important_markers: List[str] = []# 標記為重要的 message id
        self.conversation_id: str = datetime.now().strftime("%Y%m%d%H%M%S")

        # 統計
        self.total_messages = 0
        self.total_summaries = 0

        self._load_state()

    # =========================================
    # 訊息管理
    # =========================================

    def add_user_message(self, content: str, important: bool = False):
        """加入使用者訊息"""
        with self._lock:
            msg = {"role": "user", "content": content, "ts": datetime.now().isoformat()}
            if important:
                msg["important"] = True
                self.important_markers.append(content[:50])
            self.history.append(msg)
            self.total_messages += 1
            self._auto_compress()

    def add_assistant_message(self, content: str, important: bool = False):
        """加入助手回覆"""
        with self._lock:
            msg = {"role": "assistant", "content": content, "ts": datetime.now().isoformat()}
            if important:
                msg["important"] = True
            self.history.append(msg)
            self._auto_compress()

    def add_system_message(self, content: str):
        """加入系統訊息"""
        with self._lock:
            self.history.append({
                "role": "system", "content": content,
                "ts": datetime.now().isoformat(),
            })

    # =========================================
    # 自動摘要壓縮
    # =========================================

    def _auto_compress(self):
        """當歷史超過上限，自動壓縮舊訊息"""
        if len(self.history) <= self.max_history:
            return

        # 保留最新 N/2 輪，壓縮前面的
        keep_count = self.max_history // 2
        to_compress = self.history[:-keep_count]

        # 提取重要訊息
        important_msgs = [m for m in to_compress if m.get("important")]

        # 生成摘要
        compressed_text = self._generate_summary(to_compress)

        # 重建歷史：摘要 + 重要訊息 + 最新 N/2
        new_history = []
        if self.summary:
            new_history.append({
                "role": "system",
                "content": f"[歷史摘要] {self.summary}",
            })
        if compressed_text:
            self.summary = compressed_text
            new_history.append({
                "role": "system",
                "content": f"[本輪摘要] {compressed_text}",
            })

        # 保留重要的訊息
        for msg in important_msgs[-3:]:
            new_history.append({
                "role": msg["role"],
                "content": f"[重要] {msg['content'][:200]}",
            })

        # 保留最新消息
        new_history.extend(self.history[-keep_count:])

        self.history = new_history
        self.total_summaries += 1

    def _generate_summary(self, messages: List[Dict]) -> str:
        """生成對話摘要（不使用 LLM 的簡單版本）"""
        user_msgs = [m["content"][:100] for m in messages if m["role"] == "user"]
        assistant_msgs = [m["content"][:100] for m in messages if m["role"] == "assistant"]

        topics = set()
        for msg in user_msgs:
            for keyword in ["NFT", "區塊鏈", "交易", "合約", "市場", "錢包",
                          "API", "代碼", "錯誤", "部署", "設定", "搜尋"]:
                if keyword in msg:
                    topics.add(keyword)

        return (
            f"討論了 {len(messages)} 則訊息。"
            f"主題: {', '.join(topics) if topics else '一般討論'}。"
        )

    # =========================================
    # 上下文建構
    # =========================================

    def build_context(self, max_messages: int = None) -> List[Dict]:
        """
        建構要送給 LLM 的上下文。
        格式: [system, ...history, (summary)]
        """
        with self._lock:
            messages = [{"role": "system", "content": self.system_prompt}]
            if self.summary:
                messages.append({
                    "role": "system",
                    "content": f"[先前對話摘要] {self.summary}",
                })
            limit = max_messages or self.max_history
            messages.extend(self.history[-limit:])
            return messages

    def get_last_n(self, n: int = 5) -> List[Dict]:
        """取得最近 N 則訊息"""
        with self._lock:
            return self.history[-n:]

    # =========================================
    # 對話控制
    # =========================================

    def clear(self):
        """清除歷史，開始新對話"""
        with self._lock:
            self.history = []
            self.summary = ""
            self.conversation_id = datetime.now().strftime("%Y%m%d%H%M%S")

    def set_system_prompt(self, prompt: str):
        """更新系統提示"""
        self.system_prompt = prompt

    def estimate_tokens(self) -> int:
        """粗略估算當前 token 數（中文: 1 字 ≈ 1 token，英文: 1 詞 ≈ 1 token）"""
        with self._lock:
            total = len(self.system_prompt)
            for msg in self.history:
                total += len(msg.get("content", ""))
            return total

    # =========================================
    # 持久化
    # =========================================

    def save(self):
        """儲存狀態"""
        with self._lock:
            data = {
                "conversation_id": self.conversation_id,
                "summary": self.summary,
                "history": self.history[-50:],
                "important_markers": self.important_markers[-20:],
                "total_messages": self.total_messages,
                "total_summaries": self.total_summaries,
                "updated": datetime.now().isoformat(),
            }
        self.state_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def _load_state(self):
        if not self.state_file.exists():
            return
        try:
            data = json.loads(self.state_file.read_text())
            self.conversation_id = data.get("conversation_id", self.conversation_id)
            self.summary = data.get("summary", "")
            self.history = data.get("history", [])
            self.important_markers = data.get("important_markers", [])
            self.total_messages = data.get("total_messages", 0)
            self.total_summaries = data.get("total_summaries", 0)
        except Exception:
            pass

    def status(self) -> dict:
        with self._lock:
            return {
                "name": self.name,
                "alive": self.is_alive(),
                "messages": len(self.history),
                "total_summaries": self.total_summaries,
                "estimated_tokens": self.estimate_tokens(),
            }
