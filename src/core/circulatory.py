"""健康循環系統 - 定時檢查器官心跳 + VPS 資源監控 + 進化循環（吸收資訊→思考運用→好的進化→不好的排除→持續進化）"""
import json
import os
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


# =============================================================================
# VPS 資源監控（原有功能）
# =============================================================================

def _get_cpu_usage() -> str:
    """從 /proc/stat 計算 CPU 使用率（取樣 0.5 秒）"""
    try:
        with open("/proc/stat", "r") as f:
            fields1 = f.readline().strip().split()[1:]
        time.sleep(0.5)
        with open("/proc/stat", "r") as f:
            fields2 = f.readline().strip().split()[1:]
        u1 = sum(int(x) for x in fields1[:4])
        u2 = sum(int(x) for x in fields2[:4])
        idle1, idle2 = int(fields1[3]), int(fields2[3])
        total = u2 - u1
        idle = idle2 - idle1
        if total == 0:
            return "0%"
        return f"{100 * (total - idle) / total:.1f}%"
    except Exception:
        return "❌"


def _get_cpu_percent() -> float:
    """回傳 CPU 使用率（浮點數）"""
    try:
        with open("/proc/stat", "r") as f:
            fields1 = f.readline().strip().split()[1:]
        time.sleep(0.5)
        with open("/proc/stat", "r") as f:
            fields2 = f.readline().strip().split()[1:]
        u1 = sum(int(x) for x in fields1[:4])
        u2 = sum(int(x) for x in fields2[:4])
        idle1, idle2 = int(fields1[3]), int(fields2[3])
        total = u2 - u1
        idle = idle2 - idle1
        if total == 0:
            return 0.0
        return 100.0 * (total - idle) / total
    except Exception:
        return -1.0


def _get_memory() -> str:
    """取得 RAM 使用率 (從 /proc/meminfo)"""
    try:
        with open("/proc/meminfo", "r") as f:
            lines = f.read()
        mem = {}
        for line in lines.splitlines():
            if line.strip():
                parts = line.split(":")
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip().split()[0]
                    mem[key] = int(value)
        total = mem.get("MemTotal", 0)
        available = mem.get("MemAvailable", mem.get("MemFree", 0))
        if total == 0:
            return "❌"
        used = total - available
        return f"{100 * used / total:.1f}%"
    except Exception:
        return "❌"


def _get_ram_percent() -> float:
    """回傳 RAM 使用率（浮點數）"""
    try:
        with open("/proc/meminfo", "r") as f:
            lines = f.read()
        mem = {}
        for line in lines.splitlines():
            if line.strip():
                parts = line.split(":")
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip().split()[0]
                    mem[key] = int(value)
        total = mem.get("MemTotal", 0)
        available = mem.get("MemAvailable", mem.get("MemFree", 0))
        if total == 0:
            return -1.0
        used = total - available
        return 100.0 * used / total
    except Exception:
        return -1.0


def _get_swap() -> str:
    """Swap 使用率"""
    try:
        with open("/proc/meminfo", "r") as f:
            lines = f.read()
        sw = {}
        for line in lines.splitlines():
            parts = line.split(":")
            if len(parts) == 2 and "Swap" in parts[0]:
                key = parts[0].strip()
                value = parts[1].strip().split()[0]
                sw[key] = int(value)
        total = sw.get("SwapTotal", 0)
        free = sw.get("SwapFree", 0)
        if total == 0:
            return "0% (無 swap)"
        used = total - free
        return f"{100 * used / total:.1f}%"
    except Exception:
        return "❌"


def _get_swap_percent() -> float:
    """回傳 Swap 使用率（浮點數）"""
    try:
        with open("/proc/meminfo", "r") as f:
            lines = f.read()
        sw = {}
        for line in lines.splitlines():
            parts = line.split(":")
            if len(parts) == 2 and "Swap" in parts[0]:
                key = parts[0].strip()
                value = parts[1].strip().split()[0]
                sw[key] = int(value)
        total = sw.get("SwapTotal", 0)
        free = sw.get("SwapFree", 0)
        if total == 0:
            return 0.0
        used = total - free
        return 100.0 * used / total
    except Exception:
        return -1.0


