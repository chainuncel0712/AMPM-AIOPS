"""
Audit Layer — 決策審計系統
============================
能夠追溯每個決策的完整生命週期：
  Input → Decision → Route → Tool Call → Output → Memory Write

用法：
    auditor = AuditLayer()
    tree = auditor.trace("abc123...")
    auditor.lineage("abc123...")  # 回傳從 root 到該 action 的路徑
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from governance.event_log import event_log


class AuditLayer:
    """以 action_id 為核心的決策追溯引擎。"""

    def trace(self, action_id: str) -> Dict[str, Any]:
        """
        完整追蹤一個 action：
        - 自身記錄
        - parent chain（向上追溯）
        - child tree（向下展開）
        - 侵犯分析（越權、違規）
        """
        entry = event_log.get_by_action_id(action_id)
        if not entry:
            return {"error": f"action_id {action_id} 不存在"}

        # 向上追溯至 root
        parent_chain = self._parent_chain(action_id)

        # 向下展開所有子節點
        child_tree = self._child_tree(action_id)

        # 侵犯檢查
        violations = self._check_violations(entry)

        return {
            "action_id": action_id,
            "entry": entry,
            "parent_chain": parent_chain,
            "child_tree": child_tree,
            "violations": violations,
            "summary": self._summarize(entry, parent_chain),
        }

    def lineage(self, action_id: str) -> List[Dict]:
        """回傳從 root 到該 action 的完整路徑。"""
        chain = self._parent_chain(action_id)
        chain.reverse()
        return chain

    def _parent_chain(self, action_id: str) -> List[Dict]:
        """向上追溯 parent 鏈。"""
        chain = []
        current_id = action_id
        visited = set()
        while current_id and current_id not in visited:
            visited.add(current_id)
            entry = event_log.get_by_action_id(current_id)
            if not entry:
                break
            chain.append(entry)
            current_id = entry.get("parent_id", "")
        return chain

    def _child_tree(self, root_id: str, max_depth: int = 5) -> List[Dict]:
        """向下展開所有子節點。"""
        return event_log.get_tree(root_id)

    def _check_violations(self, entry: Dict) -> List[str]:
        """檢查該 entry 是否有違規。"""
        issues = []
        action = entry.get("action", "")
        source = entry.get("source", "")

        if "cross_zone_violation" in action:
            issues.append(f"🚫 跨區越權：{source} — {entry.get('input', {}).get('action', '')}")
        if "permission_denied" in action:
            issues.append(f"🔒 權限不足：{source}")
        if "stateless_violation" in action:
            issues.append(f"📦 隱性 state：{source}")

        return issues

    def _summarize(self, entry: Dict, parent_chain: List[Dict]) -> str:
        """產生一行摘要。"""
        source = entry.get("source", "?")
        action = entry.get("action", "?")
        decision = entry.get("decision", "")
        parent = parent_chain[-1] if parent_chain else None
        trigger = parent.get("action", "root") if parent else "root"
        return f"{source} 執行了 {action}（觸發者: {trigger}）→ {decision or 'no decision'}"

    def replay_session(self, start_id: str = None, end_id: str = None) -> List[Dict]:
        """重播一段決策區間。"""
        return event_log.replay(start_id=start_id, end_id=end_id)

    def export_trace(self, action_id: str, path: str):
        """匯出完整 trace 為 JSON。"""
        trace_data = self.trace(action_id)
        Path(path).write_text(json.dumps(trace_data, ensure_ascii=False, indent=2))
        return path

    def stats(self) -> Dict:
        """審計統計。"""
        es = event_log.stats()
        return {
            "total_traced": es["total_events"],
            "unique_sources": len(es["by_source"]),
            "by_source": es["by_source"],
            "last_rollback": es["last_rollback"],
        }


auditor = AuditLayer()
