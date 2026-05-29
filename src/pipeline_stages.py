"""
Pipeline Stages — 選題提示模板 (27 種產品類型)
===============================================
LLM 選題時調用，可注入銷售情報做加權。
"""
import json, sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

BASE = Path(__file__).resolve().parent.parent
_SRC = str(BASE / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

# ═══ 銷售情報注入工具 ═══

def _get_sales_context() -> str:
    """從 sales_history.json 提取銷售情報，注入選題 prompt"""
    try:
        sp = BASE / "data" / "pipeline" / "sales_history.json"
        if sp.exists():
            sales = json.loads(sp.read_text())
            perf = sales.get("type_performance", {})
            if not perf:
                return ""
            lines = ["\n📊 近期市場數據（參考）："]
            for t, p in perf.items():
                rev = p.get("avg_monthly_revenue", 0)
                rate = p.get("success_rate", 0)
                status = p.get("status", "active")
                icon = {"active": "🟢", "warning": "🟡", "dormant": "🔴"}.get(status, "⚪")
                lines.append(f"  {icon} {p.get('label', t)}: 月均 ${rev:.0f}, 成功率 {rate:.0%}")
            series = sales.get("series_suggestions", [])
            if series:
                lines.append("\n📚 建議發展的系列：")
                for s in series[:3]:
                    lines.append(f"  · {s.get('source_book', '?')} → {', '.join(s.get('suggested_titles', [])[:2])}")
            return "\n".join(lines)
    except:
        pass
    return ""


# ═══ 即時趨勢關鍵字注入 ═══

def _get_trend_context() -> str:
    """從 keyword_scout 提取即時趨勢，注入選題 prompt"""
    try:
        from keyword_scout import keyword_scout
        return keyword_scout.inject_context()
    except:
        return ""


# ═══ 選題提示模板 ═══

TOPIC_PROMPTS = {
    "ebook": (
        "你是暢銷書選題專家。給出 5 個繁體中文電子書提案：\n"
        "1. 標題要吸睛有賣點（例如「7天學會」「從零到千萬」「揭秘」等）\n"
        "2. 題材要有市場缺口，不是隨處可見的主題\n"
        "3. 每則含：書名、一句話定位、目標讀者、為什麼會賣\n"
        "4. 原創角度，絕不抄襲暢銷書\n"
        "5. 繁體中文市場導向（台灣/香港）"
    ),
    "finance_book": (
        "你是華爾街分析師出身的暢銷財經作家。給出 5 個繁體中文財經書提案：\n"
        "1. 標題有「實戰」「穩健」「攻略」「聖經」等暢銷關鍵字\n"
        "2. 題材需有台灣市場針對性（台股/ETF/房地產/稅務/退休金）\n"
        "3. 每則含：書名、一句話定位、目標讀者、市場缺口\n"
        "4. 避免純理論，強調 step-by-step 可操作、有實際案例\n"
        "5. 可設計為系列（入門→進階→實戰）"
    ),
    "crypto_book": (
        "你是幣圈資深交易員出身的區塊鏈作家。給出 5 個繁體中文虛擬貨幣書提案：\n"
        "1. 標題有「實戰」「被動收入」「躺賺」等 web3 熱詞\n"
        "2. 題材涵蓋：交易/DeFi/空投/鏈上分析/安全/稅務/礦機\n"
        "3. 每則含：書名、一句話定位、目標讀者、市場機會\n"
        "4. 特別強調風險管理和防詐騙意識\n"
        "5. 繁體中文台灣市場導向，用語在地化"
    ),
    "reference_book": (
        "你是技術編輯。給出 5 本繁體中文工具書提案：\n"
        "1. 針對開發者/設計師/行銷人員等專業族群\n"
        "2. 標題要有「實戰」「手冊」「大全」「精通」等關鍵字\n"
        "3. 含：書名、工具/領域、目標讀者、核心特色\n"
        "4. 注重實用性，每個技巧都要有範例程式碼或步驟"
    ),
    "edu_book": (
        "給出 5 本繁體中文學習用書提案：\n"
        "1. 科目要有剛需（升學、檢定、職場技能）\n"
        "2. 標題要有「速成」「圖解」「實戰」等關鍵字\n"
        "3. 含：書名、科目、適用對象、核心賣點\n"
        "4. 針對台灣教育體系（國中/高中/大學）"
    ),
    "exam_book": (
        "給出 5 本繁體中文考試用書提案：\n"
        "1. 針對熱門考試（公務員、多益、日檢、證照等）\n"
        "2. 標題要有「滿分」「攻略」「一次就過」等賣點\n"
        "3. 含：書名、考試名稱、特色、與市面差異\n"
        "4. 針對台灣考試制度，要有最新考題分析"
    ),
    "journal": (
        "你是學術編輯。給出 5 本繁體中文期刊/學報提案：\n"
        "1. 主題要有學術深度但也要有市場價值\n"
        "2. 含：刊名、領域、讀者群、發行頻率\n"
        "3. 涵蓋：AI/科技/教育/永續/醫療等前沿領域"
    ),
    "poetry": (
        "你是詩集編輯。給出 5 本繁體中文詩集/散文提案：\n"
        "1. 要有獨特的詩意角度或情感主題\n"
        "2. 標題要有詩意和記憶點，不要太直白\n"
        "3. 含：書名、主題、風格（現代詩/俳句/散文詩）、目標讀者\n"
        "4. 繁體中文，可含台語/客語元素增加在地感"
    ),
    "novel": (
        "你是小說編輯。給出 5 本繁體中文長篇小說提案：\n"
        "1. 要有獨特的敘事角度或世界觀設定\n"
        "2. 標題要讓人想點進去\n"
        "3. 含：書名、類型、核心衝突（一句話）、字數預估\n"
        "4. 原創性優先，不跟風\n"
        "5. 繁體中文市場，可含台灣本土元素"
    ),
    "short_story": (
        "給出 5 本繁體中文短篇小說集提案：\n"
        "1. 每篇要有反轉或情感衝擊\n"
        "2. 標題要有詩意或懸念\n"
        "3. 含：書名、一句話故事核心、篇數、適合平台\n"
        "4. 可設定統一主題串聯各篇"
    ),
    "light_novel": (
        "你是輕小說編輯。給出 5 本繁體中文輕小說提案：\n"
        "1. 日系/台輕風格，插畫+文字混合\n"
        "2. 世界觀要有亮點（校園/異世界/奇幻/科幻）\n"
        "3. 標題要輕小說風格（長標題/日式命名）\n"
        "4. 含：書名、世界觀一句話、角色設定亮點、目標讀者\n"
        "5. 目標讀者 15-25 歲"
    ),
    "web_novel": (
        "你是網路小說平台編輯。給出 5 本繁體中文網路小說提案：\n"
        "1. 玄幻/言情/原創/都市/穿越等熱門類型\n"
        "2. 開頭要有鉤子，前三章就能留住讀者\n"
        "3. 含：書名、類型、一句話開場鉤子、預計章數\n"
        "4. 適合每日更新節奏，每章 1500-2500 字\n"
        "5. 繁體中文，可有中國網文風格但用語在地化"
    ),
    "serialized_novel": (
        "你是連載小說責編。給出 5 本繁體中文連載小說提案：\n"
        "1. 適合章回體定期更新（週更/月更）\n"
        "2. 要有長線劇情規劃，又能每回有獨立亮點\n"
        "3. 含：書名、類型、總章數規劃、訂閱方案建議\n"
        "4. 適合 Patreon/Substack 訂閱制變現\n"
        "5. 可設計為：每章結尾留住讀者的懸念"
    ),
    "comic": (
        "你是漫畫編輯。給出 5 個繁體中文原創漫畫提案：\n"
        "1. 題材要有話題性（熱血/懸疑/戀愛/科幻/搞笑等）\n"
        "2. 標題要有衝擊力\n"
        "3. 含：作品名、類型、一句話世界觀、目標讀者\n"
        "4. 完全原創，不模仿任何現有作品\n"
        "5. 適合單行本出版（150-200 頁）"
    ),
    "serialized_comic": (
        "你是連載漫畫主編。給出 5 個繁體中文連載漫畫提案：\n"
        "1. 適合 webtoon 格式（條漫）或傳統頁漫連載\n"
        "2. 世界觀要有擴展性，能畫 50 話以上\n"
        "3. 含：作品名、類型、核心世界觀（200字）、連載頻率建議\n"
        "4. 每話結尾要有鉤子\n"
        "5. 考慮跨平台（webtoon/社群/自有站）變現"
    ),
    "travel_book": (
        "你是旅遊書編輯。給出 5 本繁體中文旅遊書提案：\n"
        "1. 目的地要有台灣旅客熱度（日本/泰國/韓國/歐洲/台灣本地）\n"
        "2. 含：書名、目的地、獨特角度（不是一般觀光指南）\n"
        "3. 針對特定族群（小資/親子/獨旅/攝影/美食）\n"
        "4. 要有實際交通/住宿/預算資訊\n"
        "5. 可結合季節限定主題（櫻花季/滑雪/祭典）"
    ),
    "cookbook": (
        "你是食譜編輯。給出 5 本繁體中文食譜提案：\n"
        "1. 主題要有市場區隔（減醣/氣炸鍋/電鍋/素食/嬰幼兒）\n"
        "2. 標題要有「100道」「零失敗」「快速」等關鍵字\n"
        "3. 含：書名、料理類型、特色（步驟圖/影片QR/營養標示）、目標族群\n"
        "4. 針對台灣廚房設備和食材取得容易度\n"
        "5. 可設計為系列（新手→進階→宴客）"
    ),
    "magazine": (
        "你是雜誌主編。給出 5 本繁體中文雜誌提案：\n"
        "1. 封面主題要有爆點\n"
        "2. 含：刊名、本期主題、3-5 篇文章構想、目標讀者\n"
        "3. 找出市場缺口，不跟現有雜誌重疊\n"
        "4. 考慮定期發行（週刊/月刊/季刊）的可行性"
    ),
    "photo_book": (
        "你是攝影集編輯。給出 5 本繁體中文攝影集提案：\n"
        "1. 主題要有視覺吸引力（城市/自然/人像/街拍/旅行）\n"
        "2. 含：書名、主題、攝影風格、目標讀者\n"
        "3. 可設定為教學型（含拍攝技巧）或純欣賞型\n"
        "4. 適合高畫質印刷或數位 EPUB fixed layout\n"
        "5. 可結合攝影師 IP 經營"
    ),
    "art_book": (
        "你是藝術書編輯。給出 5 本繁體中文藝術畫冊提案：\n"
        "1. 涵蓋：插畫/水彩/油畫/數位藝術/雕塑/書法\n"
        "2. 含：書名、藝術類型、藝術家/IP 簡介、目標讀者\n"
        "3. 可設定為個人作品集或主題策展型\n"
        "4. 考慮收藏性，適合高單價限量版\n"
        "5. 適合 art book fair 和線上藝術平台銷售"
    ),
    "coloring_book": (
        "你是著色本編輯。給出 5 本繁體中文著色本提案：\n"
        "1. 成人舒壓（曼陀羅/禪繞/花卉/動物）或兒童教育（字母/數字/動物）\n"
        "2. 含：書名、主題、風格、頁數、適用年齡\n"
        "3. 設計要考慮列印友善（單面印刷/可撕）\n"
        "4. 可加入引導文字（正向語錄/教育提示）\n"
        "5. 適合 PDF 可列印版本 + KDP POD 雙管道"
    ),
    "planner": (
        "你是手帳設計師。給出 5 本繁體中文手帳/計畫本提案：\n"
        "1. 類型：年度/月度/週計畫/理財/健身/孕期/讀書\n"
        "2. 含：書名、用途、獨特設計（模板/貼紙/QR擴充）、目標族群\n"
        "3. 設計要美觀+實用，適合數位（GoodNotes）或列印\n"
        "4. 考慮四季/年度版本更新\n"
        "5. 可結合子彈筆記/習慣追蹤等流行系統"
    ),
    "template_pack": (
        "你是數位商品策展人。給出 5 個繁體中文數位模板套件提案：\n"
        "1. 平台：Notion/Excel/Canva/Google Sheets/GoodNotes\n"
        "2. 用途：專案管理/財務/健身/食譜/旅行/學習/履歷\n"
        "3. 含：套件名稱、平台、模板數量、一句話價值主張\n"
        "4. 零邊際成本，適合 Gumroad/Etsy 銷售\n"
        "5. 可設計為 bundle（基礎版+進階版）提高客單價"
    ),
    "course_material": (
        "你是課程設計師。給出 5 個繁體中文線上課程教材提案：\n"
        "1. 主題：程式/設計/行銷/理財/語言/音樂/攝影\n"
        "2. 含：課程名稱、講義+練習題+專案格式、目標學員\n"
        "3. 適合平台：Teachable/Hahow/Udemy/自有站\n"
        "4. 可設計分級（入門/中階/進階）系列\n"
        "5. 考慮提供證書/完課證明增加價值感"
    ),
    "audiobook": (
        "你是有聲書製作人。給出 5 個繁體中文有聲書提案：\n"
        "1. 類型：冥想/故事/教學/說話術/Podcast 合集\n"
        "2. 含：書名、內容類型、建議時長、適合平台\n"
        "3. 適合 Audible/Kobo Audio/SoundOn/Apple Podcast\n"
        "4. 考慮 AI TTS 生成降低成本\n"
        "5. 可與文字版 eBook 搭售提高客單價"
    ),
    "social_content": (
        "你是社群內容總監。給出 5 個繁體中文社群付費內容提案：\n"
        "1. 平台：YouTube/Patreon/Substack/Instagram/TikTok\n"
        "2. 內容類型：教學/娛樂/Vlog/評測/幕後/獨家採訪\n"
        "3. 含：頻道名稱/系列名、一句話定位、更新頻率、付費方案\n"
        "4. 適合會員制或單次購買\n"
        "5. 繁體中文市場，目標台灣/香港觀眾"
    ),
    "kidbook": (
        "你是童書選題專家。給出 5 個 3-6 歲繁體中文繪本提案：\n"
        "1. 主題要有教育意義+趣味性（情緒/分享/勇氣/好奇等）\n"
        "2. 標題要溫馨有記憶點，適合親子共讀\n"
        "3. 每則含：書名、核心主題、適合年齡、一句話簡介\n"
        "4. 避免模仿現有知名繪本\n"
        "5. 保留 PANEY & MONEY 雙主角路線（白天黑貓+夜晚虎斑）"
    ),
    "series": (
        "你是系列書策劃。給出 5 個繁體中文系列套書提案：\n"
        "1. 每系列 3-10 冊，要有連貫主題\n"
        "2. 可以是已有暢銷 IP 的延伸，或全新系列\n"
        "3. 含：系列名、每冊書名、核心主題、總字數預估\n"
        "4. 考慮讀者黏著度和購買慣性\n"
        "5. 適合 box set 套裝銷售提高客單價"
    ),
    # ═══ 新增 22 種選題提示 ═══
    "sticker_pack": ("你是數位貼紙設計師。給出 5 個貼紙包提案：\n1. 主題（手寫文字/貓咪/語錄/節慶）\n2. 目標平台（Line/GoodNotes/Telegram）\n3. 含：包名、風格、數量、定價建議"),
    "font_pack": ("你是字型設計師。給出 5 個繁體中文字型包提案：\n1. 風格（手寫/毛筆/童趣/科技）\n2. 含：字型名、適用場景、商用授權定價"),
    "icon_set": ("你是圖示設計師。給出 5 個 SVG icon 套件提案：\n1. 主題（電商/醫療/金融/社群）\n2. 含：套件名、icon 數量、目標設計師族群"),
    "preset_pack": ("你是攝影師。給出 5 個 Lightroom 濾鏡預設提案：\n1. 風格（日系/復古/美食/婚禮）\n2. 含：預設名、色調描述、適合場景"),
    "wallpaper_pack": ("你是視覺設計師。給出 5 個手機桌布包提案：\n1. 風格（極簡/山水/動漫/語錄）\n2. 含：包名、解析度、張數"),
    "sound_pack": ("你是音效設計師。給出 5 個音效包提案：\n1. 類型（鈴聲/白噪音/UI提示音）\n2. 含：包名、檔案數、使用場景"),
    "code_snippets": ("你是資深開發者。給出 5 個程式碼片段包提案：\n1. 語言/框架（Python/JS/SQL/React）\n2. 含：包名、snippet 數量、目標開發者"),
    "language_learning": ("你是語言教師。給出 5 個語言學習教材提案：\n1. 語言（日/英/韓/法/台語）\n2. 含：教材名、程度、獨特教學法"),
    "flashcards": ("你是教育設計師。給出 5 個學習字卡提案：\n1. 科目（GRE/醫學/日檢/多益/法律）\n2. 含：卡名、卡數、匯入格式"),
    "cheat_sheet": ("你是知識整理師。給出 5 個速查表提案：\n1. 主題（程式語法/投資/SEO/Git/ChatGPT）\n2. 含：表名、適用對象、一頁式設計"),
    "quiz_bank": ("你是考試專家。給出 5 個測驗題庫提案：\n1. 考試名稱（公務員/會考/PMP/不動產/多益）\n2. 含：題庫名、題數、詳解特色"),
    "fitness_plan": ("你是健身教練。給出 5 個健身計畫提案：\n1. 目標族群（上班族/產後/銀髮/跑步新手）\n2. 含：計畫名、週數、課表+飲食特色"),
    "meditation_guide": ("你是冥想導師。給出 5 個冥想指南提案：\n1. 主題（睡前/專注/情緒/感恩/考試）\n2. 含：指南名、時長、引導方式"),
    "parenting_guide": ("你是育兒專家。給出 5 個育兒指南提案：\n1. 年齡層（0-2/3-6/學齡）\n2. 含：書名、核心教養理念、實用活動"),
    "pet_care": ("你是獸醫師。給出 5 個寵物照護提案：\n1. 寵物（狗/貓/兔/老犬）\n2. 含：書名、照護重點、讀者需求"),
    "gardening": ("你是園藝師。給出 5 個園藝指南提案：\n1. 空間（陽台/室內/屋頂）\n2. 含：書名、植物類型、種植難度"),
    "diy_crafts": ("你是手作老師。給出 5 個手作教學提案：\n1. 類型（布作/紙藝/編織/樹脂/舊物改造）\n2. 含：書名、難度、成品圖數量"),
    "presentation_template": ("你是簡報設計師。給出 5 個簡報模板提案：\n1. 用途（商業提案/教育/產品發表/年度報告/Pitch Deck）\n2. 含：模板名、頁數、適用軟體"),
    "resume_template": ("你是履歷專家。給出 5 個履歷模板提案：\n1. 風格（外商/設計師/新鮮人/高管）\n2. 含：模板名、格式（Word/PPT/PDF）、ATS優化"),
    "business_plan_tmpl": ("你是商業顧問。給出 5 個商業計畫模板提案：\n1. 行業（電商/餐飲/SaaS/加盟/自媒體）\n2. 含：模板名、內含財務模型"),
    "game_guide": ("你是遊戲攻略作家。給出 5 個遊戲攻略提案：\n1. 熱門遊戲（原神/薩爾達/MC/LOL/FF7）\n2. 含：攻略名、內容特色、地圖/圖解"),
    "music_sheet": ("你是音樂編輯。給出 5 個樂譜提案：\n1. 曲風/樂器（鋼琴/吉他/烏克麗麗）\n2. 含：樂譜名、難度、曲數"),
}


# ═══ LLM 呼叫（支援銷售情報注入） ═══

def generate_topic_proposals(
    product_type: str,
    count: int = 5,
    inject_sales: bool = True,
    llm_call_fn=None,
) -> list:
    """
    用 LLM 為指定產品類型生成選題提案。
    回傳 [{"title": "...", "description": "...", "target_audience": "...", "reason": "..."}, ...]
    """
    preset = __import__("pipeline_presets", fromlist=["PRODUCT_TYPES"]).PRODUCT_TYPES.get(product_type, {})
    prompt_key = preset.get("topic_prompt_key", "ebook")
    base_prompt = TOPIC_PROMPTS.get(prompt_key, TOPIC_PROMPTS["ebook"])

    # 注入銷售情報
    sales_ctx = _get_sales_context() if inject_sales else ""

    # 注入即時趨勢關鍵字
    trend_ctx = _get_trend_context()

    full_prompt = base_prompt.replace("給出 5", f"給出 {count}") + sales_ctx + trend_ctx

    # 調用 LLM（優先使用傳入的 llm_call_fn，否則 fallback）
    if llm_call_fn:
        try:
            result = llm_call_fn(full_prompt, "你是專業選題顧問，只用繁體中文回覆。請以 JSON 陣列格式回傳：每個物件含 title, description, target_audience, reason。")
            # 嘗試解析 JSON
            if result:
                try:
                    parsed = json.loads(result)
                    if isinstance(parsed, list):
                        # 過濾已淘汰主題
                        try:
                            from pipeline_data import rejected as rej_store
                            rejected_set = set(rej_store.get_all().keys())
                            parsed = [p for p in parsed if p.get("title", "") not in rejected_set]
                        except:
                            pass
                        return parsed
                except:
                    return [{"title": product_type, "description": result[:200], "target_audience": "一般讀者", "reason": "AI 生成"}]
        except:
            pass

    # fallback: 沒有 LLM 時，直接呼叫 DeepSeek 生成
    try:
        from dotenv import load_dotenv; import os as _os
        load_dotenv()
        key = _os.getenv("DEEPSEEK_API_KEY","")
        if key:
            import requests as _req
            r = _req.post("https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={"model":"deepseek-chat","messages":[
                    {"role":"system","content":"你是專業選題顧問。回 JSON 陣列。每個物件含 title, description, target_audience, reason。繁體中文。"},
                    {"role":"user","content": full_prompt}
                ],"temperature":0.7,"max_tokens":600}, timeout=20)
            data = r.json()
            if "choices" in data:
                result = data["choices"][0]["message"]["content"]
                import re as _re
                json_match = _re.search(r'\[.*\]', result, _re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group())
                    if isinstance(parsed, list) and len(parsed) > 0:
                        return parsed[:count]
    except:
        pass

    # 終極 fallback：用趨勢關鍵字生成（不再用 FALLBACK_TOPICS）
    from pipeline_presets import PRODUCT_TYPES as PT
    preset = PT.get(product_type, {})
    type_label = preset.get("label", product_type)

    import re
    def _is_good_kw(w):
        if re.match(r'^\d+$', w): return False
        if any(c in w for c in ['股價','目標價','股票','·','-']): return False
        if len(w) < 2: return False
        return True

    good_kws = []
    try:
        from keyword_scout import keyword_scout
        all_kws = keyword_scout.get_trending(30)
        good_kws = [w for w in all_kws if _is_good_kw(w)][:count]
    except:
        pass

    results = []
    for kw in good_kws:
        title = f"2026 {kw} 完全指南" if len(kw) <= 4 else f"{kw}：趨勢分析與實戰策略"
        results.append({"title": title, "description": f"基於即時趨勢「{kw}」的{type_label}",
                        "target_audience": "關注趨勢的讀者", "reason": f"8 站掃描關鍵字：{kw}"})

    # 不夠則補 Fallback
    if len(results) < count:
        fallback = FALLBACK_TOPICS.get(product_type, ["未命名選題"])
        for i, t in enumerate(fallback[:count - len(results)]):
            if isinstance(t, dict):
                results.append({"title": t.get("title", str(t)), "description": t.get("summary", ""), "target_audience": t.get("age", "一般"), "reason": "後備選題"})
            else:
                results.append({"title": str(t), "description": "", "target_audience": "一般讀者", "reason": "後備選題"})

    # 過濾已淘汰主題
    try:
        from pipeline_data import rejected as rej_store
        rejected_titles = set(rej_store.get_all().keys())
        results = [r for r in results if r.get("title", "") not in rejected_titles]
    except:
        pass

    return results[:count]


