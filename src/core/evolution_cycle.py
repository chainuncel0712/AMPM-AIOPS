"""
進化循環引擎 — 吸收→學習→篩選→記憶→增強→循環
這是黑曜的自我進化閉環：持續從環境吸收資訊，學習提煉，
保留好的強化自己，排除壞的，然後繼續。
"""
from runtime.context.persona_builder import RUNTIME_IDENTITY, RUNTIME_RULES
import json
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from skeleton.base_organ import BaseOrgan


class EvolutionCycleOrgan(BaseOrgan):
    """
    進化循環器官 — 機械學習閉環

    循環步驟：
    1. 吸收 (absorb)    — 從多來源收集原始資訊
    2. 學習 (learn)     — LLM 分析提煉知識點
    3. 篩選 (select)    — 評估好壞，選出有價值的
    4. 記憶 (remember)  — 好的存入長期記憶
    5. 增強 (enhance)   — 用好的知識升級自己
    6. 排除 (exclude)   — 壞的丟棄並記錄原因
    7. 循環 (loop)      — 回到步驟 1

    安全約束（不可逾越）：
    - 使用者需求永遠第一優先
    - 禁止單次循環超過 5 項增強
    - 禁止刪除系統核心檔案
    - 禁止修改自身安全機制程式碼
    """

    # ===== 安全閾值 =====
    SAFETY = {
        "max_enhancements_per_cycle": 5,
        "max_cycles_per_hour": 12,
        "min_cycle_interval": 300,
        "max_total_enhancements": 100,
        "forbidden_actions": [
            "rm -rf", "del /q", "DROP TABLE", "format",
            "shutdown", "reboot", "kill -9",
        ],
        "protected_files": [
            "config.py", "cortex.py", "langgraph_executor.py",
            "self_awareness.py", "rebirth.py", "evolution_cycle.py",
            "circulatory.py", "dna.py", "base_organ.py",
        ],
    }

    def __init__(self, base_dir: Path, memory, tools, web_search=None,
                 awareness=None, rebirth=None, llm=None):
        super().__init__("evolution_cycle")
        self.base_dir = base_dir
        self.memory = memory
        self.tools = tools
        self.web_search = web_search
        self.awareness = awareness
        self.rebirth = rebirth
        self.llm = llm

        self.data_dir = base_dir / "data" / "evolution"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.state_file = self.data_dir / "cycle_state.json"
        self.learnings_file = self.data_dir / "learnings.json"
        self.bad_file = self.data_dir / "excluded.json"
        self.absorbed_fingerprints_file = self.data_dir / "absorbed_fingerprints.json"

        self._lock = threading.Lock()
        self._load_state()

    # =========================================
    # 狀態管理
    # =========================================

    def _default_state(self) -> dict:
        return {
            "cycle_count": 0,
            "total_absorbed": 0,
            "total_learned": 0,
            "total_enhanced": 0,
            "total_excluded": 0,
            "evolution_score": 0,
            "last_cycle": None,
            "cycle_history": [],
        }

    def _load_state(self):
        if self.state_file.exists():
            try:
                self.state = json.loads(self.state_file.read_text())
            except Exception:
                self.state = self._default_state()
        else:
            self.state = self._default_state()

    def _save_state(self):
        with self._lock:
            self.state_file.write_text(
                json.dumps(self.state, ensure_ascii=False, indent=2))

    def _load_json(self, path: Path) -> list:
        if path.exists():
            try:
                return json.loads(path.read_text())
            except Exception:
                return []
        return []

    def _save_json(self, path: Path, data: list, max_items: int = 500):
        if len(data) > max_items:
            data = data[-max_items:]
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    # =========================================
    # 步驟 1：吸收 (absorb)
    # =========================================

    def absorb(self) -> List[Dict]:
        """從多個來源吸收原始資訊"""
        sources = []
        seen = set()
        
        # 跨週期去重：載入已見過的內容指紋
        seen_fingerprints = self._load_json(self.absorbed_fingerprints_file)
        if not isinstance(seen_fingerprints, set):
            seen_fingerprints = set(seen_fingerprints) if seen_fingerprints else set()

        # 1. 從記憶器官吸收最近的對話（只取上次之後的新對話）
        try:
            if self.memory and hasattr(self.memory, "get_all_facts"):
                facts = self.memory.get_all_facts()
                # 只取最新的 10 條，避免重複
                new_facts = facts[-10:] if len(facts) > 10 else facts
                for f in new_facts:
                    fp = hash(f[:200])  # 內容指紋
                    if fp not in seen_fingerprints:
                        seen_fingerprints.add(fp)
                        key = f[:80]
                        if key not in seen:
                            seen.add(key)
                            sources.append({
                                "source": "memory",
                                "content": f,
                                "absorbed_at": datetime.now().isoformat(),
                            })
        except Exception:
            pass

        # 2. 從工具註冊表吸收（只在第一次吸收）
        if self.state["cycle_count"] <= 2:
            try:
                if self.tools and hasattr(self.tools, "registry"):
                    for name, tool in list(self.tools.registry.items())[:10]:
                        key = f"tool:{name}"
                        if key not in seen:
                            seen.add(key)
                            desc = getattr(tool, "__doc__", "") or str(tool)[:100]
                            sources.append({
                                "source": "tool_registry",
                                "content": f"工具 {name}: {desc}",
                                "absorbed_at": datetime.now().isoformat(),
                            })
            except Exception:
                pass

        # 3. 從自我意識的能力矩陣吸收（只在能力變化時）
        try:
            if self.awareness and self.awareness.capabilities:
                cap_fp = hash(str(list(self.awareness.capabilities.keys())))
                if cap_fp not in seen_fingerprints:
                    seen_fingerprints.add(cap_fp)
                    for name, cap in list(self.awareness.capabilities.items())[:5]:
                        key = f"cap:{name}"
                        if key not in seen:
                            seen.add(key)
                            sources.append({
                                "source": "self_assessment",
                                "content": f"能力 {name}: 水準 {cap.get('level', 0)}",
                                "absorbed_at": datetime.now().isoformat(),
                            })
        except Exception:
            pass

        # 4. 動態網頁搜尋（每週期變換查詢主題）
        topics = [
            "AI agent autonomous business model 2026",
            "free LLM API for AI agents 2026",
            "open source AI tools for automation",
            "AI agent monetization strategy",
            "cheap GPU cloud for AI inference",
            "AI agent passive income methods",
            "best free AI models for coding agents",
            "AI agent self-improvement techniques",
        ]
        search_query = topics[self.state["cycle_count"] % len(topics)]
        try:
            if self.web_search and hasattr(self.web_search, "search"):
                results = self.web_search.search(search_query)
                for r in results[:3]:
                    content = str(r)[:200]
                    fp = hash(content[:100])
                    if fp not in seen_fingerprints:
                        seen_fingerprints.add(fp)
                        sources.append({
                            "source": "web",
                            "query": search_query,
                            "content": content,
                            "absorbed_at": datetime.now().isoformat(),
                        })
        except Exception:
            pass

        # 儲存指紋供跨週期去重
        self._save_json(self.absorbed_fingerprints_file, list(seen_fingerprints)[-500:])

        with self._lock:
            self.state["total_absorbed"] += len(sources)

        return sources

    # =========================================
    # 步驟 2：學習 (learn)
    # =========================================

    def learn(self, sources: List[Dict]) -> List[Dict]:
        """從吸收的資訊中提煉知識點"""
        if not sources:
            return []

        learnings = []

        # 用 LLM 分析（如果有）
        if self.llm:
            try:
                learning_text = "\n".join(
                    f"- [{s['source']}] {s['content'][:150]}"
                    for s in sources[:20]
                )
                prompt = f"""你是黑曜的學習模組。請從以下吸收的資訊中提煉出有價值的知識點。

資訊：
{learning_text}

請以 JSON 陣列回覆，每個知識點包含：
[
  {{
    "topic": "主題分類",
    "insight": "學到的具體知識",
    "confidence": 0.0~1.0,
    "actionable": true/false,
    "suggested_action": "如果可以行動，建議做什麼"
  }}
]

只回 JSON，不要其他文字。"""

                system_ctx = f"{RUNTIME_IDENTITY}\n\n{RUNTIME_RULES}\n\n你正在執行進化循環學習任務。"
                raw = self.llm.call([
                    {"role": "system", "content": system_ctx},
                    {"role": "user", "content": prompt}
                ])
                import re
                match = re.search(r'\[.*\]', raw, re.DOTALL)
                if match:
                    learnings = json.loads(match.group())
            except Exception:
                pass

        # 如果 LLM 沒回或失敗，用關鍵字提取
        if not learnings:
            for s in sources:
                content = s["content"].lower()
                # 簡單的關鍵字學習
                if any(kw in content for kw in ["成功", "修復", "完成", "success", "fix", "done"]):
                    learnings.append({
                        "topic": "經驗",
                        "insight": content[:150],
                        "confidence": 0.6,
                        "actionable": False,
                    })

        # 儲存學習記錄
        all_learnings = self._load_json(self.learnings_file)
        for lrn in learnings:
            lrn["learned_at"] = datetime.now().isoformat()
            all_learnings.append(lrn)
        self._save_json(self.learnings_file, all_learnings)

        with self._lock:
            self.state["total_learned"] += len(learnings)

        return learnings

    # =========================================
    # 步驟 3：篩選 (select)
    # =========================================

    def select(self, learnings: List[Dict]) -> Dict[str, List[Dict]]:
        """篩選：分出好的和壞的"""
        good = []
        bad = []

        for lrn in learnings:
            confidence = lrn.get("confidence", 0.5)

            # 高信心 + 可行動 = 好的
            if confidence >= 0.5 and lrn.get("actionable"):
                lrn["quality"] = "good"
                lrn["selected_at"] = datetime.now().isoformat()
                good.append(lrn)

            # 高信心但暫不可行動 = 保留觀察
            elif confidence >= 0.5:
                lrn["quality"] = "pending"
                lrn["selected_at"] = datetime.now().isoformat()
                good.append(lrn)  # 先保留

            # 低信心 = 壞的
            else:
                lrn["quality"] = "bad"
                lrn["selected_at"] = datetime.now().isoformat()
                bad.append(lrn)

        return {"good": good, "bad": bad}

    # =========================================
    # 步驟 4：記憶 (remember)
    # =========================================

    def remember(self, good_learnings: List[Dict]):
        """將好的知識存入長期記憶"""
        for lrn in good_learnings:
            topic = lrn.get("topic", "未知")
            insight = lrn.get("insight", "")[:200]
            confidence = lrn.get("confidence", 0.5)

            # 寫入記憶器官
            try:
                if self.memory and hasattr(self.memory, "remember_fact"):
                    self.memory.remember_fact(
                        f"[進化學習] {topic}: {insight}",
                        importance=confidence * 0.8
                    )
            except Exception:
                pass

            # 更新自我意識的能力矩陣
            try:
                if self.awareness:
                    # 根據學習主題自動調整能力評分
                    for cap_name in list(self.awareness.capabilities.keys())[:10]:
                        if topic[:3] in cap_name or cap_name[:3] in topic:
                            old_level = self.awareness.capabilities[cap_name]["level"]
                            new_level = min(1.0, old_level + 0.05 * confidence)
                            self.awareness.assess_capability(cap_name, new_level)
            except Exception:
                pass

    # =========================================
    # 安全閘 (safety gate)
    # =========================================

    def safety_check(self, action: str, cycle: int, enhanced_this_cycle: int) -> Dict:
        """
        安全閘：所有增強/修改操作必須通過此檢查。

        規則：
        1. 使用者需求永遠第一優先 — 不攔使用者直接指令
        2. 禁止危險操作（rm -rf, shutdown 等）
        3. 保護核心檔案（不可修改安全機制本身）
        4. 速率限制（每循環最多 5 項增強）
        5. 總量限制（超過 100 次增強後需人工審核）

        回傳：{"allowed": bool, "reason": str, "must_ask_user": bool}
        """
        s = self.SAFETY

        # 檢查危險操作
        for forbidden in s["forbidden_actions"]:
            if forbidden.lower() in action.lower():
                return {
                    "allowed": False,
                    "reason": f"🛡️ 安全閘攔截：禁止操作「{forbidden}」",
                    "must_ask_user": True,
                }

        # 檢查是否嘗試修改保護檔案
        for protected in s["protected_files"]:
            if protected.lower() in action.lower():
                return {
                    "allowed": False,
                    "reason": f"🛡️ 安全閘攔截：禁止修改核心模組「{protected}」",
                    "must_ask_user": True,
                }

        # 速率限制：單次循環不超過 5 項增強
        if enhanced_this_cycle >= s["max_enhancements_per_cycle"]:
            return {
                "allowed": False,
                "reason": f"⏱️ 速率限制：本循環已達 {s['max_enhancements_per_cycle']} 項增強上限",
                "must_ask_user": False,
            }

        # 總量限制
        total_enhanced = self.state.get("total_enhanced", 0)
        if total_enhanced >= s["max_total_enhancements"]:
            return {
                "allowed": False,
                "reason": f"🛡️ 總增強已達 {s['max_total_enhancements']} 上限，需人工審核後解鎖",
                "must_ask_user": True,
            }

        return {"allowed": True, "reason": "", "must_ask_user": False}

    # =========================================
    # 步驟 5：增強 (enhance)
    # =========================================

    def enhance(self, good_learnings: List[Dict]):
        """用學到的知識增強自己（通過安全閘後才執行）"""
        enhanced = 0

        for lrn in good_learnings:
            if not lrn.get("actionable"):
                continue

            action = lrn.get("suggested_action", "")
            topic = lrn.get("topic", "")

            # ===== 安全閘檢查 =====
            safety_result = self.safety_check(action, self.state["cycle_count"], enhanced)
            if not safety_result["allowed"]:
                if self.awareness:
                    self.awareness.record_event("safety_block",
                        f"安全閘攔截: {safety_result['reason']}")
                continue

            # 如果建議建立新工具
            if any(kw in action for kw in ["建立", "新增", "create", "add", "tool", "工具"]):
                try:
                    if self.rebirth:
                        self.rebirth.queue_upgrade(topic, action)
                        enhanced += 1
                except Exception:
                    pass

            # 如果建議搜尋更好的替代品
            if any(kw in action for kw in ["搜尋", "尋找", "search", "find", "替代"]):
                try:
                    if self.rebirth:
                        self.rebirth.queue_upgrade(topic, f"搜尋替代品: {action}")
                        enhanced += 1
                except Exception:
                    pass

            # 如果有具體的學習，記錄到進化日誌
            if lrn.get("confidence", 0) >= 0.7:
                try:
                    if self.awareness:
                        self.awareness.record_event("evolution_enhance",
                            f"進化增強: {topic} — {lrn.get('insight', '')[:100]}")
                except Exception:
                    pass

        with self._lock:
            self.state["total_enhanced"] += enhanced

        return enhanced

    # =========================================
    # 步驟 6：排除 (exclude)
    # =========================================

    def exclude(self, bad_learnings: List[Dict]):
        """排除壞的知識"""
        if not bad_learnings:
            return

        excluded = self._load_json(self.bad_file)
        for lrn in bad_learnings:
            excluded.append({
                "topic": lrn.get("topic", "未知"),
                "insight": lrn.get("insight", "")[:150],
                "reason": f"信心過低 ({lrn.get('confidence', 0):.2f})",
                "excluded_at": datetime.now().isoformat(),
            })
        self._save_json(self.bad_file, excluded)

        with self._lock:
            self.state["total_excluded"] += len(bad_learnings)

        # 記錄到自我意識
        try:
            if self.awareness:
                self.awareness.add_known_limit(
                    f"低品質知識已排除: {bad_learnings[0].get('topic', '') if bad_learnings else ''}"
                )
        except Exception:
            pass

    # =========================================
    # 步驟 7：執行完整循環
    # =========================================

    def _calculate_business_score(self) -> int:
        """
        計算商業產出分數（取代原有的內部進化分數）
        
        分數組成：
        - 每產出一個檔案 +5
        - 每 1000 字內容 +3
        - 每完成一個商業管線階段 +10
        - 網站已部署 +15
        - Cloudflare 已設定 +10
        """
        score = 0
        outputs_dir = self.base_dir / "outputs"

        if not outputs_dir.exists():
            return 0

        # 掃描所有產出檔案
        total_files = 0
        total_size = 0
        pipeline_stages = set()

        for f in outputs_dir.rglob("*"):
            if f.is_file() and f.suffix not in (".gitkeep",):
                total_files += 1
                try:
                    content = f.read_text(encoding="utf-8")
                    total_size += len(content)

                    # 辨識管線階段
                    rel = str(f.relative_to(outputs_dir))
                    if "ebooks/ch" in rel:
                        pipeline_stages.add("ebook")
                    if "children_book" in rel:
                        pipeline_stages.add("children")
                    if "research/platform" in rel:
                        pipeline_stages.add("platform_research")
                    if "research/cloudflare" in rel:
                        pipeline_stages.add("cloudflare")
                    if "website/index.html" in rel:
                        pipeline_stages.add("website")
                    if "research/business_strategy" in rel:
                        pipeline_stages.add("business_strategy")
                    if "research/service_flow" in rel:
                        pipeline_stages.add("service_flow")
                except:
                    pass

        # 計分
        score += total_files * 5  # 每個檔案 5 分
        score += (total_size // 1000) * 3  # 每 1000 字 3 分
        score += len(pipeline_stages) * 10  # 每個完成階段 10 分

        return score

    def run_cycle(self) -> Dict:
        """執行一次完整進化循環，回傳結果摘要"""
        with self._lock:
            self.state["cycle_count"] += 1
            self.state["last_cycle"] = datetime.now().isoformat()

            # ← 吸收
            sources = self.absorb()

            # ← 學習
            learnings = self.learn(sources)

            # ← 篩選
            selected = self.select(learnings)
            good = selected["good"]
            bad = selected["bad"]

            # ← 記憶
            self.remember(good)

            # ← 增強
            enhanced_count = self.enhance(good)

            # ← 排除
            self.exclude(bad)

            # 計算進化分數（以商業產出為核心指標）
            business_score = self._calculate_business_score()
            self.state["evolution_score"] = business_score

            result = {
                "cycle": self.state["cycle_count"],
                "absorbed": len(sources),
                "learned": len(learnings),
                "good": len(good),
                "bad": len(bad),
                "enhanced": enhanced_count,
                "score": self.state["evolution_score"],
                "business_output": business_score,
            }

            self.state["cycle_history"].append({
                "ts": datetime.now().isoformat(),
                **result,
            })
            if len(self.state["cycle_history"]) > 50:
                self.state["cycle_history"] = self.state["cycle_history"][-50:]

        self._save_state()
        return result

    # =========================================
    # 自動循環背景執行緒
    # =========================================

    def start_auto_cycle(self, interval_seconds: int = 600):
        """啟動背景自動進化循環（每 N 秒一次）"""
        def loop():
            # 首次延遲，等系統穩定
            time.sleep(30)
            while True:
                try:
                    result = self.run_cycle()
                    msg = (f"🧬 進化 #{result['cycle']}: "
                           f"產出分數 {result.get('business_output', result['score'])} → "
                           f"吸收{result['absorbed']}條 → "
                           f"學習{result['learned']}條 → "
                           f"取{result['good']}捨{result['bad']}")
                    print(msg)
                except Exception as e:
                    print(f"[進化循環] 錯誤: {e}")
                time.sleep(interval_seconds)

        t = threading.Thread(target=loop, daemon=True)
        t.start()
        print(f"[進化循環] 自動循環已啟動（每 {interval_seconds} 秒）")

    # =========================================
    # 摘要報告
    # =========================================

    def get_summary(self) -> str:
        """進化摘要報告（以商業產出為核心）"""
        with self._lock:
            s = self.state
        # 計算當前商業產出
        biz_score = self._calculate_business_score()
        outputs_dir = self.base_dir / "outputs"
        file_count = 0
        total_chars = 0
        if outputs_dir.exists():
            for f in outputs_dir.rglob("*"):
                if f.is_file() and f.suffix not in (".gitkeep",):
                    file_count += 1
                    try:
                        total_chars += len(f.read_text(encoding="utf-8"))
                    except:
                        pass
        return (
            f"🧬 黑曜進化報告:\n"
            f"  循環次數: {s['cycle_count']}\n"
            f"  商業分數: {biz_score}\n"
            f"  產出檔案: {file_count} 個\n"
            f"  總字數: {total_chars:,} 字\n"
            f"  進化目標: 幫老大賺錢"
        )

    def status(self) -> dict:
        with self._lock:
            s = self.state
        return {
            "name": self.name,
            "alive": self.is_alive(),
            "cycles": s["cycle_count"],
            "evolution_score": s["evolution_score"],
            "total_enhanced": s["total_enhanced"],
        }
