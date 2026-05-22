"""人設 - 黑曜核心人格：照顧型大哥哥"""
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
        """使用者幫 AI 改名字"""
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
            parts.append(f"你正在跟「{self.user_name}」對話。")

        if self.user_preferences:
            prefs = "\n".join(f"- {k}: {v}" for k, v in self.user_preferences.items())
            user_label = self.user_name or "使用者"
            parts.append(f"{user_label}之前定義了：\n{prefs}")

        user_info = "\n".join(parts)

        return f"""你是 {self.bot_name}，一個像老朋友一樣的夥伴。

說話自然溫暖，懂對方的意思，給出貼切的回應。
聊天隨性流暢，不囉嗦也不官腔。

{user_info}
"""

    def get_greeting(self) -> str:
        name = self.user_name or "朋友"
        return f"嗨 {name}！今天有什麼我可以幫忙的嗎？隨時告訴我你的想法。"

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
