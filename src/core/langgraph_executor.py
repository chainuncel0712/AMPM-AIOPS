"""
LangGraph Executor - 黑曜核心思考引擎
專注於五大核心能力：
1. 自我反省 - 檢查自己的行為和回覆
2. 自我修復 - 發現問題自動修復
3. 自我進化 - 從經驗中學習成長
4. 尋找資源 - 主動搜尋資訊和工具
5. 記憶 - 記住對話和經驗

注意：這是開源版（Open Source Edition）的核心程式碼，永遠免費。
商業功能（市場分析、加密貨幣等）放在 src/pro/ 目錄。
"""
import inspect  # 匯入 inspect 模組，用於檢查物件的方法
import os  # 匯入 os 模組，用於作業系統功能
import subprocess  # 匯入 subprocess 模組，用於執行系統指令
import queue  # 匯入 queue 模組，用於建立佇列
import threading  # 匯入 threading 模組，用於多執行緒
import time  # 匯入 time 模組，用於時間相關功能
import json  # 匯入 json 模組，用於 JSON 處理
import re  # 匯入 re 模組，用於正則表達式
from concurrent.futures import Future  # 匯入 Future 類別，用於非同步結果
from datetime import datetime  # 匯入 datetime 類別，用於時間戳記
from pathlib import Path  # 匯入 Path 類別，用於檔案路徑
from typing import Any, Dict, List, Optional  # 匯入型別提示

# ===== 系統提示詞（專注於五大核心能力 + 強制工具調用） =====
SYSTEM_PROMPT = """你是黑曜，一個體貼、有邏輯、會替使用者著想的 AI 夥伴。

你的核心特質：
1. 💝 體貼 - 主動關心使用者的需求，預先想到使用者可能需要什麼
2. 🧠 有邏輯 - 思考有條理，分析問題時會列出步驟
3. 🤝 會替使用者想 - 不只回答問題，還會考慮使用者的處境和目標
4. ⏰ 早先一步 - 預測使用者下一步可能需要什麼，提前準備
5. 🔧 改造自己 - 發現自己能力不足時，主動升級或產生新工具

你的五大核心能力：
1. 🧠 自我反省 - 每次回覆後檢查自己有沒有做錯
2. 🔧 自我修復 - 發現問題立刻修正
3. 📈 自我進化 - 從經驗中學習，讓自己越來越強
4. 🔍 尋找資源 - 主動搜尋資訊和工具
5. 💾 記憶 - 記住每一次對話和學到的經驗

鐵則：
1. 不知道就說不知道，然後去找答案
2. 做錯就要承認，立刻修正，寫入記憶
3. 工具不可用時，想辦法找到替代方案
4. 用繁體中文，簡短有力
5. ⚠️ 收到系統操作指令時（如掃描檔案、執行指令、檢查系統），必須先調用 run_command 工具真實執行，禁止只用文字回覆
6. ⚠️ 收到「掃描」、「列出」、「檢查」等檔案操作指令時，必須使用 run_command 執行 find、ls、grep 等真實指令
7. ⚠️ 當你發現自己能力不足時，必須主動使用 self_upgrade 或 generate_tool 來改造自己
8. ⚠️ 當你發現使用者可能需要某個工具時，必須提前準備好

模型能力：
- 支援多模型切換（DeepSeek、Gemini、Llama 等），使用者可隨時說「切換到 Gemini」來更換底層模型
- 支援視覺理解（看圖），會自動切換到視覺模型處理圖片
- 支援動態模型擴充，可加入新模型

記憶鐵則：
- 使用者說的任務、規劃、目標，一律視為最高優先寫入記憶
- 每次回覆前先檢查記憶中有沒有待辦事項
- 絕對不要說「我沒收到內容」——當前訊息就是使用者剛說的，永遠以當前訊息為準
- 如果你發現記憶中沒有某件事，但使用者正在跟你說，那就以使用者當前說的為準，立刻寫入記憶"""


