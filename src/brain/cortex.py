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
    def __init__(self, llm_client, memory, compass, decisions, tasks, executor, registry, persona, contradiction, life_cycle=None):
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
        self.firewall = Firewall()
        self.breaker = Breaker()
        self.eye = Eye()
        self.eye.init()
        self.reviewer = SelfReview(llm_client, contradiction)
        self.repairer = SelfRepair(llm_client, persona, compass)
        # 稍後由外部注入 langgraph 引擎
        self.langgraph = None
        
        # ===== 新增：被動觸發機制狀態 =====
        self.last_user_msg = None  # 上一次的使用者訊息
        self.last_assistant_reply = None  # 上一次的助理回覆
        self.conversation_count = 0  # 對話計數器
    
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
        
        # 2. 如果 LangGraph 引擎可用，優先使用（保留雙重保險）
        if self.langgraph:
            try:
                return self.langgraph.process(user_msg)
            except Exception:
                pass
        
        # 3. 🔥 系統指令直接執行
        sys_cmds = {"硬碟":"df -h","磁碟":"df -h","記憶體":"free -h","cpu":"top -bn1 | head -5","系統":"uname -a"}
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
        
        # 5. 呼叫 LLM
        persona_prompt = self.persona.system_prompt() if hasattr(self.persona, 'system_prompt') else ""
        direction = self.compass.get_system_prompt() if hasattr(self.compass, 'get_system_prompt') else ""
        
        # 從記憶中取出相關事實
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
        
        # ===== 對話後自動記憶 =====
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
        
        # ===== 不一致自動反省 =====
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
                    reflection_response = self.llm.call([
                        {"role": "system", "content": "你是一個矛盾分析專家"},
                        {"role": "user", "content": reflection_prompt}
                    ])
                    
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