def _get_disk_io() -> str:
    """磁碟 I/O 監控（每秒讀寫量，kB/s）"""
    try:
        def _read_stats():
            reads = 0
            writes = 0
            with open("/proc/diskstats", "r") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) < 11:
                        continue
                    dev = parts[2]
                    if dev.startswith(("sd", "vd", "nvme", "xvd")):
                        reads += int(parts[5])
                        writes += int(parts[9])
            return reads, writes

        r1, w1 = _read_stats()
        time.sleep(1.0)
        r2, w2 = _read_stats()
        read_kb = (r2 - r1) * 512 / 1024
        write_kb = (w2 - w1) * 512 / 1024
        return f"Read: {read_kb:.0f} kB/s, Write: {write_kb:.0f} kB/s"
    except Exception:
        return "❌"


def _get_network_traffic() -> str:
    """網路流量監控（每秒接收/傳送量，kB/s）"""
    try:
        def _read_net():
            rx = 0
            tx = 0
            with open("/proc/net/dev", "r") as f:
                lines = f.readlines()
            for line in lines[2:]:
                if ":" not in line:
                    continue
                iface, data = line.split(":", 1)
                iface = iface.strip()
                if iface == "lo":
                    continue
                fields = data.split()
                if len(fields) < 10:
                    continue
                rx += int(fields[0])
                tx += int(fields[8])
            return rx, tx

        r1, t1 = _read_net()
        time.sleep(1.0)
        r2, t2 = _read_net()
        rx_kb = (r2 - r1) / 1024
        tx_kb = (t2 - t1) / 1024
        return f"↓ {rx_kb:.0f} kB/s, ↑ {tx_kb:.0f} kB/s"
    except Exception:
        return "❌"


def get_vps_stats() -> str:
    """回傳格式化的 VPS 資源字串（含 CPU、RAM、Swap、磁碟 I/O、網路流量）"""
    return (
        f"CPU: {_get_cpu_usage()}  "
        f"RAM: {_get_memory()}  "
        f"Swap: {_get_swap()}  "
        f"IO: {_get_disk_io()}  "
        f"Net: {_get_network_traffic()}"
    )


def check_thresholds() -> str:
    """檢查資源是否超過 80%，回傳警告訊息"""
    cpu = _get_cpu_percent()
    ram = _get_ram_percent()
    swap = _get_swap_percent()
    warnings = []
    if cpu > 80:
        warnings.append(f"CPU 使用率過高: {cpu:.1f}%")
    if ram > 80:
        warnings.append(f"RAM 使用率過高: {ram:.1f}%")
    if swap > 80:
        warnings.append(f"Swap 使用率過高: {swap:.1f}%")
    if not warnings:
        return "✅ 所有資源正常"
    return "⚠️ 資源警告:\n" + "\n".join(warnings)


# =============================================================================
# 進化循環系統（新增）
# =============================================================================