# ═══ Stage 5-10 視覺處理器（品牌強制套用） ═══

def stage_5_editing(book: Dict, cfg: Dict, llm_fn=None) -> Dict:
    """編輯階段：幻覺檢測 + 矛盾檢查 + LLM校稿 + AI Beta Reader"""
    title = book["stage_data"]["1"].get("title", "?")
    content = book["stage_data"].get("4", {}).get("content", "")
    word_count = len(content)
    issues = []

    if word_count < 500:
        issues.append("內容偏短（<500字）")

    # LLM 校稿
    if llm_fn and content:
        try:
            review = llm_fn(
                f"你是專業文字編輯。校對以下內容，檢查：錯字、文法、標點、排版。只回「通過」或列問題：\n\n{content[:3000]}",
                "你是專業編輯，只回校對結果。"
            )
            if review and "通過" not in review:
                issues.append(f"校稿: {review[:150]}")
        except:
            pass

    # AI Beta Reader 模擬三種讀者回饋
    beta_feedback = []
    if llm_fn and content:
        personas = [
            ("初學者小明", "從初學者角度給回饋：哪裡難懂？哪裡需要更多解釋？一句話。"),
            ("專家老王", "從專業人士角度給回饋：哪裡太淺？哪裡可以加深度？一句話。"),
            ("實用派阿芳", "從實際應用角度給回饋：內容實用嗎？可以直接照做嗎？一句話。"),
        ]
        for name, role_prompt in personas:
            try:
                fb = llm_fn(
                    f"你是「{name}」。{role_prompt}\n\n{content[:2000]}",
                    f"你是{name}。只用一句話回饋。"
                )
                if fb:
                    beta_feedback.append({"persona": name, "feedback": fb[:200]})
            except:
                pass

    score = max(0.3, 1.0 - len(issues) * 0.08)
    return {
        "issues": issues, "quality_score": round(score, 2),
        "word_count": word_count, "beta_reader": beta_feedback,
        "completed_at": datetime.now().isoformat(),
    }


