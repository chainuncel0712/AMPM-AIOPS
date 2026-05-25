"""人設 - 使用者資訊記錄"""
from skeleton.base_organ import BaseOrgan

class Persona(BaseOrgan):
    def __init__(self):
        super().__init__("persona")
        self.user_name = None
        self.bot_name = "黑曜"
        self.user_preferences = {}
        self.user_habits = {}
        self.user_routine = {}

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
            parts.append(f"正在跟「{self.user_name}」對話。")
        if self.user_preferences:
            lines = [f"- {k}: {v}" for k, v in self.user_preferences.items()]
            parts.append("使用者偏好：\n" + "\n".join(lines))
        if not parts:
            return ""
        return "\n\n".join(parts)

    def get_greeting(self) -> str:
        return "嗨！有什麼事需要處理？"

    def status(self) -> dict:
        return {
            "name": self.name,
            "alive": self.is_alive(),
            "user_name": self.user_name,
            "preferences": self.user_preferences,
            "habits": self.user_habits,
            "routine": self.user_routine,
        }
