"""自我修復層 - 回覆品質不佳時，用更強模型重新生成 + 被動觸發機制"""
from skeleton.base_organ import BaseOrgan
from datetime import datetime  # 導入 datetime 用於時間戳記

class SelfRepair(BaseOrgan):
    def __init__(self, llm_client, persona, compass):
        super().__init__("self_repair")
        self.llm = llm_client
        self.persona = persona
        self.compass = compass
        
        # ===== 新增：被動觸發機制狀態 =====
        self.repair_count = 0  # 修復次數
        self.last_repair_time = None  # 上一次修復時間
        self.repair_history = []  # 修復歷史記錄

    def repair(self, user_msg: str, bad_reply: str, issues: list, suggestions: list) -> str:
        """
        根據審查結果，重新生成更好的回覆
        
        參數：
            user_msg: 使用者訊息
            bad_reply: 失敗的回覆
            issues: 問題列表
            suggestions: 改進建議列表
        
        回傳：
            修復後的回覆
        """
        # ===== 新增：記錄修復嘗試 =====
        self.repair_count += 1
        self.last_repair_time = datetime.now()
        
        repair_prompt = f"""你剛才的回覆被品質審查員指出了以下問題：

問題：
{chr(10).join(f'- {i}' for i in issues)}

改進建議：
{chr(10).join(f'- {s}' for s in suggestions)}

原來你的回覆：
{bad_reply}

請根據以上回饋，重新生成一個更好的回覆。
要點：
1. 保持原來的正確資訊
2. 修正被指出的問題
3. 加入具體的行動建議
4. 用繁體中文，語氣專業
"""
        try:
            persona_prompt = self.persona.system_prompt()
            direction = self.compass.get_system_prompt()
            messages = [
                {"role": "system", "content": f"{persona_prompt}\n{direction}"},
                {"role": "user", "content": repair_prompt}
            ]
            repaired = self.llm.call(messages)
            
            # ===== 新增：記錄修復結果 =====
            self._record_repair_result(user_msg, bad_reply, repaired, issues)
            
            return repaired if repaired else bad_reply
        except:
            # 如果修復失敗，記錄失敗
            self._record_repair_result(user_msg, bad_reply, None, issues, success=False)
            return bad_reply

    # ===== 新增：記錄修復結果 =====
    def _record_repair_result(self, user_msg, bad_reply, repaired_reply, issues, success=True):
        """
        記錄修復結果到歷史記錄
        
        參數：
            user_msg: 使用者訊息
            bad_reply: 失敗的回覆
            repaired_reply: 修復後的回覆（可能為 None）
            issues: 問題列表
            success: 是否成功
        """
        record = {
            "repair_number": self.repair_count,
            "timestamp": datetime.now().isoformat(),
            "user_msg": user_msg[:100],
            "bad_reply": bad_reply[:100],
            "repaired_reply": repaired_reply[:100] if repaired_reply else None,
            "issues": issues,
            "success": success
        }
        
        self.repair_history.append(record)
        # 最多保留 50 條歷史記錄
        if len(self.repair_history) > 50:
            self.repair_history = self.repair_history[-50:]
        
        if success:
            print(f"✅ 修復成功（第 {self.repair_count} 次）")
        else:
            print(f"❌ 修復失敗（第 {self.repair_count} 次）")
    
    # ===== 新增：取得修復統計 =====
    def get_repair_stats(self) -> dict:
        """
        取得修復統計資訊
        
        回傳：
            包含修復統計的字典
        """
        successful = sum(1 for r in self.repair_history if r.get("success"))
        failed = sum(1 for r in self.repair_history if not r.get("success"))
        
        return {
            "name": self.name,
            "alive": self.is_alive(),
            "total_repairs": self.repair_count,
            "successful_repairs": successful,
            "failed_repairs": failed,
            "success_rate": successful / max(1, self.repair_count),
            "last_repair_time": self.last_repair_time.isoformat() if self.last_repair_time else None
        }

    def status(self) -> dict:
        return self.get_repair_stats()
