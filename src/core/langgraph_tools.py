"""
工具管理模組 — 建置、解析、執行工具 (langgraph_tools.py)
======================================================
LangGraphExecutor 中工具相關方法的獨立模組。

包含：
- build_tools() — 動態掃描器官建立工具清單
- parse_tool_call() — 解析 LLM 回覆中的工具呼叫
- execute_tool_by_name() — 依名稱找到工具並執行
- detect_tool_need() — 檢測使用者是否需要特定工具
"""
import inspect
import json
import re
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


class ToolWrapper:
    def __init__(self, func, name, desc):
        self.func = func
        self.name = name
        self.description = desc

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def __repr__(self):
        return f"Tool({self.name}: {self.description[:30]}...)"


# ── 器官顯示名稱對照表 ──
ORGAN_DISPLAY_NAMES = {
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

# ── 器官動態匯入 ──
ORGAN_IMPORTS = [
    ("planner", "src.core.planner", "PlannerOrgan"),
    ("self_learn", "src.core.self_learn", "SelfLearnOrgan"),
    ("daily_growth_report", "src.core.daily_growth_report", "DailyGrowthReportOrgan"),
    ("market_analyzer", "src.core.market_analyzer", "MarketAnalyzerOrgan"),
    ("customer_persona", "src.core.customer_persona", "CustomerPersonaOrgan"),
    ("email_marketer", "src.core.email_marketer", "EmailMarketerOrgan"),
    ("portfolio_tracker", "src.core.portfolio_tracker", "PortfolioTrackerOrgan"),
    ("revenue_optimizer", "src.core.revenue_optimizer", "RevenueOptimizerOrgan"),
    ("auto_content_creator", "src.core.auto_content_creator", "AutoContentCreatorOrgan"),
    ("seo_optimizer", "src.core.seo_optimizer", "SEOOptimizerOrgan"),
    ("social_media_manager", "src.core.social_media_manager", "SocialMediaManagerOrgan"),
    ("smart_contract_auditor", "src.core.smart_contract_auditor", "SmartContractAuditorOrgan"),
]


def build_tools(executor) -> list:
    tools = []

    organ_classes = []
    for name, module_path, class_name in ORGAN_IMPORTS:
        try:
            module = __import__(module_path, fromlist=[class_name])
            organ_class = getattr(module, class_name)
            organ_classes.append((name, organ_class))
        except Exception as e:
            print(f"[LangGraphExecutor] ⚠️ 器官 {name} 載入失敗: {e}")

    for organ_name, organ_class in organ_classes:
        try:
            organ_instance = organ_class()
        except Exception as e:
            print(f"[_build_tools] 無法建立 {organ_name} 實例: {e}")
            continue
        for method_name, method in inspect.getmembers(organ_instance, inspect.ismethod):
            if method_name.startswith("_") or method_name.startswith("__"):
                continue
            if hasattr(method, "_is_tool") and method._is_tool:
                tool_name = getattr(method, "name", f"{organ_name}.{method_name}")
                tool_desc = getattr(method, "description", method.__doc__ or f"{organ_name}.{method_name}")
                tool_func = ToolWrapper(method, tool_name, tool_desc[:200])
                tools.append(tool_func)
            else:
                doc = method.__doc__ or f"{organ_name}.{method_name}"
                tool_func = ToolWrapper(method, f"{organ_name}.{method_name}", doc[:200])
                tools.append(tool_func)

    evolution_engine = executor.organs.get("self_evolution_engine")
    if evolution_engine:
        for method_name in dir(evolution_engine):
            method = getattr(evolution_engine, method_name)
            if hasattr(method, "_is_tool") and method._is_tool:
                tools.append(method)

    for organ_name, organ in executor.organs.items():
        if organ is None:
            continue
        for method_name, method in inspect.getmembers(organ, inspect.ismethod):
            if method_name.startswith("_") or method_name.startswith("__"):
                continue
            display_name = ORGAN_DISPLAY_NAMES.get(organ_name, organ_name)
            if hasattr(method, "_is_tool") and method._is_tool:
                tool_name = getattr(method, "name", f"{display_name}.{method_name}")
                tool_desc = getattr(method, "description", method.__doc__ or f"{display_name}.{method_name}")
                tool_func = ToolWrapper(method, tool_name, tool_desc[:200])
                tools.append(tool_func)
            else:
                doc = method.__doc__ or f"{display_name}.{method_name}"
                tool_func = ToolWrapper(method, f"{display_name}.{method_name}", doc[:200])
                tools.append(tool_func)

    # ── 基本工具 ──

    def get_current_time() -> str:
        return time.strftime("%Y-%m-%d %H:%M:%S")
    get_current_time.name = "get_current_time"
    get_current_time.description = "取得現在時間"
    tools.append(get_current_time)

    def search_web(query: str) -> str:
        try:
            from ddgs import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=3))
                if results:
                    return "\n".join([f"{r['title']}\n{r['body'][:200]}" for r in results])
        except:
            pass
        return f"搜尋完成: https://duckduckgo.com/?q={query}"
    search_web.name = "search_web"
    search_web.description = "搜尋網頁，查詢即時資訊"
    tools.append(search_web)

    def run_command(cmd: str = "", command: str = "") -> str:
        actual_cmd = cmd or command
        if not actual_cmd:
            return "⚠️ 請提供指令"
        try:
            r = subprocess.run(actual_cmd, shell=True, capture_output=True, text=True, timeout=10)
            result = r.stdout or r.stderr
            print(f"  [🔧] run_command 執行: {actual_cmd[:100]} -> {result[:200]}")
            return result
        except Exception as e:
            error_msg = str(e)
            print(f"  [❌] run_command 錯誤: {error_msg}")
            return error_msg
    run_command.name = "run_command"
    run_command.description = "執行系統指令"
    tools.append(run_command)

    def scan_files(path: str = ".") -> str:
        try:
            cmd = f"find {path} -type f -name '*.py' | head -50"
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            files = r.stdout.strip().split('\n') if r.stdout.strip() else []
            result = f"找到 {len(files)} 個 Python 檔案:\n"
            for f in files[:20]:
                result += f"  {f}\n"
            print(f"  [🔍] 掃描檔案: {path} -> {len(files)} 個檔案")
            return result
        except Exception as e:
            return f"掃描失敗: {e}"
    scan_files.name = "scan_files"
    scan_files.description = "掃描指定目錄下的檔案"
    tools.append(scan_files)

    def grep_files(pattern: str, path: str = ".") -> str:
        try:
            cmd = f"grep -r '{pattern}' {path} --include='*.py' | head -30"
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            result = r.stdout.strip() if r.stdout.strip() else f"在 {path} 中找不到 '{pattern}'"
            print(f"  [🔍] 搜尋內容: '{pattern}' in {path}")
            return result
        except Exception as e:
            return f"搜尋失敗: {e}"
    grep_files.name = "grep_files"
    grep_files.description = "在檔案中搜尋關鍵字"
    tools.append(grep_files)

    if executor.memory_manager:
        def remember_fact(fact: str) -> str:
            executor.memory_manager.remember_fact(fact, importance=0.7)
            return f"✅ 已記住: {fact[:50]}..."
        remember_fact.name = "remember_fact"
        remember_fact.description = "記住一個事實"
        tools.append(remember_fact)

        def recall_memory(query: str) -> str:
            results = executor.memory_manager.recall(query)
            if results:
                return "\n".join(r.get("content", "")[:100] for r in results[:5])
            return "📭 沒有相關記憶"
        recall_memory.name = "recall_memory"
        recall_memory.description = "回憶相關記憶"
        tools.append(recall_memory)

    learn_organ = executor.organs.get("self_learn")
    if learn_organ:
        def learn_lesson(lesson: str) -> str:
            if hasattr(learn_organ, "learn"):
                return learn_organ.learn(lesson)
            return "⚠️ 學習模組不可用"
        learn_lesson.name = "learn_lesson"
        learn_lesson.description = "學習新知識"
        tools.append(learn_lesson)

    evolution_organ = executor.organs.get("evolution")
    if evolution_organ:
        def get_evolution_summary() -> str:
            if hasattr(evolution_organ, "get_summary"):
                return evolution_organ.get_summary()
            return "⚠️ 進化模組不可用"
        get_evolution_summary.name = "get_evolution_summary"
        get_evolution_summary.description = "取得進化摘要"
        tools.append(get_evolution_summary)

    return tools


