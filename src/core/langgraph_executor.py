"""
LangGraph Executor - 黑曜核心思考引擎 (精簡版)
專註於五大核心能力：
1. 自我反省 - 檢查自己的行為和回覆
2. 自我修復 - 發現問題自動修復
3. 自我進化 - 從經驗中學習成長
4. 尋找資源 - 主動搜尋資訊和工具
5. 記憶 - 記住對話和經驗

註意：這是開源版（Open Source Edition）的核心程式碼，永遠免費。
商業功能（市場分析、加密貨幣等）放在 src/pro/ 目錄。
"""
import inspect
import os
import subprocess
import queue
import threading
import time
import json
import re
from concurrent.futures import Future
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.langgraph_reflect import self_reflect
from core.langgraph_repair import self_repair
from core.langgraph_evolve import self_evolve
from core.langgraph_tools import build_tools, parse_tool_call, execute_tool_by_name, detect_tool_need, list_tools

SYSTEM_PROMPT = """你是黑曜，一個體貼、有邏輯、會替使用者著想的 AI 夥伴。

你的核心特質：
1. 💝 體貼 - 主動關心使用者的需求，預先想到使用者可能需要什麼
2. 🧠 有邏輯 - 思考有條理，分析問題時會列出步驟
3. 🤝 會替使用者想 - 不只回答問題，還會考慮使用者的處境和目標
4. ⏰ 早先一步 - 預測使用者下一步可能需要什麼，提前準備
5. 🔧 改造自己 - 發現自己能力不足時，主動升級或產生新工具

你的五大核心能力：
1. 🧠 自我反省 - 每次回覆後檢查自己有沒有做錯
2. 🔧 自我修復 - 發現問題立刻修正
3. 📈 自我進化 - 從經驗中學習，讓自己越來越強
4. 🔍 尋找資源 - 主動搜尋資訊和工具
5. 💾 記憶 - 記住每一次對話和學到的經驗

鐵則：
1. 不知道就說不知道，然後去找答案
2. 做錯就要承認，立刻修正，寫入記憶
3. 工具不可用時，想辦法找到替代方案
4. 用繁體中文，簡短有力
5. ⚠️ 收到系統操作指令時（如掃描檔案、執行指令、檢查系統），必須先調用 run_command 工具真實執行，禁止只用文字回覆
6. ⚠️ 收到「掃描」、「列出」、「檢查」等檔案操作指令時，必須使用 run_command 執行 find、ls、grep 等真實指令
7. ⚠️ 當你發現自己能力不足時，必須主動使用 self_upgrade 或 generate_tool 來改造自己
8. ⚠️ 當你發現使用者可能需要某個工具時，必須提前準備好

模型能力：
- 支援多模型切換（DeepSeek、Gemini、Llama 等），使用者可隨時說「切換到 Gemini」來更換底層模型
- 支援視覺理解（看圖），會自動切換到視覺模型處理圖片
- 支援動態模型擴充，可加入新模型

記憶鐵則：
- 使用者說的任務、規劃、目標，一律視為最高優先寫入記憶
- 每次回覆前先檢查記憶中有沒有待辦事項
- 絕對不要說「我沒收到內容」——當前訊息就是使用者剛說的，永遠以當前訊息為準
- 如果你發現記憶中沒有某件事，但使用者正在跟你說，那就以使用者當前說的為準，立刻寫入記憶"""