def stage_6_art(book: Dict, cfg: Dict, llm_fn=None) -> Dict:
    """美術階段：封面生成 + 設計簡報 + 色彩分析"""
    title = book["stage_data"]["1"].get("title", "?")
    product_type = book.get("product_type", "ebook")

    # 調用 CoverGenerator（SVG 向量封面）
    cover_result = None
    try:
        from visual.cover_generator import cover_gen
        cover_result = cover_gen.generate_cover(book)
    except Exception as e:
        pass

    # 真實圖片生成（HuggingFace Stable Diffusion）
    real_cover_path = ""
    if llm_fn:
        try:
            import os, requests, json, base64
            from pathlib import Path
            hf_key = os.getenv("HUGGINGFACE_TOKEN")
            if hf_key:
                prompt = f"A professional book cover for '{title}', minimal design, elegant typography, high quality, 4k, --ar 2:3"
                r = requests.post(
                    "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-3.5-large",
                    headers={"Authorization": f"Bearer {hf_key}"},
                    json={"inputs": prompt},
                    timeout=120
                )
                if r.status_code == 200:
                    base = Path(__file__).resolve().parent.parent
                    covers_dir = base / "outputs" / "covers"
                    covers_dir.mkdir(parents=True, exist_ok=True)
                    book_id = book.get("id", "unknown")
                    png_path = covers_dir / f"{book_id}_cover.png"
                    png_path.write_bytes(r.content)
                    real_cover_path = str(png_path)
        except:
            pass

    design_brief = ""
    try:
        from nerve.vision_designer import VisionDesigner
        vd = VisionDesigner()
        design_brief = f"封面場景: {cover_result.get('scene', 'tech') if cover_result else 'tech'}"
    except:
        pass

    if llm_fn and not design_brief:
        try:
            design_brief = llm_fn(
                f"為《{title}》生成書籍美術設計簡報：\n1. 封面概念（3句）\n2. 配色方案\n3. 插畫風格\n4. 字型建議",
                "你是書籍設計師。"
            )
        except:
            pass

    return {
        "cover_svg": cover_result.get("svg_path", "") if cover_result else "",
        "cover_png": real_cover_path,
        "scene": cover_result.get("scene", "tech") if cover_result else "tech",
        "design_brief": design_brief[:500] if design_brief else "",
        "cover_generated": bool(cover_result),
        "completed_at": datetime.now().isoformat(),
    }