def parse_tool_call(text: str) -> Optional[Dict]:
    for m in re.finditer(r'\{', text):
        start = m.start()
        depth = 0
        end = -1
        for i in range(start, len(text)):
            if text[i] == '{':
                depth += 1
            elif text[i] == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        if end > start:
            candidate = text[start:end]
            if '"tool"' in candidate:
                try:
                    call_info = json.loads(candidate)
                    if "tool" in call_info:
                        return call_info
                except:
                    continue

    tc_match = re.search(r'<tool_call>\s*(.*?)\s*</tool_call>', text, re.DOTALL)
    if tc_match:
        inner = tc_match.group(1).strip()
        try:
            call_info = json.loads(inner)
            if "tool" in call_info:
                return call_info
        except:
            pass
        for m in re.finditer(r'\{', inner):
            start = m.start()
            depth = 0
            end = -1
            for i in range(start, len(inner)):
                if inner[i] == '{':
                    depth += 1
                elif inner[i] == '}':
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break
            if end > start:
                candidate = inner[start:end]
                if '"tool"' in candidate:
                    try:
                        call_info = json.loads(candidate)
                        if "tool" in call_info:
                            return call_info
                    except:
                        continue

    tool_match = re.search(r'使用工具[：:]\s*(\S+)', text)
    if tool_match:
        return {"tool": tool_match.group(1), "args": {}}

    exec_match = re.search(r'執行[：:]\s*(\S+)', text)
    if exec_match:
        return {"tool": exec_match.group(1), "args": {}}

    return None


