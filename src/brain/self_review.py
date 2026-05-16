"""自我審查層 - 用另一個模型檢查自己的回覆品質"""
from skeleton.base_organ import BaseOrgan

class SelfReview(BaseOrgan):
    def __init__(self, llm_client, contradiction_detector):
        super().__init__("self_review")
        self.llm = llm_client
        self.contradiction = contradiction_detector

    def review(self, user_msg: str, assistant_reply: str, memory) -> dict:
        """審查回覆品質，回傳分數和建議"""
        result = {
            "passed": True,
            "score": 0,
            "issues": [],
            "suggestions": [],
        }

        # 1. 矛盾檢測
        contra = self.contradiction.check(assistant_reply)
        if contra.get("is_contradiction"):
            result["passed"] = False
            result["issues"].append(f"矛盾：{contra.get('old_statement', '')}")

        # 2. 品質審查（用 LLM 給回覆打分數）
        review_prompt = f"""你是品質審查員。請審查以下 AI 回覆的品質。

使用者問題：{user_msg}

AI 回覆：{assistant_reply}

請用 JSON 格式回覆：
{{
    "score": 1-10,
    "issues": ["問題1", "問題2"],
    "suggestions": ["改進建議1", "改進建議2"],
    "should_retry": true/false
}}

審查標準：
- 是否有具體行動建議（不是空泛的建議）
- 是否有邏輯矛盾或前後不一致
- 是否使用了搜尋結果（如果有需要的話）
- 是否用繁體中文、語氣專業
"""
        try:
            raw = self.llm.call([{"role": "user", "content": review_prompt}])
            import json, re
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                review = json.loads(match.group())
                result["score"] = review.get("score", 5)
                result["issues"].extend(review.get("issues", []))
                result["suggestions"].extend(review.get("suggestions", []))
                if review.get("should_retry") or review.get("score", 5) < 4:
                    result["passed"] = False
        except:
            pass

        return result

    def status(self) -> dict:
        return {"name": self.name, "alive": self.is_alive()}