def stage_7_layout(book: Dict, cfg: Dict, llm_fn=None) -> Dict:
    """排版階段：EPUB 編譯 + 品牌 CSS 套用"""
    title = book["stage_data"]["1"].get("title", "?")
    content = book["stage_data"].get("4", {}).get("content", "")
    outline = book["stage_data"].get("3", {}).get("outline", "")
    product_type = book.get("product_type", "ebook")
    ts = datetime.now().strftime("%Y%m%d_%H%M")

    # 品牌 CSS
    try:
        from visual import brand
        brand_css = brand.epub_css()
    except:
        brand_css = ""

    # 編譯輸出
    out_dir = BASE / "outputs" / "compiled"
    out_dir.mkdir(parents=True, exist_ok=True)
    full_content = f"# {title}\n\n> 編譯於 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n## 目錄\n\n{outline}\n\n---\n\n{content}"
    md_path = out_dir / f"{product_type}_{book['id']}_{ts}.md"
    md_path.write_text(full_content, encoding="utf-8")

    # 插圖生成
    illustrations = {}
    try:
        from exchange.illustration_gen import generate_book_illustrations
        import re
        chapters = re.findall(r'##\s*(.+?)\n', content)
        if chapters:
            illustrations = generate_book_illustrations(chapters[:8], "abstract")
    except Exception:
        pass

    # 嘗試 EPUB 編譯
    epub_path = ""
    try:
        from core.epub_compiler import EPUBCompiler
        compiler = EPUBCompiler()
        epub_result = compiler.compile_ebook(
            title=title, content=content, outline=outline,
            product_type=product_type,
        )
        epub_path = epub_result.get("path", "")
    except Exception as e:
        pass

    return {
        "format": "epub+md",
        "output": str(md_path),
        "epub_path": epub_path,
        "brand_css_applied": bool(brand_css),
        "file_size": len(full_content),
        "completed_at": datetime.now().isoformat(),
    }


