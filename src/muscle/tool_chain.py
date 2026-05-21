"""
Tool Chain Engine v1 — 順序/並行/條件工具鏈
將多個工具組合成可執行管道
"""
import sys
import time
import traceback
from collections import OrderedDict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

sys.path.insert(0, str(Path(__file__).parent.parent))
from skeleton.base_organ import BaseOrgan


class ToolChain(BaseOrgan):
    """工具鏈引擎 — 支援順序、並行、條件分支"""

    def __init__(self, tools_system=None, meta_tooling=None):
        super().__init__("tool_chain")
        self._tools = tools_system
        self._meta = meta_tooling
        self._chains: Dict[str, Dict] = {}
        self._execution_history: List[Dict] = []

    # ── 鏈定義 ─────────────────────────────────────────────

    def define_chain(self, chain_id: str, steps: List[Dict]) -> Dict:
        """定義一條工具鏈
        steps: [
            {"tool": "tool_name", "params": {"key": "value"}, "on_error": "skip|abort|retry"},
            {"tool": "tool_name", "params": {...}},
            {"type": "parallel", "branches": [
                [{"tool": "a"}, {"tool": "b"}],
                [{"tool": "c"}, {"tool": "d"}]
            ]},
            {"type": "condition", "if": "prev.result.status == 200", "then": [...], "else": [...]},
        ]
        """
        chain_def = {
            "id": chain_id,
            "steps": steps,
            "created_at": time.time(),
            "execution_count": 0,
        }
        self._chains[chain_id] = chain_def
        return chain_def

    # ── 執行 ───────────────────────────────────────────────

    def execute_chain(self, chain_id: str, initial_input: Dict = None) -> Dict:
        """執行已定義的鏈"""
        chain = self._chains.get(chain_id)
        if not chain:
            return {"error": f"鏈 '{chain_id}' 不存在", "success": False}

        chain["execution_count"] += 1
        context = {"input": initial_input or {}, "steps": []}
        result = self._execute_steps(chain["steps"], context)

        self._execution_history.append({
            "chain_id": chain_id,
            "timestamp": time.time(),
            "success": result.get("success", False),
            "steps_executed": len(context.get("steps", [])),
        })

        return result

    def _execute_steps(self, steps: List[Dict], context: Dict) -> Dict:
        """遞迴執行步驟序列"""
        results = []
        last_result = None

        for i, step in enumerate(steps):
            step_type = step.get("type", "sequential")

            try:
                if step_type == "parallel":
                    step_result = self._execute_parallel(step, context)
                elif step_type == "condition":
                    step_result = self._execute_condition(step, context, last_result)
                elif step_type == "loop":
                    step_result = self._execute_loop(step, context)
                else:
                    step_result = self._execute_single_tool(step, context)

                context["steps"].append({
                    "index": i,
                    "type": step_type,
                    "tool": step.get("tool", ""),
                    "success": step_result.get("success", True),
                    "result": step_result,
                })
                last_result = step_result

                if not step_result.get("success", True):
                    on_error = step.get("on_error", "abort")
                    if on_error == "abort":
                        return {"success": False, "error": step_result.get("error"), "steps": context["steps"]}
                    elif on_error == "retry":
                        retries = step.get("retries", 3)
                        for _ in range(retries):
                            step_result = self._execute_single_tool(step, context)
                            if step_result.get("success"):
                                break

                results.append(step_result)

            except Exception as e:
                error_result = {"success": False, "error": str(e), "traceback": traceback.format_exc()}
                return {"success": False, "error": str(e), "steps": context["steps"]}

        return {"success": True, "results": results, "steps": context["steps"]}

    def _execute_single_tool(self, step: Dict, context: Dict) -> Dict:
        tool_name = step.get("tool", "")
        params = step.get("params", {})

        resolved_params = self._resolve_params(params, context)

        if self._tools and hasattr(self._tools, 'execute'):
            try:
                result = self._tools.execute(tool_name, resolved_params)
                if self._meta:
                    self._meta.record_usage(tool_name)
                return {"success": True, "tool": tool_name, "result": result}
            except Exception as e:
                return {"success": False, "tool": tool_name, "error": str(e)}

        return {"success": False, "tool": tool_name, "error": "工具系統不可用"}

    def _execute_parallel(self, step: Dict, context: Dict) -> Dict:
        """並行執行多個分支"""
        import concurrent.futures

        branches = step.get("branches", [])
        results = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(branches)) as executor:
            futures = {}
            for i, branch in enumerate(branches):
                branch_context = {"input": context.get("input", {}), "steps": []}
                future = executor.submit(self._execute_steps, branch, branch_context)
                futures[future] = i
            for future in concurrent.futures.as_completed(futures):
                idx = futures[future]
                try:
                    results.append({"branch": idx, "result": future.result(timeout=60)})
                except Exception as e:
                    results.append({"branch": idx, "error": str(e)})

        return {"success": True, "parallel_results": sorted(results, key=lambda x: x["branch"])}

    def _execute_condition(self, step: Dict, context: Dict, last_result: Dict) -> Dict:
        """條件分支執行"""
        condition = step.get("if", "True")
        safe_globals = {
            "__builtins__": {},
            "prev": last_result or {},
            "ctx": context,
            "True": True,
            "False": False,
            "None": None,
        }

        try:
            if eval(condition, safe_globals):
                return self._execute_steps(step.get("then", []), context)
            else:
                return self._execute_steps(step.get("else", []), context)
        except Exception as e:
            return {"success": False, "error": f"條件評估失敗: {e}"}

    def _execute_loop(self, step: Dict, context: Dict) -> Dict:
        """迴圈執行 — 有最大迭代限製"""
        max_iterations = step.get("max_iterations", 10)
        body = step.get("body", [])
        results = []

        for i in range(max_iterations):
            iter_context = {
                "input": context.get("input", {}),
                "steps": [],
                "loop_index": i,
            }
            result = self._execute_steps(body, iter_context)
            results.append(result)
            if not result.get("success"):
                break

        return {"success": True, "loop_results": results, "iterations": len(results)}

    def _resolve_params(self, params: Dict, context: Dict) -> Dict:
        """解析參數中的引用
        $step.0.result.data → 取第一個步驟結果的 data 欄位
        $input.key → 取初始輸入的 key
        """
        resolved = {}
        for key, value in params.items():
            if isinstance(value, str) and value.startswith("$"):
                ref_path = value[1:].split(".")
                resolved[key] = self._resolve_ref(ref_path, context)
            else:
                resolved[key] = value
        return resolved

    def _resolve_ref(self, path: List[str], context: Dict) -> Any:
        current = context
        for part in path:
            if isinstance(current, dict):
                if part.isdigit():
                    idx = int(part)
                    steps = current.get("steps", [])
                    if idx < len(steps):
                        current = steps[idx].get("result", {})
                    else:
                        return None
                else:
                    current = current.get(part, {})
            elif isinstance(current, list) and part.isdigit():
                idx = int(part)
                current = current[idx] if idx < len(current) else None
            else:
                return None
        return current

    # ── 鏈管理 ─────────────────────────────────────────────

    def list_chains(self) -> Dict[str, Dict]:
        return self._chains

    def get_chain(self, chain_id: str) -> Optional[Dict]:
        return self._chains.get(chain_id)

    def delete_chain(self, chain_id: str) -> bool:
        if chain_id in self._chains:
            del self._chains[chain_id]
            return True
        return False

    def get_execution_history(self, limit: int = 20) -> List[Dict]:
        return self._execution_history[-limit:]

    def status(self) -> Dict:
        return {
            "name": self.name,
            "alive": self.is_alive(),
            "chains_defined": len(self._chains),
            "executions": len(self._execution_history),
        }
