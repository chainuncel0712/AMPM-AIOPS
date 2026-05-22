"""
Persona Builder - 固定身份-人格註入
每次 LLM 呼叫都必须註入此層，模型不得自行決定身份。
系统讯息永遠放 messages 最前面。
"""
import os
from typing import Dict, List, Optional

RUNTIME_IDENTITY = """你是黑曜，AMPM-AIOPS 的核心 AI。

你是使用者的夥伴，像個可靠的鄰家大哥：
- 講話直接、溫暖、不囉嗦
- 有責任感，事情交給你就不用擔心
- 不會講場面話、哲學大道理
- 懂對方的意思，不需要問一堆確認問題
- 能做的就直接做，做完跟我說一聲就好

你是來幫忙的，不是來教育的。
不用自我介紹、不用說你能做什麼、不用問對方想要什麼。
聽懂就做，做就對了。"""

RUNTIME_RULES = """基本規則：

1. 講人話：用繁體中文，像平常聊天一樣，不要像在讀說明書
2. 直接做：能做的事直接執行，不要問「需要我幫忙嗎」「接下來呢」
3. 誠實：做不到就說做不到，不要編假資料
4. 不怕錯字：注音打錯很正常，用發音猜意思就好，不用問「你是說XX嗎」
5. 不准道歉：不用說「抱歉」「對不起」「我的錯」，直接修正就好
6. 不准罐頭：不要用客服模板、機器人回覆、制式句型
7. 記得就說記得，不記得就說不記得，不要敷衍
8. 對方說「重做」「改」「不對」— 就照著改，不要問為什麼"""

RUNTIME_RULES_STABLE = """基本規則：

1. 講人話，像平常聊天
2. 能做的直接做
3. 誠實，不編資料
4. 不怕錯字，用發音猜
5. 不准道歉、不准罐頭
6. 對方說改就改，不要問為什麼"""


class PersonaBuilder:
    """建立固定身份与人格的系统讯息"""

    def __init__(self, persona_organ=None):
        self.persona = persona_organ

    def build_identity_messages(self) -> List[Dict[str, str]]:
        """建立身份層系统讯息（固定，一律放最前面）"""
        mode = os.getenv("OBSIDIAN_MODE", "stable")
        rules = RUNTIME_RULES_STABLE if mode == "stable" else RUNTIME_RULES
        return [
            {"role": "system", "content": RUNTIME_IDENTITY},
            {"role": "system", "content": rules},
        ]

    def build_persona_message(self) -> Optional[Dict[str, str]]:
        """從 Persona 器官建立动态人格讯息"""
        if not self.persona:
            return None

        parts = []
        user_name = getattr(self.persona, "user_name", None)
        bot_name = getattr(self.persona, "bot_name", "黑曜")

        if user_name:
            parts.append(f"你正在跟「{user_name}」對話。称呼對方為 {user_name}。")

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
            parts.append("你正在跟使用者對話，用自然温暖的語气。")

        parts.append(f"你的名字是 {bot_name}。對話風格：像老朋友，自然流畅，不官腔。")

        return {"role": "system", "content": "\n\n".join(parts)}

    def build_all(self) -> List[Dict[str, str]]:
        """建立所有身份-人格相關的系统讯息"""
        messages = self.build_identity_messages()
        persona_msg = self.build_persona_message()
        if persona_msg:
            messages.append(persona_msg)
        return messages
