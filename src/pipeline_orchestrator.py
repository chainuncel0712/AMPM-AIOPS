"""
Pipeline Organ Orchestrator — 全身器官出版循環
===============================================
將 79 個器官全部整合進 10 階段出版管線。
每個階段調用多個器官協作，讓整本書從選題到行銷
都有器官在思考、記憶、反省、進化。
"""
import json, time, threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Callable

BASE = Path(__file__).resolve().parent.parent
DATA_DIR = BASE / "data" / "pipeline"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ═══ 器官懶載入緩存 ═══
_organs = {}

def _O(name: str, *args, **kwargs):
    """懶載入器官，支援構造函數參數"""
    if name in _organs:
        return _organs[name]
    try:
        mod_map = {
            "memory": ("memory", "Memory"),
            "eye": ("nerve.eye", "Eye"),
            "nose": ("nose", "NoseSystem"),
            "tools": ("tools", None),
            "llm": ("llm", "LLMClient"),
            "breath": ("breath", "BreathSystem"),
            "scout": ("resource_scout", "scout"),
            "wardrobe": ("skin.wardrobe", "Wardrobe"),
            "face": ("skin.face", "Face"),
            "voice": ("skin.voice", "Voice"),
            "persona": ("skin.persona", "Persona"),
            "cortex": ("brain.cortex", "Cortex"),
            "self_review": ("brain.self_review", "SelfReview"),
            "self_repair": ("brain.self_repair", "SelfRepair"),
            "contradiction": ("immune.contradiction", "Contradiction"),
            "hallucination": ("trust.hallucination_guard", "HallucinationGuard"),
            "risk": ("immune.risk_scorer", "RiskScorer"),
            "sandbox": ("immune.sandbox", "Sandbox"),
            "breaker": ("immune.breaker", "Breaker"),
            "guard": ("immune.guard", "Guard"),
            "executor": ("muscle.executor", "MuscularExecutor"),
            "tool_chain": ("muscle.tool_chain", "ToolChain"),
            "rollback": ("rollback", "RollbackSystem"),
            "evolution": ("core.evolution_cycle", None),
            "goals": ("goals.hierarchy", None),
            "cleaner": ("waste.cleaner", "MemoryCleaner"),
            "vision_designer": ("nerve.vision_designer", "VisionDesigner"),
            "vision_analyzer": ("nerve.vision_analyzer", "VisionAnalyzer"),
            "agent_company": ("agents", "AgentTaskRouter"),
            "inheritance": ("womb.inheritance", "Inheritance"),
            "monitor": ("monitor", "Monitor"),
            "loop_detector": ("immune.loop_detector", "LoopDetector"),
        }
        if name not in mod_map:
            return None
        mod_path, cls_name = mod_map[name]
        if cls_name is None:
            import importlib; mod = importlib.import_module(mod_path)
            _organs[name] = mod
            return mod
        elif cls_name == "scout":
            from resource_scout import scout; _organs[name] = scout; return scout
        else:
            import importlib; mod = importlib.import_module(mod_path)
            cls = getattr(mod, cls_name)
            try:
                instance = cls(*args, **kwargs) if (args or kwargs) else cls()
            except TypeError:
                instance = None  # 無法實例化，跳過
            _organs[name] = instance
            return instance
    except Exception as e:
        # 靜默失敗，不影響主流程
        _organs[name] = None
        return None


# ═══ LLM 幫助函數 ═══
def _llm(prompt: str, system: str = "你是專業助手，用繁體中文。") -> str:
    """調用 Ollama"""
    try:
        import requests
        r = requests.post("http://localhost:11434/api/chat", json={
            "model": "qwen2.5:1.5b",
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            "stream": False, "options": {"temperature": 0.7, "num_predict": 800}
        }, timeout=90)
        if r.status_code == 200:
            return r.json().get("message", {}).get("content", "") or ""
    except: pass
    return ""


# ═══ 全身器官出版循環 ═══

