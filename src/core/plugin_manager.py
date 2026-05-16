"""
PluginManagerOrgan — 外掛管理器
掃描 plugins/ 目錄，動態匯入 .py 檔案，支援熱重載與啟用/停用。
"""
import importlib
import importlib.util
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from skeleton.brain_component import BrainComponent


class PluginManagerOrgan(BrainComponent):
    """
    外掛管理器器官

    功能：
    1. 掃描 plugins/ 目錄發現所有 .py 外掛
    2. 使用 importlib 動態匯入
    3. 追蹤外掛中繼資料（名稱、版本、作者、狀態）
    4. 支援熱重載（卸載後重新載入）
    5. 啟用/停用外掛
    """

    def __init__(self, dna: Optional[dict] = None):
        super().__init__(dna)
        self.plugin_dir = self._resolve_plugin_dir()
        self.plugins: Dict[str, Dict[str, Any]] = {}
        self._loaded_modules: Dict[str, Any] = {}
        self._ensure_plugin_dir()

    # ── 公開方法 ──────────────────────────────────────────────

    def discover_plugins(self) -> str:
        """
        掃描 plugins/ 目錄，發現所有可用的 .py 外掛檔案，
        但不自動載入。

        回傳：
            發現的外掛清單
        """
        if not self.plugin_dir.exists():
            return f"📭 plugins/ 目錄不存在: {self.plugin_dir}"

        py_files = sorted(
            p for p in self.plugin_dir.glob("*.py") if not p.name.startswith("_")
        )

        if not py_files:
            return "📭 plugins/ 目錄中沒有可用的 .py 外掛"

        discovered = []
        for py_file in py_files:
            plugin_name = py_file.stem
            info = self._scan_plugin_metadata(py_file)
            info["file"] = str(py_file)
            info["status"] = (
                self.plugins[plugin_name]["status"]
                if plugin_name in self.plugins
                else "undiscovered"
            )
            self.plugins[plugin_name] = info
            discovered.append(info)

        lines = [f"🔍 發現 {len(discovered)} 個外掛:"]
        for info in discovered:
            status_icon = {
                "loaded": "🔵",
                "enabled": "🟢",
                "disabled": "⚫",
                "undiscovered": "🟡",
            }.get(info.get("status"), "⚪")
            lines.append(
                f"  {status_icon} {info['name']} v{info.get('version', '?')} "
                f"— {info.get('description', '無描述')[:50]}"
            )
        return "\n".join(lines)

    def load_plugin(self, name: str) -> str:
        """
        動態載入指定外掛。

        參數：
            name: 外掛名稱（不含 .py 副檔名）

        回傳：
            載入結果訊息
        """
        plugin_info = self.plugins.get(name)
        if not plugin_info or "file" not in plugin_info:
            return f"❌ 未發現外掛「{name}」，請先執行 discover_plugins()"

        py_file = Path(plugin_info["file"])
        if not py_file.exists():
            return f"❌ 外掛檔案不存在: {py_file}"

        # 若已載入，先卸載
        if name in self._loaded_modules:
            self._unload_module(name)

        try:
            spec = importlib.util.spec_from_file_location(name, py_file)
            if spec is None or spec.loader is None:
                return f"❌ 無法建立模組規格: {name}"

            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)

            # 提取中繼資料
            metadata = {
                "name": name,
                "version": getattr(module, "__version__", getattr(module, "VERSION", "0.0.0")),
                "author": getattr(module, "__author__", "未知"),
                "description": getattr(module, "__doc__", "").strip().split("\n")[0]
                if module.__doc__
                else "無描述",
            }

            self._loaded_modules[name] = module
            plugin_info.update(metadata)
            plugin_info["status"] = "loaded"
            plugin_info["loaded_at"] = datetime.now().isoformat()
            plugin_info["reload_count"] = plugin_info.get("reload_count", 0)

            return (
                f"✅ 已載入外掛「{name}」v{metadata['version']}\n"
                f"  作者: {metadata['author']}\n"
                f"  描述: {metadata['description'][:80]}"
            )

        except Exception as e:
            plugin_info["status"] = "error"
            plugin_info["error"] = str(e)
            return f"❌ 載入外掛「{name}」失敗: {e}"

    def unload_plugin(self, name: str) -> str:
        """
        卸載指定外掛模組。

        參數：
            name: 外掛名稱
        """
        return self._unload_module(name)

    def get_plugin_info(self, name: str) -> str:
        """
        取得指定外掛的詳細中繼資料。

        參數：
            name: 外掛名稱

        回傳：
            格式化的外掛資訊
        """
        info = self.plugins.get(name)
        if not info:
            return f"❌ 找不到外掛: {name}"

        status_icon = {
            "loaded": "🔵 已載入",
            "enabled": "🟢 已啟用",
            "disabled": "⚫ 已停用",
            "undiscovered": "🟡 未載入",
            "error": "🔴 錯誤",
        }.get(info.get("status"), "⚪ 未知")

        lines = [
            f"🔌 外掛資訊: {name}",
            f"  ─────────────────",
            f"  版本: {info.get('version', '?')}",
            f"  作者: {info.get('author', '未知')}",
            f"  狀態: {status_icon}",
            f"  描述: {info.get('description', '無描述')}",
            f"  檔案: {info.get('file', '?')}",
        ]
        if info.get("loaded_at"):
            lines.append(f"  載入時間: {info['loaded_at']}")
        if info.get("reload_count", 0) > 0:
            lines.append(f"  重載次數: {info['reload_count']}")
        if info.get("error"):
            lines.append(f"  錯誤: {info['error']}")

        return "\n".join(lines)

    def list_plugins(self) -> str:
        """
        列出所有已知外掛及其狀態。

        回傳：
            格式化的外掛清單
        """
        if not self.plugins:
            return "📭 尚未發現任何外掛，請先執行 discover_plugins()"

        lines = [f"🔌 外掛清單 (共 {len(self.plugins)} 個):"]
        for name, info in self.plugins.items():
            status = info.get("status", "undiscovered")
            version = info.get("version", "?")
            lines.append(
                f"  [{status:12s}] {name:20s} v{version}"
            )
        return "\n".join(lines)

    def enable_plugin(self, name: str) -> str:
        """
        啟用指定外掛。若尚未載入則自動載入。

        參數：
            name: 外掛名稱
        """
        info = self.plugins.get(name)
        if not info:
            return f"❌ 找不到外掛: {name}"

        current = info.get("status")

        if current == "loaded" or current == "enabled":
            return f"⚠️ 外掛「{name}」已是 {current} 狀態"

        # 自動載入後設為 enabled
        if current not in ("loaded", "enabled"):
            load_result = self.load_plugin(name)
            if "❌" in load_result:
                return load_result

        info["status"] = "enabled"
        info["enabled_at"] = datetime.now().isoformat()
        return f"✅ 已啟用外掛「{name}」"

    def disable_plugin(self, name: str) -> str:
        """
        停用指定外掛（不卸載模組，僅標記為停用）。

        參數：
            name: 外掛名稱
        """
        info = self.plugins.get(name)
        if not info:
            return f"❌ 找不到外掛: {name}"

        current = info.get("status")
        if current == "disabled":
            return f"⚠️ 外掛「{name}」已是停用狀態"

        info["status"] = "disabled"
        info["disabled_at"] = datetime.now().isoformat()
        return f"⚫ 已停用外掛「{name}」"

    # ── 內部方法 ──────────────────────────────────────────────

    def _resolve_plugin_dir(self) -> Path:
        """解析 plugins/ 目錄的絕對路徑。"""
        # 優先使用 dna 中的自訂路徑
        custom = (self._dna or {}).get("plugin_dir")
        if custom:
            p = Path(custom)
            if p.is_absolute():
                return p
        # 預設為專案根目錄下的 plugins/
        return Path(__file__).resolve().parent.parent.parent / "plugins"

    def _ensure_plugin_dir(self):
        """確保 plugins/ 目錄存在。"""
        if not self.plugin_dir.exists():
            self.plugin_dir.mkdir(parents=True, exist_ok=True)
            init_py = self.plugin_dir / "__init__.py"
            if not init_py.exists():
                init_py.touch()

    def _scan_plugin_metadata(self, py_file: Path) -> Dict[str, Any]:
        """
        掃描單一 .py 檔案，提取基本中繼資料（不執行模組）。
        """
        try:
            content = py_file.read_text(encoding="utf-8")
        except Exception:
            content = ""

        metadata: Dict[str, Any] = {
            "name": py_file.stem,
            "version": "0.0.0",
            "author": "未知",
            "description": "無描述",
            "status": "undiscovered",
            "file": str(py_file),
            "reload_count": 0,
        }

        # 嘗試從檔案內容中解析基本資訊
        for line in content.split("\n")[:30]:
            line = line.strip()
            if line.startswith("__version__") or line.startswith("VERSION"):
                try:
                    metadata["version"] = line.split("=")[1].strip().strip("\"'")
                except Exception:
                    pass
            elif line.startswith("__author__"):
                try:
                    metadata["author"] = line.split("=")[1].strip().strip("\"'")
                except Exception:
                    pass
            elif '"""' in line or "'''" in line:
                # 嘗試擷取 docstring 第一行作為描述
                if metadata["description"] == "無描述":
                    doc = line.split('"""')[1] if '"""' in line else line.split("'''")[1]
                    metadata["description"] = doc.strip()[:100]

        return metadata

    def _unload_module(self, name: str) -> str:
        """卸載模組並從 sys.modules 中移除。"""
        if name in self._loaded_modules:
            del self._loaded_modules[name]
        if name in sys.modules:
            del sys.modules[name]
        if name in self.plugins:
            self.plugins[name]["status"] = "unloaded"
            self.plugins[name]["reload_count"] = (
                self.plugins[name].get("reload_count", 0) + 1
            )
        return f"🗑 已卸載外掛「{name}」"

    # ── 器官狀態 ──────────────────────────────────────────────

    def status(self) -> dict:
        total = len(self.plugins)
        loaded = sum(
            1 for p in self.plugins.values() if p.get("status") == "loaded"
        )
        enabled = sum(
            1 for p in self.plugins.values() if p.get("status") == "enabled"
        )
        disabled = sum(
            1 for p in self.plugins.values() if p.get("status") == "disabled"
        )
        return {
            "name": "PluginManagerOrgan",
            "alive": True,
            "total_plugins": total,
            "loaded": loaded,
            "enabled": enabled,
            "disabled": disabled,
            "plugin_dir": str(self.plugin_dir),
        }
