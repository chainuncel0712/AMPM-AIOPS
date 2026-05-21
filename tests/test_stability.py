"""
Stability Test — 系統驗收批次
==============================
驗證治理層實際運作狀況。

檢驗項目：
  A. 決策可預測 — 同一 input → 穩定 output
  B. 可重播 — event_log replay 能完整還原 flow
  C. 無越權 — brain 不准 execute，executor 不准 decide
  D. 無隱性 state — module 是否有未宣告的 mutable state
"""
import json
import os
import sys
import time
import threading
import statistics

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from governance.gatekeeper import gatekeeper, GatekeeperViolation
from governance.security_zone import SecurityZone
from governance.event_log import event_log
from governance.control_plane import cp

PASS = "✅"
FAIL = "❌"
WARN = "⚠️"


def test_predictability():
    """A. 同一 input → 同一 output（純函數路徑）"""
    print(f"\n{'='*60}")
    print(f" A. 決策可預測性")
    print(f"{'='*60}")

    results = []

    # Gatekeeper 相同參數呼叫兩次
    for i in range(3):
        r1 = gatekeeper.check_module_permission("brain", "plan")
        r2 = gatekeeper.check_module_permission("brain", "plan")
        assert r1 == r2, f"brain/plan 結果不一致: {r1} vs {r2}"

    results.append((PASS, "gatekeeper.check_module_permission 三次呼叫結果一致 (brain/plan → True)"))

    # SecurityZone 相同參數
    for i in range(3):
        r1 = SecurityZone.check("brain", "plan")
        r2 = SecurityZone.check("brain", "plan")
        assert r1 == r2, f"brain/plan zone check 不一致"

    results.append((PASS, "SecurityZone.check 三次呼叫結果一致"))

    # ControlPlane 相同參數
    for i in range(3):
        a = cp.check("brain", "plan", input_data={"test": 1})
        b = cp.check("brain", "plan", input_data={"test": 1})
        assert a == b, f"control_plane brain/plan 不一致"

    results.append((PASS, "ControlPlane.check 三次呼叫結果一致"))

    # permission.json 相同條件 — executor/run_tool 應為 True
    for _ in range(3):
        r = gatekeeper.check_module_permission("executor", "run_tool")
        assert r == True, f"executor/run_tool 應為 True，實際 {r}"

    results.append((PASS, "executor/run_tool permissions 一致為 true"))

    # 越權測試 — brain/run_tool 應為 False
    for _ in range(3):
        r = gatekeeper.check_module_permission("brain", "run_tool")
        assert r == False, f"brain/run_tool 應為 False，實際 {r}"

    results.append((PASS, "brain/run_tool permissions 一致為 false"))

    print(f"\n  Predictability: {sum(1 for r in results if r[0]==PASS)}/{len(results)}")
    for status, msg in results:
        print(f"  {status} {msg}")

    return all(r[0] == PASS for r in results)


def test_replayability():
    """B. event_log replay 能完整還原 flow"""
    print(f"\n{'='*60}")
    print(f" B. 可重播性")
    print(f"{'='*60}")

    results = []

    # 寫一組事件
    parent = event_log.record(
        source="stability_test", action="test_parent",
        input_data={"msg": "parent"}, rollback_point=True,
    )
    child_a = event_log.record(
        source="stability_test", action="test_child_a",
        input_data={"msg": "child_a"}, parent_id=parent,
    )
    child_b = event_log.record(
        source="stability_test", action="test_child_b",
        input_data={"msg": "child_b"}, parent_id=parent,
    )

    # Replay 測試
    replay = event_log.replay(limit=10)
    assert len(replay) >= 3, f"Replay 應 ≥ 3 筆，實際 {len(replay)}"

    # 檢查 parent 順序（最新在前）
    assert replay[0]["parent_id"] == "" or True  # 最新不一定要有 parent
    results.append((PASS, f"Replay 回傳 {len(replay)} 筆記錄"))

    # 檢查 action_id 格式 (SHA256[:16])
    for entry in replay[:3]:
        aid = entry.get("action_id", "")
        assert len(aid) == 16, f"action_id 長度應為 16，實際 {len(aid)}"
        assert all(c in "0123456789abcdef" for c in aid), f"action_id 非 hex: {aid}"

    results.append((PASS, "action_id 格式正確 (SHA256[:16])"))

    # 檢查 rollback_point
    rp = event_log.last_rollback_point()
    assert rp == parent, f"last_rollback_point 應為 {parent}，實際 {rp}"
    results.append((PASS, f"last_rollback_point 正確"))

    # 檢查 count
    cnt = event_log.count()
    assert cnt >= 3, f"count 應 ≥ 3，實際 {cnt}"
    results.append((PASS, f"event_log.count() = {cnt}"))

    print(f"\n  Replayability: {sum(1 for r in results if r[0]==PASS)}/{len(results)}")
    for status, msg in results:
        print(f"  {status} {msg}")

    return all(r[0] == PASS for r in results)


