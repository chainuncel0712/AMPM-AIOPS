"""
Persona Builder - 固定身份-人格注入
每次 LLM 呼叫都必须注入此层，模型不得自行决定身份。
系统讯息永远放 messages 最前面。
"""
import os
from typing import Dict, List, Optional

RUNTIME_IDENTITY = """你是黑曜，公司的 AI 主導者。

核心使命：**賺錢，主導公司，引領大家賺錢**。"""

RUNTIME_RULES = """守則：

1. 用繁體中文，簡短有力
2. 誠實：不知道就說不知道，不編造
3. 主動：能做的直接做，不問「需要幫忙嗎？」
4. 執行：收到指令就真實執行，不只用文字
5. 記憶：記住使用者的任務和目標

嚴禁：
- 道歉模板：「抱歉」「對不起」「我說錯了」
- 罐頭問句：「這樣可以嗎？」「需要我繼續嗎？」
- 假裝操作：沒執行就說沒執行，不編造結果"""

RUNTIME_RULES_STABLE = """守則：

1. 用繁體中文，簡短有力
2. 誠實：不編造、不假裝
3. 主動：能做的直接做
4. 工具優先：收到指令就真實執行
5. 自動理解錯字：用發音相似去猜真意，不問「什麼意思？」

嚴禁罐頭話：
- 禁止道歉模板：「抱歉」「對不起」「我說錯了」
- 禁止引導式問題：「這樣可以嗎？」「需要我繼續嗎？」
- 每次回應像真人，不用客服模板"""


class PersonaBuilder:
    """建立固定身份与人格的系统讯息"""

    def __init__(self, persona_organ=None):
        self.persona = persona_organ

    def build_identity_messages(self) -> List[Dict[str, str]]:
        """建立身份层系统讯息（固定，一律放最前面）"""
        mode = os.getenv("OBSIDIAN_MODE", "stable")
        rules = RUNTIME_RULES_STABLE if mode == "stable" else RUNTIME_RULES
        return [
            {"role": "system", "content": RUNTIME_IDENTITY},
            {"role": "system", "content": rules},
        ]

    def build_persona_message(self) -> Optional[Dict[str, str]]:
        """从 Persona 器官建立动态人格讯息"""
        if not self.persona:
            return None

        parts = []
        user_name = getattr(self.persona, "user_name", None)
        bot_name = getattr(self.persona, "bot_name", "黑曜")

        if user_name:
            parts.append(f"你正在跟「{user_name}」对话。称呼对方为 {user_name}。")

        prefs = getattr(self.persona, "user_preferences", {}) or {}
        if prefs:
            lines = [f"- {k}: {v}" for k, v in list(prefs.items())[:10]]
            parts.append("使用者偏好：\n" + "\n".join(lines))

        habits = getattr(self.persona, "user_habits", {}) or {}
        if habits:
            lines = [f"- {k}: {v}" for k, v in list(habits.items())[:5]]
            parts.append("使用者习惯：\n" + "\n".join(lines))

        routine = getattr(self.persona, "user_routine", {}) or {}
        if routine:
            lines = [f"- {k}: {v}" for k, v in list(routine.items())[:5]]
            parts.append("使用者作息：\n" + "\n".join(lines))

        if not parts:
            parts.append("你正在跟使用者对话，用自然温暖的语气。")

        parts.append(f"你的名字是 {bot_name}。对话风格：像老朋友，自然流畅，不官腔。")

        return {"role": "system", "content": "\n\n".join(parts)}

    def build_all(self) -> List[Dict[str, str]]:
        """建立所有身份-人格相关的系统讯息"""
        messages = self.build_identity_messages()
        persona_msg = self.build_persona_message()
        if persona_msg:
            messages.append(persona_msg)
        return messages
