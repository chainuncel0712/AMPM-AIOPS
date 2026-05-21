"""
Loop Detector v1 — 遞迴/無限循環檢測與熔斷
追蹤執行路徑，檢測循環模式，自動熔斷
"""
import sys
import time
import hashlib
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))
from skeleton.base_organ import BaseOrgan


class LoopDetector(BaseOrgan):
    """循環檢測器 — 追蹤呼叫圖、檢測循環、自動熔斷"""

    def __init__(self, max_depth: int = 50, window_size: int = 100):
        super().__init__("loop_detector")
        self._max_depth = max_depth
        self._window_size = window_size
        # 呼叫追蹤
        self._call_stack: List[str] = []
        self._call_graph: Dict[str, Set[str]] = defaultdict(set)
        self._call_history: deque = deque(maxlen=window_size)
        # 指紋記錄（用於相似性檢測）
        self._fingerprints: Dict[str, List[float]] = defaultdict(list)
        # 熔斷狀態
        self._breakers: Dict[str, Dict] = {}
        self._tripped_count = 0

    # ── 呼叫追蹤 ───────────────────────────────────────────

    def enter(self, tool_name: str) -> Dict:
        """進入工具呼叫，檢查是否觸發循環"""
        now = time.time()

        # 檢查深度限製
        self._call_stack.append(tool_name)
        if len(self._call_stack) > self._max_depth:
            self._call_stack.pop()
            return {"allowed": False, "reason": f"超過最大呼叫深度 {self._max_depth}", "depth": len(self._call_stack) + 1}

        # 檢查直接遞迴（連續呼叫同一個工具）
        self._call_history.append((tool_name, now))
        if self._detect_direct_recursion(tool_name):
            return {"allowed": False, "reason": f"檢測到直接遞迴: {tool_name}", "type": "direct_recursion"}

        # 檢查間接循環（A→B→A）
        cycle = self._detect_cycle(tool_name)
        if cycle:
            return {"allowed": False, "reason": f"檢測到循環依賴: {' → '.join(cycle)}", "type": "cycle", "cycle": cycle}

        # 檢查熔斷器狀態
        breaker = self._breakers.get(tool_name, {})
        if breaker.get("open"):
            if now - breaker["tripped_at"] < breaker.get("cooldown", 60):
                return {"allowed": False, "reason": f"熔斷器開啟: {tool_name}", "type": "breaker_open"}
            else:
                # 半開狀態
                self._breakers[tool_name]["open"] = False
                self._breakers[tool_name]["half_open"] = True

        return {"allowed": True, "depth": len(self._call_stack)}

    def exit(self, tool_name: str, success: bool = True):
        """退出工具呼叫，更新追蹤"""
        if self._call_stack and self._call_stack[-1] == tool_name:
            self._call_stack.pop()
        else:
            # 避免堆疊不一致時出錯
            if tool_name in self._call_stack:
                self._call_stack.remove(tool_name)

        # 記錄失敗
        if not success and tool_name in self._breakers:
            breaker = self._breakers[tool_name]
            breaker["failures"] += 1
            if breaker["failures"] >= breaker.get("threshold", 5):
                breaker["open"] = True
                breaker["tripped_at"] = time.time()
                self._tripped_count += 1

    def _detect_direct_recursion(self, tool_name: str) -> bool:
        """檢測是否在短時間內重複呼叫同一工具"""
        recent = list(self._call_history)[-5:]
        count = sum(1 for t, _ in recent if t == tool_name)
        return count >= 3  # 最近 5 次呼叫中有 3 次是同一工具

    def _detect_cycle(self, tool_name: str) -> Optional[List[str]]:
        """DFS 檢測呼叫圖中的循環"""
        visited = set()
        rec_stack = []

        def dfs(node, path):
            visited.add(node)
            rec_stack.append(node)
            for neighbor in self._call_graph.get(node, set()):
                if neighbor not in visited:
                    result = dfs(neighbor, path + [neighbor])
                    if result:
                        return result
                elif neighbor in rec_stack:
                    cycle_start = rec_stack.index(neighbor)
                    return rec_stack[cycle_start:] + [neighbor]
            rec_stack.pop()
            return None

        if tool_name not in visited:
            return dfs(tool_name, [tool_name])
        return None

    # ── 指紋檢測 ───────────────────────────────────────────

    def fingerprint(self, response: str) -> str:
        """生成輸出的輕量指紋"""
        return hashlib.md5(response.encode()).hexdigest()[:12]

    def check_repetition(self, response: str, tool_name: str) -> Dict:
        """檢查輸出是否重複（可能的死循環徵兆）"""
        fp = self.fingerprint(response)
        fps = self._fingerprints.get(tool_name, [])

        now = time.time()
        self._fingerprints[tool_name] = [t for t in fps if now - t < 60]
        self._fingerprints[tool_name].append(now)

        recent_fps = list(self._call_history)[-20:]
        same_fp_count = len([f for f, _ in recent_fps if f == fp])

        if same_fp_count >= 5:
            return {"repeated": True, "fingerprint": fp, "count": same_fp_count, "warning": "輸出重複超過 5 次"}
        return {"repeated": False, "fingerprint": fp}

    # ── 熔斷器 ─────────────────────────────────────────────

    def set_breaker(self, tool_name: str, threshold: int = 5, cooldown: int = 60):
        self._breakers[tool_name] = {
            "threshold": threshold,
            "cooldown": cooldown,
            "failures": 0,
            "open": False,
            "half_open": False,
            "tripped_at": 0,
        }

    def record_failure(self, tool_name: str):
        breaker = self._breakers.get(tool_name)
        if breaker:
            breaker["failures"] += 1
            if breaker["failures"] >= breaker["threshold"]:
                breaker["open"] = True
                breaker["tripped_at"] = time.time()
                self._tripped_count += 1

    def record_success(self, tool_name: str):
        breaker = self._breakers.get(tool_name)
        if breaker:
            breaker["failures"] = 0
            if breaker.get("half_open"):
                breaker["open"] = False
                breaker["half_open"] = False

    def is_breaker_open(self, tool_name: str) -> bool:
        breaker = self._breakers.get(tool_name, {})
        return breaker.get("open", False)

    # ── 呼叫圖 ─────────────────────────────────────────────

    def add_edge(self, from_tool: str, to_tool: str):
        self._call_graph[from_tool].add(to_tool)

    def find_all_cycles(self) -> List[List[str]]:
        """找出所有已知的循環"""
        visited = set()
        rec_stack = set()
        all_cycles = []

        def dfs(node, path):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            for neighbor in self._call_graph.get(node, set()):
                if neighbor not in visited:
                    dfs(neighbor, path.copy())
                elif neighbor in rec_stack:
                    cycle_start = path.index(neighbor)
                    all_cycles.append(path[cycle_start:] + [neighbor])
            rec_stack.discard(node)

        for node in self._call_graph:
            if node not in visited:
                dfs(node, [])
        return all_cycles

    def status(self) -> Dict:
        return {
            "name": self.name,
            "alive": self.is_alive(),
            "current_depth": len(self._call_stack),
            "call_graph_size": len(self._call_graph),
            "cycles": len(self.find_all_cycles()),
            "breakers": len(self._breakers),
            "tripped": self._tripped_count,
            "history": len(self._call_history),
        }