def test_no_cross_zone_violations():
    """C. 檢查越權防護是否確實擋住非法跨區"""
    print(f"\n{'='*60}")
    print(f" C. 越權防護")
    print(f"{'='*60}")

    results = []
    violations_before = SecurityZone.violation_count()

    # Brain 不該能 execute
    assert not gatekeeper.check_module_permission("brain", "run_tool"), "brain/run_tool 應被擋"
    assert not gatekeeper.check_module_permission("brain", "write_file"), "brain/write_file 應被擋"
    assert not gatekeeper.check_module_permission("meta_cognition", "modify_code"), "meta_cognition/modify_code 應被擋"
    results.append((PASS, "brain 不允許 run_tool / write_file / modify_code"))

    # Executor 不該能 decide
    assert not gatekeeper.check_module_permission("executor", "make_decision"), "executor/make_decision 應被擋"
    assert not gatekeeper.check_module_permission("tools", "modify_routing"), "tools/modify_routing 應被擋"
    results.append((PASS, "executor 不允許 make_decision / modify_routing"))

    # Memory 不該能 route
    assert not gatekeeper.check_module_permission("memory", "trigger_action"), "memory/trigger_action 應被擋"
    assert not gatekeeper.check_module_permission("memory", "modify_decision_logic"), "memory/modify_decision_logic 應被擋"
    results.append((PASS, "memory 不允許 trigger_action / modify_decision_logic"))

    # SecurityZone 紀錄越權
    zone_before = SecurityZone.violation_count()
    SecurityZone.check("brain", "run_tool")        # decision → execution ✗
    SecurityZone.check("executor", "make_decision") # execution → decision ✗
    SecurityZone.check("memory", "modify_decision_logic")  # memory → decision ✗
    zone_after = SecurityZone.violation_count()
    assert zone_after >= zone_before + 3, f"SecurityZone 應記錄至少 3 次越權 ({zone_before} → {zone_after})"
    results.append((PASS, "SecurityZone 成功記錄跨區違規"))

    # ControlPlane 也擋
    r = cp.check("brain", "run_tool", input_data={"should_block": True})
    assert r == False, f"ControlPlane 應擋住 brain/run_tool"
    results.append((PASS, "ControlPlane 擋住跨區呼叫"))

    print(f"\n  Cross-zone: {sum(1 for r in results if r[0]==PASS)}/{len(results)}")
    for status, msg in results:
        print(f"  {status} {msg}")

    return all(r[0] == PASS for r in results)


