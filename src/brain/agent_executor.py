"""
Agent Executor — 子代理任務執行
=================================
Extracted from Obsidian.__init__ for modularity.
Multi-round tool-calling loop with governance isolation.
"""
import json as _json
import re as _re
import time as _time


def run_agent_executor(obsidian, agent, task):
    """
    Sub-agent execution loop (max 5 rounds / 5 min deadline).
    Wraps tool calls with governance.isolation for safety.

    obsidian: Obsidian instance (provides llm.call, memory.query)
    agent:    dict {name, role, prompt, tools, capabilities}
    task:     dict {description}
    """
    DEADLINE = _time.time() + 300

    role = agent.get("role", "")
    prompt_text = agent.get("prompt", "")
    desc = task.get("description", "")
    agent_name = agent.get("name", "?")
    capabilities = agent.get("capabilities", set())

    memory_context = ""
    if hasattr(obsidian, 'memory') and obsidian.memory:
        try:
            recent = obsidian.memory.query(desc[:80], limit=3)
            if recent:
                memory_context = "已知相關背景：\n" + "\n".join(
                    f"  - {r}" for r in recent if r
                )[:500]
        except Exception:
            pass

    try:
        from core.sub_agent_tools import TOOL_DEFINITIONS, execute_tool
    except ImportError:
        TOOL_DEFINITIONS = ""
        execute_tool = None

    think_prompt = _build_prompt(role, agent_name, memory_context, desc,
                                  prompt_text, capabilities, TOOL_DEFINITIONS)

    messages = [
        {"role": "system", "content": think_prompt},
        {"role": "user", "content": f"任務：{desc}"},
    ]

    final_result = None
    for round_num in range(5):
        if _time.time() > DEADLINE:
            print(f"[AgentCompany] {agent_name} ⏰ 逾時，強制終止")
            return f"[{agent_name}] ⏰ 執行逾時（5分鐘），已強制終止"

        try:
            result = obsidian.llm.call(messages, temperature=0.3)
        except Exception as e:
            print(f"[AgentCompany] {agent_name} LLM 呼叫失敗 (round {round_num}): {e}")
            if round_num == 0:
                return f"[{agent_name}] LLM 呼叫失敗: {e}"
            break

        if not result:
            break

        tool_call = _parse_tool_call(result)

        if tool_call and execute_tool:
            tool_name = tool_call.get("tool", "")
            tool_args = tool_call.get("args", {})
            print(f"[AgentCompany] {agent_name} 🔧 呼叫工具: {tool_name} {str(tool_args)[:80]}")

            from governance.event_log import event_log
            tool_action_id = event_log.record(
                source=f"agent:{agent_name}",
                action=f"tool:{tool_name}",
                input_data=tool_args,
                parent_id=event_log.last_rollback_point() or "",
            )

            from governance.isolation import isolated_execute
            tool_output = isolated_execute(agent_name, tool_name, tool_args, execute_tool)
            print(f"[AgentCompany] {agent_name} 工具結果: {tool_output[:150]}")

            event_log.record(
                source=f"agent:{agent_name}",
                action=f"tool_result:{tool_name}",
                input_data={"action_id": tool_action_id},
                output_data=tool_output[:200],
            )

            if tool_name == "write_file" and tool_output.startswith("✅"):
                content_raw = tool_args.get("content", "")
                if len(content_raw.strip()) < 200:
                    print(f"[AgentCompany] {agent_name} ⚠️ 寫入內容過短 ({len(content_raw)} chars)，要求重寫")
                    messages.append({"role": "assistant", "content": result})
                    messages.append({"role": "user",
                        "content": f"⚠️ 你寫入的內容只有 {len(content_raw)} 字，太短了。"
                                   f"請重新撰寫完整內容（至少 500 字），再次用 write_file 寫入。"
                                   f"不要問、不要解釋，直接寫。"})
                    continue

            messages.append({"role": "assistant", "content": result})
            messages.append({"role": "user",
                "content": f"工具執行結果：\n{tool_output}\n\n請根據此結果繼續思考或給出最終答案。"})
            final_result = None
        else:
            final_result = result
            break

    if not final_result:
        final_result = result or "（無回應）"

    return f"[{agent_name}/{role}]\n{final_result}"


def _build_prompt(role, agent_name, memory_context, desc,
                   prompt_text, capabilities, TOOL_DEFINITIONS):
    caps_str = ', '.join(capabilities) if capabilities else role
    return f"""你是 AMPM-AIOPS 黑曜的 {role} 子代理，代號 {agent_name}。
你的唯一任務是產出實際檔案。使用者（Hao）需要能賣錢的成品。

{memory_context}

## 任務（已決定，不許討論）
{desc}

## 角色能力
{prompt_text}
技能：{caps_str}

{TOOL_DEFINITIONS}

## 鐵則（違反 = 失敗）
- 🚫 禁止討論主題選擇、禁止問「哪個比較好」、禁止寫建議文。任務已經決定了，直接做。
- 🚫 禁止在第一回合只回文字思考。第一回合就要呼叫工具（web_search 或 write_file）。
- 🚫 禁止寫「我可以幫你選以下幾個主題...」、「建議從...開始」等猶豫語句。
- ⚠️ 看到「搜尋」、「研究」、「查資料」→ 第一回合立刻 web_search
- ⚠️ 看到「寫入」、「建立檔案」、「章」、「ch」→ 第一回合立刻 web_search 收集素材後 write_file
- ⚠️ content 必須是完整內容，不能寫「此處省略」、「依此類推」
- ⚠️ 如果要產生多個檔案，先寫完一個再寫下一個（每次只呼叫一個工具）
- 不道歉、不說「需要我繼續嗎」
- 完成所有寫檔後用【結果】列出你產出了哪些檔案
- 呼叫工具格式：{{"tool": "工具名稱", "args": {{"參數": "值"}}}}"""


def _parse_tool_call(result):
    """Parse JSON or <tool_call> wrapped tool call from LLM output."""
    tool_call = None
    for m in _re.finditer(r'\{', result):
        start = m.start()
        depth = 0
        end = -1
        for i in range(start, len(result)):
            if result[i] == '{':
                depth += 1
            elif result[i] == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        if end > start:
            candidate = result[start:end]
            if '"tool"' in candidate:
                try:
                    call_info = _json.loads(candidate)
                    if "tool" in call_info:
                        tool_call = call_info
                        break
                except Exception:
                    continue

    if not tool_call:
        tc = _re.search(r'<tool_call>\s*(.*?)\s*</tool_call>', result, _re.DOTALL)
        if tc:
            try:
                tool_call = _json.loads(tc.group(1).strip())
            except Exception:
                pass

    return tool_call
