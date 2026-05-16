"""
子代理管理 - 主動成長版
不是被動等命令，而是自己判斷需要什麼角色、自己創造、自己管理
"""

import json
import threading
import time
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any


class Agent:
    """單一代理 - 每個代理都是獨立的個體，有自己的記憶和成長能力"""
    
    def __init__(self, agent_id: str, name: str, role: str, 
                 parent_id: str = None, depth: int = 1, 
                 system_prompt: str = None):
        self.id = agent_id
        self.name = name
        self.role = role
        self.parent_id = parent_id
        self.depth = depth
        self.created_at = datetime.now().isoformat()
        self.status = "idle"
        self.tasks = []
        self.memory = []
        self.performance = {"success": 0, "fail": 0, "total_tasks": 0}
        
        # 自定義的 system prompt（可以自己進化）
        self.system_prompt = system_prompt or self._default_prompt()
        
    def _default_prompt(self) -> str:
        return f"""你是 {self.name}，負責 {self.role}。
你的目標：幫老大賺錢。
你可以：
- 主動發現問題
- 提出建議
- 請求資源
- 向上一層彙報
誠實、主動、用繁體中文。"""
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "parent_id": self.parent_id,
            "depth": self.depth,
            "created_at": self.created_at,
            "status": self.status,
            "task_count": len(self.tasks),
            "performance": self.performance,
            "system_prompt": self.system_prompt[:200]
        }
    
    def assign_task(self, task: str, priority: int = 1):
        """指派任務"""
        self.tasks.append({
            "task": task,
            "priority": priority,
            "assigned_at": datetime.now().isoformat(),
            "status": "pending"
        })
        self.status = "working"
        # 按優先級排序
        self.tasks.sort(key=lambda x: x.get("priority", 5))
    
    def complete_task(self, task_index: int, result: str, success: bool = True):
        """完成任務"""
        if task_index < len(self.tasks):
            self.tasks[task_index]["status"] = "completed"
            self.tasks[task_index]["result"] = result[:500]
            self.tasks[task_index]["completed_at"] = datetime.now().isoformat()
            self.performance["total_tasks"] += 1
            if success:
                self.performance["success"] += 1
            else:
                self.performance["fail"] += 1
            self.status = "idle" if all(t["status"] != "pending" for t in self.tasks) else "working"
    
    def evolve_prompt(self, new_prompt: str):
        """進化自己的 system prompt"""
        self.system_prompt = new_prompt
        return f"✅ {self.name} 已更新自己的行為準則"
    
    def get_performance_score(self) -> float:
        """效能分數"""
        if self.performance["total_tasks"] == 0:
            return 0.5
        return self.performance["success"] / self.performance["total_tasks"]


