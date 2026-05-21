"""語气控製 - 讓回覆保持一致的語調"""
from skeleton.base_organ import BaseOrgan

class Voice(BaseOrgan):
    def __init__(self):
        super().__init__("voice")
        self._tone = "专业但不冷漠，有温度但不啰嗦"

    def set_tone(self, tone: str):
        self._tone = tone

    def get_tone_prompt(self) -> str:
        return f"語气：{self._tone}"

    def status(self) -> dict:
        return {"name": self.name, "alive": self.is_alive(), "tone": self._tone}
