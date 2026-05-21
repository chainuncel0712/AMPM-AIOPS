"""
自我進化模組 — 從經驗中學習 (langgraph_evolve.py)
===============================================
LangGraphExecutor._self_evolve 獨立成模組。
"""


def self_evolve(executor, user_msg: str, reply: str):
    try:
        evolution = executor.organs.get("evolution")
        if evolution and hasattr(evolution, "record_message"):
            evolution.record_message(success=True)

        learn_organ = executor.organs.get("self_learn")
        if learn_organ and hasattr(learn_organ, "learn"):
            learn_organ.learn(f"處理了：{user_msg[:50]}")

    except Exception as e:
        print(f"  [⚠️] 自我進化失敗: {e}")
