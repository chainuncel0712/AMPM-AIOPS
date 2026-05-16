import json
import os
from pathlib import Path
from datetime import datetime
from functools import wraps  # 導入 wraps 裝飾器，用於保留原函數的元數據

class ToolSystem:
    def __init__(self, registry_file="data/tools/registry.json"):
        self.registry_file = Path(registry_file)
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
        self.registry = self._load_registry()
        self._register_builtin_tools()

    def _load_registry(self):
        if self.registry_file.exists():
            try:
                return json.loads(self.registry_file.read_text())
            except:
                return {}
        return {}

    def _save_registry(self):
        savable = {}
        for k, v in self.registry.items():
            if callable(v.get("code")):
                savable[k] = {key: val for key, val in v.items() if key != "code"}
                savable[k]["code"] = "<function>"
            else:
                savable[k] = v
        self.registry_file.write_text(json.dumps(savable, indent=4, ensure_ascii=False))

    def _register_builtin_tools(self):
        # 1. ls 工具
        self.registry["ls"] = {
            "description": "列出目錄內容",
            "type": "builtin",
            "code": "def execute(path='.'): import os; return os.listdir(path)",
            "created_at": datetime.now().isoformat(),
            "use_count": 0
        }
        # 2. cat 工具
        self.registry["cat"] = {
            "description": "讀取檔案內容",
            "type": "builtin",
            "code": "def execute(path): return open(path, 'r').read()",
            "created_at": datetime.now().isoformat(),
            "use_count": 0
        }
        # 3. web_search 工具
        self.registry["web_search"] = {
            "description": "搜尋網頁內容",
            "type": "builtin",
            "code": "def execute(query): from web.search import Search; return Search().query(query)",
            "created_at": datetime.now().isoformat(),
            "use_count": 0
        }
        # 4. system_stats 工具
        self.registry["system_stats"] = {
            "description": "查詢系統硬碟和記憶體使用狀況",
            "type": "builtin",
            "code": "def execute(): import subprocess; disk = subprocess.run(['df', '-h'], capture_output=True, text=True).stdout; mem = subprocess.run(['free', '-h'], capture_output=True, text=True).stdout; return f'硬碟:\\n{disk}\\n記憶體:\\n{mem}'",
            "created_at": datetime.now().isoformat(),
            "use_count": 0
        }
        self._save_registry()
        print(f"✅ 已成功組裝 {len(self.registry)} 個核心工具")

    def get_tool(self, name):
        return self.registry.get(name)

    def list_tools(self):
        return list(self.registry.keys())

    # ===== 新增：註冊工具的方法 =====
    def register_tool(self, name, func, description=""):
        """
        註冊一個工具函數到工具系統中
        
        參數：
            name: 工具名稱
            func: 工具函數
            description: 工具描述
        """
        self.registry[name] = {
            "description": description or func.__doc__ or "無描述",
            "type": "decorated",
            "code": func,  # 直接儲存函數參考
            "created_at": datetime.now().isoformat(),
            "use_count": 0
        }
        self._save_registry()
        print(f"🔧 已註冊工具：{name}")

    def execute_tool(self, name, *args, **kwargs):
        """
        執行一個已註冊的工具
        
        參數：
            name: 工具名稱
            *args: 位置參數
            **kwargs: 關鍵字參數
        """
        tool = self.registry.get(name)
        if not tool:
            raise ValueError(f"找不到工具：{name}")
        
        # 更新使用次數
        tool["use_count"] += 1
        self._save_registry()
        
        # 執行工具
        if tool["type"] == "decorated":
            # 如果是裝飾器註冊的函數，直接呼叫
            return tool["code"](*args, **kwargs)
        else:
            # 如果是內建工具，執行程式碼字串
            code = tool["code"]
            local_vars = {}
            exec(code, {"__builtins__": __builtins__}, local_vars)
            execute_func = local_vars.get("execute")
            if execute_func:
                return execute_func(*args, **kwargs)
            else:
                raise ValueError(f"工具 {name} 沒有 execute 函數")


# ===== 新增：@tool 裝飾器 =====
def tool(name=None, description=None):
    """
    @tool 裝飾器：將一個函數註冊為工具
    
    用法：
        @tool(name="my_tool", description="我的工具")
        def my_tool(param1, param2):
            '''工具功能說明'''
            return f"結果：{param1} {param2}"
    
    參數：
        name: 工具名稱（可選，預設使用函數名稱）
        description: 工具描述（可選，預設使用函數的文檔字串）
    """
    def decorator(func):
        # 使用 @wraps 保留原函數的元數據（名稱、文檔等）
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 執行原函數
            return func(*args, **kwargs)
        
        # 設定工具名稱
        tool_name = name or func.__name__
        # 設定工具描述
        tool_desc = description or func.__doc__ or "無描述"
        
        # 將工具註冊到全域工具系統
        # 注意：這裡需要一個全域的 ToolSystem 實例
        # 我們將在 Obsidian 初始化時設定
        if hasattr(tool, '_tool_system'):
            tool._tool_system.register_tool(tool_name, wrapper, tool_desc)
        
        # 在 wrapper 上儲存工具資訊，方便後續查詢
        wrapper._tool_name = tool_name
        wrapper._tool_description = tool_desc
        
        return wrapper
    
    # 如果 @tool 沒有參數（直接使用 @tool），則 name 是函數本身
    if callable(name):
        # 這種情況是 @tool 直接用在函數上，沒有括號
        func = name
        name = None
        return decorator(func)
    
    # 如果 @tool 有參數（使用 @tool(name="xxx")），則回傳裝飾器
    return decorator


# ===== 新增：設定 @tool 裝飾器使用的工具系統 =====
def set_tool_system(tool_system):
    """
    設定 @tool 裝飾器使用的工具系統實例
    
    參數：
        tool_system: ToolSystem 實例
    """
    tool._tool_system = tool_system
