"""
Workflow Compiler v1 — DAG 工作流 → 可執行管線
任務自動分配到共享記憶代理執行
"""
import sys
import time
import json
import uuid
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))
from skeleton.base_organ import BaseOrgan


class WorkflowCompiler(BaseOrgan):
    """
    工作流編譯器 — 將 DAG 任務圖編譯為可執行管線
    支援代理分配、共享記憶、平行執行、依賴解析
    """

    def __init__(self, tool_chain=None, agents=None, shared_memory=None):
        super().__init__("workflow_compiler")
        self._tool_chain = tool_chain
        self._agents = agents or []
        self._shared_memory = shared_memory or {}
        self._workflows: Dict[str, Dict] = {}
        self._execution_results: Dict[str, Dict] = {}

    # ── Workflow 定義 ──────────────────────────────────────

    def define(self, workflow_id: str, dag: Dict) -> Dict:
        """定義 DAG 工作流
        dag = {
            "nodes": {
                "A": {"tool": "fetch_data", "params": {...}, "agent": "agent_1"},
                "B": {"tool": "analyze", "params": {...}, "agent": "auto"},
                "C": {"tool": "report", "depends_on": ["A", "B"]},
            },
            "edges": [["A", "C"], ["B", "C"]],
            "entry": "A",
        }
        支援自動推導 edges 從 depends_on
        """
        nodes = dag.get("nodes", {})
        edges = dag.get("edges", [])

        if not edges:
            edges = self._infer_edges(nodes)

        # 驗證 DAG 無循環
        if self._has_cycle(nodes, edges):
            return {"error": "DAG 包含循環依賴", "workflow_id": workflow_id}

        # 拓墣排序
        topo_order = self._topological_sort(nodes, edges)

        workflow = {
            "id": workflow_id,
            "nodes": nodes,
            "edges": edges,
            "topo_order": topo_order,
            "created_at": time.time(),
            "status": "defined",
        }
        self._workflows[workflow_id] = workflow
        return workflow

    def _infer_edges(self, nodes: Dict) -> List[List[str]]:
        edges = []
        for name, node in nodes.items():
            for dep in node.get("depends_on", []):
                if dep in nodes:
                    edges.append([dep, name])
        return edges

    def _has_cycle(self, nodes: Dict, edges: List[List[str]]) -> bool:
        adj = defaultdict(list)
        in_degree = defaultdict(int)

        for node in nodes:
            in_degree[node] = 0
        for src, dst in edges:
            adj[src].append(dst)
            in_degree[dst] += 1

        queue = deque([n for n in nodes if in_degree[n] == 0])
        visited = 0
        while queue:
            n = queue.popleft()
            visited += 1
            for neighbor in adj[n]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return visited != len(nodes)

    def _topological_sort(self, nodes: Dict, edges: List[List[str]]) -> List[str]:
        adj = defaultdict(list)
        in_degree = defaultdict(int)
        for node in nodes:
            in_degree[node] = 0
        for src, dst in edges:
            adj[src].append(dst)
            in_degree[dst] += 1

        queue = deque([n for n in nodes if in_degree[n] == 0])
        order = []
        while queue:
            n = queue.popleft()
            order.append(n)
            for neighbor in adj[n]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        return order

    # ── 代理分配 ───────────────────────────────────────────

    def assign_agents(self, workflow_id: str, agents: List[str] = None) -> Dict:
        """將工作流節點分配到代理
        策略：負載均衡 + 能力匹配
        """
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            return {"error": "工作流不存在"}
        if agents:
            self._agents = agents

        nodes = workflow["nodes"]
        available = list(self._agents) if self._agents else ["default_agent"]

        # 負載均衡分配
        agent_load = {a: 0 for a in available}
        assignments = {}

        for node_name in workflow["topo_order"]:
            node = nodes.get(node_name, {})

            # 如果節點指定了代理，直接使用
            specified = node.get("agent", "auto")
            if specified != "auto" and specified in available:
                agent = specified
            else:
                # 選負載最低的代理
                agent = min(available, key=lambda a: agent_load[a])

            assignments[node_name] = agent
            agent_load[agent] += 1

        workflow["assignments"] = assignments
        return {"workflow_id": workflow_id, "assignments": assignments, "load": agent_load}

    # ── 執行 ───────────────────────────────────────────────

    def execute(self, workflow_id: str, initial_input: Dict = None) -> Dict:
        """執行 DAG 工作流
        按拓墣順序執行，平行層級可同時執行
        """
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            return {"error": "工作流不存在", "success": False}

        workflow["status"] = "running"
        nodes = workflow["nodes"]
        topo = workflow["topo_order"]

        # 分層：找出所有平行層級
        levels = self._compute_levels(nodes, workflow["edges"], topo)

        results = {}
        context = {"input": initial_input or {}, "shared_memory": self._shared_memory}
        exec_id = str(uuid.uuid4())[:8]

        for level_idx, level_nodes in enumerate(levels):
            level_results = self._execute_level(level_nodes, nodes, results, context)

            for node_name, result in level_results.items():
                results[node_name] = result
                # 寫入共享記憶
                self._shared_memory[f"workflow:{exec_id}:{node_name}"] = result

            # 檢查是否有節點失敗
            for node_name, result in level_results.items():
                if not result.get("success", True):
                    workflow["status"] = "failed"
                    return {
                        "success": False,
                        "exec_id": exec_id,
                        "failed_node": node_name,
                        "error": result.get("error"),
                        "results": results,
                    }

        workflow["status"] = "completed"
        exec_result = {
            "success": True,
            "exec_id": exec_id,
            "results": results,
            "nodes_executed": len(results),
        }
        self._execution_results[exec_id] = exec_result
        return exec_result

    def _compute_levels(self, nodes: Dict, edges: List[List[str]], topo: List[str]) -> List[List[str]]:
        """計算 DAG 層級，同層可平行執行"""
        in_degree = defaultdict(int)
        adj = defaultdict(list)
        for node in nodes:
            in_degree[node] = 0
        for src, dst in edges:
            adj[src].append(dst)
            in_degree[dst] += 1

        levels = []
        current = [n for n in topo if in_degree[n] == 0]
        while current:
            levels.append(list(current))
            next_level = []
            for n in current:
                for neighbor in adj[n]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        next_level.append(neighbor)
            current = next_level
        return levels

    def _execute_level(self, level_nodes: List[str], nodes: Dict, prev_results: Dict, context: Dict) -> Dict:
        """平行執行同一層的所有節點"""
        import concurrent.futures

        level_results = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(level_nodes)) as executor:
            futures = {}
            for node_name in level_nodes:
                node = nodes[node_name]
                future = executor.submit(
                    self._execute_node, node_name, node, prev_results, context
                )
                futures[future] = node_name
            for future in concurrent.futures.as_completed(futures):
                node_name = futures[future]
                try:
                    level_results[node_name] = future.result(timeout=120)
                except Exception as e:
                    level_results[node_name] = {"success": False, "error": str(e)}

        return level_results

    def _execute_node(self, node_name: str, node: Dict, prev_results: Dict, context: Dict) -> Dict:
        """執行單個 DAG 節點"""
        tool_name = node.get("tool", "")

        # 解析參數（可引用前序節點結果）
        params = node.get("params", {})
        resolved_params = self._resolve_node_params(params, prev_results, context)

        if self._tool_chain:
            chain_id = f"wf_node_{node_name}"
            self._tool_chain.define_chain(chain_id, [{"tool": tool_name, "params": resolved_params}])
            result = self._tool_chain.execute_chain(chain_id)
            return result

        return {"success": False, "error": "無工具鏈引擎可用"}

    def _resolve_node_params(self, params: Dict, prev_results: Dict, context: Dict) -> Dict:
        resolved = {}
        for key, value in params.items():
            if isinstance(value, str) and value.startswith("@"):
                ref = value[1:]
                if "." in ref:
                    node, field = ref.split(".", 1)
                    resolved[key] = prev_results.get(node, {}).get("result", {}).get(field, value)
                else:
                    resolved[key] = prev_results.get(ref, {}).get("result", value)
            elif isinstance(value, str) and value.startswith("$"):
                mem_key = value[1:]
                resolved[key] = context["shared_memory"].get(mem_key, value)
            else:
                resolved[key] = value
        return resolved

    # ── 共享記憶空間 ───────────────────────────────────────

    def write_memory(self, key: str, value: Any, ttl: int = 3600):
        """寫入共享記憶"""
        self._shared_memory[key] = {
            "value": value,
            "timestamp": time.time(),
            "ttl": ttl,
        }

    def read_memory(self, key: str) -> Any:
        """讀取共享記憶（自動過期清理）"""
        entry = self._shared_memory.get(key)
        if entry and isinstance(entry, dict):
            if time.time() - entry["timestamp"] > entry["ttl"]:
                del self._shared_memory[key]
                return None
            return entry["value"]
        return entry

    def list_memory(self, prefix: str = "") -> Dict[str, Any]:
        result = {}
        for key, val in self._shared_memory.items():
            if key.startswith(prefix):
                result[key] = val.get("value", val) if isinstance(val, dict) else val
        return result

    def clear_memory(self, prefix: str = ""):
        if prefix:
            keys = [k for k in self._shared_memory if k.startswith(prefix)]
            for k in keys:
                del self._shared_memory[k]
        else:
            self._shared_memory.clear()

    # ── 工作流管理 ─────────────────────────────────────────

    def list_workflows(self) -> Dict[str, Dict]:
        return {k: {"status": v["status"], "nodes": len(v["nodes"])} for k, v in self._workflows.items()}

    def get_workflow(self, workflow_id: str) -> Optional[Dict]:
        return self._workflows.get(workflow_id)

    def delete_workflow(self, workflow_id: str) -> bool:
        if workflow_id in self._workflows:
            del self._workflows[workflow_id]
            return True
        return False

    def get_execution(self, exec_id: str) -> Optional[Dict]:
        return self._execution_results.get(exec_id)

    def status(self) -> Dict:
        return {
            "name": self.name,
            "alive": self.is_alive(),
            "workflows": len(self._workflows),
            "executions": len(self._execution_results),
            "shared_memory_keys": len(self._shared_memory),
            "agents_assigned": len(self._agents),
        }