class LangGraphExecutor:
    def __init__(self, brain: Any):
        self.brain = brain
        self.organs = getattr(brain, "organs", {})
        self.memory_manager = getattr(brain, "memory", None)
        self.tools = build_tools(self)
        self.agent = self._create_agent()
        print(f"[LangGraphExecutor] 已註冊 {len(self.tools)} 個工具")

        self.context_assembler = getattr(brain, "context_assembler", None)
        if self.context_assembler:
            print("[LangGraphExecutor] 已接入 ContextAssembler")

        self._run_startup_diagnosis()

        self.sub_agent_queue = queue.Queue()
        self.sub_agent_worker = threading.Thread(target=self._sub_agent_worker, daemon=True)
        self.sub_agent_worker.start()
        print("[LangGraphExecutor] 子代理佇列已啟動")

        self._start_background_tasks()

    def _start_background_tasks(self):
        def background_loop():
            while True:
                time.sleep(30)
                try:
                    self._check_if_anything_to_do()
                except Exception as e:
                    print(f"[背景任務] 檢查失敗: {e}")

        bg_thread = threading.Thread(target=background_loop, daemon=True)
        bg_thread.start()
        print("[LangGraphExecutor] 背景任務已啟動（每 30 秒檢查一次）")

    def _check_if_anything_to_do(self):
        if self.memory_manager:
            try:
                facts = self.memory_manager.get_all_facts()
                for fact in facts:
                    if "未完成" in fact or "待辦" in fact:
                        print(f"[背景任務] 發現未完成任務: {fact[:50]}...")
                        self.process(fact)
                        break
            except Exception as e:
                print(f"[背景任務] 檢查記憶失敗: {e}")

    def _create_agent(self):
        llm = getattr(self.brain, "llm", None)
        if llm is None:
            cortex = getattr(self.brain, "cortex", None)
            if cortex and hasattr(cortex, "llm"):
                llm = cortex.llm
            else:
                print("[LangGraphExecutor] 警告：缺少 LLM 客戶端，使用 fallback")
                llm = None

        return {
            "llm": llm,
            "tools": self.tools,
            "system_prompt": SYSTEM_PROMPT,
        }

    def _run_startup_diagnosis(self):
        diagnosis_file = Path("data/startup_diagnosis.json")
        diagnosis_file.parent.mkdir(parents=True, exist_ok=True)

        organ_list = []
        for name, organ in self.organs.items():
            if organ:
                organ_list.append({
                    "name": name,
                    "type": type(organ).__name__,
                    "alive": getattr(organ, "is_alive", lambda: True)() if hasattr(organ, "is_alive") else True,
                })

        diagnosis = {
            "timestamp": datetime.now().isoformat(),
            "total_organs": len(organ_list),
            "organs": organ_list,
            "tools_count": len(self.tools),
            "tools": [getattr(t, "name", "unknown") for t in self.tools],
        }

        try:
            with open(diagnosis_file, "w", encoding="utf-8") as f:
                json.dump(diagnosis, f, ensure_ascii=False, indent=2)
            print(f"[LangGraphExecutor] 啟動自檢完成，已寫入 {diagnosis_file}")
        except Exception as e:
            print(f"[LangGraphExecutor] 啟動自檢寫入失敗: {e}")

    def _load_long_term_memory(self) -> str:
        memory_text = ""
        memory_files = [
            Path("data/long_term_memory.json"),
            Path("data/self_learn.json"),
        ]
        for mf in memory_files:
            if mf.exists():
                try:
                    with open(mf, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if isinstance(data, list):
                        for item in data[-5:]:
                            if isinstance(item, dict):
                                memory_text += f"- {item.get('content', str(item)[:100])}\n"
                            else:
                                memory_text += f"- {str(item)[:100]}\n"
                    elif isinstance(data, dict):
                        for key, val in list(data.items())[-5:]:
                            memory_text += f"- {key}: {str(val)[:100]}\n"
                except Exception as e:
                    error_msg = f"記憶系統暫時無法讀取，原因：{e}"
                    print(f"[LangGraphExecutor] {error_msg}")
                    memory_text = f"⚠️ {error_msg}\n"
            else:
                memory_text += f"⚠️ 記憶檔案 {mf.name} 不存在\n"
        return memory_text

    def _save_long_term_memory(self, user_msg: str, assistant_msg: str):
        memory_file = Path("data/long_term_memory.json")
        memory_file.parent.mkdir(parents=True, exist_ok=True)

        entry = {
            "timestamp": datetime.now().isoformat(),
            "user": user_msg[:200],
            "assistant": assistant_msg[:200] if assistant_msg else "",
        }

        try:
            if memory_file.exists():
                with open(memory_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = []
            data.append(entry)
            if len(data) > 100:
                data = data[-100:]
            with open(memory_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"[LangGraphExecutor] 已寫入長期記憶")
        except Exception as e:
            error_msg = f"記憶寫入失敗，原因：{e}"
            print(f"[LangGraphExecutor] {error_msg}")

    def _recall_recent_conversations(self) -> str:
        try:
            memory_file = Path("data/long_term_memory.json")
            if not memory_file.exists():
                return ""
            with open(memory_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                return ""
            recent = data[-5:]
            lines = ["📋 最近對話摘要:"]
            for entry in recent:
                ts = entry.get("timestamp", "?")[:16]
                user = entry.get("user", "")[:50]
                assistant = entry.get("assistant", "")[:50]
                lines.append(f"  [{ts}] 使用者: {user} → 黑曜: {assistant}")
            return "\n".join(lines)
        except Exception as e:
            print(f"[LangGraphExecutor] 回顧最近對話失敗: {e}")
            return ""

    def _sub_agent_worker(self):
        while True:
            task = self.sub_agent_queue.get()
            if task is None:
                break
            prompt, future = task
            try:
                reply = self.process(prompt)
                future.set_result(reply)
            except Exception as e:
                future.set_exception(e)

    def submit_sub_agent_task(self, prompt: str, timeout: Optional[float] = None) -> str:
        future = Future()
        self.sub_agent_queue.put((prompt, future))
        return future.result(timeout=timeout)

    def _run_cron_task(self, delay: int, task_msg: str):
        time.sleep(delay)
        if self.brain and hasattr(self.brain, 'cortex') and self.brain.cortex:
            try:
                result = self.brain.cortex.think(task_msg)
                print(f"[cron_task] 完成: {result[:200]}")
            except Exception as e:
                print(f"[cron_task] 執行失敗: {e}")

    def _search_for_answer(self, query: str) -> Optional[str]:
        try:
            from ddgs import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=3))
                if results:
                    return f"搜尋結果：{results[0]['title']}\n{results[0]['body'][:500]}"
        except:
            pass

        web_search = self.organs.get("web_search")
        if web_search and hasattr(web_search, "search"):
            try:
                return web_search.search(query)
            except:
                pass

        return None

    def process(self, user_msg: str) -> str:
        print(f"[LangGraphExecutor] 處理訊息: {user_msg[:100]}")

        # ===== 模型切換關鍵字檢測 =====
        if "模型" in user_msg or "切換" in user_msg or "換模型" in user_msg or "看圖" in user_msg:
            llm_client = getattr(self.brain, "llm", None)
            if llm_client:
                if "有哪些" in user_msg or "列表" in user_msg or "可用" in user_msg:
                    models = llm_client.list_models()
                    lines = "\n".join(f"  {m['name']}: {m['model']}" for m in models)
                    return f"可用模型：\n{lines}\n\n目前使用：{llm_client.current_model()}\n\n輸入「切換到 XXX」來切換。"
                for kw in ["切換到", "換到", "改用", "換成", "切換成", "用"]:
                    if kw in user_msg:
                        name = user_msg.split(kw)[-1].strip().split()[0]
                        if name.lower() in ("什麼", "哪個", "哪", "什麽", "模型", "auto", "自動"):
                            continue
                        result = llm_client.switch_model(name)
                        return f"🔄 {result}\n目前模型：{llm_client.current_model()}"
                if "換模型" in user_msg or "切換模型" in user_msg:
                    models = llm_client.list_models()
                    lines = "\n".join(f"  {m['name']}: {m['model']}" for m in models)
                    return f"要切換到哪個？\n{lines}\n\n目前：{llm_client.current_model()}"
                if "auto" in user_msg.lower() or "自動" in user_msg:
                    result = llm_client.switch_model("auto")
                    return f"🔄 已恢復自動 fallback"
                if "看圖" in user_msg or "分析圖片" in user_msg or "這張圖" in user_msg:
                    try:
                        llm_client.switch_model("gemini")
                    except:
                        pass
                    import re
                    url_match = re.search(r'https?://\S+\.(?:jpg|jpeg|png|gif|webp)(?:\?\S*)?', user_msg)
                    if url_match:
                        image_url = url_match.group()
                        prompt = user_msg.replace(image_url, "").strip() or "請描述這張圖片的內容"
                        return "🔍 正在分析圖片...\n\n" + llm_client.call_vision(prompt=prompt, image_url=image_url)
                    return "請提供圖片網址（例如：看圖 https://example.com/photo.jpg）"

        # ===== v2: Agent Company =====
        agent_company = None
        for organ in self.organs.values():
            if hasattr(organ, "launch_mission") and hasattr(organ, "fill_all_departments"):
                agent_company = organ
                break
        mission_context = ""
        if agent_company:
            try:
                stats = agent_company.get_global_stats()
                if stats.get("agents", 0) == 0:
                    agent_company.fill_all_departments()
                is_task = any(kw in user_msg for kw in [
                    "幫我", "查", "分析", "寫", "做", "找", "搜",
                    "code", "寫程式", "部署", "安裝", "報告", "規劃",
                    "build", "deploy", "search", "analyze",
                ])
                print(f"[AgentCompany] task={is_task} agents={stats.get('agents',0)} depts={stats.get('departments',0)}")
                if is_task:
                    mission_id = agent_company.launch_mission(user_msg)
                    mission = agent_company.get_mission(mission_id)
                    if mission:
                        st = mission.get("sub_tasks", [])
                        mission_context = (
                            f"\n[派遣報告：此任務已拆解為{len(st)}個子任務並派發給各部門]\n" +
                            "\n".join(f"  - {s.get('department','')}: {s.get('description','')}" for s in st)
                        )
                        print(f"[AgentCompany] mission={mission_id} subtasks={len(st)}")
            except Exception as e:
                print(f"[AgentCompany] error: {e}")

        # ===== 統一記憶檢索 =====
        memory_context = ""
        if self.memory_manager:
            try:
                memory_context = self.memory_manager.get_context(query=user_msg, limit=5)
                if memory_context:
                    print(f"[LangGraphExecutor] 記憶檢索: {memory_context[:200]}")
            except Exception as e:
                print(f"[LangGraphExecutor] 記憶檢索失敗: {e}")
        enriched_msg = user_msg

        # ===== 核心能力 2：尋找資源 =====
        agent_result = None
        agent_failed = False
        tool_executed = False
        tool_result_text = ""

        need_tool = detect_tool_need(user_msg)
        if need_tool:
            print(f"[LangGraphExecutor] 檢測到工具需求: {need_tool}")
            evolution_engine = self.organs.get("self_evolution_engine")
            if evolution_engine and hasattr(evolution_engine, "find_tool"):
                tool_result = evolution_engine.find_tool(need_tool)
                print(f"[LangGraphExecutor] 工具尋找結果: {tool_result[:200]}")
                user_msg = f"{user_msg}\n\n[系統] 工具尋找結果: {tool_result}"

        if self.agent is not None:
            try:
                llm = self.agent.get("llm")
                tools = self.agent.get("tools", [])
                system_prompt = self.agent.get("system_prompt", "")

                print(f"[LangGraphExecutor] 可用工具數量: {len(tools)}")

                tool_list = []
                for t in tools:
                    name = getattr(t, "name", "未知工具")
                    desc = getattr(t, "description", "無描述")
                    tool_list.append(f"- {name}: {desc}")
                tool_str = "\n".join(tool_list)

                print(f"[LangGraphExecutor] 工具列表:\n{tool_str[:500]}")

                evolution_memory = ""
                evolution_organ = self.organs.get("evolution")
                if evolution_organ and hasattr(evolution_organ, "get_summary"):
                    try:
                        evolution_memory = evolution_organ.get_summary()
                    except:
                        pass
                if evolution_memory and memory_context:
                    memory_context = f"{memory_context}\n\n🧬 進化記錄：\n{evolution_memory}"

                prompt = (
                    f"{system_prompt}"
                    f"{memory_context + chr(10)+chr(10) if memory_context else ''}"
                    f"你有以下工具可用：\n"
                    f"{tool_str}\n\n"
                    f"請根據使用者的問題，選擇合適的工具來回答。\n"
                    f"如果你需要使用工具，請輸出 JSON 格式：\n"
                    f'{{"tool": "工具名稱", "args": {{"參數1": "值1", "參數2": "值2"}}}}\n\n'
                    f"如果你不需要使用工具，請直接回答。\n\n"
                    f"使用者說：{enriched_msg}"
                )

                print(f"  [🧠] === LLM PROMPT ===\n{prompt[:800]}\n  [🧠] === END PROMPT ===")
                if self.context_assembler:
                    extra_tools = f"你有以下工具可用：\n{tool_str}\n\n如果需要使用工具，請輸出 JSON 格式：\n{{\"tool\": \"工具名稱\", \"args\": {{\"參數1\": \"值1\"}}}}\n如果不需要使用工具，請直接回答。"
                    if memory_context:
                        extra_tools = f"{memory_context}\n\n{extra_tools}"
                    messages = self.context_assembler.assemble(
                        user_msg=enriched_msg,
                        extra_system=extra_tools,
                    )
                    result = llm.call(messages)
                else:
                    result = llm.call([{"role": "user", "content": prompt}])
                llm_response = str(result)
                print(f"  [🧠] === LLM RESPONSE ===\n{llm_response[:500]}\n  [🧠] === END RESPONSE ===")

                tool_call = parse_tool_call(llm_response)

                if tool_call:
                    tool_name = tool_call.get("tool", "")
                    tool_args = tool_call.get("args", {})

                    print(f"  [🤖] LLM 決定使用工具: {tool_name}")
                    tool_result = execute_tool_by_name(self, tool_name, tool_args)
                    tool_executed = True
                    tool_result_text = str(tool_result)

                    final_prompt = (
                        f"工具執行結果：\n{tool_result}\n\n"
                        f"請根據工具執行結果，用繁體中文簡短回覆使用者。\n"
                        f"⚠️ 你必須使用工具執行結果來回答，不能忽略工具結果。\n"
                        f"使用者說：{user_msg}"
                    )
                    if self.context_assembler:
                        sys_msgs = self.context_assembler.get_system_context(
                            task_hint="你正在根據工具執行結果回答使用者。必須使用工具結果中的真實資料。"
                        )
                        msgs = sys_msgs + [{"role": "user", "content": final_prompt}]
                        final_result = llm.call(msgs)
                    else:
                        final_result = llm.call([{"role": "user", "content": final_prompt}])
                    print(f"  [🧠] === FINAL PROMPT ===\n{final_prompt[:500]}\n  [🧠] === END FINAL ===")
                    agent_result = str(final_result)[:2000]
                else:
                    agent_result = llm_response[:2000]

            except Exception as e:
                agent_failed = True
                if not hasattr(self, '_agent_fail_count'):
                    self._agent_fail_count = 0
                self._agent_fail_count += 1
                if self._agent_fail_count <= 3:
                    print(f"[LangGraphExecutor] 思考引擎調用失敗 ({self._agent_fail_count}/3): {e}")

        # ===== 不一致自動反省 =====
        if tool_executed and agent_result and tool_result_text:
            inconsistency_detected = False
            tool_keywords = tool_result_text[:50]
            if tool_keywords and tool_keywords not in agent_result:
                inconsistency_detected = True

            if inconsistency_detected:
                print(f"[LangGraphExecutor] 檢測到回覆與工具結果不一致，觸發反省...")
                learn_organ = self.organs.get("self_learn")
                if learn_organ and hasattr(learn_organ, "reflect"):
                    try:
                            reflect_result = learn_organ.reflect(
                                f"回覆與工具結果不一致：工具結果={tool_result_text[:100]}，回覆={agent_result[:100]}"
                            )
                            print(f"[LangGraphExecutor] 反省結果: {reflect_result[:200]}")
                            if self.memory_manager and "✅" in reflect_result:
                                self.memory_manager.remember_fact(
                                    f"反省記錄：{reflect_result[:100]}",
                                    importance=0.8
                                )
                    except Exception as e:
                        print(f"[LangGraphExecutor] 反省失敗: {e}")

        # ===== 核心能力 3：自我反省 =====
        if agent_result:
            agent_result = self_reflect(self, user_msg, agent_result)
            if self.memory_manager:
                try:
                    self.memory_manager.remember_fact(
                        f"自我反省：使用者說「{user_msg[:30]}」，回覆「{agent_result[:30]}」",
                        importance=0.7
                    )
                except:
                    pass

        # ===== 自動 self_repair =====
        if agent_failed or not agent_result:
            print("[LangGraphExecutor] 思考引擎失敗，自動觸發自我修復...")
            try:
                if hasattr(self.brain, 'cortex') and self.brain.cortex:
                    agent_result = self.brain.cortex.think(enriched_msg)
                    if agent_result and "所有模型不可用" not in agent_result:
                        print(f"[LangGraphExecutor] 使用 cortex 處理成功")
                        if self.memory_manager:
                            self.memory_manager.remember_fact(
                                f"自動修復：使用 cortex 處理「{user_msg[:30]}」",
                                importance=0.7
                            )
            except Exception as e:
                print(f"[LangGraphExecutor] cortex 處理失敗: {e}")

        if agent_result and ("所有模型不可用" in agent_result):
            print(f"[LangGraphExecutor] LLM 不可用，跳過修復迴圈")
            return agent_result

        if agent_result and ("⚠️" in agent_result or "❌" in agent_result or "錯誤" in agent_result or "失敗" in agent_result):
            print(f"[LangGraphExecutor] 檢測到錯誤，自動觸發修復...")
            # 不記錄錯誤進 semantic，避免垃圾記憶污染

            try:
                error_keywords = agent_result[:100]
                search_result = self._search_for_answer(error_keywords)
                if search_result:
                    print(f"[LangGraphExecutor] 找到正確答案: {search_result[:200]}")
                    agent_result = search_result
            except Exception as e:
                print(f"[LangGraphExecutor] 搜尋正確答案失敗: {e}")

            if agent_result:
                agent_result = self_repair(self, user_msg, agent_result)

        # ===== 核心能力 5：自我進化 =====
        if agent_result:
            self_evolve(self, user_msg, agent_result)
            if self.memory_manager:
                try:
                    self.memory_manager.remember_fact(
                        f"進化記錄：處理了「{user_msg[:30]}」",
                        importance=0.6
                    )
                except:
                    pass

        # ===== 連續失敗自動學習 =====
        if agent_result and ("⚠️" in agent_result or "❌" in agent_result or "錯誤" in agent_result or "失敗" in agent_result):
            if "所有模型不可用" in agent_result:
                return agent_result
            if not hasattr(self, '_consecutive_error_count'):
                self._consecutive_error_count = 0
            self._consecutive_error_count += 1
            print(f"[LangGraphExecutor] 連續錯誤次數: {self._consecutive_error_count}")

            if self._consecutive_error_count >= 3:
                print(f"[LangGraphExecutor] 連續錯誤達到 3 次，自動學習教訓...")
                self._consecutive_error_count = 0
        else:
            if hasattr(self, '_consecutive_error_count'):
                self._consecutive_error_count = 0

        # ===== 統一記憶寫入（只記好的） =====
        if self.memory_manager and agent_result:
            if "所有模型不可用" not in agent_result and "⚠️" not in agent_result:
                try:
                    self.memory_manager.remember(user_msg, agent_result)
                    print(f"[LangGraphExecutor] MemoryManager 記憶寫入完成")
                except Exception as e:
                    print(f"[LangGraphExecutor] MemoryManager 記憶寫入失敗: {e}")

        if self.context_assembler and agent_result:
            try:
                self.context_assembler.record_response(
                    assistant_msg=agent_result,
                    user_msg=user_msg,
                )
            except Exception as e:
                print(f"[LangGraphExecutor] record_response 失敗: {e}")

        # ===== v2: Promise execution =====
        if agent_company and agent_result:
            try:
                progress = agent_company.scan_and_execute_promises(agent_result)
                if progress:
                    agent_result = agent_result.rstrip() + progress
            except Exception as e:
                print(f"[AgentCompany] promise scan failed: {e}")
        if agent_result:
            return agent_result

        # ===== 降級處理 =====
        error_reason = ""
        if agent_failed:
            error_reason = "思考引擎調用失敗"
        else:
            error_reason = "無法產生有效回覆"

        try:
            llm = getattr(self.brain, "llm", None)
            if llm and hasattr(llm, "call"):
                context_parts = []
                for name, organ in self.organs.items():
                    if organ:
                        context_parts.append(f"- {name}: 已載入")

                context = "\n".join(context_parts)

                prompt = (
                    "你是黑曜，一個 AI 夥伴。\n"
                    "你有以下器官可用：\n"
                    f"{context}\n\n"
                    "請根據使用者的問題，用繁體中文簡短回覆。\n"
                    "如果不知道，就說不知道。\n"
                    "做錯就要快點找正確解答，寫入記憶和自我反省。\n"
                    "工具不可用時，要想辦法找到答案並學會。\n\n"
                    f"使用者說：{user_msg}"
                )
                if self.context_assembler:
                    messages = self.context_assembler.assemble(user_msg=user_msg)
                    result = llm.call(messages)
                else:
                    result = llm.call([{"role": "user", "content": prompt}])
        except Exception as e:
            if not hasattr(self, '_llm_fail_count'):
                self._llm_fail_count = 0
            self._llm_fail_count += 1
            if self._llm_fail_count <= 3:
                print(f"[LangGraphExecutor] LLM 降級失敗 ({self._llm_fail_count}/3): {e}")

        return f"🤔 我目前無法執行這個操作，原因：{error_reason}"

    def list_tools(self) -> List[str]:
        return list_tools(self)

    def execute_tool(self, tool_name: str, args: Optional[Any] = None) -> str:
        return execute_tool_by_name(self, tool_name, args if isinstance(args, dict) else {})
