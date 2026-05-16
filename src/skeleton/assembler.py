"""
Assembler - 掃描所有器官目錄，實例化繼承 BrainComponent 的類別
支援舊器官目錄（nerve, immune, blood, muscle, skin, womb, waste, circuit, bag, web, brain 子目錄）
和新器官目錄（core），並根據 link_map.json 執行依賴注入
"""
import importlib
import inspect
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from skeleton.brain_component import BrainComponent
except ImportError:
    class BrainComponent:
        def __init__(self, dna: Optional[dict] = None):
            self.dna = dna or {}


class Assembler:
    def __init__(self, base_dir: Optional[Path] = None):
        if base_dir is None:
            base_dir = Path(__file__).resolve().parent.parent  # src/
        self.base_dir = base_dir
        self.organs: Dict[str, Any] = {}
        self.instantiated_organs: Dict[str, Any] = {}
        self.link_map: Dict[str, List[str]] = {}

    def load_link_map(self):
        """載入 link_map.json 中的器官依賴關係"""
        link_map_path = self.base_dir.parent / "link_map.json"
        if not link_map_path.exists():
            link_map_path = self.base_dir / "link_map.json"
        if link_map_path.exists():
            try:
                with open(link_map_path, "r", encoding="utf-8") as f:
                    self.link_map = json.load(f)
                print(f"  [🔗] 已載入 link_map.json ({len(self.link_map)} 條連線)")
            except Exception as e:
                print(f"  [⚠️] 無法載入 link_map.json: {e}")
        else:
            print("  [⚠️] 找不到 link_map.json")

    def scan_and_load(self):
        """修復 3：掃描整個 src/ 目錄，把所有繼承 BrainComponent 的類別全部載入"""
        # 掃描所有子目錄
        for subdir in self.base_dir.iterdir():
            if not subdir.is_dir():
                continue
            if subdir.name.startswith("_"):
                continue
            if subdir.name == "__pycache__":
                continue
            
            for py_file in subdir.glob("*.py"):
                if py_file.name.startswith("_"):
                    continue
                # 跳過 obsidian.py 本身
                if py_file.name == "obsidian.py":
                    continue
                self._load_organs_from_file(py_file)
        
        print(f"[Assembler] 總共載入 {len(self.instantiated_organs)} 個器官")

    def _scan_directory(self, dir_path: Path):
        """掃描單一目錄下的所有 .py 檔案"""
        for py_file in dir_path.glob("*.py"):
            if py_file.name.startswith("__"):
                continue
            self._load_organs_from_file(py_file)

    def _scan_brain_root(self, brain_dir: Path):
        """掃描 brain 根目錄下的特定檔案"""
        target_files = [
            "hypothalamus",
            "thalamus",
            "self_repair",
            "self_review",
            "evolution",
            "models",
        ]
        for name in target_files:
            py_file = brain_dir / f"{name}.py"
            if py_file.exists():
                self._load_organs_from_file(py_file)

    def _load_organs_from_file(self, py_file: Path):
        """從單一 .py 檔案載入所有繼承 BrainComponent 的類別並實例化"""
        try:
            # 計算相對於 src/ 的模組路徑
            rel_path = py_file.relative_to(self.base_dir)
            module_name = str(rel_path.with_suffix("")).replace(os.sep, ".")
            src_path = str(self.base_dir)
            if src_path not in sys.path:
                sys.path.insert(0, src_path)
            module = importlib.import_module(module_name)
        except Exception as e:
            print(f"  [⚠️] 無法載入 {py_file}: {e}")
            return

        # 機械零組件代號對應表 - 包含所有已知器官
        organ_display_names = {
            "memory": "記憶模組",
            "evolution": "進化模組",
            "self_learn": "學習模組",
            "planner": "任務排程器",
            "web_search": "搜尋引擎",
            "market_analyzer": "市場分析儀",
            "customer_persona": "客戶畫像儀",
            "email_marketer": "郵件發射器",
            "portfolio_tracker": "投資組合儀",
            "revenue_optimizer": "營收優化器",
            "auto_content_creator": "內容產生器",
            "seo_optimizer": "SEO 優化器",
            "social_media_manager": "社群管理器",
            "smart_contract_auditor": "合約審計儀",
            "daily_growth_report": "成長報告儀",
            "nose": "嗅覺感測器",
            "breath": "呼吸調節器",
            "cortex": "中央處理器",
            "hypothalamus": "定時調度器",
            "thalamus": "訊息中繼器",
            "self_repair": "自我修復單元",
            "self_review": "自我審查單元",
            "circuit_breaker": "電路保護器",
            "contradiction_detector": "矛盾檢測器",
            "health_checker": "健康檢查儀",
            "compass": "方向感測器",
            "task_tracker": "任務追蹤器",
            "tool_system": "工具系統",
            "plugin_loader": "插件載入器",
            "web_search_plugin": "搜尋插件",
            "voice_ear": "語音接收器",
            "vision_eye": "視覺感測器",
            "nose_system": "嗅覺系統",
            "auto_grow": "自動成長單元",
            "fallback_chain": "降級鏈",
            "registry": "註冊表",
            "face": "面部顯示器",
            "skin": "外殼",
            "blood": "血液循環系統",
            "muscle": "肌肉驅動器",
            "womb": "孕育單元",
            "waste": "廢棄物處理器",
            "bag": "背包儲存器",
            "nerve": "神經網路",
            "immune": "免疫系統",
            "circuit": "電路系統",
            "brain": "大腦核心",
            # 以下為啟動自檢中發現的遺漏器官
            "crosschainbridgeorgan": "跨鏈橋接器",
            "nftfloorscannerorgan": "NFT 地板價掃描儀",
            "gastrackerorgan": "Gas 追蹤器",
            "landingpagecrmorgan": "登陸頁 CRM",
            "nftmanagerorgan": "NFT 管理器",
            "nftsniperorgan": "NFT 狙擊手",
            "admanagerorgan": "廣告管理器",
            "autolearningorgan": "自動學習器",
            "cryptowalletorgan": "加密錢包",
            "nftairdropcheckerorgan": "NFT 空投檢查器",
            "nftmarketmakerorgan": "NFT 做市商",
            "marketdataorgan": "市場數據器",
            "nftwhaletrackerorgan": "NFT 巨鯨追蹤器",
            "pluginmanager": "插件管理器",
            "autojobsystemorgan": "自動工作系統",
            "crosschainbridge": "跨鏈橋接器",
            "nftfloorscanner": "NFT 地板價掃描儀",
            "gastracker": "Gas 追蹤器",
            "landingpagecrm": "登陸頁 CRM",
            "nftmanager": "NFT 管理器",
            "nftsniper": "NFT 狙擊手",
            "admanager": "廣告管理器",
            "autolearning": "自動學習器",
            "cryptowallet": "加密錢包",
            "nftairdropchecker": "NFT 空投檢查器",
            "nftmarketmaker": "NFT 做市商",
            "marketdata": "市場數據器",
            "nftwhaletracker": "NFT 巨鯨追蹤器",
            "autojobsystem": "自動工作系統",
        }

        for name, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, BrainComponent) and obj is not BrainComponent:
                try:
                    instance = obj(dna={})
                    organ_name = getattr(instance, "name", name.lower())
                    display_name = organ_display_names.get(organ_name, organ_name)
                    self.instantiated_organs[organ_name] = instance
                    print(f"  [✅] 載入 {display_name} ({obj.__name__})")
                except Exception as e:
                    print(f"  [❌] 實例化 {name} 失敗: {e}")

    def connect_all(self):
        """根據 link_map.json 執行器官之間的依賴注入"""
        if not self.link_map:
            print("  [⚠️] link_map 為空，跳過連線")
            return

        connected = 0
        for source_key, target_keys in self.link_map.items():
            # 在 instantiated_organs 中尋找對應的器官
            source_organ = None
            for organ_name, organ in self.instantiated_organs.items():
                if source_key in organ_name.lower():
                    source_organ = organ
                    break

            if source_organ is None:
                print(f"  [⚠️] 找不到來源器官: {source_key}")
                continue

            if isinstance(target_keys, str):
                target_keys = [target_keys]

            for target_key in target_keys:
                target_organ = None
                for organ_name, organ in self.instantiated_organs.items():
                    if target_key in organ_name.lower():
                        target_organ = organ
                        break

                if target_organ is None:
                    print(f"  [⚠️] 找不到目標器官: {target_key}")
                    continue

                # 將目標器官注入到來源器官的對應屬性
                attr_name = target_key.replace("-", "_")
                if hasattr(source_organ, attr_name):
                    setattr(source_organ, attr_name, target_organ)
                    connected += 1
                    print(f"  [🔗] {source_key}.{attr_name} = {target_key}")
                else:
                    # 嘗試直接設定屬性
                    try:
                        setattr(source_organ, attr_name, target_organ)
                        connected += 1
                        print(f"  [🔗] {source_key}.{attr_name} = {target_key}")
                    except Exception as e:
                        print(f"  [⚠️] 無法注入 {source_key}.{attr_name}: {e}")

        print(f"  [✅] 已建立 {connected} 條器官連線")

    def health_check(self):
        """檢查所有器官的健康狀態"""
        alive_count = 0
        dead_count = 0
        for name, organ in self.instantiated_organs.items():
            if hasattr(organ, "is_alive"):
                try:
                    alive = organ.is_alive()
                    status = "✅" if alive else "❌"
                except Exception:
                    status = "⚠️"
            else:
                status = "✅"
            print(f"  {status} {name}")
            if status == "✅":
                alive_count += 1
            elif status == "❌":
                dead_count += 1
        print(f"  總器官: {len(self.instantiated_organs)} | 正常: {alive_count} | 異常: {dead_count}")
