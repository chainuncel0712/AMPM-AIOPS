"""
Control Plane — 統一控製層
===========================
Single call point for all cross-cutting concerns:
  - Module permission check (gatekeeper)
  - Cross-zone enforcement (security_zone)
  - Event logging (event_log)
  - LLM routing guard
  - Static analysis (statelessness check)

Usage:
    from governance.control_plane import cp
    cp.check("module_x", "run_tool", input_data=...)
"""
import json
import os
import threading
import time
from typing import Any, Dict, Optional

from governance.event_log import event_log
from governance.gatekeeper import gatekeeper


class ControlPlane:
    """
    Thread-safe single authority that all modules must call before
    executing any operation that crosses layers (decision→execution,
    execution→memory, etc.).
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._stats: Dict[str, int] = {"allowed": 0, "blocked": 0, "warned": 0}
        self._last_call: float = 0.0
        self._total_latency_ms: float = 0.0
        self._call_count: int = 0

    # ── public API ──────────────────────────────────────────────

    def check(
        self,
        module: str,
        action: str,
        *,
        input_data: Any = None,
        output_data: Any = None,
        decision: str = "",
        parent_id: str = "",
        rollback_point: bool = False,
        zone_check: bool = True,
        permission_check: bool = True,
    ) -> bool:
        """
        Unified permission check + event logging.
        Returns True if allowed, False if blocked/warned.

        All modules MUST call this before executing any action that:
          - Calls an external tool
          - Writes to memory
          - Modifies routing/plan
          - Delegates to another module
        """
        t0 = time.perf_counter()
        allowed = True

        # 1. Permissions check
        if permission_check:
            perm_ok = gatekeeper.check_module_permission(module, action)
            if not perm_ok:
                with self._lock:
                    self._stats["blocked"] += 1
                event_log.record(
                    source=f"control_plane:{module}",
                    action=f"permission_denied:{action}",
                    input_data={"module": module, "action": action},
                    decision="BLOCKED",
                )
                allowed = False

        # 2. Zone check (decision→execution etc.)
        if zone_check and allowed:
            from governance.security_zone import SecurityZone
            zone_ok = SecurityZone.check(module, action)
            if not zone_ok:
                with self._lock:
                    self._stats["blocked"] += 1
                allowed = False

        # 3. Event log
        event_log.record(
            source=f"control_plane:{module}",
            action=action,
            input_data=input_data,
            output_data=output_data,
            decision=decision or ("ALLOWED" if allowed else "BLOCKED"),
            parent_id=parent_id,
            rollback_point=rollback_point,
        )

        # 4. Stats
        with self._lock:
            if not allowed:
                self._stats["blocked"] += 1
            else:
                self._stats["allowed"] += 1
            self._call_count += 1
            self._total_latency_ms += (time.perf_counter() - t0) * 1000
            self._last_call = time.time()

        return allowed

    def check_llm(self, module: str, system_prompt: str, user_message: str) -> bool:
        """
        LLM-specific guard: ensures the module is allowed to call LLM
        and logs the request/response boundaries.
        """
        return self.check(module, "call_llm", input_data={
            "module": module,
            "system_len": len(system_prompt),
            "user_len": len(user_message),
        })

    def assert_stateless(self, module: str, state_keys: list) -> bool:
        """
        Enforces statelessness: checks that a module is not storing
        mutable state between calls. Logs violations.
        """
        has_mutation = any(k for k in state_keys if k in ("_state", "_cache", "_memory"))
        if has_mutation:
            event_log.record(
                source="control_plane",
                action="stateless_violation",
                input_data={"module": module, "state_keys": state_keys},
                decision="WARN",
            )
            return False
        return True

    def current_decision_id(self) -> str:
        """Return the latest action_id for tracing."""
        last = event_log.replay(limit=1)
        return last[0]["action_id"] if last else ""

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            avg_lat = self._total_latency_ms / max(self._call_count, 1)
            return {
                **self._stats,
                "total_calls": self._call_count,
                "avg_latency_ms": round(avg_lat, 2),
                "last_call_ago_s": round(time.time() - self._last_call, 1) if self._last_call else None,
            }

    def last_rollback_point(self) -> str:
        return event_log.last_rollback_point()


# Module-level singleton
cp = ControlPlane()
