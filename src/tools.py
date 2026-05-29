# [public] AMPM-AIOPS public tool interface
# Internal execution policies and routing hooks stripped — moved to AMPM-KERNEL

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
            "description": "列出目錄內容，支援 ~ 開頭的路徑",
            "type": "builtin",
            "code": "def execute(path='.'):\n from pathlib import Path\n p = Path(path).expanduser()\n if p.is_dir():\n  return '\\n'.join(sorted(p.iterdir()))\n else:\n  return f'路徑不存在或不是目錄: {p}'",
            "created_at": datetime.now().isoformat(),
            "use_count": 0
        }
        # 2. cat 工具
        self.registry["cat"] = {
            "description": "讀取檔案內容，支援 ~ 開頭的路徑",
            "type": "builtin",
            "code": "def execute(path):\n from pathlib import Path\n p = Path(path).expanduser()\n if p.exists() and p.is_file():\n  return p.read_text(encoding='utf-8', errors='replace')\n else:\n  return f'檔案不存在: {p}'",
            "created_at": datetime.now().isoformat(),
            "use_count": 0
        }
        # 2.5 find_file 工具
        self.registry["find_file"] = {
            "description": "搜尋檔案，依名稱或模式尋找",
            "type": "builtin",
            "code": "def execute(name_pattern, search_path='~'):\n from pathlib import Path\n import fnmatch\n results = []\n base = Path(search_path).expanduser()\n if not base.exists():\n  return f'搜尋起點不存在: {base}'\n try:\n  for p in base.rglob('*'):\n   if fnmatch.fnmatch(p.name, name_pattern) or fnmatch.fnmatch(p.name.lower(), name_pattern.lower()):\n    results.append(str(p))\n except PermissionError:\n  pass\n if results:\n  return '\\n'.join(results[:20]) + (f'\\n...還有 {len(results)-20} 個' if len(results) > 20 else '')\n else:\n  return f'在 {base} 底下找不到符合「{name_pattern}」的檔案'",
            "created_at": datetime.now().isoformat(),
            "use_count": 0
        }
        # 3. web_search 工具
        self.registry["web_search"] = {
            "description": "搜尋網頁內容",
            "type": "builtin",
            "code": "def execute(query): from web.search import WebSearch; return WebSearch().search(query)",
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
        # 5. write_file 工具 — 寫入內容到檔案（允許寫入家目錄，排除敏感位置）
        self.registry["write_file"] = {
            "description": "將文字內容寫入指定的檔案路徑。支援 ~ 開頭的路徑。保護：禁止寫入 .ssh/、金鑰、密碼等敏感位置。",
            "type": "builtin",
            "code": "def execute(path, content):\n import os\n from pathlib import Path\n p = Path(path).expanduser()\n abs_p = p.resolve()\n home = Path.home()\n \n sensitive_patterns = [\n  '/.ssh/', '/.gnupg/', '/.aws/', '/.azure/',\n  'id_rsa', 'id_dsa', 'id_ecdsa', 'id_ed25519',\n  'private_key', 'secret', 'password',\n ]\n p_str = str(abs_p).lower()\n for pat in sensitive_patterns:\n  if pat.lower() in p_str:\n   return f'禁止寫入敏感位置: {abs_p}'\n \n if not str(abs_p).startswith(str(home)):\n  return f'僅允許寫入家目錄內的路徑: {home}'\n \n if 'venv/' in str(abs_p) or '__pycache__' in str(abs_p):\n  return '不允許寫入 venv'\n \n os.makedirs(abs_p.parent, exist_ok=True)\n abs_p.write_text(content, encoding='utf-8')\n return f'已寫入 {len(content)} 字元到 {abs_p}'",
            "created_at": datetime.now().isoformat(),
            "use_count": 0
        }
        # 6. check_cloudflare 工具 — 驗證 Cloudflare API 金鑰是否可用
        self.registry["check_cloudflare"] = {
            "description": "檢查 Cloudflare API 金鑰是否有效，可用於確認 DNS 管理、Email Routing、Workers 等服務的連線狀態",
            "type": "builtin",
            "code": "def execute():\n import os, json, urllib.request\n token = os.getenv('CLOUDFLARE_API_TOKEN', '')\n if not token:\n  return json.dumps({'status': 'error', 'message': '未設定 CLOUDFLARE_API_TOKEN'}, ensure_ascii=False)\n req = urllib.request.Request('https://api.cloudflare.com/client/v4/user/tokens/verify', headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'})\n try:\n  resp = urllib.request.urlopen(req, timeout=10)\n  data = json.loads(resp.read())\n  return json.dumps(data, ensure_ascii=False, indent=2)\n except Exception as e:\n  return json.dumps({'status': 'error', 'message': str(e)}, ensure_ascii=False)",
            "created_at": datetime.now().isoformat(),
            "use_count": 0
        }
        # 7. list_memory 工具 — 查詢黑曜的記憶內容
        self.registry["list_memory"] = {
            "description": "列出黑曜的記憶內容（working/semantic/episodic），可指定記憶類型和數量",
            "type": "builtin",
            "code": "def execute(memory_type='semantic', count=10):\n import json\n from pathlib import Path\n base = Path.home() / '.ampm_brain' / 'memory'\n file_map = {'working': base/'working.json', 'semantic': base/'semantic.json', 'episodic': base/'episodic.json'}\n path = file_map.get(memory_type)\n if not path or not path.exists():\n  return f'找不到記憶檔案: {memory_type}'\n data = json.loads(path.read_text())\n if isinstance(data, list):\n  items = data[-count:]\n  lines = []\n  for e in items:\n   fact = e.get('fact', e.get('user', ''))[:120]\n   imp = e.get('importance', 0)\n   lines.append(f'[imp={imp}] {fact}')\n  return '\\n'.join(lines)\n return str(data)[:2000]",
            "created_at": datetime.now().isoformat(),
            "use_count": 0
        }
        # 8. exchange_status 工具 — 檢查交易所連線狀態
        self.registry["exchange_status"] = {
            "description": "檢查交易所 API 連線、餘額、BTC 價格",
            "type": "builtin",
            "code": "def execute():\n import os, sys, json\n from pathlib import Path\n sys.path.insert(0, str(Path(__file__).resolve().parent))\n try:\n  from exchange.gate import GateIO\n  api_key = os.getenv('GATE_IO_API_KEY', '')\n  api_secret = os.getenv('GATE_IO_API_SECRET', '')\n  if not api_key or not api_secret:\n   return json.dumps({'status': 'error', 'message': '未設定 GATE_IO_API_KEY 或 GATE_IO_API_SECRET'}, ensure_ascii=False)\n  gate = GateIO(api_key, api_secret)\n  result = gate.status()\n  return json.dumps(result, ensure_ascii=False, indent=2)\n except Exception as e:\n  return json.dumps({'status': 'error', 'message': str(e)}, ensure_ascii=False)",
            "created_at": datetime.now().isoformat(),
            "use_count": 0
        }
        # 9. spot_buy_market 工具 — 市價買入現貨
        self.registry["spot_buy_market"] = {
            "description": "現貨市價買入，參數: pair=交易對(預設BTC_USDT), quote_amount=要花費的quote貨幣數量(例如100代表花100 USDT)",
            "type": "builtin",
            "code": "def execute(pair='BTC_USDT', quote_amount='100'):\n import os, sys, json\n from pathlib import Path\n sys.path.insert(0, str(Path(__file__).resolve().parent))\n try:\n  from exchange.gate import GateIO\n  api_key = os.getenv('GATE_IO_API_KEY', '')\n  api_secret = os.getenv('GATE_IO_API_SECRET', '')\n  if not api_key or not api_secret:\n   return json.dumps({'error': '未設定 API Key'}, ensure_ascii=False)\n  gate = GateIO(api_key, api_secret)\n  result = gate.quick_buy_market(pair, quote_amount)\n  return json.dumps(result, ensure_ascii=False, indent=2)\n except Exception as e:\n  return json.dumps({'error': str(e)}, ensure_ascii=False)",
            "created_at": datetime.now().isoformat(),
            "use_count": 0
        }
        # 10. spot_sell_market 工具 — 市價賣出現貨
        self.registry["spot_sell_market"] = {
            "description": "現貨市價賣出，參數: pair=交易對, base_amount=要賣出的base貨幣數量(例如0.01代表賣0.01 BTC)",
            "type": "builtin",
            "code": "def execute(pair='BTC_USDT', base_amount='0.01'):\n import os, sys, json\n from pathlib import Path\n sys.path.insert(0, str(Path(__file__).resolve().parent))\n try:\n  from exchange.gate import GateIO\n  api_key = os.getenv('GATE_IO_API_KEY', '')\n  api_secret = os.getenv('GATE_IO_API_SECRET', '')\n  if not api_key or not api_secret:\n   return json.dumps({'error': '未設定 API Key'}, ensure_ascii=False)\n  gate = GateIO(api_key, api_secret)\n  result = gate.quick_sell_market(pair, base_amount)\n  return json.dumps(result, ensure_ascii=False, indent=2)\n except Exception as e:\n  return json.dumps({'error': str(e)}, ensure_ascii=False)",
            "created_at": datetime.now().isoformat(),
            "use_count": 0
        }
        # 11. get_price 工具 — 獲取交易對價格
        self.registry["get_price"] = {
            "description": "獲取交易對最新價格，參數: pair=交易對(預設BTC_USDT)",
            "type": "builtin",
            "code": "def execute(pair='BTC_USDT'):\n import sys, json\n from pathlib import Path\n sys.path.insert(0, str(Path(__file__).resolve().parent))\n try:\n  from exchange.gate import GateIO\n  gate = GateIO()\n  price = gate.get_price(pair)\n  if price:\n   return json.dumps({'pair': pair, 'price': price}, ensure_ascii=False)\n  return json.dumps({'error': f'無法獲取 {pair} 價格'}, ensure_ascii=False)\n except Exception as e:\n  return json.dumps({'error': str(e)}, ensure_ascii=False)",
            "created_at": datetime.now().isoformat(),
            "use_count": 0
        }
         # 12. trading_report 工具 — 交易狀態報告
        self.registry["trading_report"] = {
            "description": "完整交易報告：餘額、價格、持倉、網格策略",
            "type": "builtin",
            "code": "def execute():\n import os, sys, json\n from pathlib import Path\n sys.path.insert(0, str(Path(__file__).resolve().parent))\n try:\n  from exchange.gate import GateIO\n  from exchange.trading_engine import get_trading_engine\n  api_key = os.getenv('GATE_IO_API_KEY', '')\n  api_secret = os.getenv('GATE_IO_API_SECRET', '')\n  report = {}\n  if api_key and api_secret:\n   gate = GateIO(api_key, api_secret)\n   balances = gate.get_spot_balances()\n   if isinstance(balances, list):\n    report['balances'] = [{'currency': b.get('currency'), 'available': b.get('available'), 'locked': b.get('locked')} for b in balances if float(b.get('available', 0)) > 0 or float(b.get('locked', 0)) > 0]\n   price = gate.get_price('BTC_USDT')\n   if price:\n    report['btc_price'] = price\n  engine = get_trading_engine()\n  grids = engine.get_grids()\n  if grids:\n   report['grids'] = grids\n  return json.dumps(report, ensure_ascii=False, indent=2)\n except Exception as e:\n  return json.dumps({'error': str(e)}, ensure_ascii=False)",
            "created_at": datetime.now().isoformat(),
            "use_count": 0
        }
        # 13. strategy_safe_scan 工具 — 安全策略掃描 (波動+TA 雙重過濾)
        self.registry["strategy_safe_scan"] = {
            "description": "安全策略掃描：波動 20~80% + MA多頭 + RSI 30~65，停利 +6% / 停損 -3%",
            "type": "builtin",
            "code": "def execute():\n import os, sys\n from pathlib import Path\n sys.path.insert(0, str(Path(__file__).resolve().parent))\n try:\n  from exchange.gate import GateIO\n  from exchange.strategy_engine import get_strategy_engine\n  api_key = os.getenv('GATE_IO_API_KEY', '')\n  api_secret = os.getenv('GATE_IO_API_SECRET', '')\n  if not api_key or not api_secret:\n   return '❌ 未設定 GATE_IO_API_KEY 或 GATE_IO_API_SECRET'\n  gate = GateIO(api_key, api_secret)\n  engine = get_strategy_engine(gate)\n  engine.set_exchange(gate)\n  signals = engine.scan_and_analyze()\n  return engine.get_report(signals)\n except Exception as e:\n  return f'❌ 安全策略掃描失敗: {e}'",
            "created_at": datetime.now().isoformat(),
            "use_count": 0
        }
        # 14. strategy_sniper_scan 工具 — 新幣狙擊掃描 (高風險、觀察模式)
        self.registry["strategy_sniper_scan"] = {
            "description": "新幣狙擊掃描：短線熱幣、買賣單壓力分析，停利 +5% / 停損 -2% (高風險，建議先觀察)",
            "type": "builtin",
            "code": "def execute():\n import os, sys\n from pathlib import Path\n sys.path.insert(0, str(Path(__file__).resolve().parent))\n try:\n  from exchange.gate import GateIO\n  from exchange.new_coin_sniper import get_new_coin_sniper\n  api_key = os.getenv('GATE_IO_API_KEY', '')\n  api_secret = os.getenv('GATE_IO_API_SECRET', '')\n  if not api_key or not api_secret:\n   return '❌ 未設定 GATE_IO_API_KEY 或 GATE_IO_API_SECRET'\n  gate = GateIO(api_key, api_secret)\n  sniper = get_new_coin_sniper(gate)\n  sniper.set_exchange(gate)\n  targets = sniper.scan()\n  return sniper.get_report(targets)\n except Exception as e:\n  return f'❌ 狙擊掃描失敗: {e}'",
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

    def create_tool_from_need(self, need: str, call_ai) -> str:
        try:
            prompt = f"根據以下需求創建一個新工具（Python function）：\n{need}\n\n回傳 JSON：{{'name': '工具名', 'description': '描述', 'code': 'Python 程式碼'}}"
            messages = [{"role": "system", "content": "你是工具產生專家，只輸出 JSON。"}, {"role": "user", "content": prompt}]
            result = call_ai(messages)
            import json, re
            match = re.search(r'\{.*\}', result, re.DOTALL)
            if match:
                data = json.loads(match.group())
                self.register_tool(data["name"], lambda *a, **kw: exec(data["code"]), data.get("description", ""))
                return f"✅ 已創建工具: {data['name']}"
            return f"❌ 無法解析 AI 回覆: {result[:200]}"
        except Exception as e:
            return f"❌ 創建工具失敗: {e}"

    def learn_tool(self, name: str, description: str, category: str = "custom", code: str = None):
        import json
        self.registry[name] = {
            "description": description,
            "type": category,
            "code": code or f"def execute():\n    return '{name} tool executed'",
            "created_at": __import__('datetime').datetime.now().isoformat(),
            "use_count": 0
        }
        self._save_registry()
        print(f"🔧 已學習工具：{name}")

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
            import builtins as _builtins
            restricted = {"__builtins__": _builtins.__dict__}
            exec(code, restricted, local_vars)
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
