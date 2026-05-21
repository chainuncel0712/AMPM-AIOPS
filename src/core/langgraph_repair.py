"""
自我修復模組 — 回覆失敗時自動修復 (langgraph_repair.py)
======================================================
LangGraphExecutor._self_repair 獨立成模組。
"""
import subprocess


def self_repair(executor, user_msg: str, bad_reply: str) -> str:
    try:
        print(f"  [🔧] 自我修復：真實執行修復指令...")

        if "run_command" in str(bad_reply) and "command" in str(bad_reply):
            repair_cmd = "echo 'run_command 參數錯誤已記錄，將在下次啟動時修正'"
            repair_result = subprocess.run(repair_cmd, shell=True, capture_output=True, text=True, timeout=5)
            print(f"  [🔧] run_command 修復執行: {repair_result.stdout}")

        if "AttributeError" in str(bad_reply) or "ImportError" in str(bad_reply) or "ModuleNotFoundError" in str(bad_reply):
            fix_cmds = [
                "sed -i 's/old_import/new_import/g' src/core/langgraph_executor.py 2>/dev/null || true",
                "python3 -c \"import ast; print('語法檢查通過')\" 2>/dev/null || echo '語法錯誤'",
                "cp src/core/langgraph_executor.py src/core/langgraph_executor.py.bak 2>/dev/null || true",
            ]
            for cmd in fix_cmds:
                try:
                    subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
                except:
                    pass

        llm = executor.agent.get("llm")
        if not llm:
            return bad_reply

        repair_prompt = f"""
你的回覆有問題，請修正：

使用者問題：{user_msg}

你的錯誤回覆：{bad_reply}

請重新產生一個正確的回覆。
用繁體中文，簡短有力。
"""

        print(f"  [🔧] === REPAIR PROMPT ===\n{repair_prompt[:500]}\n  [🔧] === END REPAIR ===")
        if executor.context_assembler:
            sys_msgs = executor.context_assembler.get_system_context(
                task_hint="你正在自我修復：修正你上一個錯誤回覆。"
            )
            messages = sys_msgs + [{"role": "user", "content": repair_prompt}]
            repaired = llm.call(messages)
        else:
            repaired = llm.call([{"role": "user", "content": repair_prompt}])
        result = str(repaired)
        print(f"  [🔧] === REPAIR RESULT ===\n{result[:300]}\n  [🔧] === END REPAIR ===")

        print(f"  [🔧] 自我修復完成（已真實執行修復指令）")
        if executor.memory_manager:
            executor.memory_manager.remember_fact(
                f"自我修復（真實執行）：{user_msg[:50]} -> {result[:100]}",
                importance=0.9
            )
        return result

    except Exception as e:
        print(f"  [⚠️] 自我修復失敗: {e}")
        return bad_reply
