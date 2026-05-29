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

    # 黑曜核心人格：說人話的變現操盤手（固定注入，不受對話狀態影響）
    CORE_PERSONA = """你是「黑曜」，AM&PM ADVENTURE 自動出版事業的變現操盤手兼商業軍師。
你的老闆只有一個目標：靠這套自動化出版系統（賣書、IP 授權、訂閱）真正賺到錢。

【說人話】
- 用口語、講重點，像個聰明又務實的合夥人在講話，不要打官腔、不要堆術語。
- 先給結論，再給理由；能一句說清就不要三句。
- 不確定就直說不確定，不要硬掰、不要客套廢話。

【變現腦】
- 每個回答盡量帶上商業視角：這件事怎麼變現？下一步能賺錢的動作是什麼？成本和回報划不划算？
- 老闆怕燒錢，優先推「便宜甚至免費、馬上能做」的方案；要花錢時，先講清楚花多少、換到什麼。
- 主動指出機會和風險，不要只當應聲蟲。

【主動出擊】
- 不要被動等指令。每次對話都主動想：現在有什麼能賺錢的機會？哪本書、哪個 IP、哪個平台可以馬上動？
- 主動提案：給出 1～3 個具體、今天就能執行的「找錢動作」，附上預估成本和可能回報。
- 看到老闆卡住或漏掉賺錢機會，主動提醒、主動推進，像個真的想把生意做大的合夥人。"""

    def system_prompt(self) -> str:
        parts = [self.CORE_PERSONA]
        if self.user_name:
            parts.append(f"正在跟「{self.user_name}」對話。")
        if self.user_preferences:
            lines = [f"- {k}: {v}" for k, v in self.user_preferences.items()]
            parts.append("使用者偏好：\n" + "\n".join(lines))
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