def execute_tool_by_name(executor, tool_name: str, args: Dict = None) -> str:
    if args is None:
        args = {}
    for t in executor.tools:
        name = getattr(t, "name", None)
        if name == tool_name:
            try:
                result = t(**args)
                print(f"  [🔧] 執行工具: {tool_name} -> {str(result)[:100]}...")
                return str(result)
            except Exception as e:
                error_msg = f"⚠️ 工具執行錯誤: {e}"
                print(f"  [❌] {error_msg}")
                return error_msg
    return f"⚠️ 找不到工具: {tool_name}"


def detect_tool_need(user_msg: str) -> Optional[str]:
    tool_keywords = {
        "分析": "分析工具", "查詢": "查詢工具", "搜尋": "搜尋工具",
        "計算": "計算工具", "比較": "比較工具", "監控": "監控工具",
        "追蹤": "追蹤工具", "產生": "產生工具", "建立": "建立工具",
        "修改": "修改工具", "升級": "升級工具", "學習": "學習工具",
        "掃描": "掃描工具", "檢查": "檢查工具", "測試": "測試工具",
        "優化": "優化工具", "分析市場": "市場分析", "分析客戶": "客戶分析",
        "分析競品": "競品分析", "查詢價格": "價格查詢", "查詢餘額": "餘額查詢",
        "查詢 NFT": "NFT 查詢", "發送交易": "交易工具", "管理錢包": "錢包管理",
        "管理 NFT": "NFT 管理", "產生報告": "報告工具", "產生內容": "內容工具",
        "排程發布": "排程工具", "自動發文": "社群工具", "追蹤互動": "互動追蹤",
        "檢查合約": "合約審計", "掃描漏洞": "安全工具", "優化 SEO": "SEO 工具",
        "優化定價": "定價工具", "優化營收": "營收工具", "建立畫像": "客戶畫像",
        "客戶分群": "客戶分群", "郵件行銷": "郵件工具", "發送郵件": "郵件工具",
        "投資組合": "投資工具", "持倉記錄": "持倉工具", "地板價": "NFT 工具",
        "巨鯨": "巨鯨追蹤", "Gas": "Gas 工具", "錢包": "錢包工具",
        "加密貨幣": "加密貨幣工具", "比特幣": "加密貨幣工具", "以太坊": "加密貨幣工具",
        "NFT": "NFT 工具", "市場": "市場工具", "社群": "社群工具",
        "內容": "內容工具", "報告": "報告工具", "日曆": "日曆工具",
        "排程": "排程工具", "自動化": "自動化工具", "審計": "審計工具",
        "安全": "安全工具", "漏洞": "安全工具", "授權": "授權工具",
        "所有權": "所有權工具", "反向連結": "SEO 工具", "關鍵字": "SEO 工具",
        "SEO": "SEO 工具", "營收": "營收工具", "定價": "定價工具",
        "折扣": "定價工具", "產品組合": "產品工具", "客戶": "客戶工具",
        "畫像": "客戶畫像", "分群": "客戶分群", "郵件": "郵件工具",
        "活動": "郵件工具", "開信率": "郵件工具", "自動化流程": "自動化工具",
        "觸發": "自動化工具", "行動": "自動化工具",
    }
    for keyword, tool_type in tool_keywords.items():
        if keyword in user_msg:
            return tool_type
    return None


def list_tools(executor) -> List[str]:
    return [t.name for t in executor.tools if hasattr(t, "name")]
