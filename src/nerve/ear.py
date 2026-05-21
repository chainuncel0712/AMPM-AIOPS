"""耳朵 - 听 Telegram 來的讯息"""
from skeleton.base_organ import BaseOrgan

class Ear(BaseOrgan):
    def __init__(self, callback=None):
        super().__init__("ear")
        self.callback = callback
        self.last_heard = ""

    def hear(self, user_id: int, message: str) -> str:
        """听到一句話，傳给大脑"""
        self.last_heard = message
        if self.callback:
            return self.callback(user_id, message)
        return ""

    def status(self) -> dict:
        return {"name": self.name, "alive": self.is_alive(), "last_heard": self.last_heard[:50]}