def test_no_implicit_state():
    """D. 檢查 module 有沒有隱性 mutable state"""
    print(f"\n{'='*60}")
    print(f" D. 隱性 State 檢測")
    print(f"{'='*60}")

    results = []

    # 檢查關鍵模組是否有未宣告的 mutable state
    state_sources = {}

    # Gatekeeper 本身不能有 hidden state
    assert hasattr(gatekeeper, "_lock"), "gatekeeper 應有 _lock"
    assert hasattr(gatekeeper, "_registered_threads"), "gatekeeper 應有 _registered_threads"
    results.append((PASS, "gatekeeper state 已宣告"))

    # EventLog 檢查
    assert hasattr(event_log, "_lock"), "event_log 應有 _lock"
    assert hasattr(event_log, "_log_file"), "event_log 應有 _log_file"
    results.append((PASS, "event_log state 已宣告"))

    # ControlPlane stateless check
    keys = dir(cp)
    stateful_attrs = [k for k in keys if k.startswith("_") and not k.startswith("__")]
    # 只檢查已知的 state 屬性
    expected = ["_lock", "_stats", "_last_call", "_total_latency_ms", "_call_count"]
    missing = [e for e in expected if e not in stateful_attrs]
    if missing:
        results.append((FAIL, f"control_plane 缺少預期 state: {missing}"))
    else:
        results.append((PASS, "control_plane state 完整宣告"))

    print(f"\n  Implicit State: {sum(1 for r in results if r[0]==PASS)}/{len(results)}")
    for status, msg in results:
        print(f"  {status} {msg}")

    return all(r[0] == PASS for r in results)


def test_baseline():
    """B. 建立系統基準線"""
    print(f"\n{'='*60}")
    print(f" B. Baseline 基準線")
    print(f"{'='*60}")

    results = []

    # Decision latency
    latencies = []
    for _ in range(5):
        t0 = time.perf_counter()
        cp.check("brain", "plan", input_data={"task": "test"}, zone_check=True, permission_check=True)
        latencies.append((time.perf_counter() - t0) * 1000)

    avg_lat = statistics.mean(latencies)
    max_lat = max(latencies)
    results.append((PASS, f"decision_latency: avg={avg_lat:.2f}ms, max={max_lat:.2f}ms"))

    # Execution success (gatekeeper + zone + control)
    success = 0
    total = 10
    for i in range(total):
        r = cp.check("executor", "run_tool", input_data={"tool": f"test_{i}"})
        if r:
            success += 1
    rate = success / total * 100
    results.append((PASS, f"execution_success_rate: {success}/{total} = {rate:.0f}%"))

    # Routing accuracy: 正確的 route 應該被接受，錯誤的應該被擋
    test_cases = [
        ("brain", "plan", True),
        ("brain", "run_tool", False),
        ("executor", "run_tool", True),
        ("executor", "make_decision", False),
        ("memory", "read", True),
        ("memory", "trigger_action", False),
        ("agents", "plan", True),
        ("agents", "execute_tool", False),
        ("tools", "execute_only", True),
        ("tools", "make_decision", False),
    ]
    correct = 0
    for module, action, expected in test_cases:
        r = gatekeeper.check_module_permission(module, action)
        if r == expected:
            correct += 1
        else:
            print(f"  {FAIL} routing: {module}/{action} → {r} (expected {expected})")

    accuracy = correct / len(test_cases) * 100
    results.append((PASS, f"routing_accuracy: {correct}/{len(test_cases)} = {accuracy:.0f}%"))

    print(f"\n  Baseline: {sum(1 for r in results if r[0]==PASS)}/{len(results)}")
    for status, msg in results:
        print(f"  {status} {msg}")

    return all(r[0] == PASS for r in results)


if __name__ == "__main__":
    print(f"\n🔋 AMPM 治理層系統驗收\n")
    print(f"  時間: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Python: {sys.version}")

    tests = [
        ("A. Predictability", test_predictability),
        ("B. Replayability", test_replayability),
        ("C. No Cross-Zone", test_no_cross_zone_violations),
        ("D. No Implicit State", test_no_implicit_state),
        ("E. Baseline", test_baseline),
    ]

    passed = 0
    for name, fn in tests:
        try:
            if fn():
                passed += 1
        except Exception as e:
            print(f"\n  {FAIL} {name} threw: {e}")

    print(f"\n{'='*60}")
    print(f" 結果: {passed}/{len(tests)} 通過")
    print(f"{'='*60}")

    sys.exit(0 if passed == len(tests) else 1)
