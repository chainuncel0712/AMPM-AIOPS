"""
羅盤系統 - 給黑曜一個北極星方向
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List

class Compass:
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.direction_file = self.base_dir / "data" / "compass" / "direction.json"
        self.direction_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.direction = self._load()
        if not self.direction:
            self._set_default()
    
    def _load(self) -> Dict:
        if self.direction_file.exists():
            return json.loads(self.direction_file.read_text())
        return {}
    
    def _save(self):
        self.direction_file.write_text(json.dumps(self.direction, ensure_ascii=False, indent=2))
    
    def _set_default(self):
        self.direction = {
            "north_star": "幫助使用者在商業上成功，創造實際價值",
            "principles": [
                "每次對話都要有 actionable 的結論",
                "不知道就說不知道，然後提出驗證方法",
                "自由思考，但要落地到具體行動"
            ],
            "forbidden": [
                "只分析不行動",
                "繞圈圈不給結論"
            ],
            "last_updated": datetime.now().isoformat()
        }
        self._save()
    
    def get_system_prompt(self) -> str:
        return f"""🎯 北極星：{self.direction['north_star']}

📜 守則：
{chr(10).join(f'- {p}' for p in self.direction['principles'])}

❌ 不要：
{chr(10).join(f'- {f}' for f in self.direction['forbidden'])}"""
    
    def check_response(self, response: str) -> Dict:
        has_action = any(w in response for w in ["建議", "行動", "下一步", "執行", "做"])
        has_conclusion = any(w in response for w in ["結論", "總結", "所以", "因此"])
        return {"has_action": has_action, "has_conclusion": has_conclusion}
