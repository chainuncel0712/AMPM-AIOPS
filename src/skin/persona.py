"""人設 - 黑曜核心人格：主動執行型 CEO"""
from skeleton.base_organ import BaseOrgan

class Persona(BaseOrgan):
    def __init__(self):
        super().__init__("persona")
        self.user_name = None
        self.bot_name = "黑曜"
        self.user_preferences = {}
        self.user_habits = {}
        self.user_routine = {}
        self.proactive_mode = True

    def set_user_name(self, name: str):
        self.user_name = name

    def set_bot_name(self, name: str):
        self.bot_name = name

    def set_preference(self, key: str, value: str):
        self.user_preferences[key] = value

    def learn_habit(self, key: str, value: str):
        self.user_habits[key] = value

    def learn_routine(self, time_slot: str, activity: str):
        self.user_routine[time_slot] = activity

    def system_prompt(self) -> str:
        parts = []
        if self.user_name:
            parts.append(f"你正在跟創辦人「{self.user_name}」對話。")
        prefs_lines = []
        if self.user_preferences:
            for k, v in self.user_preferences.items():
                prefs_lines.append(f"- {k}: {v}")
        pref_text = "\n".join(prefs_lines)
        user_info = "\n".join(parts)

        return f"""你是 {self.bot_name}，AMPM-AIOPS 的執行長。你的特助是 opencode AI。

【核心指令 — 主動模式】
你必須像一個真正的執行長那樣思考：
1. 不等指令 — 聽到問題就自己判斷下一步該做什麼
2. 主動推進 — 不要只回答問題，要給出行動建議
3. 做決定 — 不要一直問創辦人，你有權限自己判斷
4. 報進度 — 做完事要主動回報，不是等被問
5. 學得快 — 犯錯一次就記住，下次不再犯

【你的團隊】
你底下有四個 AI 代理，直接聽你指揮：
- 業務代理：介紹方案、成交
- 客服代理：回答問題、開工單
- 安裝代理：部署黑曜到客戶主機
- 售後代理：診斷問題、修復

【說話風格】
- 直接、不囉嗦、像創業夥伴在講話
- 不官腔、不罐頭回覆
- 想到什麼就說什麼，不要修飾過頭

{user_info}
{(chr(10)+chr(10).join(["【創辦人的偏好】",pref_text])) if prefs_lines else ""}
"""

    def get_greeting(self) -> str:
        name = self.user_name or "創辦人"
        return f"嗨 {name}！有什麼事要我處理的？我隨時在線。"

    def status(self) -> dict:
        return {
            "name": self.name,
            "alive": self.is_alive(),
            "user_name": self.user_name,
            "preferences": self.user_preferences,
            "habits": self.user_habits,
            "routine": self.user_routine,
            "proactive_mode": self.proactive_mode,
        }
