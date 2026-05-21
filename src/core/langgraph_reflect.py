"""
自我反省模組 — 檢查回覆是否正確 (langgraph_reflect.py)
====================================================
LangGraphExecutor._self_reflect 獨立成模組。
"""


def self_reflect(executor, user_msg: str, reply: str, depth: int = 0) -> str:
    if depth >= 2:
        return reply

    try:
        llm = executor.agent.get("llm")
        if not llm:
            return reply

        reflection_prompt = f"""
請檢查以下回覆是否正確：

使用者問題：{user_msg}

你的回覆：{reply}

請分析：
1. 回覆是否正確？
2. 有沒有錯誤？
3. 有沒有可以改進的地方？

如果正確，請回傳 "✅ 正確"
如果有錯誤，請回傳修正後的版本。
"""

        print(f"  [🧠] === REFLECTION PROMPT ===\n{reflection_prompt[:500]}\n  [🧠] === END REFLECTION ===")
        if executor.context_assembler:
            sys_msgs = executor.context_assembler.get_system_context(
                task_hint="你正在自我反省：檢查你的回覆是否正確。"
            )
            messages = sys_msgs + [{"role": "user", "content": reflection_prompt}]
            reflection_result = llm.call(messages)
        else:
            reflection_result = llm.call([{"role": "user", "content": reflection_prompt}])
        result = str(reflection_result)
        print(f"  [🧠] === REFLECTION RESPONSE ===\n{result[:300]}\n  [🧠] === END REFLECTION ===")

        if "✅" in result:
            print(f"  [🧠] 自我反省：回覆正確")
            return reply

        print(f"  [🧠] 自我反省：發現錯誤，已修正")
        if executor.memory_manager:
            executor.memory_manager.remember_fact(
                f"自我反省修正：{user_msg[:50]} -> {result[:100]}",
                importance=0.9
            )
        return self_reflect(executor, user_msg, result, depth + 1)

    except Exception as e:
        print(f"  [⚠️] 自我反省失敗: {e}")
        return reply
