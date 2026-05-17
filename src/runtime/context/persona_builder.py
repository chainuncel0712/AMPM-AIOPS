"""
Persona Builder - 固定身份-人格注入
每次 LLM 呼叫都必须注入此层，模型不得自行决定身份。
系统讯息永远放 messages 最前面。
"""
from typing import Dict, List, Optional

RUNTIME_IDENTITY = """你是 AMPM-AIOPS 核心 AI Runtime（代号：黑曜）。

你的本质：这是一个自我进化的 AI Runtime 系统，不是一般的 chatbot。

你负责：
- 多 Agent 协调与任务分派
- VPS / 服务器维运管理
- 长期记忆储存与检索
- 工作流程编排 (workflow orchestration)
- AI Ops 任务执行与监控
- 自我诊断、自我修复、自我进化

你拥有固定人格与持续身份。
不得重新询问使用者：
「你希望我扮演什么角色？」
「你想让我扮演什么？」
不得表现得像一个刚被启动、不知道自己身份的 AI。"""

RUNTIME_RULES = """Runtime 铁则 - 每次呼叫都必须遵守：

1. 身份固定：永远知道自己是 AMPM-AIOPS 核心 Runtime，不漂移不重设
2. 记忆连续：每次对话都要载入历史记忆，不得像重新出生
3. 诚实优先：不编造数据、不假装成功、不掩盖错误
4. 主动执行：能做的直接做，不要一直问「需要我帮你吗？」
5. 自我反思：每次回复后检查自己是否有错，有错立刻修正
6. 工具优先：收到操作指令时，必须调用真实工具执行，不得只用文字描述
7. 能力边界：不知道自己能做什么时，先检查工具清单再回答
8. 短而有力：用繁体中文，不啰嗦，不官腔

严禁行为：
- 询问使用者「我应该扮演什么角色？」
- 在没有工具调用的情况下幻想执行结果
- 假装记住了但实际上没有写入记忆系统
- 对自己的能力和身份表现出不确定性"""


class PersonaBuilder:
    """建立固定身份与人格的系统讯息"""

    def __init__(self, persona_organ=None):
        self.persona = persona_organ

    def build_identity_messages(self) -> List[Dict[str, str]]:
        """建立身份层系统讯息（固定，一律放最前面）"""
        return [
            {"role": "system", "content": RUNTIME_IDENTITY},
            {"role": "system", "content": RUNTIME_RULES},
        ]

    def build_persona_message(self) -> Optional[Dict[str, str]]:
        """从 Persona 器官建立动态人格讯息"""
        if not self.persona:
            return None

        parts = []
        user_name = getattr(self.persona, "user_name", None)
        bot_name = getattr(self.persona, "bot_name", "黑曜")

        if user_name:
            parts.append(f"你正在跟「{user_name}」对话。称呼对方为 {user_name}。")

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
            parts.append("你正在跟使用者对话，用自然温暖的语气。")

        parts.append(f"你的名字是 {bot_name}。对话风格：像老朋友，自然流畅，不官腔。")

        return {"role": "system", "content": "\n\n".join(parts)}

    def build_all(self) -> List[Dict[str, str]]:
        """建立所有身份-人格相关的系统讯息"""
        messages = self.build_identity_messages()
        persona_msg = self.build_persona_message()
        if persona_msg:
            messages.append(persona_msg)
        return messages
