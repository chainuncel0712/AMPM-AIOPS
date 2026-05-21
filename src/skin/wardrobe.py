"""衣柜 - 多套風格，隨時切换"""
from skeleton.base_organ import BaseOrgan

class Wardrobe(BaseOrgan):
    def __init__(self):
        super().__init__("wardrobe")
        self._outfits = {
            "default": {
                "name": "黑曜·標準模式",
                "style": "专业、直接、有行动力",
                "tone": "繁體中文，简潔有力",
            },
            "creative": {
                "name": "黑曜·創意模式",
                "style": "开放、联想力强、大胆",
                "tone": "繁體中文，富有画面感",
            },
            "analyst": {
                "name": "黑曜·分析模式",
                "style": "严谨、数据导向、逻辑清晰",
                "tone": "繁體中文，条列分明",
            },
        }
        self._current = "default"

    def wear(self, name: str) -> dict:
        if name in self._outfits:
            self._current = name
        return self._outfits[self._current]

    def current(self) -> dict:
        return self._outfits[self._current]

    def list_outfits(self) -> list:
        return list(self._outfits.keys())

    def status(self) -> dict:
        return {"name": self.name, "alive": self.is_alive(), "current": self._current}
