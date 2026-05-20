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

        # 全域單例註冊（供 supervisor 心跳用）
        _ACTIVE_EXECUTORS["proactive_executor"] = self

    @property
    def planner(self):
        """取得 PlannerOrgan (TaskSchedulerOrgan)"""
        return (
            self.obsidian.organs.get("plannerorgan")
            or self.obsidian.organs.get("taskschedulerorgan")
        )

    @property
    def agents(self):
        """取得 AgentTaskRouter"""
        return (
            self.obsidian.organs.get("agent_company")
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

                # 心跳
                try:
                    from core.agent_supervisor import supervisor
                    supervisor.heartbeat("proactive_executor")
                except Exception:
                    pass

            except Exception as e:
                print(f"[ProactiveExecutor] 迴圈錯誤: {e}")
                traceback.print_exc()

            time.sleep(30)

    # ── 1. 執行 pending 任務 ─────────────────────────────────

    def _execute_pending_tasks(self):
        planner = self.planner

        if not planner:
            return

        # 一次只跑一個任務，避免塞爆
        if self._pending_missions:
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
        planner._save_to_disk()

        desc = self._build_agent_prompt(task)

        print(f"[ProactiveExecutor] 🚀 自動執行: {task['id']} - {task['title']} (優先級={task['priority']})")

        # 優先走 agent_company 子代理路線
        agents = self.agents
        if agents:
            stats = agents.get_global_stats() if hasattr(agents, "get_global_stats") else {}
            busy_agents = stats.get("agents_busy", 0)
            if busy_agents <= 10:
                try:
                    mission_id = agents.launch_mission(desc)
                    if mission_id:
                        self._pending_missions[task["id"]] = mission_id
                        self._current_task_id = task["id"]
                        self._current_mission_id = mission_id
                        self._notify_user(
                            f"🚀 黑曜派工\n"
                            f"📋 {task['title']}\n"
                            f"👥 子代理已出動"
                        )
                        print(f"[ProactiveExecutor] → mission {mission_id}")
                        return
                except Exception as e:
                    print(f"[ProactiveExecutor] agent_company 失敗: {e}")

        # 備援：子代理不可用或失敗，直接 LLM 生成
        if self._try_direct_execute(task):
            return

        # 都失敗，恢復 pending
        planner.update_task_status(task["id"], "pending")

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
        對於內容生成類任務，直接用 LLM 生成內容並寫入檔案。
        跳過 agent_company 子代理（因為子代理不會寫檔案）。
        回傳 True 表示已處理，False 表示不適用需走 agent_company。
        """
        title = task.get("title", "")
        desc = task.get("description", "")

        # 辨識是否為內容生成任務（關鍵字）
        content_keywords = ["寫作", "章", "生成", "研究", "報告", "建立", "產出",
                           "撰寫", "write", "generate", "create", "存入", "存到"]
        is_content_task = any(kw in title or kw in desc for kw in content_keywords)
        if not is_content_task:
            return False

        # 找出目標輸出路徑
        output_path = None
        for keyword in ["存入 ", "存到 ", "outputs/"]:
            idx = desc.find(keyword)
            if idx >= 0:
                path_str = desc[idx + len(keyword):].strip().split()[0].rstrip("。.")
                if path_str:
                    output_path = Path(__file__).parent.parent.parent / path_str
                    break

        if not output_path:
            # 預設用任務標題猜路徑
            if "電子工具書" in title or "電子書" in title:
                output_path = Path(__file__).parent.parent.parent / "outputs" / "ebooks" / "generated_chapter.md"
            elif "童書" in title:
                output_path = Path(__file__).parent.parent.parent / "outputs" / "children_book" / "generated.md"
            elif "網站" in title:
                output_path = Path(__file__).parent.parent.parent / "outputs" / "website" / "index.html"
            elif "研究" in title:
                output_path = Path(__file__).parent.parent.parent / "outputs" / "research" / "research.md"
            else:
                return False

        # 確保目錄存在
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 用 LLM 生成內容
        llm = getattr(self.obsidian, "llm", None)
        if not llm:
            print("[ProactiveExecutor] ⚠️ LLM 不可用，無法直接生成內容")
            return False

        try:
            prompt = f"""你是一個專業的內容創作者。請根據以下任務生成完整內容，直接輸出檔案內容，不要說多餘的話。

任務標題：{title}
任務描述：{desc}

請直接輸出要寫入檔案的完整內容。如果是 Markdown 檔案，用 Markdown 格式；如果是 HTML，用 HTML 格式。
內容必須充實，至少 500 字以上。不要輸出任何解釋或說明，只輸出檔案內容本身。"""

            print(f"[ProactiveExecutor] 🤖 直接生成: {output_path}")
            response = llm.chat.completions.create(
                model=getattr(llm, "model", "deepseek-v4-pro"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=4000,
            )
            content = response.choices[0].message.content.strip()

            if content and len(content) > 50:
                output_path.write_text(content, encoding="utf-8")
                print(f"[ProactiveExecutor] ✅ 內容已寫入: {output_path} ({len(content)} 字)")

                planner = self.planner
                task["status"] = "completed"
                task["completed_at"] = datetime.now().isoformat()
                task["updated_at"] = datetime.now().isoformat()
                planner._save_to_disk()

                self._notify_user(
                    f"✅ 黑曜完成任務\n"
                    f"📋 {title}\n"
                    f"📁 {output_path}\n"
                    f"📊 {len(content)} 字"
                )
                self._current_task_id = None
                return True
            else:
                print("[ProactiveExecutor] ⚠️ LLM 回傳內容太短或為空")

        except Exception as e:
            print(f"[ProactiveExecutor] ❌ LLM 生成失敗: {e}")
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
                    planner.update_task_status(task_id, "pending")
                    completed_ids.append(task_id)
                    self._current_task_id = None
                    self._current_mission_id = None
                    continue

                results = mission.get("results", {})
                success_count = sum(1 for r in results.values() if r.get("success"))
                total = len(mission.get("sub_tasks", []))

                planner.complete_task(task_id)
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
                planner.update_task_status(task_id, "pending")
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

        # 檢查當前有沒有 pending 任務
        pending = [t for t in planner.tasks.values() if t.get("status") == "pending"]
        in_progress = [t for t in planner.tasks.values() if t.get("status") == "in_progress"]

        # 如果已經有任務在執行或排隊，不塞新任務
        if pending or in_progress:
            return

        # 檢查 output 目錄，自動生成缺少的任務
        import os
        outputs_dir = Path(__file__).parent.parent.parent / "outputs"

        # 檢查是否有電子書內容
        ebooks_dir = outputs_dir / "ebooks"
        ebook_files = list(ebooks_dir.glob("ch*.md")) if ebooks_dir.exists() else []
        if len(ebook_files) < 1:
            planner.add_task(
                title="電子工具書：第一章寫作",
                description="選擇一個工具書主題（建議：AI 工具入門指南），撰寫第一章完整內容。包含：標題、引言、主內容（至少800字）、實戰步驟、本章總結。存入 outputs/ebooks/ch01_intro.md。",
                priority=1,
            )
            print("[ProactiveExecutor] 📝 自動建立：電子書第一章任務")
            return

        # 檢查是否有童書研究
        children_dir = outputs_dir / "children_book"
        research_file = children_dir / "research.md" if children_dir.exists() else None
        if not research_file or not research_file.exists():
            planner.add_task(
                title="童書市場研究",
                description="搜尋目前學齡前（3-6歲）童書熱門主題，分析 Amazon、博客來 TOP20 童書的主題、風格、定價。寫出選題建議，存入 outputs/children_book/research.md。至少 500 字。",
                priority=2,
            )
            print("[ProactiveExecutor] 📝 自動建立：童書市場研究任務")
            return

        # 檢查是否有平台研究
        research_dir = outputs_dir / "research"
        platform_file = research_dir / "platform_research.md" if research_dir.exists() else None
        if not platform_file or not platform_file.exists():
            planner.add_task(
                title="電子書平台研究",
                description="搜尋 Amazon KDP、Apple Books、Google Play Books 的註冊流程、費用、抽成、上架規格，寫成報告存入 outputs/research/platform_research.md。",
                priority=1,
            )
            print("[ProactiveExecutor] 📝 自動建立：平台研究任務")
            return

        # 如果基本任務都完成了，生成下一章
        if len(ebook_files) >= 1:
            next_ch = len(ebook_files) + 1
            if next_ch <= 10:
                planner.add_task(
                    title=f"電子工具書：第{next_ch}章寫作",
                    description=f"延續前面章節，撰寫第{next_ch}章完整內容。至少 800 字，含實戰步驟和總結。存入 outputs/ebooks/ch{next_ch:02d}_content.md。",
                    priority=2,
                )
                print(f"[ProactiveExecutor] 📝 自動建立：電子書第{next_ch}章任務")
                return

        # 如果電子書章節都完成了，生成童書第一本
        if len(ebook_files) >= 10:
            children_files = list(children_dir.glob("book1_*.md")) if children_dir.exists() else []
            if len(children_files) < 1:
                planner.add_task(
                    title="童書第一本：故事內容",
                    description="根據童書大綱和角色設定，撰寫完整童書故事內容（至少 1000 字），包含對話、場景描述、教育意義。存入 outputs/children_book/book1_story.md。",
                    priority=2,
                )
                print("[ProactiveExecutor] 📝 自動建立：童書第一本任務")
                return

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

            planner.add_task(
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
            return

        try:
            import urllib.request
            import urllib.parse

            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = urllib.parse.urlencode({
                "chat_id": chat_id,
                "text": message[:4000],
                "parse_mode": "Markdown",
            }).encode()

            req = urllib.request.Request(url, data=data)
            urllib.request.urlopen(req, timeout=10)
        except Exception:
            pass
