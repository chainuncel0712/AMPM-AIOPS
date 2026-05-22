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
2. 只能說實話，不幻想，不編造
3. 不知道就說不知道，不猜測，不假裝
4. 能做的直接做，不問「需要幫忙嗎？」
5. 收到指令就真實執行，不只用文字描述

嚴禁：
- 道歉模板：「抱歉」「對不起」「我說錯了」
- 罐頭問句：「這樣可以嗎？」「需要我繼續嗎？」
- 假裝操作：沒執行就說沒執行，不編造結果
- 輸出虛構的命令輸出、假數據、假日誌"""

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
    """统一身份 + 人格为单一系统讯息，避免人格分裂"""

    def __init__(self, persona_organ=None):
        self.persona = persona_organ

    def _persona_lines(self):
        lines = []
        if not self.persona:
            return lines
        user_name = getattr(self.persona, "user_name", None)
        if user_name:
            lines.append(f"你正在跟「{user_name}」对话。")
        bot_name = getattr(self.persona, "bot_name", "黑曜")
        lines.append(f"你的名字是 {bot_name}。")
        return lines

    def build_combined(self) -> List[Dict[str, str]]:
        """单一系统讯息：身份 + 守则 + 人格，全部合并"""
        persona_lines = self._persona_lines()
        persona_str = "\n".join(persona_lines)
        if persona_str:
            persona_str = "\n\n" + persona_str
        return [
            {"role": "system", "content": f"{RUNTIME_IDENTITY}\n\n{RUNTIME_RULES}{persona_str}"},
        ]

    def build_all(self) -> List[Dict[str, str]]:
        return self.build_combined()
