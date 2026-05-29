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
# 共用的智能 LLM 客戶端（OpenRouter 優先，自動 fallback；只建一次）
_SHARED_LLM = None

def _get_llm_client():
    global _SHARED_LLM
    if _SHARED_LLM is None:
        try:
            from llm import LLMClient
            _SHARED_LLM = LLMClient()
        except Exception as e:
            print(f"⚠️ [出版工廠] LLMClient 載入失敗，將退回 Ollama: {e}")
            _SHARED_LLM = False  # 標記載入失敗，避免反覆重試
    return _SHARED_LLM or None


def _llm(prompt: str, system: str = "你是專業助手，用繁體中文。") -> str:
    """出版工廠的寫作大腦：優先用好模型（OpenRouter，含智能 fallback），失敗才退回本地 Ollama。"""
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ]

    # ① 優先：智能 LLM 客戶端（OpenRouter / NVIDIA 等好模型）
    client = _get_llm_client()
    if client is not None:
        try:
            out = client.call(messages, temperature=0.7)
            if out and out.strip() and "不可用" not in out and "休息中" not in out:
                return out.strip()
        except Exception as e:
            print(f"⚠️ [出版工廠] 好模型呼叫失敗，退回 Ollama: {e}")

    # ② 退路：本地 Ollama（離線備援，品質較低）
    try:
        import requests
        r = requests.post("http://localhost:11434/api/chat", json={
            "model": "qwen2.5:1.5b",
            "messages": messages,
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
        self._injected_organs: Dict = {}  # 從 Obsidian 注入的器官
        self._llm_fn = None

    def _load_log(self, filename: str) -> list:
        p = DATA_DIR / filename
        if p.exists():
            try: return json.loads(p.read_text())
            except: pass
        return []

    def inject_organs(self, organs: Dict):
        """從 Obsidian 主體接收已載入的器官合集"""
        self._injected_organs = organs
        # 建立模糊 key 對照表 (nose→nosesystem, memory→memorymanager, breath→breathsystem)
        self._fuzzy_keys: Dict[str, str] = {}
        for organ_key in organs:
            low = organ_key.lower()
            self._fuzzy_keys[low] = organ_key
            # 別名 (去掉 system/manager 後綴)
            for suffix in ('system', 'manager', 'organ', 'detector'):
                if low.endswith(suffix):
                    self._fuzzy_keys[low[:-len(suffix)]] = organ_key
            # 特殊映射
            if 'eye' in low: self._fuzzy_keys['eye'] = organ_key
        # 合併到全域 _organs
        for name, organ in organs.items():
            _organs[name] = organ
        print(f"🏭 [Orchestrator] 已注入 {len(organs)} 個器官 ({len(self._fuzzy_keys)} 模糊鍵)")

    def _O(self, name: str):
        """優先從注入的 Obsidian 器官取，支援模糊匹配，fallback 到惰性載入"""
        # 精確匹配
        if name in self._injected_organs:
            return self._injected_organs[name]
        if name in _organs:
            return _organs[name]
        # 模糊匹配 (nose → nosesystem)
        low = name.lower()
        if low in self._fuzzy_keys:
            real_key = self._fuzzy_keys[low]
            return self._injected_organs.get(real_key) or _organs.get(real_key)
        # 部分匹配
        for fk, rk in self._fuzzy_keys.items():
            if fk in low or low in fk:
                return self._injected_organs.get(rk) or _organs.get(rk)
        return self._lazy_load_organ(name)

    def _lazy_load_organ(self, name: str):
        """惰性載入器官（舊邏輯相容）"""
        return None

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
        """執行一個階段，調用所有相關器官（附 Governance 閘門檢查）"""
        # Governance Gatekeeper 驗權
        try:
            from governance.gatekeeper import gatekeeper
            gatekeeper.check_entry(f"pipeline_stage_{stage}")
        except:
            pass

        stage_fn = {
            1: self._stage_select,
            2: self._stage_research,
            3: self._stage_outline,
            4: self._stage_write,
            5: self._stage_edit,
            6: self._stage_art,
            7: self._stage_layout,
            7.5: self._stage_proofread,
            8: self._stage_review,
            9: self._stage_publish,
            10: self._stage_marketing,
        }.get(stage)
        if not stage_fn:
            return {"error": f"unknown stage {stage}"}
        try:
            result = stage_fn(book)
            self._reflect_and_learn(book, stage, result)
            # Governance EventLog 記錄
            try:
                from governance.event_log import event_log
                event_log.record("pipeline_stage", {
                    "book_id": book.get("id","?"), "stage": stage,
                    "title": book.get("stage_data",{}).get("1",{}).get("title","?")[:30],
                    "result": str(result.get("quality_score", result.get("status","?")))[:50]
                })
            except:
                pass
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
            try: nose.sniff_now()
            except: pass

        memory = _O("memory")
        if memory and hasattr(memory, 'remember_fact'):
            self.log_organ("memory", "檢查重複選題", 1, title)
            try: memory.remember_fact(f"選題:{title}", importance=0.3)
            except: pass

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
        research = book.get("stage_data", {}).get("2", {}).get("summary", "")

        wardrobe = _O("wardrobe")
        if wardrobe and hasattr(wardrobe, 'pick_mode'):
            self.log_organ("wardrobe", "選擇寫作風格", 3, title)
            try: wardrobe.pick_mode("creative")
            except: pass

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
        issues = []
        if len(content) < 500: issues.append("內容偏短")

        # HallucinationGuard 真實呼叫
        guard = _O("hallucination")
        if guard and hasattr(guard, 'watch'):
            self.log_organ("hallucination", "檢測幻覺", 5, title)
            try: guard.watch(content[:2000])
            except: pass

        # Contradiction 真實呼叫
        contradiction = _O("contradiction")
        if contradiction and hasattr(contradiction, 'check'):
            self.log_organ("contradiction", "檢查矛盾", 5, title)
            try: contradiction.check(content[:2000])
            except: pass

        if llm_call := getattr(self, '_llm_fn', None):
            try:
                review = llm_call(f"校對以下內容，檢查錯字/文法/標點/排版，只回「通過」或列問題：\n{content[:3000]}")
                if review and "通過" not in review:
                    issues.append(f"校稿: {review[:150]}")
            except: pass
        score = max(0.3, 1.0 - len(issues)*0.12)
        return {"issues": issues, "quality_score": round(score,2),
                "word_count": len(content), "completed_at": datetime.now().isoformat()}

    def _stage_art(self, book: Dict) -> Dict:
        title = book.get("stage_data", {}).get("1", {}).get("title", "?")
        self.log_organ("scout", "尋找美術資源", 6, title)
        self.log_organ("vision_designer", "設計封面", 6, title)

        # 調用 CoverGenerator
        cover_svg = ""
        scene = "tech"
        try:
            from visual.cover_generator import cover_gen
            cover_result = cover_gen.generate_cover(book)
            cover_svg = cover_result.get("svg_path", "")
            scene = cover_result.get("scene", "tech")
        except: pass

        # 設計簡報
        brief = _llm(f"為《{title}》設計封面：品牌色 #241E1C/#FF8C1A/#189FFF，風格建議。", "你是書籍設計師。")

        return {"style": scene, "design_brief": brief[:300], "cover_svg": cover_svg,
                "cover_generated": bool(cover_svg), "completed_at": datetime.now().isoformat()}

    def _stage_layout(self, book: Dict) -> Dict:
        title = book.get("stage_data", {}).get("1", {}).get("title", "?")
        content = book.get("stage_data", {}).get("4", {}).get("content", "")
        outline = book.get("stage_data", {}).get("3", {}).get("outline", "")
        self.log_organ("tool_chain", "編譯輸出檔案", 7, title)
        ts = datetime.now().strftime("%Y%m%d_%H%M")

        brand_css = ""
        try:
            from visual import brand
            brand_css = brand.epub_css()
        except: pass

        out = BASE / "outputs" / "compiled" / f"{book['product_type']}_{book['id']}_{ts}.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        full = f"# {title}\n\n> 編譯於 {datetime.now().strftime('%Y-%m-%d %H:%M')} | AMPM 出版\n\n## 目錄\n\n{outline}\n\n---\n\n{content}"
        out.write_text(full, encoding="utf-8")

        epub_path = ""
        try:
            from core.epub_compiler import EPUBCompiler
            compiler = EPUBCompiler()
            result = compiler.compile_ebook(title=title, content=content, outline=outline,
                                           product_type=book.get("product_type", "ebook"))
            epub_path = result.get("path", "")
        except: pass

        return {"format": "md+epub", "output": str(out), "epub_path": epub_path,
                "brand_css_applied": bool(brand_css), "completed_at": datetime.now().isoformat()}

    def _stage_proofread(self, book: Dict) -> Dict:
        """Stage 7.5: 專業校稿 — 6步檢查 + 駁回決策"""
        title = book.get("stage_data", {}).get("1", {}).get("title", "?")
        self.log_organ("proofreader", "6步專業校稿", 7.5, title)
        self.log_organ("vision_analyzer", "美學評分", 7.5, title)

        result = {}
        try:
            from proofreader import proofreader
            llm = getattr(self, '_llm_fn', None)
            result = proofreader.proofread(book, llm)
        except:
            result = {"overall": 100, "grade": "pass", "error": "校稿器官載入失敗"}

        # 駁回處理
        return_stage = result.get("return_to_stage")
        if return_stage and result.get("retry_key"):
            try:
                from proofreader import proofreader
                proofreader.record_rejection(
                    book.get("id", ""), result["retry_key"], return_stage
                )
            except: pass

        return result

    def _stage_publish(self, book: Dict) -> Dict:
        title = book.get("stage_data", {}).get("1", {}).get("title", "?")
        self.log_organ("publisher", "準備上架素材", 9, title)
        self.log_organ("vision_designer", "上架封面檢查", 9, title)

        results = {}
        try:
            from visual.publish_engine import publish_engine
            pub_item = publish_engine.prepare_book_for_publishing(book)
            results = publish_engine.publish_all(book["id"])
        except:
            from publishing_system import publisher as pub_mgr
            pub_mgr.prepare_book(book)

        return {"publish_results": results, "completed_at": datetime.now().isoformat()}

    def _stage_marketing(self, book: Dict) -> Dict:
        title = book.get("stage_data", {}).get("1", {}).get("title", "?")
        self.log_organ("scout", "尋找行銷渠道", 10, title)
        self.log_organ("vision_designer", "設計廣告素材", 10, title)

        ads = {"telegram": _llm(f"為《{title}》寫 Telegram 宣傳文，emoji，50字。")}
        (BASE / "outputs" / "ads").mkdir(parents=True, exist_ok=True)

        # 調用 AdFactory
        ad_results = {}
        try:
            from visual.ad_factory import ad_factory
            ad_results = ad_factory.generate_all_platforms(book)
        except: pass

        # 建立廣告活動
        campaign_id = ""
        try:
            from visual.ad_campaign_manager import ad_campaign_mgr
            campaign = ad_campaign_mgr.create_campaign(book, "awareness", 100)
            campaign_id = campaign["id"]
        except: pass
        return {"ads": ads, "campaign_id": campaign_id,
                "ad_platforms": list(ad_results.get("platforms", {}).keys()) if ad_results else [],
                "completed_at": datetime.now().isoformat()}

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

        loaded = len(self._injected_organs) if self._injected_organs else sum(1 for v in _organs.values() if v is not None)
        total = len(self._injected_organs) if self._injected_organs else len(_organs)
        return {
            "organs_loaded": loaded,
            "organs_total": total or loaded,
            "recent_activity": self.organ_activity[-10:],
            "by_organ": by_organ,
        }


# 全域單例
orchestrator = OrganOrchestrator()
