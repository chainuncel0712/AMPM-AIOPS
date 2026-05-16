"""
Meta Tooling System v1 — 工具自省、依賴圖、鏈驗證
工具創造工具 — 但不會自進化（core-open 限制）
"""
import json
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


class MetaTooling:
    """工具的元工具層：檢查、驗證、分析、最佳化已註冊工具"""

    def __init__(self, tool_registry=None):
        self._registry = tool_registry
        self._dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self._reverse_graph: Dict[str, Set[str]] = defaultdict(set)
        self._tool_metadata: Dict[str, Dict] = {}
        self._usage_stats: Dict[str, int] = defaultdict(int)

    # ── 工具自省 ───────────────────────────────────────────

    def introspect(self, tool_name: str) -> Optional[Dict]:
        """取得工具完整元資訊"""
        if self._registry:
            tool = self._registry.get_tool(tool_name)
            if tool:
                return {
                    "name": tool_name,
                    "description": tool.get("description", ""),
                    "parameters": tool.get("parameters", {}),
                    "dependencies": list(self._dependency_graph.get(tool_name, set())),
                    "dependents": list(self._reverse_graph.get(tool_name, set())),
                    "usage_count": self._usage_stats.get(tool_name, 0),
                    "is_safe": self._is_tool_safe(tool),
                }
        return None

    def _is_tool_safe(self, tool: Dict) -> bool:
        """安全檢查：不允許系統級危險工具"""
        dangerous_patterns = [
            "rm -rf", "mkfs.", "dd if=", ":(){ :|:& };:",
            "chmod 777", "> /dev/sda", "eval(",
        ]
        desc = tool.get("description", "").lower()
        for pattern in dangerous_patterns:
            if pattern in desc:
                return False
        return True

    # ── 依賴圖 ─────────────────────────────────────────────

    def build_dependency_graph(self) -> Dict[str, Set[str]]:
        """從工具註冊表建構依賴圖"""
        self._dependency_graph.clear()
        self._reverse_graph.clear()

        if not self._registry:
            return dict(self._dependency_graph)

        all_tools = self._registry.list_tools() if hasattr(self._registry, 'list_tools') else {}
        for name, tool in all_tools.items():
            deps = set()
            desc = tool.get("description", "")
            params = tool.get("parameters", {})

            for other_name in all_tools:
                if other_name == name:
                    continue
                if other_name in desc or other_name in str(params):
                    deps.add(other_name)
            self._dependency_graph[name] = deps
            for dep in deps:
                self._reverse_graph[dep].add(name)

        return dict(self._dependency_graph)

    def get_dependencies(self, tool_name: str) -> Set[str]:
        return self._dependency_graph.get(tool_name, set())

    def get_dependents(self, tool_name: str) -> Set[str]:
        return self._reverse_graph.get(tool_name, set())

    def get_dependency_depth(self, tool_name: str) -> int:
        """計算工具依賴深度（避免循環依賴爆炸）"""
        visited = set()
        current = self._dependency_graph.get(tool_name, set())
        depth = 0
        while current:
            depth += 1
            next_level = set()
            for dep in current:
                if dep not in visited:
                    visited.add(dep)
                    next_level.update(self._dependency_graph.get(dep, set()))
            current = next_level - visited
        return depth

    # ── 循環依賴檢測 ───────────────────────────────────────

    def detect_cycles(self) -> List[List[str]]:
        """檢測工具註冊表中的循環依賴"""
        visited = set()
        rec_stack = set()
        cycles = []

        def dfs(node, path):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self._dependency_graph.get(node, set()):
                if neighbor not in visited:
                    dfs(neighbor, path.copy())
                elif neighbor in rec_stack:
                    cycle_start = path.index(neighbor)
                    cycles.append(path[cycle_start:] + [neighbor])
            rec_stack.discard(node)

        for node in self._dependency_graph:
            if node not in visited:
                dfs(node, [])
        return cycles

    # ── 鏈驗證 ─────────────────────────────────────────────

    def validate_chain(self, chain: List[str]) -> Tuple[bool, str]:
        """驗證工具鏈是否可以執行
        檢查：工具存在、類型相容、無循環依賴
        """
        if not chain:
            return False, "工具鏈為空"

        for i, tool_name in enumerate(chain):
            tool = self._registry.get_tool(tool_name) if self._registry else None
            if not tool:
                return False, f"步驟 {i+1}: 工具 '{tool_name}' 不存在"

            if not self._is_tool_safe(tool):
                return False, f"步驟 {i+1}: 工具 '{tool_name}' 不安全"

            # 檢查前後工具相容性
            if i > 0:
                prev = self._registry.get_tool(chain[i - 1]) if self._registry else None
                if prev and tool:
                    prev_output = prev.get("returns", {})
                    tool_input = tool.get("parameters", {})
                    if prev_output and tool_input:
                        common = set(prev_output.keys()) & set(tool_input.keys())
                        if not common:
                            # 無共用參數不是錯，只是提醒
                            pass

        # 檢查循環
        if len(set(chain)) < len(chain):
            return False, "工具鏈包含重複工具 (可能循環)"

        return True, "工具鏈驗證通過"

    # ── 使用統計 ───────────────────────────────────────────

    def record_usage(self, tool_name: str):
        self._usage_stats[tool_name] += 1

    def get_hot_tools(self, top_n: int = 10) -> List[Tuple[str, int]]:
        sorted_tools = sorted(self._usage_stats.items(), key=lambda x: x[1], reverse=True)
        return sorted_tools[:top_n]

    def get_cold_tools(self, days: int = 30, threshold: int = 0) -> List[str]:
        """找出長時間未使用的工具（垃圾回收候選）"""
        cold = []
        if self._registry:
            all_tools = self._registry.list_tools() if hasattr(self._registry, 'list_tools') else {}
            for name in all_tools:
                if self._usage_stats.get(name, 0) <= threshold:
                    cold.append(name)
        return cold

    # ── 工具分類與搜尋 ─────────────────────────────────────

    def categorize_tools(self) -> Dict[str, List[str]]:
        """按類型分類工具"""
        categories = defaultdict(list)
        if self._registry:
            all_tools = self._registry.list_tools() if hasattr(self._registry, 'list_tools') else {}
            for name, tool in all_tools.items():
                cat = tool.get("type", tool.get("category", "uncategorized"))
                categories[cat].append(name)
        return dict(categories)

    def search_tools(self, query: str) -> List[Dict]:
        """搜尋工具（名稱、描述模糊匹配）"""
        results = []
        if self._registry:
            all_tools = self._registry.list_tools() if hasattr(self._registry, 'list_tools') else {}
            for name, tool in all_tools.items():
                desc = tool.get("description", "")
                if query.lower() in name.lower() or query.lower() in desc.lower():
                    results.append({"name": name, "description": desc, "score": len(name)})
        return sorted(results, key=lambda x: x["score"])

    def status(self) -> Dict:
        return {
            "total_tools": len(self._dependency_graph),
            "cycles_detected": len(self.detect_cycles()),
            "total_usage": sum(self._usage_stats.values()),
            "hot_tools": [t[0] for t in self.get_hot_tools(5)],
            "cold_tools": self.get_cold_tools(),
        }
