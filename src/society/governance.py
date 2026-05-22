"""
Governance — AI 社會治理
=========================
管理 agent 之間的權限、角色、投票與共識。
決定誰能做什麼、誰有否決權、何時需要投票。
"""
import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


class Governance:

    ROLES = {
        "founder":    {"permissions": {"all"}, "vote_weight": 100},
        "admin":      {"permissions": {"deploy", "configure", "manage_agents", "view_all"}, "vote_weight": 50},
        "developer":  {"permissions": {"deploy", "configure", "view_all"}, "vote_weight": 30},
        "analyst":    {"permissions": {"view_all", "run_analysis"}, "vote_weight": 20},
        "operator":   {"permissions": {"view_all", "monitor"}, "vote_weight": 15},
        "guest":      {"permissions": {"view_public"}, "vote_weight": 1},
    }

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir or Path.home() / ".ampm_brain")
        self.config_file = self.base_dir / "data" / "society" / "governance.json"
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._asleep = False

        self.agents: Dict[str, Dict] = {}
        self.proposals: Dict[str, Dict] = {}
        self.decision_log: List[Dict] = []
        self._load()

    def _load(self):
        if self.config_file.exists():
            try:
                data = json.loads(self.config_file.read_text())
                self.agents = data.get("agents", {})
                self.proposals = data.get("proposals", {})
                self.decision_log = data.get("log", [])
            except Exception:
                pass

    def _save(self):
        with self._lock:
            self.config_file.write_text(json.dumps({
                "agents": self.agents,
                "proposals": self.proposals,
                "log": self.decision_log[-1000:],
            }, ensure_ascii=False, indent=2))

    def register_agent(self, agent_id: str, role: str = "guest",
                       name: str = ""):
        with self._lock:
            role_info = self.ROLES.get(role, self.ROLES["guest"])
            self.agents[agent_id] = {
                "id": agent_id,
                "name": name or agent_id,
                "role": role,
                "permissions": list(role_info["permissions"]),
                "vote_weight": role_info["vote_weight"],
                "registered_at": datetime.now().isoformat(),
                "active": True,
                "violations": 0,
            }
            self._save()

    def can(self, agent_id: str, action: str) -> bool:
        """Check if an agent is allowed to perform an action."""
        agent = self.agents.get(agent_id, {})
        if not agent.get("active"):
            return False
        perms = set(agent.get("permissions", []))
        if "all" in perms:
            return True
        return action in perms

    def propose(self, title: str, description: str, proposer_id: str,
                options: List[str] = None) -> str:
        """Create a proposal for agent voting."""
        import uuid
        pid = str(uuid.uuid4())[:8]
        with self._lock:
            self.proposals[pid] = {
                "id": pid,
                "title": title,
                "description": description,
                "proposer": proposer_id,
                "options": options or ["approve", "reject"],
                "votes": {opt: [] for opt in (options or ["approve", "reject"])},
                "status": "open",
                "created_at": datetime.now().isoformat(),
                "closed_at": None,
                "result": None,
            }
            self._save()
        return pid

    def vote(self, proposal_id: str, agent_id: str, option: str) -> bool:
        """Cast a vote on a proposal."""
        with self._lock:
            p = self.proposals.get(proposal_id)
            if not p or p["status"] != "open":
                return False
            if option not in p["options"]:
                return False
            # Remove previous vote by same agent
            for votes in p["votes"].values():
                if agent_id in votes:
                    votes.remove(agent_id)
            p["votes"][option].append(agent_id)
            self._save()
        return True

    def tally(self, proposal_id: str) -> Dict:
        """Count votes and determine result."""
        with self._lock:
            p = self.proposals.get(proposal_id)
            if not p:
                return {"error": "not found"}
            weighted: Dict[str, float] = {}
            for opt, voters in p["votes"].items():
                weight = sum(
                    self.agents.get(v, {}).get("vote_weight", 1)
                    for v in voters
                )
                weighted[opt] = weight
            winner = max(weighted, key=weighted.get) if weighted else None
            p["status"] = "closed"
            p["closed_at"] = datetime.now().isoformat()
            p["result"] = winner
            self.decision_log.append({
                "type": "proposal",
                "id": proposal_id,
                "result": winner,
                "weighted_votes": weighted,
                "timestamp": datetime.now().isoformat(),
            })
            self._save()
            return {"proposal_id": proposal_id, "result": winner, "votes": weighted}

    def sleep(self): self._asleep = True
    def wake(self): self._asleep = False
    def is_asleep(self) -> bool: return self._asleep
    def memory_estimate_mb(self) -> int: return len(self.agents) // 50 + 2

    def status(self) -> dict:
        return {
            "name": "Governance",
            "agents": len(self.agents),
            "open_proposals": sum(1 for p in self.proposals.values() if p["status"] == "open"),
            "roles_distribution": {
                role: sum(1 for a in self.agents.values() if a["role"] == role)
                for role in self.ROLES
            },
        }
