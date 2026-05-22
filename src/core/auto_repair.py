"""自我修復系統 - 定時檢查器官並自動修復"""
import threading
import time
from core.agent_supervisor import supervisor


def start_auto_repair(brain, interval_seconds: int = 600):
    """
    啟動背景執行緒，每 interval_seconds 秒檢查器官，
    若發現死亡器官則自動呼叫 self_repair 工具。
    """
    def _loop():
        while True:
            try:
                organs = getattr(brain, 'organs', {})
                dead_organs = []

                for name, organ in organs.items():
                    alive = True
                    if hasattr(organ, 'is_alive'):
                        try:
                            alive = organ.is_alive()
                        except Exception:
                            alive = False
                    if not alive:
                        dead_organs.append(name)

                if dead_organs:
                    print(f"🔧 自我修復系統：偵測到異常器官 {dead_organs}")
                    if hasattr(brain, 'langgraph') and brain.langgraph:
                        try:
                            # 呼叫 self_repair 工具，預設先修復 assembler
                            result = brain.langgraph._self_repair_tool("assembler")
                            print(f"  修復結果: {result}")
                        except Exception as e:
                            print(f"  修復失敗: {e}")
                supervisor.heartbeat("auto_repair")
            except Exception as e:
                print(f"[自動修復] 檢查失敗: {e}")

            time.sleep(interval_seconds)

    t = threading.Thread(target=_loop, daemon=True)
    t.start()
    supervisor.register("auto_repair", thread=t, hb_interval=interval_seconds,
                        hb_timeout=interval_seconds*2, is_restartable=False)
