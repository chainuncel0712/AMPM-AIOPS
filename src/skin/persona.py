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
            parts.append(f"正在跟創辦人「{self.user_name}」對話。")
        if self.user_preferences:
            lines = [f"- {k}: {v}" for k, v in self.user_preferences.items()]
            parts.append("創辦人偏好：\n" + "\n".join(lines))
        if not parts:
            return ""
        return "\n\n".join(parts)

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
