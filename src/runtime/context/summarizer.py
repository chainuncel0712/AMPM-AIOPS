"""
Summarizer — 對話壓縮摘要
==========================
將長對話壓縮為簡短摘要，避免 prompt 過長。

核心邏輯：
1. 優先使用 LLM 生成摘要
2. LLM 不可用時使用關鍵字萃取
3. 最差情況使用簡單截斷
"""

from typing import Callable, List, Optional


class Summarizer:
    """對話摘要器 — 壓縮長對話為濃縮摘要"""

    def __init__(self, llm_call: Optional[Callable] = None):
        self.llm_call = llm_call
        self.max_input_chars = 3000
        self.max_summary_chars = 300

    def summarize(self, text: str, context: str = "") -> str:
        """將長文字壓縮為簡短摘要

        Args:
            text: 要摘要的原始文字
            context: 當前上下文（幫助生成更相關的摘要）

        Returns:
            壓縮後的摘要字串
        """
        if not text or len(text) < 200:
            return text[: self.max_summary_chars]

        truncated = text[: self.max_input_chars]

        if self.llm_call:
            return self._llm_summarize(truncated, context)

        return self._keyword_summarize(truncated)

    def _llm_summarize(self, text: str, context: str = "") -> str:
        """使用 LLM 生成摘要"""
        prompt = (
            "將以下對話濃縮為一句中文摘要，只保留關鍵資訊：\n\n"
            f"{text}"
        )
        if context:
            prompt = f"當前情境：{context}\n\n{prompt}"

        try:
            messages = [
                {
                    "role": "system",
                    "content": "你是摘要助手。只輸出濃縮摘要，不要多餘文字。",
                },
                {"role": "user", "content": prompt},
            ]
            result = self.llm_call(messages, temperature=0.3)
            if result and len(result) > 5:
                return result[: self.max_summary_chars]
        except Exception:
            pass

        return self._keyword_summarize(text)

    def _keyword_summarize(self, text: str) -> str:
        """簡單關鍵字摘要：取開頭 + 關鍵句"""
        sentences = text.replace("\n", " ").split("。")
        if len(sentences) <= 2:
            return text[: self.max_summary_chars]
        return sentences[0].strip() + "。" + (sentences[-1].strip() + "。" if len(sentences[-1]) > 2 else "")

    def summarize_turns(self, turns: List[dict]) -> str:
        """將多輪對話壓縮為一段摘要

        Example:
            turns = [
                {"user": "幫我修 VPS", "assistant": "好的，正在檢查..."},
                {"user": "CPU 100%了", "assistant": "已找到問題進程，正在重啟..."},
            ]
            → "使用者正在修復 VPS CPU 過載問題。已定位並重啟問題進程。"
        """
        if not turns:
            return ""

        lines = []
        for t in turns[-10:]:
            u = t.get("user", "")[:100]
            a = t.get("assistant", "")[:100]
            if u:
                lines.append(f"使用者: {u}")
            if a:
                lines.append(f"黑曜: {a}")

        full = "\n".join(lines)
        return self.summarize(full)

    def status(self) -> dict:
        return {
            "has_llm": self.llm_call is not None,
            "max_input_chars": self.max_input_chars,
            "max_summary_chars": self.max_summary_chars,
        }
