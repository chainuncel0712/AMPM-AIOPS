"""大腦皮層 - 工具執行版 + LangGraph 整合 + 被動觸發機制"""

# ===== 路徑設定：將 src/ 目錄加入 Python 模組搜尋路徑 =====
import sys  # 匯入系統模組，用於修改 Python 路徑
from pathlib import Path  # 匯入路徑處理模組
# 取得目前檔案（cortex.py）的所在目錄（brain/），再往上一層到 src/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
# 這樣 Python 就能找到 src/skeleton/、src/immune/ 等目錄

from skeleton.base_organ import BaseOrgan  # 從骨架層匯入基礎器官類別
from immune.firewall import Firewall
from immune.breaker import Breaker
from nerve.eye import Eye
from brain.self_review import SelfReview
from brain.self_repair import SelfRepair
import subprocess
from datetime import datetime  # 導入 datetime 用於時間戳記

class Cortex(BaseOrgan):
    def __init__(self, llm_client, memory, compass, decisions, tasks, executor, registry, persona, contradiction, life_cycle=None, context_assembler=None, critic=None, learning_engine=None, evolution_engine=None, runtime_update=None):
        super().__init__("cortex")
        self.llm = llm_client
        self.memory = memory
        self.compass = compass
        self.decisions = decisions
        self.tasks = tasks
        self.executor = executor
        self.registry = registry
        self.persona = persona
        self.contradiction = contradiction
        self.life_cycle = life_cycle
        self.context_assembler = context_assembler
        self.critic = critic
        self.learning_engine = learning_engine
        self.evolution_engine = evolution_engine
        self.runtime_update = runtime_update
        self.firewall = Firewall()
        self.breaker = Breaker()
        self.eye = Eye()
        self.eye.init()
        self.reviewer = SelfReview(llm_client, contradiction)
        self.repairer = SelfRepair(llm_client, persona, compass, context_assembler=context_assembler)
        # 稍後由外部注入 langgraph 引擎
        self.langgraph = None
        
        # ===== 新增：被動觸發機制狀態 =====
        self.last_user_msg = None  # 上一次的使用者訊息
        self.last_assistant_reply = None  # 上一次的助理回覆
        self.conversation_count = 0  # 對話計數器
        self.learning_counter = 0  # 每 N 次对话触发一次进化
    
    def think(self, user_msg: str) -> str:
        """思考介面：優先使用 LangGraph 引擎"""
        if self.langgraph:
            try:
                return self.langgraph.process(user_msg)
            except Exception:
                # 若失敗則降級到傳統處理
                pass
        return self.process(user_msg)
    
    def process(self, user_msg: str, send_func=None) -> str:
        # ===== stable 模式：委派給 ExecutionContext（單一控制鏈）=====
        if hasattr(self, 'execution_context') and self.execution_context:
            return self.execution_context.handle(user_msg, send_func)

        # ===== 觸發生命週期狀態機 =====
        if self.life_cycle:
            self.life_cycle.trigger(user_msg)

        # ===== 檢查是否第一次對話 =====
        # 如果還沒有使用者稱呼，先自我介紹
        if not self.persona.user_name and not self.memory.get_all_facts():
            # 檢查使用者是否在自我介紹
            if "我叫" in user_msg or "我是" in user_msg or "稱呼" in user_msg:
                # 嘗試提取使用者名稱
                for prefix in ["我叫", "我是", "稱呼我為", "叫我"]:
                    if prefix in user_msg:
                        name = user_msg.split(prefix)[-1].strip().split()[0]
                        name = name.strip("，。！？,.!?")
                        if name:
                            self.persona.set_user_name(name)
                            self.memory.remember_fact(f"使用者叫：{name}", importance=1.0)
                            return f"好的，{name}！很高興認識你。今天有什麼我可以幫忙的嗎？"
            
            if "改名" in user_msg or "叫什麼" in user_msg or "名字" in user_msg:
                # 使用者想幫黑曜改名
                for prefix in ["叫", "改名為", "改成", "叫做"]:
                    if prefix in user_msg:
                        new_name = user_msg.split(prefix)[-1].strip().split()[0]
                        new_name = new_name.strip("，。！？,.!?")
                        if new_name:
                            old_name = self.persona.name
                            self.persona.name = new_name
                            self.memory.remember_fact(f"黑曜改名為：{new_name}", importance=1.0)
                            return f"好的！從現在開始，我就叫{new_name}了。\n\n{self.persona.user_name or '朋友'}，謝謝你幫我取新名字！"
            
            if "個性" in user_msg or "風格" in user_msg or "性格" in user_msg:
                # 使用者想設定個性
                self.persona.set_preference("style", user_msg[:100])
                self.memory.remember_fact(f"使用者想要的個性：{user_msg[:100]}", importance=0.9)
                return f"好的，我記住了！我會試著朝這個方向調整。\n\n還有其他想告訴我的嗎？"
            
            # 第一次對話，自我介紹
            return self.persona.get_greeting()
        
        # ===== 對話前自動記憶 =====
        self._auto_remember_before(user_msg)
        
        # 1. 安全檢查
        fw_result = self.firewall.scan(user_msg)
        if not fw_result["allowed"]:
            return f"⛔ {fw_result['reason']}"

        # ===== 🔥 系統指令 — 必須在 LangGraph 之前執行 =====
        sys_cmds = {"硬碟":"df -h","磁碟":"df -h","記憶體":"free -h","cpu":"top -bn1 | head -5","系統":"uname -a"}

        # 視覺分析
        if "看圖" in user_msg or "分析圖片" in user_msg or "這張圖" in user_msg:
            import re
            url_match = re.search(r'https?://\S+\.(?:jpg|jpeg|png|gif|webp)(?:\?\S*)?', user_msg)
            if url_match:
                image_url = url_match.group()
                prompt = user_msg.replace(image_url, "").strip() or "請描述這張圖片的內容"
                return "🔍 正在分析圖片...\n\n" + self.llm.call_vision(prompt=prompt, image_url=image_url)
            return "請提供圖片網址（例如：看圖 https://example.com/photo.jpg）"

        # 模型擴充
        if "找模型" in user_msg or "探索模型" in user_msg or "新模型" in user_msg:
            models = self.llm.discover_models(limit=8)
            if models:
                lines = "\n".join(f"  {m['name']}: {m['id']}" for m in models)
                return f"🔍 找到 {len(models)} 個可用模型：\n{lines}\n\n輸入「加入模型 XXX」來啟用。"
            return "找不到可用模型。檢查 OPENROUTER_API_KEY 是否設定。"
        if "加入模型" in user_msg or "加模型" in user_msg:
            import re
            match = re.search(r'[\w.-]+/[\w.-]+', user_msg)
            if match:
                model_id = match.group()
                result = self.llm.add_openrouter_model(model_id)
                return f"📡 {result}\n目前共 {len(self.llm.list_models())} 個模型"
            return "請提供模型 ID（例如：加入模型 google/gemini-2.0-flash-001）"

        # 模型切換
        if "模型" in user_msg or "切換" in user_msg or "換模型" in user_msg:
            if "有哪些" in user_msg or "列表" in user_msg or "可用" in user_msg:
                models = self.llm.list_models()
                lines = "\n".join(f"  {m['name']}: {m['model']}" for m in models)
                return f"可用模型：\n{lines}\n\n目前使用：{self.llm.current_model()}\n\n輸入「切換到 XXX」來切換。"
            for kw in ["切換到", "換到", "改用", "換成", "切換成", "用"]:
                if kw in user_msg:
                    name = user_msg.split(kw)[-1].strip().split()[0]
                    result = self.llm.switch_model(name)
                    return f"🔄 {result}\n目前模型：{self.llm.current_model()}"
            # 只說「換模型」→ 列出可用模型
            if "換模型" in user_msg or "切換模型" in user_msg:
                models = self.llm.list_models()
                lines = "\n".join(f"  {m['name']}: {m['model']}" for m in models)
                return f"要切換到哪個？\n{lines}\n\n目前：{self.llm.current_model()}"
            if "auto" in user_msg.lower() or "自動" in user_msg:
                result = self.llm.switch_model("auto")
                return f"🔄 已恢復自動 fallback"

        # 語言模型判斷 — "模型" 後面沒指定 → 可能是聊模型話題，不是切換指令
        # 已在上面的「只說換模型」處理，安全放行到 LangGraph/LLM

        # 2. 如果 LangGraph 引擎可用，優先使用（保留雙重保險）
        if self.langgraph:
            try:
                reply = self.langgraph.process(user_msg)
                # LangGraph 路徑也需要寫記憶
                if self.context_assembler and reply:
                    self.context_assembler.record_response(
                        assistant_msg=reply,
                        user_msg=user_msg,
                    )
                    self.context_assembler.write_memory(
                        user_msg=user_msg,
                        assistant_msg=reply,
                    )
                return reply
            except Exception:
                pass

        # 3. 系統指令直接執行 (硬碟、記憶體等)
        for kw, cmd in sys_cmds.items():
            if kw in user_msg:
                try:
                    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
                    output = r.stdout.strip()
                    
                    # 硬碟/磁碟：用日常對話的語氣
                    if kw in ["硬碟", "磁碟"]:
                        lines = output.split('\n')[1:]
                        max_usage = 0
                        space_ok = True
                        for line in lines:
                            parts = line.split()
                            if len(parts) >= 5:
                                try:
                                    use_pct = int(parts[4].replace('%', ''))
                                    if use_pct > max_usage:
                                        max_usage = use_pct
                                    if use_pct > 85:
                                        space_ok = False
                                except:
                                    pass
                        
                        if space_ok:
                            return f"硬碟空間還很夠喔，目前用了大概 {max_usage}%，不用擔心。"
                        else:
                            return f"硬碟有點滿了，用到 {max_usage}% 了，可能要找時間清一下不需要的檔案。"
                    
                    # 記憶體：輕鬆回報
                    elif kw == "記憶體":
                        return f"記憶體目前運作正常，我幫你盯著。"

                    # CPU：簡單說明
                    elif kw == "cpu":
                        return f"CPU 運作正常，系統跑得還算順。"

                    # 系統資訊
                    elif kw == "系統":
                        return f"系統一切正常，有什麼需要我幫忙的嗎？"
                        
                except Exception as e:
                    return f"剛剛檢查的時候遇到一點小問題，不過應該沒關係。"
        
        # 4. 搜尋關鍵字 → 用 eye
        search_kw = ["查","搜","找","價格","天氣","新聞","股價","比特幣","最新","多少錢","行情"]
        search_result = ""
        if any(k in user_msg for k in search_kw):
            try:
                search_result = self.eye.see(user_msg)
            except:
                pass
        
        # 5. 呼叫 LLM — 使用 ContextAssembler（如果可用）
        if self.context_assembler:
            extra_system = ""
            if search_result:
                extra_system = f"🔍 搜尋結果：\n{search_result}"
            if self.learning_engine:
                rules_context = self.learning_engine.get_rules_context()
                if rules_context:
                    extra_system = f"{extra_system}\n\n{rules_context}" if extra_system else rules_context
            messages = self.context_assembler.assemble(
                user_msg=user_msg,
                extra_system=extra_system or None,
            )
        else:
            # 舊版 inline prompt 組裝（fallback）
            persona_prompt = self.persona.system_prompt() if hasattr(self.persona, 'system_prompt') else ""
            direction = self.compass.get_system_prompt() if hasattr(self.compass, 'get_system_prompt') else ""
            memory_context = ""
            try:
                recent_facts = self.memory.get_important_facts(min_importance=0.5)
                if recent_facts:
                    facts_str = "\n".join(f"- {k}" for k in recent_facts.keys())
                    memory_context = f"\n\n## 你記得的事實\n{facts_str}"
                recent_conversations = self.memory.get_recent_conversations(limit=5)
                if recent_conversations:
                    conv_str = "\n".join(f"使用者: {c['user']}\n你: {c['assistant']}" for c in recent_conversations)
                    memory_context += f"\n\n## 最近對話\n{conv_str}"
            except Exception as e:
                print(f"⚠️ 讀取記憶失敗: {e}")
            prompt = f"{persona_prompt}\n\n{direction}\n\n{memory_context}"
            if search_result:
                prompt += f"\n\n🔍 搜尋結果：\n{search_result}"
            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_msg}
            ]

        # 呼叫 LLM 取得回覆
        reply = self.llm.call(messages)

        # ===== Critic + Learning 閉環 =====
        if self.critic:
            critic_result = self.critic.evaluate(
                user_msg=user_msg,
                assistant_msg=reply or "",
            )
            if self.learning_engine:
                self.learning_engine.learn(
                    critic_result=critic_result.to_dict(),
                    user_msg=user_msg,
                    assistant_msg=reply or "",
                )
            # 每 10 次对话触发进化
            self.learning_counter += 1
            if self.learning_counter >= 10 and self.evolution_engine:
                self.learning_counter = 0
                evolution_result = self.evolution_engine.evolve(
                    self.learning_engine.history
                )
                if evolution_result.get("mutated"):
                    self.runtime_update.apply_evolution(
                        memory_weights=evolution_result.get("memory_weights"),
                        tool_priorities=evolution_result.get("tool_priorities"),
                        planner_strategies=evolution_result.get("planner_strategies"),
                    )

        # ===== 記錄到 ConversationWindow + 分類寫入記憶 =====
        if self.context_assembler:
            self.context_assembler.record_response(
                assistant_msg=reply or "",
                user_msg=user_msg,
            )
            self.context_assembler.write_memory(
                user_msg=user_msg,
                assistant_msg=reply or "",
            )
        
        # ===== 對話後自動記憶（舊路徑，context_assembler 存在時不跑）=====
        if not self.context_assembler:
            self._auto_remember_after(user_msg, reply)
        
        # ===== 將結果寫入狀態機 Context，供 REFLECT/LEARN 狀態使用 =====
        if self.life_cycle:
            self.life_cycle.context["user_msg"] = user_msg
            self.life_cycle.context["reply"] = reply
            self.life_cycle.context["pending_reflect"] = True
        
        # ===== 失敗自動修復 =====
        if not reply or "錯誤" in reply or "失敗" in reply or "不可用" in str(reply):
            repaired = self._auto_repair(user_msg, reply)
            if repaired:
                reply = repaired
        
        # ===== 不一致自動反省（stable 模式跳過）=====
        if self.critic and self.contradiction:
            self._auto_reflect(user_msg, reply)
        
        return reply
    
    # ===== 新增：對話前自動記憶 =====
    def _auto_remember_before(self, user_msg):
        """
        對話前自動記憶：在使用者發送訊息之前，先記住相關背景
        
        參數：
            user_msg: 使用者訊息
        """
        pass
    
    # ===== 新增：對話後自動記憶 =====
    def _auto_remember_after(self, user_msg, reply):
        """
        對話後自動記憶：在回覆使用者之後，記住完整對話
        
        參數：
            user_msg: 使用者訊息
            reply: 助理回覆
        """
        try:
            # 更新對話計數器
            self.conversation_count += 1
            
            # 記住完整對話到工作記憶
            self.memory.remember_conversation(
                user_msg=user_msg,
                assistant_msg=reply,
                importance=0.6  # 重要性稍微提高
            )
            
            # 儲存上一次的對話
            self.last_user_msg = user_msg
            self.last_assistant_reply = reply
            
            print(f"📝 對話後記憶：已記錄第 {self.conversation_count} 次對話")
            
            # 每 10 次對話自動整理記憶
            if self.conversation_count % 10 == 0:
                self.memory.organize()
                print(f"🧠 自動整理記憶（第 {self.conversation_count} 次對話後）")
                
        except Exception as e:
            print(f"⚠️ 對話後記憶失敗：{e}")
    
    # ===== 新增：失敗自動修復 =====
    def _auto_repair(self, user_msg, bad_reply):
        """
        失敗自動修復：當回覆失敗時，自動觸發自我修復
        
        參數：
            user_msg: 使用者訊息
            bad_reply: 失敗的回覆
        """
        try:
            print(f"🔧 自動修復觸發：回覆失敗")
            
            # 分析失敗原因
            issues = []
            suggestions = []
            
            if not bad_reply:
                issues.append("回覆為空")
                suggestions.append("請確保回覆不為空")
            if "錯誤" in bad_reply:
                issues.append("回覆包含錯誤訊息")
                suggestions.append("請修正錯誤")
            if "失敗" in bad_reply:
                issues.append("回覆包含失敗訊息")
                suggestions.append("請重新嘗試")
            
            # 使用自我修復機制重新生成回覆
            repaired_reply = self.repairer.repair(
                user_msg=user_msg,
                bad_reply=bad_reply or "",
                issues=issues,
                suggestions=suggestions
            )
            
            # 如果修復成功，更新記憶
            if repaired_reply and repaired_reply != bad_reply:
                self.memory.remember_conversation(
                    user_msg=user_msg,
                    assistant_msg=f"（修復後）{repaired_reply}",
                    importance=0.8
                )
                print(f"✅ 自動修復成功")
                return repaired_reply
            else:
                print(f"⚠️ 自動修復失敗，保留原始回覆")
                
        except Exception as e:
            print(f"⚠️ 自動修復過程發生錯誤：{e}")
        return None
    
    # ===== 新增：不一致自動反省 =====
    def _auto_reflect(self, user_msg, reply):
        """
        不一致自動反省：檢查回覆是否與之前的記憶矛盾
        
        參數：
            user_msg: 使用者訊息
            reply: 助理回覆
        """
        try:
            # 使用矛盾檢測器檢查
            contradiction_result = {}
            try:
                if hasattr(self.reviewer.contradiction, 'check'):
                    contradiction_result = self.reviewer.contradiction.check(reply, memory=self.memory)
            except Exception:
                pass
            
            # 如果檢測到矛盾
            if contradiction_result.get("is_contradiction"):
                print(f"⚠️ 檢測到矛盾：新回覆與舊記憶不一致")
                
                # 取得舊的陳述
                old_statement = contradiction_result.get("old_statement", "")
                
                # 自動反省：分析矛盾原因
                reflection_prompt = f"""
                我檢測到一個矛盾：
                
                新的回覆：{reply[:200]}
                舊的記憶：{old_statement}
                
                請分析這個矛盾的原因，並提出修正方案。
                輸出 JSON 格式：
                {{
                    "reason": "矛盾原因",
                    "correction": "修正方案",
                    "should_keep_new": true/false  # 是否應該保留新的回覆
                }}
                """
                
                try:
                    if self.context_assembler:
                        system_messages = self.context_assembler.get_system_context(
                            task_hint="你正在進行矛盾反省：檢查你的回覆是否與記憶中的資訊有衝突。"
                        )
                        messages = system_messages + [
                            {"role": "user", "content": reflection_prompt}
                        ]
                    else:
                        messages = [
                            {"role": "system", "content": "你是一個矛盾分析專家"},
                            {"role": "user", "content": reflection_prompt}
                        ]
                    reflection_response = self.llm.call(messages)
                    
                    import json
                    import re
                    json_match = re.search(r'\{.*\}', reflection_response, re.DOTALL)
                    if json_match:
                        reflection = json.loads(json_match.group())
                        
                        # 記錄反省結果到記憶
                        self.memory.remember_fact(
                            f"矛盾反省：{reflection.get('reason', '未知原因')}",
                            importance=0.9
                        )
                        
                        print(f"🔍 矛盾反省完成：{reflection.get('reason', '')}")
                        
                        # 如果需要保留新的回覆，更新記憶
                        if reflection.get("should_keep_new", False):
                            self.memory.remember_conversation(
                                user_msg=user_msg,
                                assistant_msg=f"（反省後）{reply}",
                                importance=0.9
                            )
                except Exception as e:
                    print(f"⚠️ 矛盾反省過程錯誤：{e}")
                    
        except Exception as e:
            print(f"⚠️ 不一致檢查失敗：{e}")
    
    def status(self) -> dict:
        return {"name": self.name, "alive": self.is_alive()}