class EvolutionCycle:
    """
    進化循環系統：
    1. 吸收資訊 - 從外部來源收集資料
    2. 思考運用 - 分析資訊、判斷好壞
    3. 好的進化 - 保留有用的資訊
    4. 不好的排除 - 丟棄無用資訊
    5. 持續進化 - 重複循環
    """

    def __init__(self, brain: Any, base_dir: Optional[Path] = None):
        self.brain = brain
        self.base_dir = base_dir or Path.home() / ".ampm_brain"
        self.evolution_file = self.base_dir / "data" / "evolution" / "cycle.json"
        self.evolution_file.parent.mkdir(parents=True, exist_ok=True)
        self._load_state()

    def _load_state(self):
        """載入進化狀態"""
        if self.evolution_file.exists():
            try:
                with open(self.evolution_file, "r", encoding="utf-8") as f:
                    self.state = json.load(f)
            except Exception:
                self.state = self._default_state()
        else:
            self.state = self._default_state()
            self._save_state()

    def _default_state(self) -> dict:
        return {
            "cycle_count": 0,
            "absorbed_info": [],
            "good_info": [],
            "bad_info": [],
            "last_cycle": datetime.now().isoformat(),
            "evolution_score": 0,
        }

    def _save_state(self):
        try:
            with open(self.evolution_file, "w", encoding="utf-8") as f:
                json.dump(self.state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[進化循環] 儲存狀態失敗: {e}")

    # ── 步驟 1：吸收資訊 ──
    def absorb_information(self) -> List[str]:
        """從多個來源吸收資訊"""
        new_info = []

        # 1. 從記憶器官吸收
        memory = getattr(self.brain, "memory", None) or self.brain.organs.get("memory")
        if memory and hasattr(memory, "get_all_facts"):
            try:
                facts = memory.get_all_facts()
                new_info.extend(facts)
            except Exception:
                pass

        # 2. 從搜尋引擎吸收
        web_search = self.brain.organs.get("web_search")
        if web_search and hasattr(web_search, "search"):
            try:
                result = web_search.search("最新科技趨勢 2025", max_results=3)
                new_info.append(f"搜尋結果: {result[:500]}")
            except Exception:
                pass

        # 3. 從市場數據吸收
        market = self.brain.organs.get("market_data")
        if market and hasattr(market, "get_price"):
            try:
                price = market.get_price("bitcoin")
                new_info.append(f"市場數據: {price}")
            except Exception:
                pass

        # 4. 從系統日誌吸收
        try:
            with open("/var/log/syslog", "r") as f:
                lines = f.readlines()[-5:]
                for line in lines:
                    new_info.append(f"系統日誌: {line.strip()[:200]}")
        except Exception:
            pass

        # 儲存吸收的資訊
        for info in new_info:
            if info not in self.state["absorbed_info"]:
                self.state["absorbed_info"].append(info)

        # 限製數量
        if len(self.state["absorbed_info"]) > 100:
            self.state["absorbed_info"] = self.state["absorbed_info"][-100:]

        self._save_state()
        return new_info

    # ── 步驟 2：思考運用 ──
    def think_and_evaluate(self, info_list: List[str]) -> Dict[str, List[str]]:
        """分析資訊，分類為好/壞"""
        good = []
        bad = []

        for info in info_list:
            # 簡單的判斷規則（未來可用 LLM 強化）
            score = self._evaluate_info(info)
            if score > 0:
                good.append(info)
            else:
                bad.append(info)

        return {"good": good, "bad": bad}

    def _evaluate_info(self, info: str) -> int:
        """評估資訊品質，回傳分數（正數=好，負數=壞）"""
        score = 0

        # 好的關鍵字（放寬標準）
        good_keywords = [
            "成功", "增長", "提升", "創新", "突破", "進步",
            "學習", "進化", "優化", "改善", "profit", "growth",
            "success", "innovation", "learn", "improve",
            "工具", "系統", "功能", "資料", "分析", "報告",
            "tool", "system", "function", "data", "analysis", "report",
            "完成", "執行", "處理", "記錄", "記憶",
            "done", "execute", "process", "record", "memory",
        ]
        for kw in good_keywords:
            if kw in info.lower():
                score += 1

        # 壞的關鍵字（縮小範圍）
        bad_keywords = [
            "崩潰", "攻擊", "漏洞",
            "crash", "attack", "vulnerability",
        ]
        for kw in bad_keywords:
            if kw in info.lower():
                score -= 1

        # 太短的資訊視為無用（放寬到 5 字）
        if len(info) < 5:
            score -= 1

        # 重複的資訊（降低扣分）
        if info in self.state["good_info"] or info in self.state["bad_info"]:
            score -= 0.5

        # 如果分數為 0，預設為正面（避免全部排除）
        if score == 0:
            score = 1

        return score

    # ── 步驟 3：好的進化 ──
    def evolve_good(self, good_info: List[str]):
        """保留好的資訊，融入系統"""
        for info in good_info:
            if info not in self.state["good_info"]:
                self.state["good_info"].append(info)
                self.state["evolution_score"] += 1

        # 限製數量
        if len(self.state["good_info"]) > 200:
            self.state["good_info"] = self.state["good_info"][-200:]

        self._save_state()

    # ── 步驟 4：不好的排除 ──
    def exclude_bad(self, bad_info: List[str]):
        """丟棄不好的資訊"""
        for info in bad_info:
            if info not in self.state["bad_info"]:
                self.state["bad_info"].append(info)
                self.state["evolution_score"] -= 1

        # 限製數量
        if len(self.state["bad_info"]) > 100:
            self.state["bad_info"] = self.state["bad_info"][-100:]

        self._save_state()

    # ── 步驟 5：執行完整循環 ──
    def run_cycle(self) -> str:
        """執行一次完整的進化循環"""
        self.state["cycle_count"] += 1
        self.state["last_cycle"] = datetime.now().isoformat()

        # 步驟 1：吸收資訊
        new_info = self.absorb_information()
        if not new_info:
            return "📭 沒有新資訊可吸收"

        # 步驟 2：思考運用
        evaluated = self.think_and_evaluate(new_info)

        # 步驟 3：好的進化
        self.evolve_good(evaluated["good"])

        # 步驟 4：不好的排除
        self.exclude_bad(evaluated["bad"])

        self._save_state()

        # 回報結果
        lines = [
            f"🧬 進化循環 #{self.state['cycle_count']}",
            f"  📥 吸收: {len(new_info)} 條",
            f"  ✅ 好的: {len(evaluated['good'])} 條",
            f"  ❌ 排除: {len(evaluated['bad'])} 條",
            f"  📊 進化分數: {self.state['evolution_score']}",
            f"  📚 累積好資訊: {len(self.state['good_info'])} 條",
        ]
        return "\n".join(lines)

    def get_summary(self) -> str:
        """取得進化摘要"""
        return (
            f"🧬 進化循環摘要:\n"
            f"  循環次數: {self.state['cycle_count']}\n"
            f"  進化分數: {self.state['evolution_score']}\n"
            f"  好資訊: {len(self.state['good_info'])} 條\n"
            f"  壞資訊: {len(self.state['bad_info'])} 條\n"
            f"  上次循環: {self.state['last_cycle']}"
        )


# =============================================================================
# 啟動循環系統（整合原有健康檢查 + 進化循環）
# =============================================================================

def start_health_loop(brain, interval_seconds: int = 300):
    """
    啟動背景執行緒，每 interval_seconds 秒執行：
    - 器官心跳檢查
    - VPS 資源監控
    - 進化循環（吸收資訊→思考運用→好的進化→不好的排除→持續進化）

    參數:
        brain: Obsidian 實例，必須有 organs 屬性 (dict)
        interval_seconds: 檢查間隔 (預設 300 秒 = 5 分鐘)
    """
    evolution = EvolutionCycle(brain)

    def _loop():
        while True:
            try:
                organs = getattr(brain, 'organs', {})
                if not organs:
                    continue

                print(f"\n💓 循環健康檢查 (每 {interval_seconds}s)")
                alive_count = 0
                dead_count = 0

                for name, organ in organs.items():
                    alive = True
                    if hasattr(organ, 'is_alive'):
                        try:
                            alive = organ.is_alive()
                        except Exception:
                            alive = False

                    status = "✅" if alive else "❌"
                    print(f"  {status} {name}")

                    if alive:
                        alive_count += 1
                    else:
                        dead_count += 1

                total = len(organs)
                print(f"  總器官: {total} | 正常: {alive_count} | 異常: {dead_count}\n")

                # ── VPS 資源即時監控 ──
                print("📊 VPS 資源:")
                print(f"  {get_vps_stats()}\n")

                # ── 資源閾值警告 ──
                threshold_msg = check_thresholds()
                if "⚠️" in threshold_msg:
                    print(f"  {threshold_msg}\n")

                if dead_count > 0:
                    print("  ⚠️ 偵測到異常器官，可能需要 self_repair")

                # ── 進化循環 ──
                print("🧬 進化循環:")
                cycle_result = evolution.run_cycle()
                print(f"  {cycle_result}\n")

                try:
                    from core.agent_supervisor import supervisor
                    supervisor.heartbeat("circulatory")
                except Exception:
                    pass
            except Exception as e:
                print(f"[循環系統] 檢查失敗: {e}")

            time.sleep(interval_seconds)

    t = threading.Thread(target=_loop, daemon=True)
    t.start()
    try:
        from core.agent_supervisor import supervisor
        supervisor.register("circulatory", thread=t, hb_interval=interval_seconds,
                            hb_timeout=interval_seconds*2, is_restartable=False)
    except Exception:
        pass