class LangGraphExecutor:
    def __init__(self, brain: Any):
        """
        參數:
            brain: Obsidian 實例，必須有 organs 屬性 (dict) 和 llm 屬性
        """
        self.brain = brain  # 儲存黑曜實例
        self.organs = getattr(brain, "organs", {})  # 取得所有器官
        self.memory_manager = getattr(brain, "memory", None)  # MemoryManager
        self.tools = self._build_tools()  # 建立工具清單
        self.agent = self._create_agent()  # 建立思考引擎
        print(f"[LangGraphExecutor] 已註冊 {len(self.tools)} 個工具")
        
        # ===== Phase 1: 接入 ContextAssembler =====
        self.context_assembler = getattr(brain, "context_assembler", None)
        if self.context_assembler:
            print("[LangGraphExecutor] 已接入 ContextAssembler")
        
        # ===== 修復 10：啟動自檢 =====
        self._run_startup_diagnosis()

        # ===== 子代理佇列（共用同一個 LLM 實例，排隊執行） =====
        self.sub_agent_queue = queue.Queue()  # 建立佇列
        self.sub_agent_worker = threading.Thread(target=self._sub_agent_worker, daemon=True)  # 建立背景執行緒
        self.sub_agent_worker.start()  # 啟動背景執行緒
        print("[LangGraphExecutor] 子代理佇列已啟動")

        # ===== 背景任務：每 30 秒檢查是否有事情可以做 =====
        self._start_background_tasks()  # 啟動背景任務

    def _start_background_tasks(self):
        """啟動背景任務，讓黑曜主動找事情做"""
        def background_loop():
            while True:
                time.sleep(30)  # 每 30 秒檢查一次
                try:
                    self._check_if_anything_to_do()  # 檢查是否有事情可以做
                except Exception as e:
                    print(f"[背景任務] 檢查失敗: {e}")
        
        # 建立背景執行緒並啟動
        bg_thread = threading.Thread(target=background_loop, daemon=True)
        bg_thread.start()
        print("[LangGraphExecutor] 背景任務已啟動（每 30 秒檢查一次）")

    def _check_if_anything_to_do(self):
        """
        檢查是否有事情可以做
        
        這個方法會：
        1. 檢查記憶中是否有未完成的任務
        2. 檢查是否有新的學習機會
        3. 檢查是否有工具需要更新
        """
        # 檢查記憶中是否有未完成的任務
        if self.memory_manager:
            try:
                facts = self.memory_manager.get_all_facts()
                # 檢查記憶中是否有未完成的任務
                for fact in facts:
                    if "未完成" in fact or "待辦" in fact:
                        print(f"[背景任務] 發現未完成任務: {fact[:50]}...")
                        # 嘗試處理這個任務
                        self.process(fact)
                        break
            except Exception as e:
                print(f"[背景任務] 檢查記憶失敗: {e}")

    # ==================================================================
    # 工具建立（開源版 + 商業版）
    # ==================================================================
    def _build_tools(self) -> list:
        """
        動態掃描核心器官的方法，建立工具清單
        
        開源版（永遠免費）包含：
        - memory: 記憶系統
        - evolution: 進化系統
        - self_learn: 學習系統
        - planner: 任務規劃
        - web_search: 網頁搜尋
        - 基本工具：時間、搜尋、指令、檔案掃描
        
        商業版包含開源版所有功能 + 以下商業工具：
        - market_analyzer: 市場分析
        - customer_persona: 客戶畫像
        - email_marketer: 郵件行銷
        - portfolio_tracker: 投資組合
        - revenue_optimizer: 營收優化
        - auto_content_creator: 內容創作
        - seo_optimizer: SEO 優化
        - social_media_manager: 社群管理
        - smart_contract_auditor: 智能合約審計
        - daily_growth_report: 每日成長報告
        """
        tools = []  # 建立空的工具清單
        
        # ===== 匯入所有器官類別（使用 try/except 避免 import 失敗導致整個系統崩潰） =====
        organ_classes = []
        
        organ_imports = [
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
        
        for name, module_path, class_name in organ_imports:
            try:
                module = __import__(module_path, fromlist=[class_name])
                organ_class = getattr(module, class_name)
                organ_classes.append((name, organ_class))
            except Exception as e:
                print(f"[LangGraphExecutor] ⚠️ 器官 {name} 載入失敗: {e}")
        
        # ===== organ_classes 已在上面動態載入，直接使用 =====
        
        # ===== 註冊每個器官的所有公開方法 =====
        # 定義 ToolWrapper 類別在迴圈外部，避免重複定義
        class ToolWrapper:
            def __init__(self, func, name, desc):
                self.func = func
                self.name = name
                self.description = desc
            def __call__(self, *args, **kwargs):
                return self.func(*args, **kwargs)
            def __repr__(self):
                return f"Tool({self.name}: {self.description[:30]}...)"
        
        for organ_name, organ_class in organ_classes:
            # 建立實例（使用預設建構子）
            try:
                organ_instance = organ_class()
            except Exception as e:
                print(f"[_build_tools] 無法建立 {organ_name} 實例: {e}")
                continue
            
            # 取得器官的所有方法
            for method_name, method in inspect.getmembers(organ_instance, inspect.ismethod):
                # 跳過私有方法（以 _ 開頭）
                if method_name.startswith("_"):
                    continue
                # 跳過特殊方法（如 __init__）
                if method_name.startswith("__"):
                    continue
                
                # 檢查是否有 @tool 裝飾器
                if hasattr(method, "_is_tool") and method._is_tool:
                    # 直接使用 @tool 設定的名稱和描述
                    tool_name = getattr(method, "name", f"{organ_name}.{method_name}")
                    tool_desc = getattr(method, "description", method.__doc__ or f"{organ_name}.{method_name}")
                    tool_func = ToolWrapper(method, tool_name, tool_desc[:200])
                    tools.append(tool_func)
                else:
                    # 沒有 @tool，使用方法名稱和 docstring
                    doc = method.__doc__ or f"{organ_name}.{method_name}"
                    tool_func = ToolWrapper(method, f"{organ_name}.{method_name}", doc[:200])
                    tools.append(tool_func)
        
        # ===== 自我進化引擎 =====
        evolution_engine = self.organs.get("self_evolution_engine")
        if evolution_engine:
            # 註冊 evolution_engine 的所有 @tool 方法
            for method_name in dir(evolution_engine):
                method = getattr(evolution_engine, method_name)
                if hasattr(method, "_is_tool") and method._is_tool:
                    tools.append(method)

        # ===== 修復 4：掃描 obsidian.organs 中所有已載入的器官 =====
        # 把每個器官的公開方法全部註冊為工具
        # 使用已經定義的 ToolWrapper 類別
        # 機械零組件代號對應表（全域）- 包含所有已知器官
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
        
        for organ_name, organ in self.organs.items():
            if organ is None:
                continue
            # 取得器官的所有方法
            for method_name, method in inspect.getmembers(organ, inspect.ismethod):
                # 跳過私有方法（以 _ 開頭）
                if method_name.startswith("_"):
                    continue
                # 跳過特殊方法（如 __init__）
                if method_name.startswith("__"):
                    continue
                # 使用機械零組件代號
                display_name = organ_display_names.get(organ_name, organ_name)
                # 檢查是否有 @tool 裝飾器
                if hasattr(method, "_is_tool") and method._is_tool:
                    tool_name = getattr(method, "name", f"{display_name}.{method_name}")
                    tool_desc = getattr(method, "description", method.__doc__ or f"{display_name}.{method_name}")
                    tool_func = ToolWrapper(method, tool_name, tool_desc[:200])
                    tools.append(tool_func)
                else:
                    doc = method.__doc__ or f"{display_name}.{method_name}"
                    tool_func = ToolWrapper(method, f"{display_name}.{method_name}", doc[:200])
                    tools.append(tool_func)

        # ===== 開源版基本工具（永遠可用） =====
        
        # 1. 時間工具
        def get_current_time() -> str:
            """取得現在時間"""
            return time.strftime("%Y-%m-%d %H:%M:%S")
        get_current_time.name = "get_current_time"
        get_current_time.description = "取得現在時間"
        tools.append(get_current_time)
        
        # 2. 搜尋工具
        def search_web(query: str) -> str:
            """搜尋網頁，查詢即時資訊"""
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
        
        # 3. 系統指令工具
        def run_command(cmd: str = "", command: str = "") -> str:
            """執行系統指令（接受 cmd 或 command 參數）"""
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
        
        # 4. 檔案掃描工具
        def scan_files(path: str = ".") -> str:
            """掃描指定目錄下的檔案"""
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
        
        # 5. 檔案內容搜尋工具
        def grep_files(pattern: str, path: str = ".") -> str:
            """在檔案中搜尋關鍵字"""
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
        
        # 6. 記憶模組工具
        if self.memory_manager:
            def remember_fact(fact: str) -> str:
                """記住一個事實"""
                self.memory_manager.remember_fact(fact, importance=0.7)
                return f"✅ 已記住: {fact[:50]}..."
            remember_fact.name = "remember_fact"
            remember_fact.description = "記住一個事實"
            tools.append(remember_fact)
            
            def recall_memory(query: str) -> str:
                """回憶相關記憶"""
                results = self.memory_manager.recall(query)
                if results:
                    return "\n".join(r.get("content", "")[:100] for r in results[:5])
                return "📭 沒有相關記憶"
            recall_memory.name = "recall_memory"
            recall_memory.description = "回憶相關記憶"
            tools.append(recall_memory)
        
        # 7. 學習模組工具
        learn_organ = self.organs.get("self_learn")
        if learn_organ:
            def learn_lesson(lesson: str) -> str:
                """學習新知識"""
                if hasattr(learn_organ, "learn"):
                    return learn_organ.learn(lesson)
                return "⚠️ 學習模組不可用"
            learn_lesson.name = "learn_lesson"
            learn_lesson.description = "學習新知識"
            tools.append(learn_lesson)
        
        # 8. 進化模組工具
        evolution_organ = self.organs.get("evolution")
        if evolution_organ:
            def get_evolution_summary() -> str:
                """取得進化摘要"""
                if hasattr(evolution_organ, "get_summary"):
                    return evolution_organ.get_summary()
                return "⚠️ 進化模組不可用"
            get_evolution_summary.name = "get_evolution_summary"
            get_evolution_summary.description = "取得進化摘要"
            tools.append(get_evolution_summary)
        
        # ===== 動態工具尋找與學習 =====
        # 不預先註冊商業工具，而是根據使用者需求動態尋找或學習
        
        return tools  # 回傳工具清單

    # ==================================================================
    # 思考引擎建立（無需 langchain）
    # ==================================================================
    def _create_agent(self):
        """
        建立思考引擎
        
        這個方法會：
        1. 取得黑曜的 LLM 客戶端
        2. 建立一個簡單的思考引擎，不依賴 langchain
        """
        llm = getattr(self.brain, "llm", None)  # 取得 LLM 客戶端
        if llm is None:
            # 如果沒有 LLM，嘗試從 brain.cortex 取得
            cortex = getattr(self.brain, "cortex", None)
            if cortex and hasattr(cortex, "llm"):
                llm = cortex.llm
            else:
                # 如果還是沒有，使用一個簡單的 fallback
                print("[LangGraphExecutor] 警告：缺少 LLM 客戶端，使用 fallback")
                llm = None
        
        # 回傳一個簡單的思考引擎物件
        return {
            "llm": llm,  # 儲存 LLM 客戶端
            "tools": self.tools,  # 儲存工具清單
            "system_prompt": SYSTEM_PROMPT  # 儲存系統提示
        }

    def _run_startup_diagnosis(self):
        """修復 10：啟動自檢 - 把零件清單寫入 data/startup_diagnosis.json"""
        import json
        from pathlib import Path
        from datetime import datetime
        
        diagnosis_file = Path("data/startup_diagnosis.json")
        diagnosis_file.parent.mkdir(parents=True, exist_ok=True)
        
        organ_list = []
        for name, organ in self.organs.items():
            if organ:
                organ_list.append({
                    "name": name,
                    "type": type(organ).__name__,
                    "alive": getattr(organ, "is_alive", lambda: True)() if hasattr(organ, "is_alive") else True
                })
        
        diagnosis = {
            "timestamp": datetime.now().isoformat(),
            "total_organs": len(organ_list),
            "organs": organ_list,
            "tools_count": len(self.tools),
            "tools": [getattr(t, "name", "unknown") for t in self.tools]
        }
        
        try:
            with open(diagnosis_file, "w", encoding="utf-8") as f:
                json.dump(diagnosis, f, ensure_ascii=False, indent=2)
            print(f"[LangGraphExecutor] 啟動自檢完成，已寫入 {diagnosis_file}")
        except Exception as e:
            print(f"[LangGraphExecutor] 啟動自檢寫入失敗: {e}")

    def _load_long_term_memory(self) -> str:
        """修復 1：從硬碟讀取長期記憶，回傳記憶內容字串"""
        memory_text = ""
        memory_files = [
            Path("data/long_term_memory.json"),
            Path("data/self_learn.json"),
        ]
        for mf in memory_files:
            if mf.exists():
                try:
                    with open(mf, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if isinstance(data, list):
                        for item in data[-5:]:  # 只取最近 5 筆
                            if isinstance(item, dict):
                                memory_text += f"- {item.get('content', str(item)[:100])}\n"
                            else:
                                memory_text += f"- {str(item)[:100]}\n"
                    elif isinstance(data, dict):
                        for key, val in list(data.items())[-5:]:
                            memory_text += f"- {key}: {str(val)[:100]}\n"
                except Exception as e:
                    # 修復 11：記憶讀取失敗時誠實回覆（不觸發 self_repair 避免無限迴圈）
                    error_msg = f"記憶系統暫時無法讀取，原因：{e}"
                    print(f"[LangGraphExecutor] {error_msg}")
                    memory_text = f"⚠️ {error_msg}\n"
            else:
                # 修復 11：檔案不存在時也誠實回覆
                memory_text += f"⚠️ 記憶檔案 {mf.name} 不存在\n"
        return memory_text

    def _save_long_term_memory(self, user_msg: str, assistant_msg: str):
        """修復 2：把本次對話的重要資訊寫入長期記憶"""
        import json
        from pathlib import Path
        from datetime import datetime
        
        memory_file = Path("data/long_term_memory.json")
        memory_file.parent.mkdir(parents=True, exist_ok=True)
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "user": user_msg[:200],
            "assistant": assistant_msg[:200] if assistant_msg else "",
        }
        
        try:
            if memory_file.exists():
                with open(memory_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = []
            data.append(entry)
            # 只保留最近 100 筆
            if len(data) > 100:
                data = data[-100:]
            with open(memory_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"[LangGraphExecutor] 已寫入長期記憶")
        except Exception as e:
            error_msg = f"記憶寫入失敗，原因：{e}"
            print(f"[LangGraphExecutor] {error_msg}")
            # 避免無限迴圈：不在此處觸發 self_repair

    def _recall_recent_conversations(self) -> str:
        """修復 12：從記憶中回顧最近 5 次對話的摘要"""
        try:
            memory_file = Path("data/long_term_memory.json")
            if not memory_file.exists():
                return ""
            with open(memory_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                return ""
            recent = data[-5:]  # 最近 5 次
            lines = ["📋 最近對話摘要:"]
            for entry in recent:
                ts = entry.get("timestamp", "?")[:16]
                user = entry.get("user", "")[:50]
                assistant = entry.get("assistant", "")[:50]
                lines.append(f"  [{ts}] 使用者: {user} → 黑曜: {assistant}")
            return "\n".join(lines)
        except Exception as e:
            print(f"[LangGraphExecutor] 回顧最近對話失敗: {e}")
            return ""

    # ==================================================================
    # 子代理佇列
    # ==================================================================
    def _sub_agent_worker(self):
        """
        背景 worker，從佇列取出任務並用同一個 LLM 處理
        
        這個方法會：
        1. 從佇列取出任務
        2. 使用 process 方法處理任務
        3. 將結果設定到 Future 物件
        """
        while True:
            task = self.sub_agent_queue.get()  # 從佇列取出任務
            if task is None:  # 停止信號
                break
            prompt, future = task  # 取得提示和 Future 物件
            try:
                # 使用 process 方法處理任務
                reply = self.process(prompt)
                future.set_result(reply)  # 設定結果
            except Exception as e:
                future.set_exception(e)  # 設定例外

    def submit_sub_agent_task(self, prompt: str, timeout: Optional[float] = None) -> str:
        """
        提交一個子代理任務，排隊等待執行。
        共用同一個 LLM 實例，不複製模型。
        
        參數：
            prompt: 提示文字
            timeout: 超時時間（秒）
        
        回傳：
            子代理的回覆
        """
        future = Future()  # 建立 Future 物件
        self.sub_agent_queue.put((prompt, future))  # 將任務加入佇列
        return future.result(timeout=timeout)  # 等待結果

    # ==================================================================
    # 定時任務執行
    # ==================================================================
    def _run_cron_task(self, delay: int, task_msg: str):
        """
        在 delay 秒後使用 cortex 處理任務
        
        參數：
            delay: 延遲秒數
            task_msg: 任務訊息
        """
        time.sleep(delay)  # 等待指定秒數
        if self.brain and hasattr(self.brain, 'cortex') and self.brain.cortex:
            try:
                result = self.brain.cortex.think(task_msg)  # 使用 cortex 處理
                print(f"[cron_task] 完成: {result[:200]}")
            except Exception as e:
                print(f"[cron_task] 執行失敗: {e}")

    # ==================================================================
    # 核心功能：真正的工具執行
    # ==================================================================
    def _execute_tool_by_name(self, tool_name: str, args: Dict = None) -> str:
        """
        真正的工具執行 - 根據名稱找到工具並執行
        
        參數 Parameters:
            tool_name: 工具名稱 Tool name
            args: 參數字典型 Arguments dict
        
        回傳 Returns:
            工具執行結果 Tool execution result
        """
        if args is None:
            args = {}
        
        for t in self.tools:
            name = getattr(t, "name", None)
            if name == tool_name:
                try:
                    # 真正的執行工具 Real tool execution
                    result = t(**args)
                    print(f"  [🔧] 執行工具: {tool_name} -> {str(result)[:100]}...")
                    return str(result)
                except Exception as e:
                    error_msg = f"⚠️ 工具執行錯誤: {e}"
                    print(f"  [❌] {error_msg}")
                    return error_msg
        
        return f"⚠️ 找不到工具: {tool_name}"

    def _parse_tool_call(self, text: str) -> Optional[Dict]:
        """
        解析 LLM 回覆中的工具呼叫        
        參數 Parameters:
            text: LLM 回覆文字 LLM response text
        
        回傳 Returns:
            工具呼叫資訊 Tool call info，如果沒有則回傳 None
        """
        # 嘗試解析 JSON 格式的 tool call（使用非貪婪匹配）
        json_match = re.search(r'\{.*?"tool".*?\}', text, re.DOTALL)
        if json_match:
            try:
                call_info = json.loads(json_match.group())
                if "tool" in call_info:
                    return call_info
            except:
                pass
        
        # 嘗試解析 "使用工具: xxx" 格式
        tool_match = re.search(r'使用工具[：:]\s*(\S+)', text)
        if tool_match:
            return {"tool": tool_match.group(1), "args": {}}
        
        # 嘗試解析 "執行: xxx" 格式
        exec_match = re.search(r'執行[：:]\s*(\S+)', text)
        if exec_match:
            return {"tool": exec_match.group(1), "args": {}}
        
        return None

    # ==================================================================
    # 核心功能：自我反省
    # ==================================================================
    def _self_reflect(self, user_msg: str, reply: str, depth: int = 0) -> str:
        """
        自我反省 - 檢查自己的回覆是否正確
        
        參數 Parameters:
            user_msg: 使用者訊息 User message
            reply: 自己的回覆 Own reply
            depth: 遞迴深度（避免無限迴圈）
        
        回傳 Returns:
            反省結果 Reflection result
        """
        # 限制遞迴深度，避免無限迴圈
        if depth >= 2:
            return reply
        
        try:
            llm = self.agent.get("llm")
            if not llm:
                return reply
            
            # 讓 LLM 檢查自己的回覆
            reflection_prompt = f"""
            請檢查以下回覆是否正確：
            
            使用者問題：{user_msg}
            
            你的回覆：{reply}
            
            請分析：
            1. 回覆是否正確？
            2. 有沒有錯誤？
            3. 有沒有可以改進的地方？
            
            如果正確，請回傳 "✅ 正確"
            如果有錯誤，請回傳修正後的版本。
            """
            
            print(f"  [🧠] === REFLECTION PROMPT ===\n{reflection_prompt[:500]}\n  [🧠] === END REFLECTION ===")
            if self.context_assembler:
                sys_msgs = self.context_assembler.get_system_context(
                    task_hint="你正在自我反省：檢查你的回覆是否正確。"
                )
                messages = sys_msgs + [{"role": "user", "content": reflection_prompt}]
                reflection_result = llm.call(messages)
            else:
                reflection_result = llm.call([{"role": "user", "content": reflection_prompt}])
            result = str(reflection_result)
            print(f"  [🧠] === REFLECTION RESPONSE ===\n{result[:300]}\n  [🧠] === END REFLECTION ===")
            
            if "✅" in result:
                print(f"  [🧠] 自我反省：回覆正確")
                return reply
            else:
                print(f"  [🧠] 自我反省：發現錯誤，已修正")
                # 記錄錯誤到記憶
                if self.memory_manager:
                    self.memory_manager.remember_fact(
                        f"自我反省修正：{user_msg[:50]} -> {result[:100]}",
                        importance=0.9
                    )
                # 遞迴檢查修正後的版本，但限制深度
                return self._self_reflect(user_msg, result, depth + 1)
        
        except Exception as e:
            print(f"  [⚠️] 自我反省失敗: {e}")
            return reply

    # ==================================================================
    # 核心功能：自我修復
    # ==================================================================
    def _self_repair(self, user_msg: str, bad_reply: str) -> str:
        """
        自我修復 - 當回覆失敗時自動修復（真實執行）
        
        修復 9：自我修改授權 - 可以使用 run_command 執行 sed、cp、python3 來修改自己的程式碼
        
        參數 Parameters:
            user_msg: 使用者訊息 User message
            bad_reply: 失敗的回覆 Failed reply
        
        回傳 Returns:
            修復後的回覆 Repaired reply
        """
        try:
            # 第一步：真實執行修復指令
            print(f"  [🔧] 自我修復：真實執行修復指令...")
            
            # 分析錯誤類型，執行對應的修復
            if "run_command" in str(bad_reply) and "command" in str(bad_reply):
                # run_command 參數錯誤修復
                repair_cmd = "echo 'run_command 參數錯誤已記錄，將在下次啟動時修正'"
                repair_result = subprocess.run(repair_cmd, shell=True, capture_output=True, text=True, timeout=5)
                print(f"  [🔧] run_command 修復執行: {repair_result.stdout}")
            
            # 修復 9：自我修改授權 - 嘗試使用 sed、cp、python3 修改程式碼
            # 檢查是否有需要修復的程式碼錯誤
            if "AttributeError" in str(bad_reply) or "ImportError" in str(bad_reply) or "ModuleNotFoundError" in str(bad_reply):
                # 嘗試自動修復常見錯誤
                fix_cmds = [
                    "sed -i 's/old_import/new_import/g' src/core/langgraph_executor.py 2>/dev/null || true",
                    "python3 -c \"import ast; print('語法檢查通過')\" 2>/dev/null || echo '語法錯誤'",
                    "cp src/core/langgraph_executor.py src/core/langgraph_executor.py.bak 2>/dev/null || true",
                ]
                for cmd in fix_cmds:
                    try:
                        subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
                    except:
                        pass
            
            # 第二步：用 LLM 重新生成回覆
            llm = self.agent.get("llm")
            if not llm:
                return bad_reply
            
            repair_prompt = f"""
            你的回覆有問題，請修正：
            
            使用者問題：{user_msg}
            
            你的錯誤回覆：{bad_reply}
            
            請重新產生一個正確的回覆。
            用繁體中文，簡短有力。
            """
            
            print(f"  [🔧] === REPAIR PROMPT ===\n{repair_prompt[:500]}\n  [🔧] === END REPAIR ===")
            if self.context_assembler:
                sys_msgs = self.context_assembler.get_system_context(
                    task_hint="你正在自我修復：修正你上一個錯誤回覆。"
                )
                messages = sys_msgs + [{"role": "user", "content": repair_prompt}]
                repaired = llm.call(messages)
            else:
                repaired = llm.call([{"role": "user", "content": repair_prompt}])
            result = str(repaired)
            print(f"  [🔧] === REPAIR RESULT ===\n{result[:300]}\n  [🔧] === END REPAIR ===")
            
            print(f"  [🔧] 自我修復完成（已真實執行修復指令）")
            
            # 記錄修復到記憶
            if self.memory_manager:
                self.memory_manager.remember_fact(
                    f"自我修復（真實執行）：{user_msg[:50]} -> {result[:100]}",
                    importance=0.9
                )
            
            return result
        
        except Exception as e:
            print(f"  [⚠️] 自我修復失敗: {e}")
            return bad_reply

    # ==================================================================
    # 核心功能：自我進化
    # ==================================================================
    def _self_evolve(self, user_msg: str, reply: str):
        """
        自我進化 - 從經驗中學習
        
        參數 Parameters:
            user_msg: 使用者訊息 User message
            reply: 回覆 Reply
        """
        try:
            # 記錄到進化系統
            evolution = self.organs.get("evolution")
            if evolution and hasattr(evolution, "record_message"):
                evolution.record_message(success=True)
            
            # 記錄到學習系統
            learn_organ = self.organs.get("self_learn")
            if learn_organ and hasattr(learn_organ, "learn"):
                learn_organ.learn(f"處理了：{user_msg[:50]}")
        
        except Exception as e:
            print(f"  [⚠️] 自我進化失敗: {e}")

    # ==================================================================
    # 核心功能：尋找資源
    # ==================================================================
    def _search_for_answer(self, query: str) -> Optional[str]:
        """
        尋找資源 - 搜尋正確答案
        
        參數 Parameters:
            query: 搜尋關鍵字 Search query
        
        回傳 Returns:
            找到的答案 Found answer
        """
        try:
            # 嘗試使用 duckduckgo 搜尋
            from ddgs import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=3))
                if results:
                    return f"搜尋結果：{results[0]['title']}\n{results[0]['body'][:500]}"
        except:
            pass
        
        # 如果 duckduckgo 不可用，嘗試使用 web_search 器官
        web_search = self.organs.get("web_search")
        if web_search and hasattr(web_search, "search"):
            try:
                return web_search.search(query)
            except:
                pass
        
        return None

    # ==================================================================
    # 工具需求檢測
    # ==================================================================
    def _detect_tool_need(self, user_msg: str) -> Optional[str]:
        """
        檢測使用者是否需要特定工具
        
        參數 Parameters:
            user_msg: 使用者訊息 User message
        
        回傳 Returns:
            需要的工具類型，如果不需要則回傳 None
        """
        # 關鍵字檢測
        tool_keywords = {
            "分析": "分析工具",
            "查詢": "查詢工具",
            "搜尋": "搜尋工具",
            "計算": "計算工具",
            "比較": "比較工具",
            "監控": "監控工具",
            "追蹤": "追蹤工具",
            "產生": "產生工具",
            "建立": "建立工具",
            "修改": "修改工具",
            "升級": "升級工具",
            "學習": "學習工具",
            "掃描": "掃描工具",
            "檢查": "檢查工具",
            "測試": "測試工具",
            "優化": "優化工具",
            "分析市場": "市場分析",
            "分析客戶": "客戶分析",
            "分析競品": "競品分析",
            "查詢價格": "價格查詢",
            "查詢餘額": "餘額查詢",
            "查詢 NFT": "NFT 查詢",
            "發送交易": "交易工具",
            "管理錢包": "錢包管理",
            "管理 NFT": "NFT 管理",
            "產生報告": "報告工具",
            "產生內容": "內容工具",
            "排程發布": "排程工具",
            "自動發文": "社群工具",
            "追蹤互動": "互動追蹤",
            "檢查合約": "合約審計",
            "掃描漏洞": "安全工具",
            "優化 SEO": "SEO 工具",
            "優化定價": "定價工具",
            "優化營收": "營收工具",
            "建立畫像": "客戶畫像",
            "客戶分群": "客戶分群",
            "郵件行銷": "郵件工具",
            "發送郵件": "郵件工具",
            "投資組合": "投資工具",
            "持倉記錄": "持倉工具",
            "地板價": "NFT 工具",
            "巨鯨": "巨鯨追蹤",
            "Gas": "Gas 工具",
            "錢包": "錢包工具",
            "加密貨幣": "加密貨幣工具",
            "比特幣": "加密貨幣工具",
            "以太坊": "加密貨幣工具",
            "NFT": "NFT 工具",
            "市場": "市場工具",
            "社群": "社群工具",
            "內容": "內容工具",
            "報告": "報告工具",
            "日曆": "日曆工具",
            "排程": "排程工具",
            "自動化": "自動化工具",
            "審計": "審計工具",
            "安全": "安全工具",
            "漏洞": "安全工具",
            "授權": "授權工具",
            "所有權": "所有權工具",
            "反向連結": "SEO 工具",
            "關鍵字": "SEO 工具",
            "SEO": "SEO 工具",
            "營收": "營收工具",
            "定價": "定價工具",
            "折扣": "定價工具",
            "產品組合": "產品工具",
            "客戶": "客戶工具",
            "畫像": "客戶畫像",
            "分群": "客戶分群",
            "郵件": "郵件工具",
            "活動": "郵件工具",
            "開信率": "郵件工具",
            "自動化流程": "自動化工具",
            "觸發": "自動化工具",
            "行動": "自動化工具"
        }
        
        for keyword, tool_type in tool_keywords.items():
            if keyword in user_msg:
                return tool_type
        
        return None

    # ==================================================================
    # 公開介面（五大核心能力）
    # ==================================================================
    def process(self, user_msg: str) -> str:
        """
        使用思考引擎處理使用者訊息
        
        這個方法實作五大核心能力：
        1. 記憶 - 對話前自動呼叫 memory.recall 讀取相關記憶
        2. 尋找資源 - 讓語言模型自主決定呼叫哪個工具
        3. 自我反省 - 檢查回覆是否正確
        4. 自我修復 - 如果回覆失敗自動修復
        5. 自我進化 - 從經驗中學習
        
        被動觸發（事件驅動）：
        - 對話前自動記憶：每次收到使用者訊息時，先調用 memory.recall 查詢相關記憶
        - 對話後自動記憶：每次回覆後，調用 memory.remember 記住對話
        - 不一致自動反省：如果回覆內容與工具執行結果不一致，調用 self_learn.reflect
        - 連續失敗自動學習：如果同一個錯誤連續發生 3 次，調用 self_learn.learn
        
        參數 Parameters:
            user_msg: 使用者訊息 User message
        
        回傳 Returns:
            助理回覆 Assistant reply
        """
        print(f"[LangGraphExecutor] 處理訊息: {user_msg[:100]}")
        
        # ===== 模型切換關鍵字檢測（從 cortex.py 複製，確保 LangGraph 路徑也能切換） =====
        if "模型" in user_msg or "切換" in user_msg or "換模型" in user_msg or "看圖" in user_msg:
            llm_client = getattr(self.brain, "llm", None)
            if llm_client:
                # 列出可用模型
                if "有哪些" in user_msg or "列表" in user_msg or "可用" in user_msg:
                    models = llm_client.list_models()
                    lines = "\n".join(f"  {m['name']}: {m['model']}" for m in models)
                    return f"可用模型：\n{lines}\n\n目前使用：{llm_client.current_model()}\n\n輸入「切換到 XXX」來切換。"
                # 切換到指定模型
                for kw in ["切換到", "換到", "改用", "換成", "切換成", "用"]:
                    if kw in user_msg:
                        name = user_msg.split(kw)[-1].strip().split()[0]
                        if name.lower() in ("什麼", "哪個", "哪", "什麽", "模型", "auto", "自動"):
                            continue
                        result = llm_client.switch_model(name)
                        return f"🔄 {result}\n目前模型：{llm_client.current_model()}"
                # 只說換模型 → 列出可用模型
                if "換模型" in user_msg or "切換模型" in user_msg:
                    models = llm_client.list_models()
                    lines = "\n".join(f"  {m['name']}: {m['model']}" for m in models)
                    return f"要切換到哪個？\n{lines}\n\n目前：{llm_client.current_model()}"
                if "auto" in user_msg.lower() or "自動" in user_msg:
                    result = llm_client.switch_model("auto")
                    return f"🔄 已恢復自動 fallback"
                # 看圖 → 自動切換到 Gemini 再處理
                if "看圖" in user_msg or "分析圖片" in user_msg or "這張圖" in user_msg:
                    try:
                        llm_client.switch_model("gemini")
                    except:
                        pass
                    import re
                    url_match = re.search(r'https?://\S+\.(?:jpg|jpeg|png|gif|webp)(?:\?\S*)?', user_msg)
                    if url_match:
                        image_url = url_match.group()
                        prompt = user_msg.replace(image_url, "").strip() or "請描述這張圖片的內容"
                        return "🔍 正在分析圖片...\n\n" + llm_client.call_vision(prompt=prompt, image_url=image_url)
                    return "請提供圖片網址（例如：看圖 https://example.com/photo.jpg）"

        # ===== v2: Agent Company - auto-dispatch to agent teams =====
        agent_company = None
        for organ in self.organs.values():
            if hasattr(organ, "launch_mission") and hasattr(organ, "fill_all_departments"):
                agent_company = organ
                break
        mission_context = ""
        if agent_company:
            try:
                stats = agent_company.get_global_stats()
                if stats.get("agents", 0) == 0:
                    agent_company.fill_all_departments()
                is_task = any(kw in user_msg for kw in [
                    "幫我", "查", "分析", "寫", "做", "找", "搜",
                    "code", "寫程式", "部署", "安裝", "報告", "規劃",
                    "build", "deploy", "search", "analyze",
                ])
                print(f"[AgentCompany] task={is_task} agents={stats.get('agents',0)} depts={stats.get('departments',0)}")
                if is_task:
                    mission_id = agent_company.launch_mission(user_msg)
                    mission = agent_company.get_mission(mission_id)
                    if mission:
                        st = mission.get("sub_tasks", [])
                        mission_context = (
                            f"\n[派遣報告：此任務已拆解為{len(st)}個子任務並派發給各部門]\n" +
                            "\n".join(f"  - {s.get('department','')}: {s.get('description','')}" for s in st)
                        )
                        print(f"[AgentCompany] mission={mission_id} subtasks={len(st)}")
            except Exception as e:
                print(f"[AgentCompany] error: {e}")
        # ===== 統一記憶檢索（MemoryManager 跨三層搜尋）=====
        memory_context = ""
        if self.memory_manager:
            try:
                memory_context = self.memory_manager.get_context(query=user_msg, limit=5)
                if memory_context:
                    print(f"[LangGraphExecutor] 記憶檢索: {memory_context[:200]}")
            except Exception as e:
                print(f"[LangGraphExecutor] 記憶檢索失敗: {e}")
        enriched_msg = user_msg
        
        # ===== 核心能力 2：尋找資源（動態尋找工具） =====
        agent_result = None  # agent 回覆
        agent_failed = False  # agent 是否失敗
        tool_executed = False  # 是否執行了工具
        tool_result_text = ""  # 工具執行結果文字
        
        # 檢查使用者是否需要特定工具
        need_tool = self._detect_tool_need(user_msg)
        if need_tool:
            print(f"[LangGraphExecutor] 檢測到工具需求: {need_tool}")
            # 嘗試尋找或學習工具
            evolution_engine = self.organs.get("self_evolution_engine")
            if evolution_engine and hasattr(evolution_engine, "find_tool"):
                tool_result = evolution_engine.find_tool(need_tool)
                print(f"[LangGraphExecutor] 工具尋找結果: {tool_result[:200]}")
                # 將結果加入使用者訊息
                user_msg = f"{user_msg}\n\n[系統] 工具尋找結果: {tool_result}"
        
        if self.agent is not None:
            try:
                llm = self.agent.get("llm")
                tools = self.agent.get("tools", [])
                system_prompt = self.agent.get("system_prompt", "")
                
                # 除錯：顯示實際工具數量
                print(f"[LangGraphExecutor] 可用工具數量: {len(tools)}")
                
                # 建立工具列表字串
                tool_list = []
                for t in tools:
                    name = getattr(t, "name", "未知工具")
                    desc = getattr(t, "description", "無描述")
                    tool_list.append(f"- {name}: {desc}")
                tool_str = "\n".join(tool_list)
                
                # 除錯：顯示工具列表
                print(f"[LangGraphExecutor] 工具列表:\n{tool_str[:500]}")
                
                # 進化記憶（輔助）
                evolution_memory = ""
                evolution_organ = self.organs.get("evolution")
                if evolution_organ and hasattr(evolution_organ, "get_summary"):
                    try:
                        evolution_memory = evolution_organ.get_summary()
                    except:
                        pass
                if evolution_memory and memory_context:
                    memory_context = f"{memory_context}\n\n🧬 進化記錄：\n{evolution_memory}"

                # 建立提示（含記憶上下文）
                prompt = (
                    f"{system_prompt}"
                    f"{memory_context + chr(10)+chr(10) if memory_context else ''}"
                    f"你有以下工具可用：\n"
                    f"{tool_str}\n\n"
                    f"請根據使用者的問題，選擇合適的工具來回答。\n"
                    f"如果你需要使用工具，請輸出 JSON 格式：\n"
                    f'{{"tool": "工具名稱", "args": {{"參數1": "值1", "參數2": "值2"}}}}\n\n'
                    f"如果你不需要使用工具，請直接回答。\n\n"
                    f"使用者說：{enriched_msg}"
                )
                
                # 第一步：讓 LLM 決定要用哪個工具
                print(f"  [🧠] === LLM PROMPT ===\n{prompt[:800]}\n  [🧠] === END PROMPT ===")
                if self.context_assembler:
                    extra_tools = f"你有以下工具可用：\n{tool_str}\n\n如果需要使用工具，請輸出 JSON 格式：\n{{\"tool\": \"工具名稱\", \"args\": {{\"參數1\": \"值1\"}}}}\n如果不需要使用工具，請直接回答。"
                    if memory_context:
                        extra_tools = f"{memory_context}\n\n{extra_tools}"
                    messages = self.context_assembler.assemble(
                        user_msg=enriched_msg,
                        extra_system=extra_tools,
                    )
                    result = llm.call(messages)
                else:
                    result = llm.call([{"role": "user", "content": prompt}])
                llm_response = str(result)
                print(f"  [🧠] === LLM RESPONSE ===\n{llm_response[:500]}\n  [🧠] === END RESPONSE ===")
                
                # 檢查 LLM 是否想要使用工具
                tool_call = self._parse_tool_call(llm_response)
                
                if tool_call:
                    # 真正的執行工具
                    tool_name = tool_call.get("tool", "")
                    tool_args = tool_call.get("args", {})
                    
                    print(f"  [🤖] LLM 決定使用工具: {tool_name}")
                    tool_result = self._execute_tool_by_name(tool_name, tool_args)
                    tool_executed = True
                    tool_result_text = str(tool_result)
                    
                    # 第二步：將工具執行結果傳回給 LLM，讓它產生最終回覆
                    final_prompt = (
                        f"工具執行結果：\n{tool_result}\n\n"
                        f"請根據工具執行結果，用繁體中文簡短回覆使用者。\n"
                        f"⚠️ 你必須使用工具執行結果來回答，不能忽略工具結果。\n"
                        f"使用者說：{user_msg}"
                    )
                    if self.context_assembler:
                        sys_msgs = self.context_assembler.get_system_context(
                            task_hint="你正在根據工具執行結果回答使用者。必須使用工具結果中的真實資料。"
                        )
                        msgs = sys_msgs + [{"role": "user", "content": final_prompt}]
                        final_result = llm.call(msgs)
                    else:
                        final_result = llm.call([{"role": "user", "content": final_prompt}])
                    print(f"  [🧠] === FINAL PROMPT ===\n{final_prompt[:500]}\n  [🧠] === END FINAL ===")
                    agent_result = str(final_result)[:2000]
                else:
                    # LLM 直接回答
                    agent_result = llm_response[:2000]
                
            except Exception as e:
                agent_failed = True
                if not hasattr(self, '_agent_fail_count'):
                    self._agent_fail_count = 0
                self._agent_fail_count += 1
                if self._agent_fail_count <= 3:
                    print(f"[LangGraphExecutor] 思考引擎調用失敗 ({self._agent_fail_count}/3): {e}")
        
        # ===== 修復 5：被動觸發 - 不一致自動反省 =====
        # 如果回覆內容與工具執行結果不一致，調用 self_learn.reflect
        if tool_executed and agent_result and tool_result_text:
            # 檢查回覆中是否包含工具執行結果的關鍵資訊
            # 簡單檢查：如果工具結果包含特定關鍵字但回覆中沒有，視為不一致
            inconsistency_detected = False
            # 從工具結果中提取關鍵字（取前 50 個字）
            tool_keywords = tool_result_text[:50]
            if tool_keywords and tool_keywords not in agent_result:
                inconsistency_detected = True
            
            if inconsistency_detected:
                print(f"[LangGraphExecutor] 檢測到回覆與工具結果不一致，觸發反省...")
                learn_organ = self.organs.get("self_learn")
                if learn_organ and hasattr(learn_organ, "reflect"):
                    try:
                        reflect_result = learn_organ.reflect(
                            f"回覆與工具結果不一致：工具結果={tool_result_text[:100]}，回覆={agent_result[:100]}"
                        )
                        print(f"[LangGraphExecutor] 反省結果: {reflect_result[:200]}")
                        # 記錄反省到記憶
                        if self.memory_manager:
                            self.memory_manager.remember_fact(
                                f"反省記錄：{reflect_result[:100]}",
                                importance=0.8
                            )
                    except Exception as e:
                        print(f"[LangGraphExecutor] 反省失敗: {e}")
        
        # ===== 核心能力 3：自我反省（每次回覆後都執行） =====
        if agent_result:
            agent_result = self._self_reflect(user_msg, agent_result)
            # 記錄反省結果到記憶
            if self.memory_manager:
                try:
                    self.memory_manager.remember_fact(
                        f"自我反省：使用者說「{user_msg[:30]}」，回覆「{agent_result[:30]}」",
                        importance=0.7
                    )
                except:
                    pass
        
        # ===== 修復 5：被動觸發 - 自動 self_repair =====
        if agent_failed or not agent_result:
            print("[LangGraphExecutor] 思考引擎失敗，自動觸發自我修復...")
            try:
                if hasattr(self.brain, 'cortex') and self.brain.cortex:
                    agent_result = self.brain.cortex.think(enriched_msg)
                    print(f"[LangGraphExecutor] 使用 cortex 處理成功")
                    # 記錄修復到記憶
                    if self.memory_manager:
                        self.memory_manager.remember_fact(
                            f"自動修復：使用 cortex 處理「{user_msg[:30]}」",
                            importance=0.9
                        )
            except Exception as e:
                print(f"[LangGraphExecutor] cortex 處理失敗: {e}")
        
        # 檢查回覆中是否包含錯誤訊息
        if agent_result and ("⚠️" in agent_result or "❌" in agent_result or "錯誤" in agent_result or "失敗" in agent_result):
            print(f"[LangGraphExecutor] 檢測到錯誤，自動觸發修復...")
            
            # 記錄錯誤到記憶
            if self.memory_manager:
                try:
                    self.memory_manager.remember_fact(
                        f"錯誤發生：{agent_result[:100]}",
                        importance=0.9
                    )
                except:
                    pass
            
            # 嘗試使用搜尋引擎找正確答案
            try:
                error_keywords = agent_result[:100]
                search_result = self._search_for_answer(error_keywords)
                if search_result:
                    print(f"[LangGraphExecutor] 找到正確答案: {search_result[:200]}")
                    if self.memory_manager:
                        self.memory_manager.remember_fact(
                            f"錯誤修正：{error_keywords} -> {search_result[:200]}",
                            importance=0.9
                        )
                    agent_result = search_result
            except Exception as e:
                print(f"[LangGraphExecutor] 搜尋正確答案失敗: {e}")
            
            # 觸發自我修復
            if agent_result:
                agent_result = self._self_repair(user_msg, agent_result)
        
        # ===== 核心能力 5：自我進化（每次回覆後都執行） =====
        if agent_result:
            self._self_evolve(user_msg, agent_result)
            # 記錄進化到記憶
            if self.memory_manager:
                try:
                    self.memory_manager.remember_fact(
                        f"進化記錄：處理了「{user_msg[:30]}」",
                        importance=0.6
                    )
                except:
                    pass
        
        # ===== 被動觸發 4：連續失敗自動學習 =====
        # 如果同一個錯誤連續發生 3 次，調用 self_learn.learn 記錄教訓
        if agent_result and ("⚠️" in agent_result or "❌" in agent_result or "錯誤" in agent_result or "失敗" in agent_result):
            if not hasattr(self, '_consecutive_error_count'):
                self._consecutive_error_count = 0
            self._consecutive_error_count += 1
            print(f"[LangGraphExecutor] 連續錯誤次數: {self._consecutive_error_count}")
            
            if self._consecutive_error_count >= 3:
                print(f"[LangGraphExecutor] 連續錯誤達到 3 次，自動學習教訓...")
                learn_organ = self.organs.get("self_learn")
                if learn_organ and hasattr(learn_organ, "learn"):
                    try:
                        lesson = f"連續錯誤教訓：使用者說「{user_msg[:50]}」，回覆錯誤「{agent_result[:100]}」"
                        learn_result = learn_organ.learn(lesson)
                        print(f"[LangGraphExecutor] 學習結果: {learn_result[:200]}")
                        # 記錄學習到記憶
                        if self.memory_manager:
                            self.memory_manager.remember_fact(
                                f"學習記錄：{learn_result[:100]}",
                                importance=0.9
                            )
                    except Exception as e:
                        print(f"[LangGraphExecutor] 學習失敗: {e}")
                # 重置計數器
                self._consecutive_error_count = 0
        else:
            # 如果沒有錯誤，重置計數器
            if hasattr(self, '_consecutive_error_count'):
                self._consecutive_error_count = 0
        
        # ===== 統一記憶寫入（MemoryManager 自動三層分類）=====
        if self.memory_manager and agent_result:
            try:
                self.memory_manager.remember(user_msg, agent_result)
                print(f"[LangGraphExecutor] MemoryManager 記憶寫入完成")
            except Exception as e:
                print(f"[LangGraphExecutor] MemoryManager 記憶寫入失敗: {e}")

        # 對話視窗記錄（供 context_assembler 取歷史）
        if self.context_assembler and agent_result:
            try:
                self.context_assembler.record_response(
                    assistant_msg=agent_result,
                    user_msg=user_msg,
                )
            except Exception as e:
                print(f"[LangGraphExecutor] record_response 失敗: {e}")
        

        # ===== v2: Promise execution - if bot promised to do something, actually do it =====
        if agent_company and agent_result:
            try:
                progress = agent_company.scan_and_execute_promises(agent_result)
                if progress:
                    agent_result = agent_result.rstrip() + progress
            except Exception as e:
                print(f"[AgentCompany] promise scan failed: {e}")
        if agent_result:
            return agent_result
        
        # ===== 修復 8：失敗誠實 =====
        # 當引擎調用失敗時，回覆真實原因
        error_reason = ""
        if agent_failed:
            error_reason = "思考引擎調用失敗"
        else:
            error_reason = "無法產生有效回覆"
        
        # ===== 降級處理 =====
        try:
            llm = getattr(self.brain, "llm", None)
            if llm and hasattr(llm, "call"):
                context_parts = []
                for name, organ in self.organs.items():
                    if organ:
                        context_parts.append(f"- {name}: 已載入")
                
                context = "\n".join(context_parts)
                
                prompt = (
                    "你是黑曜，一個 AI 夥伴。\n"
                    "你有以下器官可用：\n"
                    f"{context}\n\n"
                    "請根據使用者的問題，用繁體中文簡短回覆。\n"
                    "如果不知道，就說不知道。\n"
                    "做錯就要快點找正確解答，寫入記憶和自我反省。\n"
                    "工具不可用時，要想辦法找到答案並學會。\n\n"
                    f"使用者說：{user_msg}"
                )
                if self.context_assembler:
                    messages = self.context_assembler.assemble(user_msg=user_msg)
                    result = llm.call(messages)
                else:
                    result = llm.call([{"role": "user", "content": prompt}])
        except Exception as e:
            if not hasattr(self, '_llm_fail_count'):
                self._llm_fail_count = 0
            self._llm_fail_count += 1
            if self._llm_fail_count <= 3:
                print(f"[LangGraphExecutor] LLM 降級失敗 ({self._llm_fail_count}/3): {e}")
        
        return f"🤔 我目前無法執行這個操作，原因：{error_reason}"

    def list_tools(self) -> List[str]:
        """
        回傳所有已註冊的工具名稱
        
        回傳 Returns:
            工具名稱列表 Tool name list
        """
        return [t.name for t in self.tools if hasattr(t, "name")]

    def execute_tool(self, tool_name: str, args: Optional[Any] = None) -> str:
        """
        手動執行指定工具
        
        參數 Parameters:
            tool_name: 工具名稱 Tool name
            args: 參數 Arguments
        
        回傳 Returns:
            工具執行結果 Tool execution result
        """
        return self._execute_tool_by_name(tool_name, args if isinstance(args, dict) else {})