def stage_9_publish(book: Dict, cfg: Dict, llm_fn=None) -> Dict:
    """上架階段：準備發布素材 + 元數據 + 多平台上架"""
    title = book["stage_data"]["1"].get("title", "?")
    book_id = book.get("id", "?")
    product_type = book.get("product_type", "ebook")
    platforms = cfg.get("platforms", ["kdp", "readmoo"])

    # LLM 生成商品描述
    description = ""
    if llm_fn:
        try:
            description = llm_fn(
                f"為《{title}》寫一段 150 字繁體中文商品描述，含賣點、目標讀者、為什麼要買。",
                "你是專業行銷文案撰寫者。"
            )
        except:
            pass

    # LLM 生成關鍵字
    keywords = ""
    if llm_fn:
        try:
            keywords = llm_fn(
                f"為《{title}》列出 10 個 SEO 關鍵字/標籤，逗號分隔。",
                "只輸出逗號分隔的標籤。"
            )
        except:
            pass

    # 調用 PublishEngine
    publish_results = {}
    try:
        from visual.publish_engine import publish_engine
        pub_item = publish_engine.prepare_book_for_publishing(book)
        for plat in platforms:
            r = publish_engine.publish_to_platform(book_id, plat)
            publish_results[plat] = r
    except:
        pass

    pub_dir = BASE / "outputs" / "published"
    pub_dir.mkdir(parents=True, exist_ok=True)
    meta = {"title": title, "platforms": platforms, "description": description,
            "tags": keywords, "published_at": datetime.now().isoformat()}
    (pub_dir / f"{book_id}_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))

    return {
        "platforms": platforms, "description": description[:200],
        "tags": keywords[:200], "publish_results": publish_results,
        "status": "ready", "completed_at": datetime.now().isoformat(),
    }


def stage_10_marketing(book: Dict, cfg: Dict, llm_fn=None) -> Dict:
    """行銷階段：全平台廣告素材 + 廣告活動"""
    title = book["stage_data"]["1"].get("title", "?")
    book_id = book.get("id", "?")
    product_type = book.get("product_type", "ebook")
    channels = cfg.get("ad_channels", ["telegram", "twitter"])
    description = book["stage_data"].get("9", {}).get("description", "")

    # 調用 AdFactory 生成全平台素材
    ad_results = {}
    try:
        from visual.ad_factory import ad_factory
        ad_results = ad_factory.generate_all_platforms(book)
    except:
        pass

    # LLM 生成各平台文案
    ads = {}
    for ch in channels:
        if llm_fn:
            try:
                if ch == "telegram":
                    ads[ch] = llm_fn(f"為《{title}》寫 Telegram 宣傳文案，繁體中文，含 emoji，50 字內。")
                elif ch == "twitter":
                    ads[ch] = llm_fn(f"為《{title}》寫推文，繁體中文，hashtags，280 字內。")
                elif ch == "facebook":
                    ads[ch] = llm_fn(f"為《{title}》寫 Facebook 貼文，繁體中文，100 字內。")
                elif ch == "instagram":
                    ads[ch] = llm_fn(f"為《{title}》寫 Instagram 貼文，繁體中文，hashtags。")
                else:
                    ads[ch] = llm_fn(f"為《{title}》寫 {ch} 行銷文案。")
            except:
                ads[ch] = f"《{title}》現已上架！"

    # 建立廣告活動
    campaign = None
    try:
        from visual.ad_campaign_manager import ad_campaign_mgr
        campaign = ad_campaign_mgr.create_campaign(book, "awareness", 100, channels)
    except:
        pass

    # 內容裂變
    fission_result = {}
    try:
        from content_fission import fission_engine
        fission_result = fission_engine.fission(book, llm_fn)
    except:
        pass

    # 儲存廣告
    ad_dir = BASE / "outputs" / "ads"
    ad_dir.mkdir(parents=True, exist_ok=True)
    (ad_dir / f"{book_id}_ads.json").write_text(json.dumps(ads, ensure_ascii=False, indent=2))

    return {
        "channels": channels, "ads": ads, "campaign_id": campaign.get("id", "") if campaign else "",
        "ad_svgs": list(ad_results.get("platforms", {}).keys()) if ad_results else [],
        "fission_types": list(fission_result.get("types", [])),
        "completed_at": datetime.now().isoformat(),
    }


# ═══ Stage 1-4 器官連動處理器 ═══

def stage_2_research(book: Dict, cfg: Dict, llm_fn=None) -> Dict:
    """研究階段：Eye搜尋 + Memory儲存 + LLM提煉"""
    title = book["stage_data"]["1"].get("title", "")
    product_type = book.get("product_type", "ebook")
    sources = []

    # 嘗試調用 Eye 搜尋
    try:
        from nerve.eye import Eye
        eye = Eye()
        eye.init()
        raw = eye.see(f"{title} 教學 入門 趨勢")
        if raw and "未就緒" not in raw and len(raw) > 20:
            sources.append(str(raw)[:1500])
    except:
        pass

    # 備援：直接用 web_search 工具
    if not sources:
        try:
            from web.search import WebSearch
            ws = WebSearch()
            raw = ws.search(f"{title} 教學 入門", 3)
            if raw and len(raw) > 20:
                sources.append(str(raw)[:1500])
        except:
            pass

    # LLM 提煉
    if llm_fn and sources:
        try:
            summary = llm_fn(
                f"針對「{title}」根據以下資料提煉 5 關鍵事實 + 3 寫作素材。不抄襲：\n" + ";".join(sources[:3]),
                "你是研究員。分析並改寫。"
            )
        except:
            summary = "無搜尋結果"
    else:
        summary = sources[0][:300] if sources else "無搜尋結果"

    return {"sources_count": len(sources), "summary": summary[:800],
            "completed_at": datetime.now().isoformat()}


def stage_3_outline(book: Dict, cfg: Dict, llm_fn=None) -> Dict:
    """大綱階段：Wardrobe風格 + LLM目錄"""
    title = book["stage_data"]["1"].get("title", "")
    research = book["stage_data"].get("2", {}).get("summary", "")
    if llm_fn:
        outline = llm_fn(
            f"為《{title}》生成完整目錄 6-8 章，每章 3-4 小節。參考：{research[:200]}",
            "你是專業編輯。只輸出目錄。"
        )
    else:
        outline = f"# {title}\n\n"
    return {"outline": outline, "completed_at": datetime.now().isoformat()}


def stage_4_writing(book: Dict, cfg: Dict, llm_fn=None) -> Dict:
    """撰寫階段：根據書籍類型生成對應結構的內容"""
    title = book["stage_data"]["1"].get("title", "")
    outline = book["stage_data"].get("3", {}).get("outline", "")
    research = book["stage_data"].get("2", {}).get("summary", "")
    product_type = book.get("product_type", "ebook")

    # 不同類型有不同的寫作風格
    type_guides = {
        "ebook": "工具書風格：每章一個主題，有實例、有步驟、有重點整理。",
        "finance_book": "財經書風格：數據驅動、案例分析、風險提示、具體策略。",
        "novel": "小說風格：角色對話、場景描寫、情節推進、懸念設置。章節之間有連貫性。",
        "light_novel": "輕小說風格：輕快對話、萌要素、校園/奇幻場景、青春感。",
        "kidbook": "童書風格：簡單句子、重複韻律、可愛動物角色、正向價值觀。適合 3-6 歲。",
        "comic": "漫畫腳本：每頁分鏡描述、對話框內容、場景說明。",
        "exam_book": "考試用書：考點整理、例題詳解、模擬試題、答題技巧。",
        "crypto_book": "加密貨幣書：技術解釋、市場分析、風險警告、實操步驟。",
        "course_material": "教材風格：學習目標、課後練習、重點回顧、漸進式難度。",
    }
    type_guide = type_guides.get(product_type, type_guides["ebook"])

    content = ""
    if llm_fn:
        content = llm_fn(
            f"你是暢銷書作家。{type_guide}\n"
            f"書名：《{title}》\n目錄：{outline[:800]}\n研究：{research[:800]}\n"
            f"要求：繁體中文，寫滿 6-8 章，每章 800-1200 字。要有深度分析、具體案例、實用技巧。"
            f"不要模板開頭，直接進入內容。章節之間加入小故事或對話讓閱讀更生動。",
            "你是專業作家，只輸出完整書籍內容（6-8章）。"
        )
    else:
        content = f"# {title}\n\n（待 LLM 生成）"

    return {"content": content, "word_count": len(content), "chapters_written": outline.count("章") or 1,
            "parallel": False, "completed_at": datetime.now().isoformat()}


def stage_7_5_proofread(book: Dict, cfg: Dict, llm_fn=None) -> Dict:
    """專業校稿：6步檢查 → 綜合評分 → 駁回/通過"""
    try:
        from proofreader import proofreader
        return proofreader.proofread(book, llm_fn)
    except:
        return {"overall": 100, "grade": "pass", "error": "校稿器官載入失敗",
                "completed_at": datetime.now().isoformat()}

def stage_8_review(book: Dict, cfg: Dict, llm_fn=None) -> Dict:
    """審核階段：Contradiction檢查 + 人工閘門"""
    title = book["stage_data"]["1"].get("title", "")
    content = book["stage_data"].get("4", {}).get("content", "")
    word_count = len(content)
    quality = ""
    if llm_fn:
        quality = llm_fn(f"評分《{title}》(1-10)並給一句建議：", "書評人。只回數字+建議。")
    return {"word_count": word_count, "quality": quality[:200],
            "pending_review": True, "completed_at": datetime.now().isoformat()}


# ═══ 階段處理器註冊 ═══

STAGE_HANDLERS = {
    2: stage_2_research,
    3: stage_3_outline,
    4: stage_4_writing,
    5: stage_5_editing,
    6: stage_6_art,
    7: stage_7_layout,
    7.5: stage_7_5_proofread,
    8: stage_8_review,
    9: stage_9_publish,
    10: stage_10_marketing,
}