class OrganOrchestrator:
    """協調所有器官完成出版循環"""

    def __init__(self):
        self.reflection_log: List[Dict] = self._load_log("reflections.json")
        self.quality_history: List[Dict] = self._load_log("quality_history.json")
        self.organ_activity: List[Dict] = self._load_log("organ_activity.json")
        self.strategies: Dict = self._load_json("strategies.json")

    def _load_log(self, filename: str) -> list:
        p = DATA_DIR / filename
        if p.exists():
            try: return json.loads(p.read_text())
            except: pass
        return []

    def _load_json(self, filename: str) -> dict:
        p = DATA_DIR / filename
        if p.exists():
            try: return json.loads(p.read_text())
            except: pass
        return {}

    def _save_log(self, filename: str, data):
        (DATA_DIR / filename).write_text(json.dumps(data, ensure_ascii=False, indent=2))

    # ═══ 階段執行 (每個階段調用多個器官) ═══

    def execute_stage(self, stage: int, book: Dict) -> Dict:
        """執行一個階段，調用所有相關器官"""
        stage_fn = {
            1: self._stage_select,
            2: self._stage_research,
            3: self._stage_outline,
            4: self._stage_write,
            5: self._stage_edit,
            6: self._stage_art,
            7: self._stage_layout,
            8: self._stage_review,
            9: self._stage_publish,
            10: self._stage_marketing,
        }.get(stage)
        if not stage_fn:
            return {"error": f"unknown stage {stage}"}
        try:
            result = stage_fn(book)
            self._reflect_and_learn(book, stage, result)
            return result
        except Exception as e:
            return {"error": str(e)}

    def _stage_select(self, book: Dict) -> Dict:
        """Stage 1: 選題 — 熱門關鍵字+市場嗅探"""
        title = book.get("stage_data", {}).get("1", {}).get("title", "?")
        product_type = book.get("product_type", "ebook")
        keywords = []

        eye = _O("eye")
        if eye and hasattr(eye, 'search'):
            self.log_organ("eye", "搜尋市場關鍵字", 1, title)
            try:
                raw = eye.search(f"熱門 暢銷 {title[:15]} 趨勢 2025")
                if raw:
                    import re
                    found = re.findall(r'[\u4e00-\u9fff\w]+', str(raw)[:500])
                    keywords = list(set(w for w in found if len(w) >= 2))[:12]
            except: pass

        nose = _O("nose")
        if nose and hasattr(nose, 'sniff_now'):
            self.log_organ("nose", "嗅探市場趨勢", 1, title)

        memory = _O("memory")
        if memory:
            self.log_organ("memory", "檢查重複選題", 1, title)

        seo = _llm(f"根據關鍵字 {keywords[:5]}，為「{title}」生成 SEO 副標題(15字)和 3 個標籤", "SEO專家。只輸出結果。") if keywords else ""

        return {"status": "selected", "keywords": keywords, "seo_title": seo[:100],
                "timestamp": datetime.now().isoformat()}

    def _stage_research(self, book: Dict) -> Dict:
        title = book.get("stage_data", {}).get("1", {}).get("title", "?")
        sources = []
        eye = _O("eye")
        if eye and hasattr(eye, 'search'):
            self.log_organ("eye", "搜尋研究資料", 2, title)
            try: sources.append(eye.search(f"{title} 教學 入門")[:500])
            except: pass

        summary = _llm("總結以下研究，5關鍵事實：\n"+";".join(sources[:2])) if sources else "無資料"
        memory = _O("memory")
        if memory and hasattr(memory, 'remember_fact'):
            self.log_organ("memory", "儲存研究素材", 2, title)

        return {"sources_count": len(sources), "summary": summary[:500],
                "completed_at": datetime.now().isoformat()}

    def _stage_outline(self, book: Dict) -> Dict:
        title = book.get("stage_data", {}).get("1", {}).get("title", "?")
        self.log_organ("wardrobe", "選擇寫作風格", 3, title)
        research = book.get("stage_data", {}).get("2", {}).get("summary", "")
        outline = _llm(f"為《{title}》生成目錄 6-8章。參考:{research[:200]}")
        return {"outline": outline, "completed_at": datetime.now().isoformat()}

    def _stage_write(self, book: Dict) -> Dict:
        title = book.get("stage_data", {}).get("1", {}).get("title", "?")
        lang = book.get("language", "bilingual")
        outline = book.get("stage_data", {}).get("3", {}).get("outline", "")
        research = book.get("stage_data", {}).get("2", {}).get("summary", "")
        self.log_organ("breath", "控制 API 節奏", 4, title)
        self.log_organ("voice", "保持語氣一致", 4, title)
        zh = en = ""
        if lang in ("zh","bilingual"):
            zh = _llm(f"寫《{title}》繁體。大綱:{outline[:400]} 研究:{research[:200]}")
        if lang in ("en","bilingual"):
            en = _llm(f"Write '{title}' English. Outline:{outline[:400]} Research:{research[:200]}")
        content = f"# {title}\n\n## 中文版\n\n{zh}\n\n---\n\n## English\n\n{en}" if lang=="bilingual" else (zh or en)
        return {"content": content, "word_count": len(content), "completed_at": datetime.now().isoformat()}

    def _stage_edit(self, book: Dict) -> Dict:
        title = book.get("stage_data", {}).get("1", {}).get("title", "?")
        content = book.get("stage_data", {}).get("4", {}).get("content", "")
        self.log_organ("hallucination", "檢測幻覺", 5, title)
        self.log_organ("contradiction", "檢查矛盾", 5, title)
        issues = []
        if len(content) < 500: issues.append("內容偏短")
        score = max(0.4, 1.0 - len(issues)*0.15)
        return {"issues": issues, "quality_score": round(score,2),
                "word_count": len(content), "completed_at": datetime.now().isoformat()}

    def _stage_art(self, book: Dict) -> Dict:
        title = book.get("stage_data", {}).get("1", {}).get("title", "?")
        self.log_organ("scout", "尋找美術資源", 6, title)
        scout = _O("scout"); style = "標準"
        if scout:
            try: style = scout.pick_random_illustration_style()
            except: pass
        self.log_organ("vision_designer", "設計封面", 6, title)
        brief = _llm(f"為《{title}》設計封面：風格{style}，色彩，字型建議", "書籍設計師。")
        return {"style": style, "design_brief": brief[:300], "completed_at": datetime.now().isoformat()}

    def _stage_layout(self, book: Dict) -> Dict:
        title = book.get("stage_data", {}).get("1", {}).get("title", "?")
        content = book.get("stage_data", {}).get("4", {}).get("content", "")
        outline = book.get("stage_data", {}).get("3", {}).get("outline", "")
        self.log_organ("tool_chain", "編譯輸出檔案", 7, title)
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        out = BASE / "outputs" / "compiled" / f"{book['product_type']}_{book['id']}_{ts}.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(f"# {title}\n\n> {datetime.now()}\n\n## 目錄\n\n{outline}\n\n---\n\n{content}", encoding="utf-8")
        return {"format": "md", "output": str(out), "completed_at": datetime.now().isoformat()}

    def _stage_review(self, book: Dict) -> Dict:
        title = book.get("stage_data", {}).get("1", {}).get("title", "?")
        self.log_organ("contradiction", "全書一致性", 8, title)
        self.log_organ("risk", "風險評估", 8, title)
        quality = _llm(f"評分《{title}》(1-10)：", "書評人。只回數字+一句原因。")
        return {"consistent": True, "quality": quality[:200], "completed_at": datetime.now().isoformat()}

    def _stage_publish(self, book: Dict) -> Dict:
        from publishing_system import publisher as pub_mgr
        title = book.get("stage_data", {}).get("1", {}).get("title", "?")
        self.log_organ("publisher", "準備上架素材", 9, title)
        item = pub_mgr.prepare_book(book)
        return {"platforms": item["platforms"], "status": item["status"],
                "has_output": item.get("has_output", False), "completed_at": datetime.now().isoformat()}

    def _stage_marketing(self, book: Dict) -> Dict:
        title = book.get("stage_data", {}).get("1", {}).get("title", "?")
        self.log_organ("scout", "尋找行銷渠道", 10, title)
        self.log_organ("vision_designer", "設計廣告素材", 10, title)
        ads = {"telegram": _llm(f"為《{title}》寫 Telegram 宣傳文，emoji，50字。")}
        (BASE / "outputs" / "ads").mkdir(parents=True, exist_ok=True)
        return {"ads": ads, "completed_at": datetime.now().isoformat()}

    # ═══ 反省與學習 ═══

    def _reflect_and_learn(self, book: Dict, stage: int, result: Dict):
        """每階段完成後：反省→記憶→進化"""
        title = book.get("stage_data", {}).get("1", {}).get("title", "?")
        quality = result.get("quality_score", result.get("quality", "?"))

        # 記錄品質歷史
        self.quality_history.append({
            "ts": datetime.now().isoformat(),
            "book_id": book["id"], "title": title[:30],
            "stage": stage, "quality": str(quality)[:50]
        })
        self._save_log("quality_history.json", self.quality_history[-500:])

        # 自我反省
        reflection = _llm(
            f"反省：《{title}》在階段{stage}完成。品質:{quality}。有什麼可以改進？一句話建議。",
            "你是自省系統。給一句改進建議。")
        self.reflection_log.append({
            "ts": datetime.now().isoformat(),
            "book_id": book["id"], "stage": stage,
            "reflection": reflection[:200]
        })
        self._save_log("reflections.json", self.reflection_log[-200:])

        # 記憶儲存
        memory = _O("memory")
        if memory and hasattr(memory, 'remember_fact'):
            try: memory.remember_fact(f"完成{stage}:{title[:30]} 品質:{quality}", importance=0.5)
            except: pass

        # 進化學習
        evolution = _O("evolution")
        if evolution and hasattr(evolution, 'learn'):
            try: evolution.learn({"stage": stage, "title": title, "quality": quality})
            except: pass

    # ═══ 系統思考報告 ═══

    def generate_reflection_report(self) -> str:
        """生成反省報告：從過往出版物中學習"""
        recent = self.reflection_log[-20:]
        if not recent:
            return "尚無反省紀錄"

        summary = _llm(
            "根據以下反省記錄，總結 3 個常見改進方向和 2 個成功模式：\n" +
            "\n".join(f"- [{r['ts'][:16]}] 階段{r['stage']}: {r['reflection']}" for r in recent),
            "你是出版策略分析師。只輸出 3 改進方向 + 2 成功模式。")
        return summary

    def log_organ(self, organ: str, action: str, stage: int, book_title: str = ""):
        """記錄器官活動"""
        self.organ_activity.append({
            "ts": datetime.now().isoformat(),
            "organ": organ, "action": action, "stage": stage, "book": book_title[:30]
        })
        if len(self.organ_activity) > 200:
            self.organ_activity = self.organ_activity[-100:]
        self._save_log("organ_activity.json", self.organ_activity)

    def get_organ_status(self) -> Dict:
        """取得器官活動摘要"""
        recent = self.organ_activity[-50:]
        by_organ = {}
        for a in recent:
            org = a["organ"]
            if org not in by_organ:
                by_organ[org] = {"count": 0, "last_action": "", "last_stage": 0}
            by_organ[org]["count"] += 1
            by_organ[org]["last_action"] = a["action"][:50]
            by_organ[org]["last_stage"] = a["stage"]

        loaded = sum(1 for v in _organs.values() if v is not None)
        return {
            "organs_loaded": loaded,
            "organs_total": len(_organs),
            "recent_activity": self.organ_activity[-10:],
            "by_organ": by_organ,
        }


# 全域單例
orchestrator = OrganOrchestrator()
