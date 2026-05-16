"""
矛盾檢測器
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

class ContradictionDetector:
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.contradictions_file = self.base_dir / "data" / "circuit" / "contradictions.json"
        self.contradictions_file.parent.mkdir(parents=True, exist_ok=True)
        self.statements = []
        self.contradictions = self._load()
    
    def _load(self) -> List[Dict]:
        if self.contradictions_file.exists():
            return json.loads(self.contradictions_file.read_text())
        return []
    
    def _save(self):
        self.contradictions = self.contradictions[-50:]
        self.contradictions_file.write_text(json.dumps(self.contradictions, ensure_ascii=False, indent=2))
    
    def record_statement(self, statement: str, source: str = "assistant") -> Dict:
        for prev in self.statements[-20:]:
            if self._is_contradictory(statement, prev["text"]):
                contradiction = {
                    "new_statement": statement,
                    "old_statement": prev["text"],
                    "timestamp": datetime.now().isoformat()
                }
                self.contradictions.append(contradiction)
                self._save()
                return {"is_contradiction": True, "old_statement": prev["text"][:100]}
        
        self.statements.append({"text": statement[:300], "source": source, "timestamp": datetime.now().isoformat()})
        self.statements = self.statements[-50:]
        return {"is_contradiction": False}
    
    def _is_contradictory(self, new: str, old: str) -> bool:
        pairs = [("是", "不是"), ("要", "不要"), ("可以", "不可以"), ("喜歡", "不喜歡"), ("好", "壞")]
        new_lower, old_lower = new.lower(), old.lower()
        for pos, neg in pairs:
            if pos in new_lower and neg in old_lower:
                return True
            if neg in new_lower and pos in old_lower:
                return True
        return False
    
    def clear_statements(self):
        self.statements = []
