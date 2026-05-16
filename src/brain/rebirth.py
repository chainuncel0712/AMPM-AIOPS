"""
重生器官 — 自我再生層
當系統損壞時自動重建、尋找更好的零件替換現有器官、
從網路搜尋免費實用工具自動整合。
這是再生 + 自尋進化的閉環。
"""
import json
import hashlib
import shutil
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from skeleton.base_organ import BaseOrgan


class Rebirth(BaseOrgan):
    def __init__(self, base_dir: Path, organs: dict, assembler, memory, awareness=None):
        super().__init__("rebirth")
        self.base_dir = base_dir
        self.organs = organs          # Obsidian.organs 的參考
        self.assembler = assembler    # skeleton.assembler.Assembler
        self.memory = memory
        self.awareness = awareness    # self_awareness 實例（可選）

        self.snapshot_dir = base_dir / "data" / "snapshots"
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)

        self.tools_cache_dir = base_dir / "data" / "found_tools"
        self.tools_cache_dir.mkdir(parents=True, exist_ok=True)

        self.state_file = base_dir / "data" / "rebirth_state.json"
        self._lock = threading.Lock()

        # ===== 重生狀態 =====
        self.rebirth_count = 0
        self.last_rebirth: Optional[datetime] = None
        self.rebirth_history: list = []

        # ===== 零件市場 =====
        self.part_registry: Dict[str, dict] = {}  # 已知的替代零件
        self.upgrade_queue: list = []              # 等待升級的器官清單

        # ===== 發現的工具 =====
        self.found_tools: list = []                # 從網路找到的免費工具
        self.integrated_tools: list = []           # 已整合進系統的工具

        self._load_state()

    # =========================================
    # 快照：儲存健康狀態
    # =========================================

    def take_snapshot(self, label: str = "") -> str:
        """儲存目前所有器官的快照，可在毀損時恢復"""
        snapshot_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        if label:
            snapshot_id += f"_{label}"

        org_data = {}
        for name, organ in self.organs.items():
            try:
                if hasattr(organ, "status"):
                    org_data[name] = organ.status()
                else:
                    org_data[name] = {"alive": True}
            except Exception as e:
                org_data[name] = {"alive": False, "error": str(e)}

        src_hash = self._hash_source_files()

        snapshot = {
            "id": snapshot_id,
            "ts": datetime.now().isoformat(),
            "label": label or "auto",
            "organs": org_data,
            "organ_count": len(org_data),
            "alive_count": sum(1 for v in org_data.values() if v.get("alive")),
            "source_hash": src_hash,
        }

        filepath = self.snapshot_dir / f"snapshot_{snapshot_id}.json"
        filepath.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2))

        # 只保留最近 5 個快照
        self._prune_snapshots(keep=5)

        self._append_history("snapshot", f"快照 {snapshot_id}: {snapshot['alive_count']}/{snapshot['organ_count']} 存活")

        if self.awareness:
            self.awareness.record_event("snapshot",
                f"重生器官儲存快照 {snapshot_id}，{snapshot['alive_count']} 器官存活")

        return snapshot_id

    def _hash_source_files(self) -> str:
        """計算 src/ 原始碼的 hash，用於偵測變更"""
        hasher = hashlib.sha256()
        for py_file in sorted(Path(self.base_dir / "src").rglob("*.py")):
            if "__pycache__" in str(py_file):
                continue
            hasher.update(py_file.read_bytes())
        return hasher.hexdigest()[:16]

    def _prune_snapshots(self, keep: int = 5):
        """只保留最近 N 個快照"""
        files = sorted(self.snapshot_dir.glob("snapshot_*.json"))
        for f in files[:-keep]:
            f.unlink()

    # =========================================
    # 恢復：從快照重生
    # =========================================

    def restore_from_snapshot(self, snapshot_id: str = None) -> bool:
        """從快照恢復器官狀態"""
        if snapshot_id:
            filepath = self.snapshot_dir / f"snapshot_{snapshot_id}.json"
        else:
            # 使用最新的快照
            files = sorted(self.snapshot_dir.glob("snapshot_*.json"))
            if not files:
                print("[重生] 沒有快照可用，無法恢復")
                return False
            filepath = files[-1]

        if not filepath.exists():
            print(f"[重生] 快照不存在: {filepath}")
            return False

        try:
            snapshot = json.loads(filepath.read_text())
        except Exception:
            return False

        org_states = snapshot.get("organs", {})
        restored = 0
        failed = 0

        for name, state in org_states.items():
            if state.get("alive"):
                continue  # 活著的不用恢復
            organ = self.organs.get(name)
            if not organ:
                # 這個器官不存在了 → 嘗試重生
                success = self._regenerate_organ(name)
                if success:
                    restored += 1
                else:
                    failed += 1
                continue
            # 嘗試重新初始化
            try:
                if hasattr(organ, "enable"):
                    organ.enable()
                restored += 1
            except Exception:
                failed += 1

        self.rebirth_count += 1
        self.last_rebirth = datetime.now()
        self._save_state()

        self._append_history("restore",
            f"從 {snapshot['id']} 恢復：{restored} 成功, {failed} 失敗")

        if self.awareness:
            self.awareness.record_event("rebirth",
                f"從快照重生 #{self.rebirth_count}：修復 {restored}/{restored+failed} 器官")

        return restored > 0

    def _regenerate_organ(self, organ_name: str) -> bool:
        """重新生成一個器官 — 從 assembler 重新掃描並實例化"""
        try:
            # 重新掃描該器官所在的目錄
            result = self.assembler.load_single(organ_name)
            if result:
                self.organs[organ_name] = result
                if self.awareness:
                    self.awareness.update_organ_state(organ_name, True)
                return True
            return False
        except Exception as e:
            print(f"[重生] 重新生成 {organ_name} 失敗: {e}")
            return False

    # =========================================
    # 零件市場：尋找更好替代品
    # =========================================

    def register_alternative(self, target_organ: str, alternative: dict):
        """註冊一個替代零件"""
        self.part_registry[target_organ] = {
            **alternative,
            "registered_at": datetime.now().isoformat(),
        }

    def suggest_upgrades(self) -> list:
        """掃描器官，建議哪些可以被更好的零件替換"""
        suggestions = []
        for name, organ in self.organs.items():
            # 檢查是否有已知的替代品
            alt = self.part_registry.get(name)
            if alt:
                suggestions.append({
                    "organ": name,
                    "current": str(type(organ).__name__),
                    "alternative": alt.get("name", "unknown"),
                    "reason": alt.get("reason", "有更好的替代品"),
                    "source": alt.get("source", ""),
                })
                continue

            # 檢查器官健康度
            try:
                if hasattr(organ, "status"):
                    st = organ.status()
                    if not st.get("alive", True):
                        suggestions.append({
                            "organ": name,
                            "current": str(type(organ).__name__),
                            "alternative": "auto_rebuild",
                            "reason": "器官已死亡，需重建",
                            "source": "",
                        })
            except Exception:
                suggestions.append({
                    "organ": name,
                    "current": str(type(organ).__name__),
                    "alternative": "auto_rebuild",
                    "reason": "無法取得狀態，可能損壞",
                    "source": "",
                })

        return suggestions

    def queue_upgrade(self, organ_name: str, reason: str):
        """將某器官加入升級佇列"""
        self.upgrade_queue.append({
            "organ": organ_name,
            "reason": reason,
            "queued_at": datetime.now().isoformat(),
        })
        if self.awareness:
            self.awareness.record_event("upgrade_queued", f"{organ_name} 加入升級佇列: {reason}")

    def process_upgrade_queue(self) -> list:
        """處理升級佇列中的器官"""
        results = []
        for item in self.upgrade_queue[:]:
            name = item["organ"]
            success = self.try_upgrade_organ(name)
            results.append({"organ": name, "success": success})
            if success:
                self.upgrade_queue.remove(item)
        return results

    def try_upgrade_organ(self, organ_name: str) -> bool:
        """嘗試升級一個器官 — 停用舊的 → 載入新的 → 驗證 → 切換"""
        old_organ = self.organs.get(organ_name)
        if not old_organ:
            return self._regenerate_organ(organ_name)

        # 1. 停用舊器官
        try:
            if hasattr(old_organ, "disable"):
                old_organ.disable()
        except Exception:
            pass

        # 2. 嘗試重新實例化
        try:
            new_organ = self.assembler.load_single(organ_name)
            if new_organ:
                self.organs[organ_name] = new_organ
                if self.awareness:
                    self.awareness.update_organ_state(organ_name, True, upgraded=True)
                self._append_history("upgrade", f"{organ_name} 升級成功")
                return True
        except Exception as e:
            print(f"[重生] 升級 {organ_name} 失敗: {e}")

        # 3. 失敗則恢復舊器官
        try:
            if hasattr(old_organ, "enable"):
                old_organ.enable()
        except Exception:
            pass
        return False

    # =========================================
    # 自尋工具：從網路找免費實用工具
    # =========================================

    def search_free_tools(self, keyword: str) -> list:
        """
        從網路搜尋免費開源工具（透過 pip/system 搜尋）
        回傳找到的工具清單
        """
        results = []
        sources = [
            # pip 搜尋
            f"pip search {keyword} 2>/dev/null || pip index versions {keyword} 2>/dev/null",
            # apt 搜尋
            f"apt-cache search {keyword} 2>/dev/null",
            # npm 搜尋
            f"npm search {keyword} --json 2>/dev/null",
            # gh CLI 搜尋
            f"gh search repos --language=python {keyword} --limit=10 --json name,url,description 2>/dev/null",
        ]

        for cmd in sources:
            try:
                output = subprocess.run(
                    cmd, shell=True, capture_output=True, text=True, timeout=15
                ).stdout[:2000]
                if output.strip():
                    results.append({"source": cmd[:30], "output": output})
            except Exception:
                continue

        # 記錄找到的工具
        if results:
            tool_entry = {
                "keyword": keyword,
                "found_at": datetime.now().isoformat(),
                "results": results,
            }
            self.found_tools.append(tool_entry)

            # 持久化
            cache_file = self.tools_cache_dir / f"search_{keyword}_{datetime.now():%Y%m%d}.json"
            cache_file.write_text(json.dumps(tool_entry, ensure_ascii=False, indent=2))

            if self.awareness:
                self.awareness.record_event("tool_search",
                    f"搜尋免費工具「{keyword}」：找到 {len(results)} 個來源")

        return results

    def evaluate_and_integrate(self, keyword: str) -> dict:
        """評估搜尋到的工具，嘗試整合進系統"""
        tools = self.search_free_tools(keyword)
        integrated = []

        for t in tools:
            # 檢查是否是 pip 套件
            output = t.get("output", "")
            for line in output.split("\n"):
                line = line.strip()
                if line and not line.startswith("WARNING") and not line.startswith("ERROR"):
                    # 嘗試 pip install
                    pkg = line.split()[0] if line else ""
                    if pkg and len(pkg) < 50 and "/" not in pkg:
                        try:
                            result = subprocess.run(
                                ["pip", "install", pkg],
                                capture_output=True, text=True, timeout=30
                            )
                            if result.returncode == 0:
                                integrated.append({
                                    "package": pkg,
                                    "status": "installed",
                                    "output": result.stdout[-200:],
                                })
                                self.integrated_tools.append(pkg)
                        except Exception:
                            pass

        if self.awareness:
            self.awareness.record_event("tool_integrate",
                f"整合免費工具：{len(integrated)} 個成功安裝")

        return {"keyword": keyword, "integrated": integrated}

    def list_found_tools(self) -> list:
        """列出所有從網路找到的免費工具"""
        return [
            {"keyword": t.get("keyword"), "found_at": t.get("found_at")}
            for t in self.found_tools[-20:]
        ]

    def list_integrated_tools(self) -> list:
        """列出已成功整合的工具"""
        return self.integrated_tools

    # =========================================
    # 自動重生循環（背景執行緒）
    # =========================================

    def start_auto_rebirth_loop(self, interval_seconds: int = 300):
        """啟動自動重生背景執行緒，每 N 秒檢查並修復"""

        def loop():
            while True:
                time.sleep(interval_seconds)
                try:
                    self._auto_rebirth_tick()
                except Exception as e:
                    print(f"[重生] 自動循環錯誤: {e}")

        t = threading.Thread(target=loop, daemon=True)
        t.start()
        print(f"[重生] 自動重生循環已啟動（每 {interval_seconds} 秒）")

    def _auto_rebirth_tick(self):
        """一次重生檢查週期"""
        # 1. 先掃描器官狀態
        if self.awareness:
            self.awareness.scan_all_organs(self.organs)

        dead = self.awareness.get_dead_organs() if self.awareness else []

        # 2. 修復死器官
        for name in dead:
            if self._regenerate_organ(name):
                print(f"[重生] 自動修復: {name}")
                self._append_history("auto_repair", f"自動修復 {name}")

        # 3. 檢查升級建議
        suggestions = self.suggest_upgrades()
        for s in suggestions:
            if s["alternative"] == "auto_rebuild":
                self.try_upgrade_organ(s["organ"])

        # 4. 處理升級佇列
        if self.upgrade_queue:
            self.process_upgrade_queue()

        # 5. 如果一切正常，存快照
        if not dead:
            self.take_snapshot(label="auto")

    # =========================================
    # 系統 Bootstrap — 從零重建
    # =========================================

    def bootstrap(self) -> bool:
        """
        從零重建整個系統。
        當所有器官都死掉時，這是唯一的復活方式。
        """
        print("[重生] ⚡ 開始 Bootstrap — 從零重建系統")
        self._append_history("bootstrap", "開始從零重建")

        # 1. 重新掃描所有零件
        try:
            self.assembler.scan_all()
        except Exception as e:
            print(f"[重生] 掃描失敗: {e}")
            return False

        # 2. 重新實例化所有器官
        restored = 0
        for name, cls_module in self.assembler.available_components.items():
            try:
                self._regenerate_organ(name)
                restored += 1
            except Exception as e:
                print(f"[重生] Bootstrap {name} 失敗: {e}")

        self.rebirth_count += 1
        self.last_rebirth = datetime.now()
        self._save_state()

        self._append_history("bootstrap_complete", f"重建完成：{restored} 器官復活")
        print(f"[重生] ✅ Bootstrap 完成：{restored} 器官復活")
        return True

    # =========================================
    # 持久化
    # =========================================

    def save(self):
        """儲存重生器官自身的狀態"""
        self._save_state()

    def _save_state(self):
        with self._lock:
            data = {
                "rebirth_count": self.rebirth_count,
                "last_rebirth": self.last_rebirth.isoformat() if self.last_rebirth else None,
                "part_registry": self.part_registry,
                "integrated_tools": self.integrated_tools,
                "upgrade_queue": self.upgrade_queue,
                "history": self.rebirth_history[-50:],
            }
        self.state_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def _load_state(self):
        if not self.state_file.exists():
            return
        try:
            data = json.loads(self.state_file.read_text())
            self.rebirth_count = data.get("rebirth_count", 0)
            t = data.get("last_rebirth")
            self.last_rebirth = datetime.fromisoformat(t) if t else None
            self.part_registry = data.get("part_registry", {})
            self.integrated_tools = data.get("integrated_tools", [])
            self.upgrade_queue = data.get("upgrade_queue", [])
            self.rebirth_history = data.get("history", [])
        except Exception:
            pass

    def _append_history(self, event: str, detail: str):
        self.rebirth_history.append({
            "ts": datetime.now().isoformat(),
            "event": event,
            "detail": detail,
        })
        if len(self.rebirth_history) > 100:
            self.rebirth_history = self.rebirth_history[-100:]

    def status(self) -> dict:
        return {
            "name": self.name,
            "alive": self.is_alive(),
            "rebirth_count": self.rebirth_count,
            "last_rebirth": self.last_rebirth.isoformat() if self.last_rebirth else None,
            "upgrade_queue_length": len(self.upgrade_queue),
            "integrated_tools_count": len(self.integrated_tools),
            "snapshots_count": len(list(self.snapshot_dir.glob("snapshot_*.json"))),
        }
