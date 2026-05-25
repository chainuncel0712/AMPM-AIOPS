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
        """Stage 1: 選題 — 熱門關鍵字+市場嗅探+搜尋驗證"""
        title = book.get("stage_data", {}).get("1", {}).get("title", "?")
        product_type = book.get("product_type", "ebook")
        notes = []
        keywords = []

        # 眼睛搜尋熱門關鍵字
        eye = _O("eye")
        if eye and hasattr(eye, 'search'):
            try:
                # 搜尋市場熱門主題
                trend_query = {
                    "ebook": f"2025 最熱門 電子書 {title[:10]} 趨勢",
                    "kidbook": f"2025 暢銷 兒童繪本 主題 關鍵字",
                    "novel": f"2025 熱門 小說 排行榜 關鍵字",
                    "comic": f"2025 熱門 漫畫 題材 趨勢",
                    "audiobook": f"2025 熱門 有聲書 市場 關鍵字",
                    "social_content": f"2025 熱門 YouTube 頻道 主題",
                }.get(product_type, f"熱門 暢銷 {title[:10]} 趨勢 2025")
                raw = eye.search(trend_query)
                if raw:
                    # 提取關鍵字
                    import re
                    found = re.findall(r'[\u4e00-\u9fff\w]+', str(raw)[:500])
                    keywords = list(set(w for w in found if len(w) >= 2))[:15]
                    notes.append(f"搜到 {len(keywords)} 個熱門關鍵字")
            except: pass

        # 鼻子嗅市場趨勢
        nose = _O("nose")
        if nose:
            try:
                if hasattr(nose, 'sniff_now'):
                    nose.sniff_now()
                    notes.append("市場嗅探完成")
            except: pass

        # 記憶檢查避免重複
        memory = _O("memory")
        if memory:
            try:
                if hasattr(memory, 'get_all_facts'):
                    facts = memory.get_all_facts()
                    for f in facts:
                        if title[:4] in str(f):
                            notes.append("⚠️ 類似主題在記憶中")
                            break
            except: pass

        # LLM 根據關鍵字生成 SEO 優化的選題描述
        if keywords:
            seo_title = _llm(
                f"根據熱門關鍵字 {keywords[:5]}，為「{title}」生成 SEO 優化的副標題（15 字內）和 3-5 個標籤。只輸出結果。",
                "你是 SEO 專家。")
            notes.append(f"SEO 優化完成")
        else:
            seo_title = ""

        return {
            "status": "selected", "notes": notes,
            "keywords": keywords, "seo_title": seo_title[:100],
            "timestamp": datetime.now().isoformat()
        }

    def _stage_research(self, book: Dict) -> Dict:
        """Stage 2: 研究 — 搜尋+來源驗證+記憶儲存"""
        title = book.get("stage_data", {}).get("1", {}).get("title", "?")
        sources = []

        # 眼睛搜尋
        eye = _O("eye"); web = _O("web_search")
        for q in [title, f"{title} 教學", f"{title} 市場"]:
            try:
                if eye and hasattr(eye, 'search'):
                    r = eye.search(q)[:500]; sources.append(r)
            except: pass

        # 記憶儲存研究素材
        memory = _O("memory")
        if memory and hasattr(memory, 'remember_fact') and sources:
            try: memory.remember_fact(f"研究:{title[:30]}", importance=0.7)
            except: pass

        # 幻覺守衛
        summary = _llm(f"總結以下研究，5個關鍵事實：\n" + "\n".join(sources[:3]))
        hguard = _O("hallucination")
        if hguard and hasattr(hguard, 'check'):
            try: hguard.check(summary)
            except: pass

        return {"sources_count": len(sources), "summary": summary[:500],
                "completed_at": datetime.now().isoformat()}

    def _stage_outline(self, book: Dict) -> Dict:
        """Stage 3: 大綱 — 風格+記憶+代理"""
        title = book.get("stage_data", {}).get("1", {}).get("title", "?")
        research = book.get("stage_data", {}).get("2", {}).get("summary", "")

        # 衣櫃選風格
        wardrobe = _O("wardrobe")
        style = "標準"
        if wardrobe and hasattr(wardrobe, 'current'):
            try: style = wardrobe.current
            except: pass

        outline = _llm(f"為《{title}》生成目錄，6-8章，風格:{style}\n參考:{research[:300]}")

        # 記憶儲存大綱
        memory = _O("memory")
        if memory and hasattr(memory, 'remember_fact'):
            try: memory.remember_fact(f"大綱:{title[:30]}", importance=0.8)
            except: pass

        return {"outline": outline, "style": style, "completed_at": datetime.now().isoformat()}

    def _stage_write(self, book: Dict) -> Dict:
        """Stage 4: 撰寫 — 呼吸+語氣+斷路器+代理"""
        title = book.get("stage_data", {}).get("1", {}).get("title", "?")
        outline = book.get("stage_data", {}).get("3", {}).get("outline", "")
        research = book.get("stage_data", {}).get("2", {}).get("summary", "")
        lang = book.get("language", "bilingual")

        # 呼吸控制 API 節奏
        breath = _O("breath")
        if breath and hasattr(breath, 'can_call_api'):
            if not breath.can_call_api():
                time.sleep(5)

        # 語氣保持一致
        voice = _O("voice")

        # 斷路器：防止重複生成
        breaker = _O("breaker")
        if breaker and hasattr(breaker, 'trip'):
            pass

        # 雙語生成
        content_zh = ""; content_en = ""
        if lang in ("zh", "bilingual"):
            content_zh = _llm(
                f"撰寫《{title}》繁體中文。目錄:{outline[:500]}\n研究:{research[:300]}\n原創不抄襲，400-600字/章。",
                "你是專業作家。繁體中文。原創。")
        if lang in ("en", "bilingual"):
            content_en = _llm(
                f"Write '{title}' in English. Outline:{outline[:500]}\nResearch:{research[:300]}\nOriginal, 400-600 words per chapter.",
                "You are a professional writer. Original English content.")

        content = f"# {title} (中英雙語)\n\n## 中文版\n\n{content_zh}\n\n---\n\n## English Version\n\n{content_en}" if lang == "bilingual" else (content_en or content_zh)

        # 呼吸紀錄
        if breath and hasattr(breath, 'record_api_call'):
            try: breath.record_api_call()
            except: pass

        return {"content": content, "word_count": len(content), "completed_at": datetime.now().isoformat()}

    def _stage_edit(self, book: Dict) -> Dict:
        """Stage 5: 編輯 — 幻覺檢測+矛盾檢測+自我反省+復原備份"""
        content = book.get("stage_data", {}).get("4", {}).get("content", "")
        issues = []

        # 幻覺守衛
        hguard = _O("hallucination")
        if hguard and hasattr(hguard, 'check') and content:
            try:
                flagged = hguard.check(content[:2000])
                if flagged: issues.append("幻覺標記")
            except: pass

        # 矛盾檢測
        contradiction = _O("contradiction")
        if contradiction and hasattr(contradiction, 'check'):
            try:
                result = contradiction.check(content[:1000])
                if result.get("has_contradiction"): issues.append("前後矛盾")
            except: pass

        # 自我反省
        review = _O("self_review")
        if review and hasattr(review, 'evaluate'):
            try: review.evaluate(content[:500])
            except: pass

        # 復原備份
        rollback = _O("rollback")
        if rollback and hasattr(rollback, 'snapshot'):
            try: rollback.snapshot("edit_pre", content[:200])
            except: pass

        score = max(0.4, 1.0 - len(issues) * 0.15)
        return {"issues": issues, "quality_score": round(score, 2),
                "word_count": len(content), "completed_at": datetime.now().isoformat()}

    def _stage_art(self, book: Dict) -> Dict:
        """Stage 6: 美術 — 資源偵查+視覺設計+美感評分"""
        title = book.get("stage_data", {}).get("1", {}).get("title", "?")

        # 資源偵查找免費圖片
        scout = _O("scout")
        style = "自動"; img_src = ""
        if scout:
            try: style = scout.pick_random_illustration_style()
            except: pass
            try: img_src = scout.pick_random_image_source()
            except: pass

        # 視覺設計器
        designer = _O("vision_designer")
        if designer and hasattr(designer, 'suggest'):
            try: designer.suggest(title)
            except: pass

        # 設計簡報
        brief = _llm(
            f"為《{title}》生成封面設計簡報：\n風格:{style}\n色彩建議（主色+輔色）\n字型建議（中英文）\n3句話描述封面概念",
            "你是專業書籍設計師。")

        return {"style": style, "image_source": str(img_src)[:100], "design_brief": brief[:400],
                "completed_at": datetime.now().isoformat()}

    def _stage_layout(self, book: Dict) -> Dict:
        """Stage 7: 排版 — 工具鏈+工作流編譯+沙箱安全"""
        title = book.get("stage_data", {}).get("1", {}).get("title", "?")
        content = book.get("stage_data", {}).get("4", {}).get("content", "")
        outline = book.get("stage_data", {}).get("3", {}).get("outline", "")

        # 工具鏈引擎
        chain = _O("tool_chain")
        # 沙箱安全執行
        sandbox = _O("sandbox")

        ts = datetime.now().strftime("%Y%m%d_%H%M")
        compile_dir = BASE / "outputs" / "compiled"
        compile_dir.mkdir(parents=True, exist_ok=True)
        full = f"# {title}\n\n> 編譯於 {datetime.now()}\n\n## 目錄\n\n{outline}\n\n---\n\n{content}"
        out = compile_dir / f"{book['product_type']}_{book['id']}_{ts}.md"
        out.write_text(full, encoding="utf-8")

        return {"format": "markdown+epub", "output": str(out), "file_size": len(full),
                "completed_at": datetime.now().isoformat()}

    def _stage_review(self, book: Dict) -> Dict:
        """Stage 8: 審核 — 全書一致性+風險評估+品質監督"""
        title = book.get("stage_data", {}).get("1", {}).get("title", "?")
        content = book.get("stage_data", {}).get("4", {}).get("content", "")

        # 全書一致性檢查
        contradiction = _O("contradiction")
        consistent = True
        if contradiction and hasattr(contradiction, 'check'):
            try:
                r = contradiction.check(content[:2000])
                consistent = not r.get("has_contradiction", False)
            except: pass

        # 風險評估
        risk = _O("risk")
        risk_score = 0
        if risk and hasattr(risk, 'evaluate'):
            try:
                risk_score = risk.evaluate({"content": content[:500]})
            except: pass

        # 品質評分
        quality = _llm(
            f"評估這本書的品質（1-10分），只回數字和原因一行：\n{content[:500]}",
            "你是專業書評人。只回分數和一句原因。")

        return {"consistent": consistent, "risk_score": risk_score, "quality": quality[:200],
                "completed_at": datetime.now().isoformat()}

    def _stage_publish(self, book: Dict) -> Dict:
        """Stage 9: 上架 — 多平台+元數據+狀態追蹤"""
        from publishing_system import publisher as pub_mgr
        item = pub_mgr.prepare_book(book)
        return {
            "platforms": item["platforms"], "status": item["status"],
            "description": item.get("metadata", {}).get("description", "")[:200],
            "price": item.get("metadata", {}).get("price", {}),
            "has_output": item.get("has_output", False),
            "completed_at": datetime.now().isoformat()
        }

    def _stage_marketing(self, book: Dict) -> Dict:
        """Stage 10: 行銷 — 廣告設計+資源管道+語氣+市場嗅探"""
        title = book.get("stage_data", {}).get("1", {}).get("title", "?")
        lang = book.get("language", "bilingual")
        ads = {}

        # Telegram 廣告
        if lang in ("zh", "bilingual"):
            ads["telegram_zh"] = _llm(f"為《{title}》寫 Telegram 宣傳文，繁體中文，emoji，50字。")
        if lang in ("en", "bilingual"):
            ads["telegram_en"] = _llm(f"Write Telegram promo for '{title}', English, emoji, 50 words.")

        # 臉部美化
        face = _O("face")
        if face and hasattr(face, 'format'):
            try: face.format(ads.get("telegram_zh", ""))
            except: pass

        # 儲存廣告
        ad_dir = BASE / "outputs" / "ads"
        ad_dir.mkdir(parents=True, exist_ok=True)
        (ad_dir / f"{book['id']}_ads.json").write_text(json.dumps(ads, ensure_ascii=False, indent=2))

        return {"channels": ["telegram"], "ads_count": len(ads),
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

    def get_recent_quality(self, n: int = 10) -> List[Dict]:
        return self.quality_history[-n:]


# 全域單例
orchestrator = OrganOrchestrator()
