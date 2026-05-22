"""
決策記錄 - 記住做過的重要決定
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

class DecisionRecorder:
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.decisions_file = self.base_dir / "data" / "decisions" / "decisions.json"
        self.decisions_file.parent.mkdir(parents=True, exist_ok=True)
        self.decisions = self._load()
    
    def _load(self) -> List[Dict]:
        if self.decisions_file.exists():
            return json.loads(self.decisions_file.read_text())
        return []
    
    def _save(self):
        self.decisions = self.decisions[-100:]
        self.decisions_file.write_text(json.dumps(self.decisions, ensure_ascii=False, indent=2))
    
    def record(self, topic: str, decision: str, context: str = "", importance: int = 5) -> str:
        entry = {
            "id": len(self.decisions) + 1,
            "topic": topic,
            "decision": decision[:500],
            "context": context[:300],
            "importance": min(10, max(1, importance)),
            "timestamp": datetime.now().isoformat()
        }
        self.decisions.append(entry)
        self._save()
        return f"📝 已記錄決定：{topic}"
    
    def recall(self, topic: str) -> Optional[Dict]:
        for d in reversed(self.decisions):
            if topic.lower() in d["topic"].lower():
                return d
        return None
    
    def get_recent(self, limit: int = 5) -> List[Dict]:
        return self.decisions[-limit:]
