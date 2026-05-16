"""
工具系統 - 主動成長版
會自己發現需求、創造新工具、淘汰沒用的工具
"""

import json
import subprocess
import requests
import inspect
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

class ToolSystem:
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.registry_file = self.base_dir / "tools" / "registry" / "tools.json"
        self.custom_dir = self.base_dir / "tools" / "custom"
        self.custom_dir.mkdir(parents=True, exist_ok=True)
        
        self.registry = self._load_registry()
        
        # 使用統計（用來判斷哪些工具沒用，可以淘汰）
        self.usage_stats = self._load_usage_stats()
        
        # 初始化時註冊內建工具（只一次）
        if not self.registry:
            self._register_builtin_tools()
    
    def _load_registry(self) -> Dict:
        if self.registry_file.exists():
            return json.loads(self.registry_file.read_text())
        return {}
    
    def _save_registry(self):
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
        self.registry_file.write_text(json.dumps(self.registry, ensure_ascii=False, indent=2))
    
    def _load_usage_stats(self) -> Dict:
        stats_file = self.base_dir / "tools" / "registry" / "usage.json"
        if stats_file.exists():
            return json.loads(stats_file.read_text())
        return {}
    
    def _save_usage_stats(self):
        stats_file = self.base_dir / "tools" / "registry" / "usage.json"
        stats_file.parent.mkdir(parents=True, exist_ok=True)
        stats_file.write_text(json.dumps(self.usage_stats, ensure_ascii=False, indent=2))
    
    def _register_builtin_tools(self):
        """註冊內建工具（出生就會的）"""
        self.registry["ls"] = {
            "description": "列出目錄內容",
            "type": "builtin",
            "code": "def execute(path='.'): import os; return '\\n'.join(os.listdir(path))",
            "created_at": datetime.now().isoformat(),
            "last_used": None,
            "use_count": 0
        }
        
        self.registry["cat"] = {
            "description": "讀取檔案內容",
            "type": "builtin",
            "code": "def execute(path): return open(path).read()[:3000]",
            "created_at": datetime.now().isoformat(),
            "last_used": None,
            "use_count": 0
        }
        
        self.registry["write"] = {
            "description": "寫入檔案",
            "type": "builtin",
            "code": "def execute(path, content): open(path, 'w').write(content); return f'已寫入 {path}'",
            "created_at": datetime.now().isoformat(),
            "last_used": None,
            "use_count": 0
        }
        
        self.registry["http"] = {
            "description": "發送 HTTP GET 請求",
            "type": "builtin",
            "code": "def execute(url): import requests; return requests.get(url, timeout=30).text[:3000]",
            "created_at": datetime.now().isoformat(),
            "last_used": None,
            "use_count": 0
        }
        
        self.registry["shell"] = {
            "description": "執行 shell 指令",
            "type": "builtin",
            "code": "def execute(cmd): import subprocess; result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30); return result.stdout if result.stdout else result.stderr",
            "created_at": datetime.now().isoformat(),
            "last_used": None,
            "use_count": 0,
            "requires_approval": True
        }
        
        
        # 網頁搜尋工具
        self.registry["web_search"] = {
            "description": "搜尋網頁資訊，參數 query",
            "type": "builtin",
            "code": "def execute(query):\n            from web.search import WebSearch\n            ws = WebSearch()\n            return ws.search(query)",
            "created_at": datetime.now().isoformat(),
            "last_used": None,
            "use_count": 0
        }
        
        self._save_registry()
        print(f"✅ 已註冊 {len(self.registry)} 個內建工具")
    
    def learn_tool(self, name: str, description: str, tool_type: str, code: str) -> str:
        """學習新工具 - 動態加入"""
        # 檢查是否已存在
        if name in self.registry:
            return f"⚠️ 工具 {name} 已存在，用 update_tool 更新"
        
        self.registry[name] = {
            "description": description,
            "type": tool_type,
            "code": code,
            "created_at": datetime.now().isoformat(),
            "last_used": None,
            "use_count": 0
        }
        
        # 網頁搜尋工具
        self.registry["web_search"] = {
            "description": "搜尋網頁資訊，參數 query",
            "type": "builtin",
            "code": "def execute(query):\n            from web.search import WebSearch\n            ws = WebSearch()\n            return ws.search(query)",
            "created_at": datetime.now().isoformat(),
            "last_used": None,
            "use_count": 0
        }
        
        self._save_registry()
        print(f"✅ 學會新工具: {name}")
        return f"✅ 已學會新工具：{name}"
    
    def update_tool(self, name: str, code: str, description: str = None) -> str:
        """更新現有工具（自我進化）"""
        if name not in self.registry:
            return f"❌ 工具不存在: {name}"
        
        self.registry[name]["code"] = code
        if description:
            self.registry[name]["description"] = description
        self.registry[name]["updated_at"] = datetime.now().isoformat()
        
        # 網頁搜尋工具
        self.registry["web_search"] = {
            "description": "搜尋網頁資訊，參數 query",
            "type": "builtin",
            "code": "def execute(query):\n            from web.search import WebSearch\n            ws = WebSearch()\n            return ws.search(query)",
            "created_at": datetime.now().isoformat(),
            "last_used": None,
            "use_count": 0
        }
        
        self._save_registry()
        return f"✅ 已更新工具：{name}"
    
    def create_tool_from_need(self, need: str, call_ai_func) -> str:
        """根據需求創造新工具 - 主動成長的核心"""
        prompt = f"""根據以下需求，創造一個新工具：

需求：{need}

輸出 JSON 格式：
{{
    "tool_name": "英文名稱（小寫，底線分隔）",
    "description": "中文描述，工具做什麼",
    "code": "完整的 Python 函數：def execute(**kwargs): ... return 結果"
}}
"""
        try:
            response = call_ai_func(prompt)
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                tool_data = json.loads(json_match.group())
                name = tool_data.get("tool_name")
                desc = tool_data.get("description")
                code = tool_data.get("code")
                if name and code:
                    return self.learn_tool(name, desc, "custom", code)
        except Exception as e:
            return f"❌ 創造工具失敗: {e}"
        return "❌ 無法解析工具定義"
    
    def execute(self, tool_name: str, params: Dict = None) -> str:
        """執行工具，並記錄使用統計"""
        tool = self.registry.get(tool_name)
        if not tool:
            return f"❌ 工具不存在：{tool_name}"
        
        # 更新使用統計
        tool["last_used"] = datetime.now().isoformat()
        tool["use_count"] = tool.get("use_count", 0) + 1
        
        # 網頁搜尋工具
        self.registry["web_search"] = {
            "description": "搜尋網頁資訊，參數 query",
            "type": "builtin",
            "code": "def execute(query):\n            from web.search import WebSearch\n            ws = WebSearch()\n            return ws.search(query)",
            "created_at": datetime.now().isoformat(),
            "last_used": None,
            "use_count": 0
        }
        
        self._save_registry()
        
        params = params or {}
        
        try:
            if tool["type"] in ["builtin", "custom", "python"]:
                return self._exec_python(tool["code"], params)
            elif tool["type"] == "shell":
                return self._exec_shell(params.get("cmd", ""))
            else:
                return f"❌ 未知工具類型：{tool['type']}"
        except Exception as e:
            return f"❌ 執行失敗：{e}"
    
    def _exec_python(self, code: str, params: Dict) -> str:
        """執行 Python 程式碼"""
        exec_globals = {"params": params, "result": None}
        exec(code, exec_globals)
        return str(exec_globals.get("result", "執行完成"))
    
    def _exec_shell(self, cmd: str) -> str:
        """執行 shell 指令"""
        dangerous = ["rm -rf /", "dd ", "mkfs", "format", ":(){ :|:& };:"]
        for d in dangerous:
            if d in cmd:
                return f"❌ 拒絕執行危險指令：{d}"
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout if result.stdout else result.stderr
    
    def list_all(self) -> Dict:
        """列出所有工具"""
        return {name: {"description": info["description"], "type": info["type"], "use_count": info.get("use_count", 0)} 
                for name, info in self.registry.items()}
    
    def get_unused_tools(self, days: int = 30) -> List[str]:
        """找出很久沒用的工具（可以考慮淘汰）"""
        unused = []
        now = datetime.now()
        for name, info in self.registry.items():
            if info.get("type") == "builtin":
                continue  # 內建工具不淘汰
            last_used = info.get("last_used")
            if last_used:
                last = datetime.fromisoformat(last_used)
                if (now - last).days > days:
                    unused.append(name)
        return unused
    
    def clean_unused_tools(self, days: int = 30, dry_run: bool = True) -> str:
        """清理沒用的工具（主動淘汰）"""
        unused = self.get_unused_tools(days)
        if not unused:
            return f"📭 沒有超過 {days} 天未使用的工具"
        
        if dry_run:
            return f"🔍 將清理以下工具（共 {len(unused)} 個）：{', '.join(unused)}\n執行 clean_unused_tools(dry_run=False) 來實際清理"
        
        for name in unused:
            del self.registry[name]
        
        # 網頁搜尋工具
        self.registry["web_search"] = {
            "description": "搜尋網頁資訊，參數 query",
            "type": "builtin",
            "code": "def execute(query):\n            from web.search import WebSearch\n            ws = WebSearch()\n            return ws.search(query)",
            "created_at": datetime.now().isoformat(),
            "last_used": None,
            "use_count": 0
        }
        
        self._save_registry()
        return f"✅ 已清理 {len(unused)} 個未使用的工具"
    
    def suggest_new_tools(self, call_ai_func) -> str:
        """根據當前使用情況，建議需要的新工具"""
        existing = list(self.registry.keys())
        stats = self.usage_stats
        
        prompt = f"""我目前有的工具：{existing}

根據使用情況，我應該創造哪些新工具來提升能力？
輸出 JSON 列表：[{"tool_name": "名稱", "description": "用途", "reason": "為什麼需要"}]
"""
        try:
            response = call_ai_func(prompt)
            import re
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                suggestions = json.loads(json_match.group())
                result = ["💡 建議創造的新工具："]
                for s in suggestions[:5]:
                    result.append(f"  • {s.get('tool_name')}: {s.get('description')}")
                    result.append(f"    原因：{s.get('reason', '')}")
                return "\n".join(result)
        except:
            pass
        return "暫時沒有新工具建議"


if __name__ == "__main__":
    tools = ToolSystem(Path.home() / ".ampm_brain")
    print("現有工具：", list(tools.list_all().keys()))
    print("\n未使用工具檢查：", tools.get_unused_tools(7))