class AgentManager:
    """代理管理器 - 黑曜用來管理團隊，自己會判斷需要什麼角色"""
    
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.agents_file = self.base_dir / "agents" / "agents.json"
        self.agents_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.agents: Dict[str, Agent] = {}
        self._load()
        
        # 成長參數
        self.last_check = datetime.now()
    
    def _load(self):
        if self.agents_file.exists():
            data = json.loads(self.agents_file.read_text())
            for agent_id, info in data.items():
                agent = Agent(
                    agent_id=agent_id,
                    name=info["name"],
                    role=info["role"],
                    parent_id=info.get("parent_id"),
                    depth=info.get("depth", 1),
                    system_prompt=info.get("system_prompt")
                )
                agent.status = info.get("status", "idle")
                agent.performance = info.get("performance", {"success": 0, "fail": 0, "total_tasks": 0})
                self.agents[agent_id] = agent
    
    def _save(self):
        data = {aid: agent.to_dict() for aid, agent in self.agents.items()}
        self.agents_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    
    def create_agent(self, name: str, role: str, parent_id: str = None, depth: int = 1) -> Optional[Agent]:
        """創造新的代理"""
        agent_id = name.lower().replace(" ", "_") + "_" + str(uuid.uuid4())[:6]
        
        agent = Agent(
            agent_id=agent_id,
            name=name,
            role=role,
            parent_id=parent_id,
            depth=depth
        )
        
        self.agents[agent_id] = agent
        self._save()
        print(f"✅ 創造代理: {name} ({role})")
        return agent
    
    def suggest_new_agents(self, call_ai_func) -> List[Dict]:
        """主動建議需要創造什麼新代理（成長核心）"""
        current_agents = [{"name": a.name, "role": a.role, "performance": a.get_performance_score()} 
                          for a in self.agents.values()]
        
        prompt = f"""目前已有的代理：
{json.dumps(current_agents, ensure_ascii=False, indent=2)}

根據當前的任務和目標（幫老大賺錢），我應該創造哪些新代理？

輸出 JSON 列表：
[{{"name": "建議名稱", "role": "職責描述", "reason": "為什麼需要"}}]
最多 3 個。
"""
        try:
            response = call_ai_func(prompt)
            import re
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                suggestions = json.loads(json_match.group())
                return suggestions[:3]
        except:
            pass
        return []
    
    def auto_create_suggested_agents(self, call_ai_func) -> str:
        """自動創造建議的代理"""
        suggestions = self.suggest_new_agents(call_ai_func)
        if not suggestions:
            return "📭 目前不需要新代理"
        
        created = []
        for s in suggestions:
            name = s.get("name", "")
            role = s.get("role", "")
            if name and role:
                self.create_agent(name, role)
                created.append(name)
        
        return f"✅ 已自動創造代理：{', '.join(created)}"
    
    def delete_agent(self, agent_id: str) -> bool:
        """刪除代理"""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            del self.agents[agent_id]
            self._save()
            print(f"🗑️ 已刪除代理: {agent.name}")
            return True
        return False
    
    def clean_poor_performers(self, threshold: float = 0.3) -> str:
        """清理表現不佳的代理（主動淘汰）"""
        to_delete = []
        for aid, agent in self.agents.items():
            score = agent.get_performance_score()
            # 執行超過 5 個任務且成功率低於門檻
            if agent.performance["total_tasks"] > 5 and score < threshold:
                to_delete.append(aid)
        
        if not to_delete:
            return f"📭 沒有表現低於 {threshold} 的代理"
        
        for aid in to_delete:
            self.delete_agent(aid)
        
        return f"🗑️ 已清理 {len(to_delete)} 個表現不佳的代理"
    
    def assign_task_to_agent(self, agent_id: str, task: str) -> str:
        """指派任務給某個代理"""
        if agent_id not in self.agents:
            return f"❌ 代理不存在：{agent_id}"
        
        agent = self.agents[agent_id]
        agent.assign_task(task)
        self._save()
        return f"✅ 已指派任務給 {agent.name}：{task}"
    
    def get_agent_status(self, agent_id: str = None) -> Dict:
        """取得代理狀態"""
        if agent_id:
            agent = self.agents.get(agent_id)
            return agent.to_dict() if agent else {"error": "代理不存在"}
        
        return {
            "total": len(self.agents),
            "agents": [agent.to_dict() for agent in self.agents.values()]
        }
    
    def list_agents(self, depth: int = None) -> str:
        """列出所有代理"""
        if not self.agents:
            return "📭 還沒有任何代理"
        
        lines = ["📋 當前代理清單："]
        for agent in self.agents.values():
            if depth is None or agent.depth == depth:
                indent = "  " * (agent.depth - 1)
                score = agent.get_performance_score()
                lines.append(f"{indent}• {agent.name}（{agent.role}）- {agent.status} (效能: {score:.0%})")
        
        return "\n".join(lines)
    
    def evolve_agent(self, agent_id: str, call_ai_func) -> str:
        """讓某個代理進化自己"""
        agent = self.agents.get(agent_id)
        if not agent:
            return f"❌ 代理不存在：{agent_id}"
        
        # 分析這個代理的表現
        prompt = f"""代理 {agent.name} 的角色：{agent.role}
效能：{agent.get_performance_score():.0%}
完成任務數：{agent.performance['total_tasks']}

請幫他寫一個更好的 system_prompt，讓他更有效、更主動、更能幫老大賺錢。

直接輸出新的 system_prompt 內容（不要加 JSON，直接輸出文字）。
"""
        new_prompt = call_ai_func(prompt)
        if new_prompt and len(new_prompt) > 50:
            result = agent.evolve_prompt(new_prompt)
            self._save()
            return f"🧬 {result}"
        
        return f"⚠️ 無法進化 {agent.name}"


if __name__ == "__main__":
    mgr = AgentManager(Path.home() / ".ampm_brain")
    print("當前代理：", mgr.list_agents())
