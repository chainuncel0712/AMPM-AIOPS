""" SelfEvolutionEngine - 自我進化引擎 """
import importlib
import importlib.util
import inspect
import os
import sys
from pathlib import Path
from typing import Optional, Dict, List
from skeleton.base_organ import BaseOrgan as BrainComponent
from tools import tool  # 匯入 @tool 裝飾器

class SelfEvolutionEngine(BrainComponent):
    def __init__(self, dna: Optional[dict] = None):
        super().__init__(dna)
        self._generated_tools: Dict[str, str] = {}
        self._tools_dir = Path(__file__).resolve().parent.parent.parent / "src" / "core"
        self._tools_dir.mkdir(parents=True, exist_ok=True)

    @tool(name="learn_from_user", description="根據使用者需求學習新知識或產生新工具")
    def learn_from_user(self, query: str) -> str:
        """根據使用者需求，分析需要什麼新工具，並自動產生對應的 Python 程式碼"""
        # 這裡使用 LLM 分析需求（模擬）
        # 實際應用中應呼叫 self.llm 進行分析
        return (
            f"🔍 分析使用者需求: {query[:100]}...\n"
            f"  建議建立新工具: {query[:20]}Tool\n"
            f"  請使用 generate_tool 來建立"
        )

    @tool(name="generate_tool", description="產生新的工具程式碼並動態載入")
    def generate_tool(self, name: str, description: str, code: str) -> str:
        """將產生的程式碼寫入 src/core/ 目錄，並動態載入"""
        # 確保檔名合法
        safe_name = name.replace(" ", "_").replace("-", "_")
        file_path = self._tools_dir / f"{safe_name}.py"
        
        # 寫入檔案
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code)
        except Exception as e:
            return f"❌ 寫入檔案失敗: {e}"
        
        # 動態載入模組
        try:
            spec = importlib.util.spec_from_file_location(safe_name, file_path)
            if spec is None or spec.loader is None:
                return f"❌ 無法載入模組: {safe_name}"
            module = importlib.util.module_from_spec(spec)
            sys.modules[safe_name] = module
            spec.loader.exec_module(module)
            
            # 檢查是否有 tool 裝飾器的方法
            tool_functions = []
            for name_attr, obj in inspect.getmembers(module):
                if hasattr(obj, "_is_tool") and obj._is_tool:
                    tool_functions.append(name_attr)
            
            self._generated_tools[safe_name] = str(file_path)
            
            # 自動註冊到 self.organs
            self._register_to_organs(safe_name, module)
            
            return (
                f"✅ 工具已產生: {safe_name}\n"
                f"  檔案路徑: {file_path}\n"
                f"  工具函式: {', '.join(tool_functions) if tool_functions else '無'}\n"
                f"  已自動註冊到引擎"
            )
        except Exception as e:
            return f"❌ 載入模組失敗: {e}"

    @tool(name="register_tool", description="將新工具註冊到 LangGraph 引擎")
    def register_tool(self, name: str) -> str:
        """將新工具註冊到 LangGraph 引擎中，使其立即可用"""
        if name not in self._generated_tools:
            return f"❌ 找不到已產生的工具: {name}，請先使用 generate_tool"
        
        # 重新載入模組並註冊
        file_path = self._generated_tools[name]
        try:
            spec = importlib.util.spec_from_file_location(name, file_path)
            if spec is None or spec.loader is None:
                return f"❌ 無法重新載入: {name}"
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
            
            # 自動註冊到 self.organs
            self._register_to_organs(name, module)
            
            return (
                f"✅ 工具 {name} 已重新註冊到引擎\n"
                f"  已自動加入器官清單，下次使用時即可調用"
            )
        except Exception as e:
            return f"❌ 重新註冊失敗: {e}"

    @tool(name="self_repair", description="自動修復工具錯誤")
    def self_repair(self, error: str) -> str:
        """當工具執行失敗時，自動分析錯誤並修復程式碼"""
        # 這裡使用 LLM 分析錯誤（模擬）
        return (
            f"🔧 分析錯誤: {error[:100]}...\n"
            f"  建議修復: 檢查參數型別或重新產生工具\n"
            f"  請使用 generate_tool 重新產生"
        )

    @tool(name="list_generated_tools", description="列出所有已產生的工具")
    def list_generated_tools(self) -> str:
        """列出所有已產生的工具"""
        if not self._generated_tools:
            return "📭 尚未產生任何工具"
        lines = ["📋 已產生的工具:"]
        for name, path in self._generated_tools.items():
            lines.append(f"  {name}: {path}")
        return "\n".join(lines)

    @tool(name="self_modify", description="修改自己的程式碼來強化能力")
    def self_modify(self, file_path: str, new_code: str) -> str:
        """修改自己的程式碼來強化能力"""
        try:
            # 確保檔案路徑在 src/core/ 目錄內
            target_path = Path(file_path)
            if not str(target_path).startswith(str(self._tools_dir)):
                return f"❌ 只能修改 src/core/ 目錄內的檔案"
            
            # 備份原始檔案
            backup_path = target_path.with_suffix(target_path.suffix + ".bak")
            if target_path.exists():
                import shutil
                shutil.copy2(target_path, backup_path)
            
            # 寫入新程式碼
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(new_code)
            
            # 重新載入模組
            module_name = target_path.stem
            try:
                spec = importlib.util.spec_from_file_location(module_name, target_path)
                if spec is not None and spec.loader is not None:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)
                    self._register_to_organs(module_name, module)
            except Exception as e:
                print(f"  [⚠️] 重新載入失敗: {e}")
            
            return (
                f"✅ 已修改: {target_path.name}\n"
                f"  備份位置: {backup_path}\n"
                f"  已重新載入模組"
            )
        except Exception as e:
            return f"❌ 修改失敗: {e}"

    @tool(name="self_upgrade", description="升級自己的能力（新增或強化功能）")
    def self_upgrade(self, capability: str, code: str) -> str:
        """升級自己的能力（新增或強化功能）"""
        # 產生新的器官檔案
        safe_name = capability.replace(" ", "_").replace("-", "_")
        file_path = self._tools_dir / f"{safe_name}.py"
        
        # 寫入檔案
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code)
        except Exception as e:
            return f"❌ 升級失敗: {e}"
        
        # 動態載入
        try:
            spec = importlib.util.spec_from_file_location(safe_name, file_path)
            if spec is None or spec.loader is None:
                return f"❌ 無法載入新能力: {safe_name}"
            module = importlib.util.module_from_spec(spec)
            sys.modules[safe_name] = module
            spec.loader.exec_module(module)
            
            self._generated_tools[safe_name] = str(file_path)
            
            # 自動註冊到 self.organs
            self._register_to_organs(safe_name, module)
            
            return (
                f"✅ 已升級能力: {safe_name}\n"
                f"  檔案路徑: {file_path}\n"
                f"  已自動註冊到引擎"
            )
        except Exception as e:
            return f"❌ 載入新能力失敗: {e}"

    def _register_to_organs(self, name: str, module):
        """
        將新載入的模組註冊到 self.organs
        
        參數 Parameters:
            name: 模組名稱 Module name
            module: 模組物件 Module object
        """
        # 取得 brain 的 organs 字典
        brain = getattr(self, "brain", None)
        if brain is None:
            # 嘗試從上層取得
            for frame_info in inspect.stack():
                local_vars = frame_info[0].f_locals
                if "self" in local_vars:
                    obj = local_vars["self"]
                    if hasattr(obj, "organs"):
                        brain = obj
                        break
        
        if brain is None or not hasattr(brain, "organs"):
            print(f"  [⚠️] 無法取得 brain.organs，工具 {name} 未註冊")
            return
        
        # 掃描模組中是否有 BrainComponent 子類別
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and issubclass(attr, BrainComponent) and attr is not BrainComponent:
                # 實例化並註冊
                try:
                    instance = attr()
                    brain.organs[name] = instance
                    print(f"  [✅] 已註冊器官: {name} ({attr_name})")
                    return
                except Exception as e:
                    print(f"  [⚠️] 無法實例化 {attr_name}: {e}")
        
        # 如果沒有找到 BrainComponent 子類別，嘗試直接註冊模組本身
        if hasattr(module, "run") and callable(module.run):
            brain.organs[name] = module
            print(f"  [✅] 已註冊插件: {name}")
            return
        
        # 如果模組中有任何可呼叫的函數，註冊為工具
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if callable(attr) and not attr_name.startswith("_"):
                brain.organs[name] = module
                print(f"  [✅] 已註冊模組: {name} (包含可呼叫函數)")
                return
        
        print(f"  [⚠️] 模組 {name} 中未找到可註冊的類別")

    @tool(name="find_tool", description="搜尋現有工具或學習新工具來滿足需求")
    def find_tool(self, requirement: str) -> str:
        """搜尋現有工具或學習新工具來滿足需求"""
        # 搜尋 src/core/ 目錄下的所有器官
        existing_tools = []
        for py_file in self._tools_dir.glob("*.py"):
            if py_file.name.startswith("_"):
                continue
            existing_tools.append(py_file.stem)
        
        # 檢查是否有符合需求的工具
        matching_tools = [t for t in existing_tools if requirement.lower() in t.lower()]
        
        if matching_tools:
            # 嘗試自動載入並註冊找到的工具
            loaded = []
            for tool_name in matching_tools:
                file_path = self._tools_dir / f"{tool_name}.py"
                try:
                    spec = importlib.util.spec_from_file_location(tool_name, file_path)
                    if spec is None or spec.loader is None:
                        continue
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[tool_name] = module
                    spec.loader.exec_module(module)
                    self._register_to_organs(tool_name, module)
                    loaded.append(tool_name)
                except Exception as e:
                    print(f"  [⚠️] 無法載入 {tool_name}: {e}")
            
            result = f"🔍 找到符合需求的工具:\n"
            result += "\n".join([f"  - {t}" for t in matching_tools])
            if loaded:
                result += f"\n\n✅ 已自動載入並註冊: {', '.join(loaded)}"
            else:
                result += "\n\n請使用 learn_from_user 來學習如何使用"
            return result
        
        # 沒有找到，建議學習新工具
        return (
            f"🔍 未找到符合需求的工具\n"
            f"  需求: {requirement}\n"
            f"  建議: 使用 learn_from_user 來學習新工具\n"
            f"  或使用 self_upgrade 來升級能力"
        )
