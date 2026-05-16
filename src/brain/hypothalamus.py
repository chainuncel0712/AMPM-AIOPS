"""下視丘 - 自主神經系統，負責定時維護 + 記憶任務執行 + 被動觸發機制"""
from skeleton.base_organ import BaseOrgan
from datetime import datetime  # 導入 datetime 用於時間戳記

class Hypothalamus(BaseOrgan):
    def __init__(self, memory, tools, nose, evolution, scheduler, tasks, call_ai_func):
        super().__init__("hypothalamus")
        self.memory = memory
        self.tools = tools
        self.nose = nose
        self.evolution = evolution
        self.scheduler = scheduler
        self.tasks = tasks
        self.call_ai = call_ai_func
        
        # ===== 新增：被動觸發機制狀態 =====
        self.failed_tasks = []  # 記錄失敗的任務
        self.last_repair_time = None  # 上一次修復時間

    def start_autonomous_tasks(self):
        self.scheduler.add("nose_sniff", 600, self._sniff)
        self.scheduler.add("memory_organize", 1800, self._organize_memory)
        self.scheduler.add("tool_cleanup", 21600, self._cleanup_tools)
        self.scheduler.add("evolution_review", 86400, self._evolution_review)
        # 新增：每 30 分鐘檢查記憶中的任務
        self.scheduler.add("memory_task_check", 1800, self._check_memory_tasks)
        # ===== 新增：每 5 分鐘檢查失敗任務 =====
        self.scheduler.add("failed_task_repair", 300, self._check_failed_tasks)

    def _sniff(self):
        try:
            findings = self.nose.sniff_now()
            print(f"👃 嗅探結果：{findings}")
        except:
            pass

    def _organize_memory(self):
        try:
            self.memory.organize()
            print("🧠 記憶整理完成")
        except:
            pass

    def _cleanup_tools(self):
        try:
            unused = self.tools.get_unused_tools(30)
            if unused:
                print(f"🔧 建議淘汰工具：{unused}")
        except:
            pass

    def _evolution_review(self):
        try:
            result = self.evolution.daily_review()
            print(f"🧬 進化反省完成")
        except Exception as e:
            print(f"🧬 進化反省失敗：{e}")

    def _check_memory_tasks(self):
        """定時檢查語義記憶中的任務，自動加入待辦"""
        try:
            facts = self.memory.get_all_facts()
            for fact in facts:
                # 辨識包含任務意圖的記憶
                if any(kw in fact for kw in ["規劃", "任務", "建立", "架構", "創作", "執行", "定時", "記錄"]):
                    # 檢查是否已經在待辦清單中
                    already_exists = False
                    for task in self.tasks.tasks:
                        if fact[:30] in task.get("title", ""):
                            already_exists = True
                            break
                    if not already_exists:
                        self.tasks.add(
                            title=fact[:80],
                            description=f"從記憶中提取的任務：{fact}",
                            priority="medium"
                        )
                        print(f"📋 從記憶中提取任務：{fact[:50]}...")
        except Exception as e:
            print(f"記憶任務檢查失敗：{e}")

    # ===== 新增：失敗任務自動修復 =====
    def _check_failed_tasks(self):
        """
        檢查失敗任務並自動修復
        
        這個方法會：
        1. 檢查任務清單中是否有失敗的任務
        2. 嘗試自動修復失敗的任務
        3. 記錄修復結果到記憶
        """
        try:
            # 取得所有任務
            all_tasks = self.tasks.get_all_tasks() if hasattr(self.tasks, 'get_all_tasks') else []
            
            # 找出失敗的任務
            failed = []
            for task in all_tasks:
                # 檢查任務狀態是否為失敗
                status = task.get("status", "")
                if status in ["failed", "error", "timeout"]:
                    failed.append(task)
            
            if not failed:
                return  # 沒有失敗任務，直接返回
            
            print(f"🔧 發現 {len(failed)} 個失敗任務，開始自動修復...")
            
            for task in failed:
                task_id = task.get("id", "")
                task_title = task.get("title", "未知任務")
                task_description = task.get("description", "")
                
                # 記錄到失敗任務列表
                self.failed_tasks.append({
                    "task_id": task_id,
                    "title": task_title,
                    "description": task_description,
                    "failed_at": datetime.now().isoformat(),
                    "repair_attempts": 0
                })
                
                # 嘗試修復
                self._repair_failed_task(task)
                
            # 更新修復時間
            self.last_repair_time = datetime.now()
            
        except Exception as e:
            print(f"⚠️ 檢查失敗任務時發生錯誤：{e}")
    
    def _repair_failed_task(self, task):
        """
        修復單個失敗任務
        
        參數：
            task: 失敗的任務字典
        """
        try:
            task_id = task.get("id", "")
            task_title = task.get("title", "未知任務")
            task_description = task.get("description", "")
            
            print(f"🔧 正在修復任務：{task_title}")
            
            # 使用 AI 分析失敗原因並提出修復方案
            repair_prompt = f"""
            任務執行失敗，需要修復：
            
            任務標題：{task_title}
            任務描述：{task_description}
            任務 ID：{task_id}
            
            請分析失敗原因並提出修復方案。
            輸出 JSON 格式：
            {{
                "failure_reason": "失敗原因分析",
                "repair_plan": "具體的修復步驟",
                "should_retry": true/false  # 是否應該重試
            }}
            """
            
            try:
                repair_response = self.call_ai([
                    {"role": "system", "content": "你是一個任務修復專家"},
                    {"role": "user", "content": repair_prompt}
                ])
                
                import json
                import re
                json_match = re.search(r'\{.*\}', repair_response, re.DOTALL)
                if json_match:
                    repair_plan = json.loads(json_match.group())
                    
                    # 記錄修復計劃到記憶
                    self.memory.remember_fact(
                        f"任務修復計劃：{task_title} - {repair_plan.get('repair_plan', '無計劃')}",
                        importance=0.8
                    )
                    
                    print(f"📋 修復計劃：{repair_plan.get('repair_plan', '')[:100]}")
                    
                    # 如果需要重試，重新加入任務
                    if repair_plan.get("should_retry", False):
                        self.tasks.add(
                            title=f"（重試）{task_title}",
                            description=f"自動重試：{task_description}",
                            priority="high"
                        )
                        print(f"🔄 已重新加入任務：{task_title}")
                        
            except Exception as e:
                print(f"⚠️ 修復分析失敗：{e}")
                
        except Exception as e:
            print(f"⚠️ 修復任務時發生錯誤：{e}")
    
    # ===== 新增：記錄任務執行結果 =====
    def record_task_result(self, task_id, success, result=""):
        """
        記錄任務執行結果
        
        參數：
            task_id: 任務 ID
            success: 是否成功
            result: 執行結果
        """
        try:
            if not success:
                # 如果失敗，記錄到失敗任務列表
                self.failed_tasks.append({
                    "task_id": task_id,
                    "failed_at": datetime.now().isoformat(),
                    "result": result,
                    "repair_attempts": 0
                })
                print(f"❌ 任務 {task_id} 執行失敗，已記錄")
            else:
                print(f"✅ 任務 {task_id} 執行成功")
                
        except Exception as e:
            print(f"⚠️ 記錄任務結果時發生錯誤：{e}")

    def status(self) -> dict:
        return {"name": self.name, "alive": self.is_alive()}
