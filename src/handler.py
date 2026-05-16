"""
訊息處理模組 - 處理使用者輸入並產生回應
"""

class MessageHandler:
    def __init__(self, llm_client, memory, compass, decisions, tasks):
        self.llm = llm_client
        self.memory = memory
        self.compass = compass
        self.decisions = decisions
        self.tasks = tasks
    
    def process(self, user_msg: str, send_func=None) -> str:
        """處理使用者訊息"""
        
        # 1. 檢查是否有相關決策
        for word in user_msg.split()[:5]:
            related = self.decisions.recall(word)
            if related:
                print(f"📝 回憶到決定：{related['topic']}")
        
        # 2. 建立系統提示
        direction = self.compass.get_system_prompt()
        next_task = self.tasks.get_next_action()
        task_reminder = f"\n📋 當前待辦：{self.tasks.suggest_next()}" if next_task else ""
        
        enhanced_prompt = f"""{direction}

{task_reminder}

使用者說：{user_msg}

請回應（記得要有結論和行動建議）："""
        
        # 3. 呼叫 AI
        messages = [{"role": "system", "content": enhanced_prompt}]
        response = self.llm.call(messages)
        if response is None:
            return "抱歉，目前無法處理您的請求。"
        
        # 4. 檢查回應是否有行動
        check = self.compass.check_response(response) if hasattr(self, 'compass') and self.compass else {}
        if not check.get("has_action", False):
            response += "\n\n💡 建議下一步：請告訴我你希望我針對哪個部分深入分析或執行？"
        
        return response
