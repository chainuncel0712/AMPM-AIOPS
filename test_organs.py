#!/usr/bin/env python3
"""黑曜零件獨立測試 - 每個零件單獨測，不拖垮整條鏈"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

TESTS = []

def test(name):
    """裝飾器：註冊測試"""
    def decorator(func):
        TESTS.append((name, func))
        return func
    return decorator

# ========== 神經零件測試 ==========
@test("eye - 搜尋功能")
def test_eye():
    from nerve.eye import Eye
    e = Eye()
    e.init()
    assert e.is_alive(), "eye 未存活"
    result = e.see("Python")
    assert result, "eye 搜尋無結果"
    print(f"  ✅ 搜尋結果: {result[:50]}...")

@test("ear - 聽覺載入")
def test_ear():
    from nerve.ear import Ear
    e = Ear()
    assert e.is_alive(), "ear 未存活"

# ========== 免疫測試 ==========
@test("firewall - 安全掃描")
def test_firewall():
    from immune.firewall import Firewall
    fw = Firewall()
    r = fw.scan("你好")
    assert r["allowed"], f"防火牆阻擋正常訊息: {r}"
    r2 = fw.scan("rm -rf /")
    assert not r2["allowed"], "防火牆沒擋危險指令"

@test("breaker - 斷路檢查")
def test_breaker():
    from immune.breaker import Breaker
    b = Breaker()
    r = b.check("test")
    assert "allowed" in r, f"breaker 回傳格式異常: {r}"

# ========== 血液測試 ==========
@test("event_bus - 事件發布")
def test_event_bus():
    from blood.event_bus import EventBus
    bus = EventBus()
    received = []
    bus.on("test", lambda d: received.append(d))
    bus.emit("test", {"msg": "hello"})
    assert len(received) > 0, "event_bus 未收到事件"

@test("scheduler - 定時任務")
def test_scheduler():
    from blood.scheduler import Scheduler
    s = Scheduler()
    results = []
    s.add("test", 1, lambda: results.append(1), repeat=False)
    s.start()
    import time
    time.sleep(1.5)
    assert len(results) > 0, "scheduler 未執行"

# ========== 記憶測試 ==========
@test("memory - 三層記憶")
def test_memory():
    from memory import Memory
    from pathlib import Path
    m = Memory(Path.home() / ".ampm_brain")
    assert m.working_file.exists() or m.episodic_file.exists(), "記憶檔不存在"

# ========== 網頁測試 ==========
@test("web_search - 搜尋引擎")
def test_web_search():
    from web.search import WebSearch
    ws = WebSearch()
    r = ws.search("test")
    assert r, "搜尋無結果"

# ========== 主程序 ==========
if __name__ == "__main__":
    print("🧪 黑曜零件獨立測試\n")
    passed = 0
    failed = 0
    
    for name, func in TESTS:
        try:
            print(f"🔍 {name}...")
            func()
            print(f"  ✅ 通過\n")
            passed += 1
        except Exception as e:
            print(f"  ❌ 失敗: {e}\n")
            failed += 1
    
    print(f"{'='*40}")
    print(f"📊 結果: ✅ {passed} / ❌ {failed} / 總計 {len(TESTS)}")
    if failed == 0:
        print("🎉 全部通過！")
    else:
        print(f"⚠️ {failed} 個失敗，請檢查")
