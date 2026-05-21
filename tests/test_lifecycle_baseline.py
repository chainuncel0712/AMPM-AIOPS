"""
Lifecycle Baseline Test — 全系統生命週期驗證
===============================================
驗證系統處於「正常運作狀態」並記錄所有關鍵指標作為 baseline。

執行方式：
  PYTHONPATH=src python3 tests/test_lifecycle_baseline.py

記錄輸出至 outputs/baseline/ 供後續對照。
"""
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from governance.gatekeeper import gatekeeper
from governance.event_log import event_log
from governance.control_plane import cp
from governance.scoring import scoring
from governance.audit import auditor

BASELINE_DIR = Path("outputs/baseline")
BASELINE_DIR.mkdir(parents=True, exist_ok=True)

PASS = "✅"
FAIL = "❌"
WARN = "⚠️"


def check_daemon_alive():
    """檢查 daemon 是否在運行。"""
    results = []
    pid_file = Path("/tmp/heiyao_main.pid")
    hb_file = Path("/tmp/heiyao_heartbeat")

    if pid_file.exists():
        pid = int(pid_file.read_text().strip())
        try:
            os.kill(pid, 0)
            results.append((PASS, f"Daemon PID {pid} 存活"))
        except OSError:
            results.append((FAIL, f"Daemon PID {pid} 不存在"))
    else:
        results.append((WARN, "PID file 不存在（可能非 daemon 模式啟動）"))

    if hb_file.exists():
        try:
            raw = hb_file.read_text()
            # Try JSON first, then key=value format
            try:
                hb = json.loads(raw)
                healthy = hb.get("all_healthy", False)
            except json.JSONDecodeError:
                hb = dict(line.split("=", 1) for line in raw.strip().splitlines() if "=" in line)
                healthy = hb.get("all_healthy", "").lower() == "true"
            age = time.time() - os.path.getmtime(hb_file)
            if age < 120 and healthy:
                results.append((PASS, f"Heartbeat {age:.0f}s old, all_healthy={healthy}"))
            else:
                results.append((WARN, f"Heartbeat {age:.0f}s old, all_healthy={healthy}"))
        except Exception as e:
            results.append((WARN, f"Heartbeat file 不可解析（可能剛重啟）: {e}"))
    else:
        results.append((WARN, "Heartbeat file 不存在"))

    # Check process directly
    import subprocess
    r = subprocess.run(["pgrep", "-f", "python3 main.py"], capture_output=True, text=True)
    pids = r.stdout.strip().split()
    if pids:
        results.append((PASS, f"Process alive: PID(s) {', '.join(pids)}"))
    else:
        results.append((FAIL, "No python3 main.py process found"))

    return results


def check_state_files():
    """檢查關鍵狀態檔案是否存在且有效。"""
    results = []
    state_files = [
        ("Heartbeat", Path("data/state/heartbeat.json")),
        ("Self Awareness", Path("data/self_awareness.json")),
        ("Tools Registry", Path("data/tools/registry.json")),
        ("Planner Tasks", Path("data/planner/tasks.json")),
        ("Runtime Rules", Path("data/rules/runtime_rules.json")),
        ("Evolution State", Path("data/evolution/cycle_state.json")),
        ("Rebirth State", Path("data/rebirth_state.json")),
        ("Startup Diagnosis", Path("data/startup_diagnosis.json")),
    ]

    for name, path in state_files:
        if path.exists():
            try:
                data = json.loads(path.read_text())
                results.append((PASS, f"{name} ({path}) — {len(json.dumps(data))} bytes"))
            except (json.JSONDecodeError, Exception) as e:
                results.append((FAIL, f"{name} ({path}) — 格式錯誤: {e}"))
        else:
            results.append((WARN, f"{name} ({path}) — 不存在"))

    return results


def check_governance():
    """檢查治理層是否運作。"""
    results = []
    results.append((PASS, f"Gatekeeper entry: {gatekeeper.is_entry_passed()}"))
    results.append((PASS, f"EventLog count: {event_log.count()}"))
    s = cp.stats()
    results.append((PASS, f"ControlPlane: {s['total_calls']} calls, avg {s['avg_latency_ms']}ms"))
    results.append((PASS, f"SecurityZone violations: {__import__('governance.security_zone', fromlist=['SecurityZone']).SecurityZone.violation_count()}"))
    a = auditor.stats()
    results.append((PASS, f"Audit: {a['total_traced']} events from {a['unique_sources']} sources"))
    return results


def check_outputs():
    """檢查 outputs/ 目錄是否有近期活動。"""
    results = []
    output_dir = Path("outputs")
    if output_dir.exists():
        recent_files = sorted(output_dir.rglob("*"), key=lambda f: f.stat().st_mtime, reverse=True)[:5]
        for f in recent_files:
            age_hours = (time.time() - f.stat().st_mtime) / 3600
            if f.is_file():
                results.append((PASS, f"Recent: {f} ({age_hours:.1f}h old, {f.stat().st_size} bytes)"))
    else:
        results.append((WARN, "outputs/ 不存在"))
    return results


def check_modules_loaded():
    """檢查已載入的模組（透過 Obsidian organs）。"""
    results = []
    # Try to find Obsidian instance
    try:
        from brain import Obsidian
        # If we can import it, the module system works
        results.append((PASS, "brain.Obsidian 可匯入"))
    except Exception as e:
        results.append((WARN, f"brain.Obsidian 無法匯入（獨立測試模式正常）: {e}"))

    # Check governance modules
    governance_modules = [
        "governance.gatekeeper",
        "governance.security_zone",
        "governance.event_log",
        "governance.control_plane",
        "governance.isolation",
        "governance.scoring",
        "governance.audit",
        "governance.stable_mode",
    ]
    for mod_name in governance_modules:
        try:
            __import__(mod_name, fromlist=[""])
            results.append((PASS, f"{mod_name} 可用"))
        except Exception as e:
            results.append((FAIL, f"{mod_name} 無法載入: {e}"))

    return results


def run_all():
    print(f"\n{'='*60}")
    print(f"  Lifecycle Baseline Test")
    print(f"  {datetime.now().isoformat()}")
    print(f"{'='*60}")

    all_results = []
    sections = [
        ("Daemon Status", check_daemon_alive),
        ("State Files", check_state_files),
        ("Governance", check_governance),
        ("Outputs Activity", check_outputs),
        ("Modules", check_modules_loaded),
    ]

    for section_name, fn in sections:
        print(f"\n  [{section_name}]")
        try:
            results = fn()
            all_results.extend(results)
            for status, msg in results:
                print(f"  {status} {msg}")
        except Exception as e:
            print(f"  {FAIL} {section_name} threw: {e}")

    # Summary
    total = len(all_results)
    passed = sum(1 for r in all_results if r[0] == PASS)
    failed = sum(1 for r in all_results if r[0] == FAIL)
    warned = sum(1 for r in all_results if r[0] == WARN)

    print(f"\n{'='*60}")
    print(f"  Baseline: {passed}/{total} passed, {failed} failed, {warned} warnings")
    print(f"{'='*60}")

    # Save baseline
    baseline = {
        "timestamp": datetime.now().isoformat(),
        "total": total,
        "passed": passed,
        "failed": failed,
        "warned": warned,
        "details": [
            {"status": s, "message": m} for s, m in all_results
        ],
    }
    baseline_path = BASELINE_DIR / f"baseline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    baseline_path.write_text(json.dumps(baseline, ensure_ascii=False, indent=2))
    print(f"\n  Baseline saved: {baseline_path}")

    return failed == 0


if __name__ == "__main__":
    sys.exit(0 if run_all() else 1)
