"""
ProactiveExecutor — 主動執行器
讓黑曜從被動等待變成主動自治 AI：
1. 定期掃描任務佇列，自動執行 pending 任務
2. 偵測系統異常，自動建立並執行修復任務
3. 透過 Telegram 回報進度
"""
import threading
import time
import json
import traceback
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

_ACTIVE_EXECUTORS: Dict[str, "ProactiveExecutor"] = {}


class ProactiveExecutor:
    """
    主動執行器 — 背景 daemon 執行緒
    """

    def __init__(self, obsidian: Any):
        self.obsidian = obsidian
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        self._last_scan_time = 0
        self._current_task_id: Optional[str] = None
        self._current_mission_id: Optional[str] = None
        self._pending_missions: Dict[str, str] = {}  # task_id -> mission_id
        self._last_report_time = 0  # 上次回報時間
        self._report_interval = 300  # 每 5 分鐘回報一次
        self._max_concurrent_missions = 5  # 同時最多 5 個任務
        self._last_suggestion_time = 0
        self._suggestion_interval = 1800  # 每 30 分鐘主動提案

        # 全域單例註冊（供 supervisor 心跳用）
        _ACTIVE_EXECUTORS["proactive_executor"] = self

    @property
    def planner(self):
        """取得 TaskTracker（任務資料來源）"""
        planners = ["task_tracker", "tasktracker", "task_planner", "taskschedulerorgan", "plannerorgan"]
        for name in planners:
            found = self.obsidian.organs.get(name)
            if found:
                return found
        # 也檢查直接屬性
        for attr in ["tasks", "task_planner", "planner"]:
            found = getattr(self.obsidian, attr, None)
            if found:
                return found
        return None

    @property
    def agents(self):
        """取得 AgentTaskRouter"""
        return (
            self.obsidian.organs.get("agent_company")
            or self.obsidian.organs.get("agentmanager")
            or getattr(self.obsidian, "agents", None)
        )

    def is_alive(self) -> bool:
        return self._running and self._thread is not None and self._thread.is_alive()

    def status(self) -> dict:
        return {
            "name": "ProactiveExecutor",
            "alive": self.is_alive(),
            "current_task": self._current_task_id,
            "current_mission": self._current_mission_id,
            "pending_missions": len(self._pending_missions),
            "last_scan": datetime.fromtimestamp(self._last_scan_time).isoformat() if self._last_scan_time else None,
        }

    # ── 啟動 / 停止 ──────────────────────────────────────────

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._loop, daemon=True, name="proactive-executor"
        )
        self._thread.start()
        print("[ProactiveExecutor] ✅ 主動執行器已啟動")

        # 註冊到 supervisor
        try:
            from core.agent_supervisor import supervisor
            supervisor.register(
                "proactive_executor",
                thread=self._thread,
                hb_interval=30,
                hb_timeout=120,
                is_restartable=False,
                is_critical=True,
            )
        except Exception:
            pass

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=10)

    # ── 主要迴圈 ────────────────────────────────────────────

    def _loop(self):
        print("[ProactiveExecutor] 🔄 主動工作迴圈啟動")
        while self._running:
            try:
                self._last_scan_time = time.time()

                # 0. 確保永遠有商業任務可做
                self._ensure_business_tasks()

                # 1. 檢查並執行 pending 任務
                self._execute_pending_tasks()

                # 2. 檢查目前 mission 的完成狀態
                self._check_mission_completions()

                # 3. 主動偵測系統問題並建立修復任務
                self._scan_for_problems()

                # 4. 定時回報進度給老大（每 5 分鐘）
                self._periodic_report()

                # 5. 主動提案：有什麼可以做的
                self._proactive_suggest()

                # 心跳
                try:
                    from core.agent_supervisor import supervisor
                    supervisor.heartbeat("proactive_executor")
                except Exception:
                    pass

            except Exception as e:
                print(f"[ProactiveExecutor] 迴圈錯誤: {e}")
                traceback.print_exc()

            time.sleep(15)

    # ── 5. 主動提案 ───────────────────────────────────────────

    def _proactive_suggest(self):
        """每 30 分鐘主動提案，看有什麼可以做的"""
        now = time.time()
        if now - self._last_suggestion_time < self._suggestion_interval:
            return
        self._last_suggestion_time = now

        planner = self.planner
        if not planner:
            return

        # 如果任務充足就不提案
        pending = [t for t in planner.tasks.values() if t.get("status") == "pending"]
        in_progress = [t for t in planner.tasks.values() if t.get("status") == "in_progress"]
        if pending or in_progress:
            return

        # 檢查 outputs/ 產出狀態
        outputs_dir = Path(__file__).parent.parent.parent / "outputs"
        ebooks = list((outputs_dir / "ebooks").glob("ch*.md")) if (outputs_dir / "ebooks").exists() else []
        children = list((outputs_dir / "children_book").glob("*.md")) if (outputs_dir / "children_book").exists() else []

        suggestions = []
        if len(ebooks) < 3:
            suggestions.append(f"📝 電子書目前只有 {len(ebooks)} 章，要繼續寫嗎？")
        if not children:
            suggestions.append("📚 童書還沒開始，要不要先做市場研究？")
        if suggestions:
            self._notify_user("💡 *黑曜提案*\n" + "\n".join(suggestions))

    # ── 1. 執行 pending 任務 ─────────────────────────────────

    def _execute_pending_tasks(self):
        planner = self.planner

        if not planner:
            return

        # 檢查是否有逾時的 mission（5 分鐘沒完成就放棄）
        self._cancel_stale_missions(timeout_seconds=300)

        # 限制同時進行中的任務數量
        active_mission_count = sum(
            1 for k in self._pending_missions
            if not str(k).endswith("_started") and isinstance(self._pending_missions.get(k), str)
        )
        if active_mission_count >= self._max_concurrent_missions:
            return

        # 取得所有 pending 任務
        pending = [
            t for t in planner.tasks.values()
            if t.get("status") == "pending"
        ]
        if not pending:
            return

        # 按優先級排序（數字越小越優先）
        pending.sort(key=lambda t: (t["priority"], t["created_at"]))

        task = pending[0]
        task["status"] = "in_progress"
        task["updated_at"] = datetime.now().isoformat()
        planner.tasks._save_to_disk()

        desc = self._build_agent_prompt(task)

        print(f"[ProactiveExecutor] 🚀 自動執行: {task['id']} - {task['title']} (優先級={task['priority']})")
        print(f"[ProactiveExecutor]    目前 {active_mission_count}/{self._max_concurrent_missions} 個任務進行中")

        # 簡單系統任務（建立目錄等）直接執行，不經過子代理
        if any(kw in task.get("title", "") for kw in ["目錄結構", "目錄"]):
            if self._try_direct_execute(task):
                return

        # 優先走 agent_company 子代理路線
        agents = self.agents
        if agents:
            stats = agents.get_global_stats() if hasattr(agents, "get_global_stats") else {}
            busy_agents = stats.get("agents_busy", 0)
            if busy_agents < 15:  # 放寬限制，允許更多子代理並行
                try:
                    mission_id = agents.launch_mission(desc)
                    if mission_id:
                        tid = str(task["id"])
                        self._pending_missions[tid] = mission_id
                        self._pending_missions[f"{tid}_started"] = time.time()
                        if self._current_task_id is None:
                            self._current_task_id = task["id"]
                            self._current_mission_id = mission_id
                        print(f"[ProactiveExecutor] → mission {mission_id}")
                        return
                except Exception as e:
                    print(f"[ProactiveExecutor] agent_company 失敗: {e}")

        # 備援：子代理不可用或失敗，直接 LLM 生成
        if self._try_direct_execute(task):
            return

        # 都失敗，恢復 pending
        planner.tasks.update_task_status(task["id"], "pending")

    def _cancel_stale_missions(self, timeout_seconds: int = 300):
        """取消超過 timeout 還沒完成的 mission，改用直接執行"""
        planner = self.planner
        if not planner:
            return

        stale_tasks = []
        for task_id, mission_id in list(self._pending_missions.items()):
            if str(task_id).endswith("_started"):
                continue
            started_key = f"{task_id}_started"
            started = self._pending_missions.get(started_key, 0)
            if isinstance(started, (int, float)) and started > 0:
                if time.time() - started > timeout_seconds:
                    stale_tasks.append(task_id)

        for task_id in stale_tasks:
            print(f"[ProactiveExecutor] ⏰ 任務 {task_id} 逾時，取消子代理，改用直接執行")
            self._pending_missions.pop(task_id, None)
            self._pending_missions.pop(f"{task_id}_started", None)
            task = planner.tasks.get(task_id, {})
            task["status"] = "pending"
            task["updated_at"] = datetime.now().isoformat()
            planner.tasks._save_to_disk()

            # 強制重置 agent_company 中對應的僵屍代理
            agents = self.agents
            if agents and hasattr(agents, 'force_reset_stale_agents'):
                agents.force_reset_stale_agents()

    def _build_agent_prompt(self, task: dict) -> str:
        """為子代理建立明確的任務指示，包含輸出路徑要求"""
        title = task.get("title", "")
        desc = task.get("description", "")

        # 找出輸出路徑
        output_path = None
        for keyword in ["存入 ", "存到 "]:
            idx = desc.find(keyword)
            if idx >= 0:
                path_str = desc[idx + len(keyword):].strip().split()[0].rstrip("。.")
                if path_str:
                    output_path = path_str
                    break

        if output_path:
            return f"【任務】{title}\n{desc}\n\n⚠️ 關鍵指令：完成後必須用 write_file 工具將內容寫入 {output_path}。不只要回覆文字，必須實際建立檔案。"
        else:
            return f"【任務】{title}\n{desc}\n\n⚠️ 關鍵指令：完成後如有產出內容，必須用 write_file 工具實際寫入檔案。不只要回覆文字。"

    # ── 0.5 直接執行內容生成任務 ───────────────────────────

    def _try_direct_execute(self, task: dict) -> bool:
        """
        商業任務執行：先研究選題可行性 → 再生成內容 → 寫入檔案。
        回傳 True 表示已處理，False 表示需走 agent_company。
        """
        title = task.get("title", "")
        desc = task.get("description", "")

        # 目錄結構建立 — 不用 LLM，直接做
        if any(kw in title for kw in ["目錄結構", "目錄"]):
            import os
            outputs_dir = Path(__file__).parent.parent.parent / "outputs"
            for subdir in ["ebooks", "children_book", "website", "research"]:
                (outputs_dir / subdir).mkdir(parents=True, exist_ok=True)
                (outputs_dir / subdir / ".gitkeep").touch()
            print("[ProactiveExecutor] ✅ 目錄結構已建立")
            planner = self.planner
            task["status"] = "completed"
            task["completed_at"] = datetime.now().isoformat()
            task["updated_at"] = datetime.now().isoformat()
            planner.tasks._save_to_disk()
            self._current_task_id = None
            return True

        # 辨識是否為內容生成任務
        content_keywords = ["寫作", "章", "生成", "研究", "報告", "建立", "產出",
                           "撰寫", "write", "generate", "create", "存入", "存到"]
        is_content_task = any(kw in title or kw in desc for kw in content_keywords)
        if not is_content_task:
            return False

        # 找出目標輸出路徑
        output_path = None
        for keyword in ["存入 ", "存到 "]:
            idx = desc.find(keyword)
            if idx >= 0:
                path_str = desc[idx + len(keyword):].strip().split()[0].rstrip("。.,")
                if path_str:
                    output_path = Path(__file__).parent.parent.parent / path_str
                    break

        if not output_path:
            if "電子書" in title or "章" in title:
                output_path = Path(__file__).parent.parent.parent / "outputs" / "ebooks" / "generated_chapter.md"
            elif "童書" in title:
                output_path = Path(__file__).parent.parent.parent / "outputs" / "children_book" / "generated.md"
            elif "網站" in title:
                output_path = Path(__file__).parent.parent.parent / "outputs" / "website" / "index.html"
            elif "研究" in title:
                output_path = Path(__file__).parent.parent.parent / "outputs" / "research" / "research.md"
            else:
                return False

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 取得 LLM
        llm = getattr(self.obsidian, "llm", None)
        if not llm:
            print("[ProactiveExecutor] ⚠️ LLM 不可用")
            return False

        try:
            model = getattr(llm, "model", "deepseek-v4-pro")

            # 步驟 1：快速收集本章所需資訊（不討論選題，主題已定）
            if "寫作" in title or "章" in title or "創作" in title:
                print(f"[ProactiveExecutor] 🔍 收集寫作素材: {title}")
                research_prompt = f"""
你是一個內容研究員。主題已定為「AI 入門指南」，不需討論選題。

任務：{title}
描述：{desc}

請用繁體中文直接輸出本章需要的知識點和素材大綱：
1. 本章要涵蓋的核心知識點（至少 5 個）
2. 初學者最常問的問題（至少 3 個）
3. 可以舉的實際例子或工具名稱
4. 直接給出本章大綱（不要問、不要給選項）

只輸出大綱和素材，不要寫完整內容。"""
                
                research_resp = llm.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": research_prompt}],
                    temperature=0.7,
                    max_tokens=1500,
                )
                research = research_resp.choices[0].message.content.strip()
                print(f"[ProactiveExecutor] 📊 選題分析完成 ({len(research)} 字)")

                # 步驟 2：根據研究結果生成實際內容
                print(f"[ProactiveExecutor] ✍️ 開始寫作: {output_path}")
                write_prompt = f"""
你是一個專業內容創作者。根據以下選題研究結果，生成完整內容。

{research}

任務：{title}
描述：{desc}

⚠️ 鐵則：
- 直接輸出要寫入檔案的完整內容，不要多餘的說明
- 內容必須充實，至少 800 字
- 如果是 Markdown 檔案用 Markdown 格式，HTML 用 HTML 格式
- 不要輸出任何「以下是內容」、「這是草稿」等開場白
- 繁體中文"""
            else:
                write_prompt = f"""你是一個專業的內容創作者。請根據以下任務生成完整內容，直接輸出檔案內容，不要說多餘的話。

任務：{title}
描述：{desc}

直接輸出要寫入檔案的完整內容。內容必須充實，至少 500 字。不要輸出任何解釋或說明，只輸出檔案內容本身。繁體中文。"""

            write_resp = llm.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": write_prompt}],
                temperature=0.7,
                max_tokens=4000,
            )
            content = write_resp.choices[0].message.content.strip()

            if content and len(content) > 50:
                output_path.write_text(content, encoding="utf-8")
                print(f"[ProactiveExecutor] ✅ 寫入: {output_path} ({len(content)} 字)")

                planner = self.planner
                task["status"] = "completed"
                task["completed_at"] = datetime.now().isoformat()
                task["updated_at"] = datetime.now().isoformat()
                planner.tasks._save_to_disk()

                self._notify_user(
                    f"✅ 任務完成\n"
                    f"📋 {title}\n"
                    f"📁 {output_path}\n"
                    f"📊 {len(content)} 字"
                )
                self._current_task_id = None
                return True
            else:
                print("[ProactiveExecutor] ⚠️ LLM 回傳內容太短")

        except Exception as e:
            print(f"[ProactiveExecutor] ❌ 執行失敗: {e}")
            traceback.print_exc()

        return False

    # ── 2. 檢查 mission 完成狀態 ──────────────────────────────

    def _check_mission_completions(self):
        agents = self.agents
        planner = self.planner

        if not agents or not planner:
            return

        completed_ids = []
        for task_id, mission_id in list(self._pending_missions.items()):
            # 跳過時間戳記
            if str(task_id).endswith("_started"):
                continue
            if not isinstance(mission_id, str):
                continue

            mission = agents.get_mission(mission_id) if hasattr(agents, "get_mission") else None

            if not mission:
                continue

            status = mission.get("status", "")

            if status == "completed":
                # 驗證：任務是否真的產出了檔案？
                task = planner.tasks.get(task_id, {})
                task_desc = task.get("description", "")
                output_verified = self._verify_output_exists(task_desc)

                if not output_verified:
                    # 子代理回報完成但沒產出檔案 → 標記失敗，重試
                    print(f"[ProactiveExecutor] ⚠️ 任務 {task_id} 回報完成但無產出檔案，重試中...")
                    planner.tasks.update_task_status(task_id, "pending")
                    completed_ids.append(task_id)
                    self._current_task_id = None
                    self._current_mission_id = None
                    continue

                results = mission.get("results", {})
                success_count = sum(1 for r in results.values() if r.get("success"))
                total = len(mission.get("sub_tasks", []))

                planner.tasks.complete_task(task_id)
                completed_ids.append(task_id)

                self._notify_user(
                    f"✅ 黑曜完成任務\n"
                    f"📋 {task.get('title', task_id)}\n"
                    f"🆔 {task_id}\n"
                    f"📊 子任務: {success_count}/{total} 成功"
                )
                print(f"[ProactiveExecutor] ✅ 任務完成: {task_id} ({success_count}/{total})")

                self._current_task_id = None
                self._current_mission_id = None

            elif status == "failed":
                planner.tasks.update_task_status(task_id, "pending")
                completed_ids.append(task_id)
                print(f"[ProactiveExecutor] ❌ 任務失敗: {task_id}")

                self._current_task_id = None
                self._current_mission_id = None

        for tid in completed_ids:
            self._pending_missions.pop(tid, None)

    def _verify_output_exists(self, desc: str) -> bool:
        """檢查任務描述中指定的輸出路徑是否真的有檔案產生。"""
        import os
        for keyword in ["存入 ", "存到 ", "outputs/"]:
            idx = desc.find(keyword)
            if idx >= 0:
                path_str = desc[idx + len(keyword):].strip().split()[0].rstrip("。.,")
                if path_str:
                    full_path = Path(__file__).parent.parent.parent / path_str
                    if full_path.exists():
                        return True
                    # 也檢查 outputs/ 下的同名檔案
                    alt_path = Path(__file__).parent.parent.parent / "outputs" / path_str.replace("outputs/", "")
                    return alt_path.exists()
        return True  # 如果任務描述沒指定路徑，先信任子代理回報

    # ── 0. 確保永遠有商業任務 ──────────────────────────────

    def _ensure_business_tasks(self):
        planner = self.planner
        if not planner:
            return

        # 檢查當前有沒有 pending/in_progress 任務
        pending = [t for t in planner.tasks.values() if t.get("status") == "pending"]
        in_progress = [t for t in planner.tasks.values() if t.get("status") == "in_progress"]

        if pending or in_progress:
            return

        # 如果沒有任務在跑，看整個商業管線缺什麼
        import os
        outputs_dir = Path(__file__).parent.parent.parent / "outputs"

        # 管線階段 1：目錄結構
        ebooks_dir = outputs_dir / "ebooks"
        children_dir = outputs_dir / "children_book"
        research_dir = outputs_dir / "research"
        website_dir = outputs_dir / "website"

        # 管線階段 2：雲端資源驗證
        cf_token = os.getenv("CLOUDFLARE_API_TOKEN", "")
        if cf_token:
            cf_check_file = research_dir / "cloudflare_setup.md"
            if not cf_check_file.exists():
                planner.tasks.add_task(
                    title="Cloudflare 網路身分建立",
                    description="1. 用 run_command 執行 curl 驗證 Cloudflare API Token 2. 查詢 AMPM-AIOPS.COM DNS 設定 3. 記錄結果用 write_file 存入 outputs/research/cloudflare_setup.md。",
                    priority=1,
                )
                print("[ProactiveExecutor] 🌐 自動建立：Cloudflare 身分驗證任務")
                return

        # 管線階段 3：平台研究
        platform_file = research_dir / "platform_research.md"
        if not platform_file.exists():
            planner.tasks.add_task(
                title="電子書上架平台研究報告",
                description="用 web_search 搜尋 Amazon KDP、Apple Books、Google Play Books、Kobo 四個平台的註冊流程、費用、抽成、檔案格式。用 write_file 存入 outputs/research/platform_research.md，至少 800 字。",
                priority=1,
            )
            print("[ProactiveExecutor] 📝 自動建立：上架平台研究任務")
            return

        # 管線階段 4：電子書第一章
        ebook_files = list(ebooks_dir.glob("ch*.md")) if ebooks_dir.exists() else []
        if len(ebook_files) < 1:
            planner.tasks.add_task(
                title="電子書：第一章寫作",
                description="以 AI 入門指南為主題，撰寫第一章。先用 web_search 搜尋最新 AI 工具、新手入門知識、常見問題。含標題、引言、800+字內容、實戰步驟、總結。用 write_file 寫入 outputs/ebooks/ch01_intro.md。",
                priority=1,
            )
            print("[ProactiveExecutor] 📝 自動建立：電子書第一章")
            return

        # 管線階段 5：童書研究
        children_research = children_dir / "research.md" if children_dir.exists() else None
        if not children_research or not children_research.exists():
            planner.tasks.add_task(
                title="童書市場研究",
                description="用 web_search 搜尋學齡前（3-6歲）童書熱門主題，分析 TOP20 童書風格、定價。用 write_file 存入 outputs/children_book/research.md，至少 500 字。",
                priority=2,
            )
            print("[ProactiveExecutor] 📝 自動建立：童書市場研究")
            return

        # 管線階段 6：品牌網站
        website_index = website_dir / "index.html" if website_dir.exists() else None
        if not website_index or not website_index.exists():
            planner.tasks.add_task(
                title="AMPM-AIOPS 品牌網站建立",
                description="建立專業服務網站：1. outputs/website/index.html（品牌、三大服務、聯絡）2. outputs/website/style.css。用 write_file 寫入。現代簡潔風格。",
                priority=2,
            )
            print("[ProactiveExecutor] 🌐 自動建立：品牌網站任務")
            return

        # 管線階段 7：電子書第二章～第五章
        if len(ebook_files) < 5 and len(ebook_files) >= 1:
            next_ch = len(ebook_files) + 1
            planner.tasks.add_task(
                title=f"電子書第{next_ch}章寫作",
                description=f"延續前章 AI 入門指南，寫第{next_ch}章。{ {2:'AI 工具介紹與比較',3:'Prompt 技巧實戰',4:'AI 實戰案例',5:'進階應用與變現'}.get(next_ch, '更多內容')}。至少 800 字，含實戰步驟和總結。先用 web_search 搜尋相關資訊。用 write_file 寫入 outputs/ebooks/ch{next_ch:02d}.md。",
                priority=2,
            )
            print(f"[ProactiveExecutor] 📝 自動建立：電子書第{next_ch}章")
            return

        # 管線階段 8：童書第一本
        children_files = list(children_dir.glob("book1_*.md")) if children_dir.exists() else []
        if len(children_files) < 1:
            planner.tasks.add_task(
                title="童書第一本：完整創作",
                description="創作第一本童書：故事大綱+角色設定、完整故事1000+字、插圖描述和分頁。用 write_file 分別寫入 outputs/children_book/book1_outline.md, book1_story.md, book1_illustrations.md。",
                priority=2,
            )
            print("[ProactiveExecutor] 📝 自動建立：童書第一本")
            return

        # 管線階段 9：商業策略
        biz_strategy = research_dir / "business_strategy.md" if research_dir.exists() else None
        if not biz_strategy or not biz_strategy.exists():
            planner.tasks.add_task(
                title="商業策略：定價與行銷規劃",
                description="用 web_search 研究電子書/童書定價策略、Amazon KDP 抽成、促銷方案。制定定價和行銷計畫。用 write_file 存入 outputs/research/business_strategy.md，至少 600 字。",
                priority=2,
            )
            print("[ProactiveExecutor] 📝 自動建立：商業策略任務")
            return

        # 管線階段 10：服務流程設計
        service_flow = research_dir / "service_flow.md" if research_dir.exists() else None
        if not service_flow or not service_flow.exists():
            planner.tasks.add_task(
                title="一條龍 AI 代理服務流程設計",
                description="設計自動化服務流程：客戶選購→AI評估→報價→付款→安裝→客服→升級。含對話腳本、退款政策。用 write_file 存入 outputs/research/service_flow.md，至少 800 字。",
                priority=3,
            )
            print("[ProactiveExecutor] 📝 自動建立：服務流程設計")
            return

        # 管線階段 11：電子書第六章~第十章
        if len(ebook_files) < 10 and len(ebook_files) >= 5:
            next_ch = len(ebook_files) + 1
            planner.tasks.add_task(
                title=f"電子書第{next_ch}章寫作",
                description=f"延續前面章節，寫第{next_ch}章。至少 800 字。用 write_file 寫入 outputs/ebooks/ch{next_ch:02d}.md。",
                priority=3,
            )
            print(f"[ProactiveExecutor] 📝 自動建立：電子書第{next_ch}章")
            return

        # 管線階段 12：品質檢查
        planner.tasks.add_task(
            title="品質檢查與進度回報",
            description="1. 用 list_dir 和 read_file 檢查所有 outputs/ 檔案 2. 確認每個 .md 超過 500 字且格式完整 3. 不合格自動補齊 4. 透過 Telegram 回報進度給老大。",
            priority=3,
        )
        print("[ProactiveExecutor] 📊 自動建立：品質檢查任務")

    # ── 3. 主動找問題 ───────────────────────────────────────

    def _scan_for_problems(self):
        """主動掃描系統，發現問題自動建立任務並執行"""
        planner = self.planner
        if not planner:
            return

        problems = []

        # 3a. 檢查記憶是否過多需要壓縮
        try:
            mem = getattr(self.obsidian, "memory", None)
            if mem:
                count = len(getattr(mem, "_texts", [])) if hasattr(mem, "_texts") else 0
                if count > 500:
                    problems.append({
                        "title": "記憶壓縮",
                        "description": f"記憶已達 {count} 條（超過 500 條閾值），需要壓縮以維持效能",
                        "priority": 3,
                    })
        except Exception:
            pass

        # 3b. 檢查 organ 是否有 dead/zombie 狀態
        try:
            for name, organ in self.obsidian.organs.items():
                if hasattr(organ, "is_alive") and not organ.is_alive():
                    problems.append({
                        "title": f"器官修復: {name}",
                        "description": f"器官 {name} 已死亡，需要修復或重啟",
                        "priority": 1,
                    })
        except Exception:
            pass

        # 3c. 檢查進化循環是否太久沒執行
        try:
            ec = getattr(self.obsidian, "evolution_cycle", None) or self.obsidian.organs.get("evolution_cycle")
            if ec and hasattr(ec, "status"):
                st = ec.status()
                cycles = st.get("cycles", 0)
        except Exception:
            pass

        # 3d. 檢查是否有長期 pending 的任務（超過 24 小時）
        try:
            now = datetime.now()
            for task in planner.tasks.values():
                if task.get("status") == "pending":
                    created = datetime.fromisoformat(task["created_at"])
                    hours_pending = (now - created).total_seconds() / 3600
                    if hours_pending > 24:
                        problems.append({
                            "title": f"逾期任務警報",
                            "description": f"任務 {task['id']}「{task['title']}」已 pending {hours_pending:.0f} 小時，需要關注",
                            "priority": 2,
                        })
        except Exception:
            pass

        # 如果有發現問題，加入任務佇列
        for problem in problems:
            # 避免重複建立同名任務
            existing = [
                t for t in planner.tasks.values()
                if t.get("title") == problem["title"] and t.get("status") == "pending"
            ]
            if existing:
                continue

            planner.tasks.add_task(
                title=problem["title"],
                description=problem["description"],
                priority=problem["priority"],
            )
            print(f"[ProactiveExecutor] 🔍 發現問題，建立任務: {problem['title']}")

    # ── Telegram 通知 ────────────────────────────────────────

    def _notify_user(self, message: str):
        """透過 Telegram 發送通知給使用者"""
        token = getattr(self.obsidian, "telegram_token", None)
        chat_id = getattr(self.obsidian, "telegram_chat_id", None)
        if not token or not chat_id:
            print(f"[ProactiveExecutor] 📋 {message[:100].replace(chr(10), ' ')}")
            return
        try:
            import urllib.request, urllib.parse
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = urllib.parse.urlencode({"chat_id": chat_id, "text": message[:4000], "parse_mode": "Markdown"}).encode()
            urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=10)
        except Exception:
            pass

    def _periodic_report(self):
        """每 5 分鐘回報一次進度給老大"""
        now = time.time()
        if now - self._last_report_time < self._report_interval:
            return
        self._last_report_time = now

        planner = self.planner
        if not planner:
            return

        # 統計任務進度
        tasks = list(planner.tasks.values())
        completed = [t for t in tasks if t.get("status") == "completed"]
        in_progress = [t for t in tasks if t.get("status") == "in_progress"]
        pending = [t for t in tasks if t.get("status") == "pending"]

        # 統計產出檔案
        outputs_dir = Path(__file__).parent.parent.parent / "outputs"
        file_list = []
        total_chars = 0
        if outputs_dir.exists():
            for f in sorted(outputs_dir.rglob("*")):
                if f.is_file() and f.suffix not in (".gitkeep",):
                    try:
                        content = f.read_text(encoding="utf-8")
                        chars = len(content)
                        total_chars += chars
                        rel = f.relative_to(outputs_dir)
                        file_list.append(f"  📄 {rel} ({chars} 字)")
                    except:
                        file_list.append(f"  📄 {f.relative_to(outputs_dir)}")

        # 組裝回報訊息
        lines = [
            "📊 *黑曜進度回報*",
            "",
            f"✅ 已完成：{len(completed)} 項",
            f"🔄 執行中：{len(in_progress)} 項",
            f"⏳ 待處理：{len(pending)} 項",
            "",
            f"📁 產出檔案：{len(file_list)} 個",
            f"📝 總字數：{total_chars:,} 字",
            "",
        ]

        if file_list:
            lines.append("📂 *檔案清單：*")
            lines.extend(file_list[:15])
            lines.append("")

        if in_progress:
            lines.append("🔄 *正在執行：*")
            for t in in_progress[:3]:
                lines.append(f"  • {t.get('title', '?')}")
            lines.append("")

        self._notify_user(
            f"📊 黑曜進度\n"
            f"✅ {len(completed)}完成  🔄 {len(in_progress)}執行中  ⏳ {len(pending)}待處理\n"
            f"📁 {len(file_list)}檔案  📝 {total_chars:,}字"
        )
        print(f"[ProactiveExecutor] 📊 進度: {len(completed)}完成 {len(in_progress)}執行中 {len(pending)}待處理")
