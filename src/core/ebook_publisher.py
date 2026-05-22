"""EbookPublisherOrgan — 電子書上架引擎器官，負責將兒童電子書自動化上架至 15+ 全球出版平台。"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from skeleton.brain_component import BrainComponent
from tools import tool

PUBLISHER_PLATFORMS: Dict[str, Dict[str, Any]] = {
    "amazon_kdp": {
        "name": "Amazon Kindle Direct Publishing",
        "url": "https://kdp.amazon.com",
        "royalty_rate": "35% 或 70%（定價 $2.99–$9.99 適用 70%）",
        "royalty_numeric": 0.70,
        "territories": ["全球（Amazon 所有市場）"],
        "accepted_formats": ["EPUB 3.0", "KPF"],
        "isbn_required": False,
        "tax_requirements": "美國稅務面談（W-8BEN 或 W-9），部分國家需加值稅 VAT",
        "payout_threshold": "$100（電匯）/ $10（禮品卡）",
        "best_for": "全球最大電子書市場，Kindle 生態系獨佔優勢",
        "childrens_book_support": "支援 Kindle Kids' Book Creator 工具，固定版面 EPUB 適合繪本",
        "setup_guide": "建立 KDP 帳號後需完成稅務面談。兒童書建議使用固定版面 EPUB 格式。啟用 Kindle Unlimited 可增加借閱收入。",
    },
    "apple_books": {
        "name": "Apple Books",
        "url": "https://authors.apple.com",
        "royalty_rate": "70%",
        "royalty_numeric": 0.70,
        "territories": ["全球 51 個國家與地區"],
        "accepted_formats": ["EPUB 3.0"],
        "isbn_required": True,
        "tax_requirements": "需填寫美國稅務表格 W-8BEN，Apple 代扣 30% 預扣稅（若有稅務協定可減免）",
        "payout_threshold": "$10",
        "best_for": "Apple 生態系使用者，高收入國家讀者群",
        "childrens_book_support": "支援 Read Aloud 朗讀功能與固定版面 EPUB，適合兒童繪本",
        "setup_guide": "透過 iTunes Connect 或 Apple Books for Authors 上架。兒童書需注意固定版面 EPUB 之圖片解析度須達 300 DPI。",
    },
    "google_play_books": {
        "name": "Google Play Books",
        "url": "https://play.google.com/books/publish",
        "royalty_rate": "70%",
        "royalty_numeric": 0.70,
        "territories": ["全球 75 個國家與地區"],
        "accepted_formats": ["EPUB 3.0", "PDF"],
        "isbn_required": False,
        "tax_requirements": "各國適用當地稅率，Google 自動計算各市場稅務",
        "payout_threshold": "$1",
        "best_for": "Android 使用者與全球覆蓋廣度",
        "childrens_book_support": "支援固定版面 EPUB，Google Play 家庭圖書館功能適合兒童內容",
        "setup_guide": "使用 Google Play Books Partner Center 上架。自動轉換 EPUB 為最佳化格式。可設定各國不同定價策略。",
    },
    "kobo": {
        "name": "Rakuten Kobo",
        "url": "https://www.kobo.com/writinglife",
        "royalty_rate": "45%–70%（定價 $2.99 以上適用 70%）",
        "royalty_numeric": 0.70,
        "territories": ["全球 190+ 國家，加拿大、日本、歐洲為主要市場"],
        "accepted_formats": ["EPUB 3.0"],
        "isbn_required": False,
        "tax_requirements": "加拿大與日本市場適用當地稅制",
        "payout_threshold": "$50",
        "best_for": "加拿大、日本與歐洲市場，Kobo Plus 訂閱制額外收入",
        "childrens_book_support": "支援固定版面 EPUB 與 Kobo Kids 分類",
        "setup_guide": "透過 Kobo Writing Life 平台上架。加入 Kobo Plus 訂閱制可增加曝光。兒童書使用 Kobo Kids 類別有專屬促銷機會。",
    },
    "barnes_noble": {
        "name": "Barnes & Noble Press",
        "url": "https://press.barnesandnoble.com",
        "royalty_rate": "65%–70%",
        "royalty_numeric": 0.70,
        "territories": ["美國、英國"],
        "accepted_formats": ["EPUB 3.0"],
        "isbn_required": False,
        "tax_requirements": "美國稅務表格 W-9 或 W-8BEN",
        "payout_threshold": "$10",
        "best_for": "美國第二大電子書市場，實體書店曝光機會",
        "childrens_book_support": "支援 Nook Kids 兒童分類，固定版面 EPUB 可用於繪本",
        "setup_guide": "使用 B&N Press 平台上架。Nook Kids 分類提供兒童專屬曝光版位。實體書店可搭配 Print On Demand 服務。",
    },
    "smashwords": {
        "name": "Smashwords",
        "url": "https://www.smashwords.com",
        "royalty_rate": "60%（Smashwords 直營）/ 80%（零售商）",
        "royalty_numeric": 0.60,
        "territories": ["全球（透過經銷網路包含 Apple Books、Kobo、Barnes & Noble 等）"],
        "accepted_formats": ["EPUB 3.0", "DOC/DOCX"],
        "isbn_required": False,
        "tax_requirements": "美國稅務表格 W-8BEN，無需自行處理各零售商稅務",
        "payout_threshold": "$10",
        "best_for": "一次上架多平台（聚合經銷商），適合新手作者",
        "childrens_book_support": "可上架兒童書至所有合作零售商，統一管理銷售報表",
        "setup_guide": "僅需一次上傳即可分發至多個零售商。需使用 Smashwords Style Guide 格式化稿件以通過自動檢查。",
    },
    "draft2digital": {
        "name": "Draft2Digital",
        "url": "https://www.draft2digital.com",
        "royalty_rate": "約零售價之 60%（聚合商抽取約 10% 淨收益）",
        "royalty_numeric": 0.60,
        "territories": ["全球（經銷至 Amazon、Apple、Kobo、B&N、圖書館等 20+ 通路）"],
        "accepted_formats": ["EPUB 3.0", "DOCX"],
        "isbn_required": False,
        "tax_requirements": "處理各市場稅務，作者只需填 W-8BEN",
        "payout_threshold": "$10",
        "best_for": "自助出版新手，自動格式化工具與廣泛經銷網路",
        "childrens_book_support": "自動排版工具支援固定版面 EPUB 轉換，適合兒童繪本",
        "setup_guide": "上傳 DOCX 或 EPUB 檔案，平台自動轉換為各零售商所需格式。支援 Universal Book Link 統一行銷頁面。",
    },
    "bookbaby": {
        "name": "BookBaby",
        "url": "https://www.bookbaby.com",
        "royalty_rate": "85%（淨收益）/ 須支付一次性製作費（$99–$399 不等）",
        "royalty_numeric": 0.85,
        "territories": ["全球（包含 Amazon、Apple Books、B&N 等）"],
        "accepted_formats": ["EPUB 3.0", "PDF"],
        "isbn_required": False,
        "tax_requirements": "美國稅務表格 W-9 或 W-8BEN",
        "payout_threshold": "$25",
        "best_for": "需要專業編輯與設計服務的作者，一站式出版方案",
        "childrens_book_support": "提供兒童書插畫與固定版面 EPUB 製作服務（另收費）",
        "setup_guide": "BookBaby 為付費服務平台，適合需要編輯、封面設計與行銷一站式方案。需規劃前置製作預算。",
    },
    "lulu": {
        "name": "Lulu",
        "url": "https://www.lulu.com",
        "royalty_rate": "80%（直接銷售）/ 90%（Lulu 書店）",
        "royalty_numeric": 0.80,
        "territories": ["全球（含實體印製與電子書發行）"],
        "accepted_formats": ["EPUB 3.0", "PDF"],
        "isbn_required": False,
        "tax_requirements": "作者自負各地稅務申報",
        "payout_threshold": "$5",
        "best_for": "同時發行電子書與按需印刷（POD）紙本書",
        "childrens_book_support": "支援全彩色按需印刷，適合兒童繪本之紙本與電子書雙軌發行",
        "setup_guide": "Lulu 提供免費 ISBN 或使用自有 ISBN。兒童繪本紙本需注意出血設定（0.125 英吋）與 CMYK 色彩模式。",
    },
    "ingramspark": {
        "name": "IngramSpark",
        "url": "https://www.ingramspark.com",
        "royalty_rate": "40%–70%（依通路批發折扣設定而異）",
        "royalty_numeric": 0.55,
        "territories": ["全球（Ingram 經銷體系涵蓋 39,000+ 零售商與圖書館）"],
        "accepted_formats": ["EPUB 3.0", "PDF"],
        "isbn_required": True,
        "tax_requirements": "各國稅務各異，需自行處理",
        "payout_threshold": "$0",
        "best_for": "最大化圖書館與實體書店通路覆蓋率",
        "childrens_book_support": "支援全彩印刷與多種裝訂方式（精裝、平裝），適合高品質兒童圖書",
        "setup_guide": "需購買自有 ISBN。設定批發折扣 40%–55% 以取得書店進貨。檔案規格要求嚴格（PDF/X-1a 標準），建議委託專業排版。",
    },
    "publishdrive": {
        "name": "PublishDrive",
        "url": "https://publishdrive.com",
        "royalty_rate": "70%–100%（訂閱制聚合商，月費約 $19–$99）",
        "royalty_numeric": 1.0,
        "territories": ["全球（Amazon、Apple、Google、Kobo 等 400+ 線上書店與圖書館）"],
        "accepted_formats": ["EPUB 3.0"],
        "isbn_required": False,
        "tax_requirements": "處理全球稅務與權利金分配",
        "payout_threshold": "$100",
        "best_for": "大量出版且需要全球廣泛經銷的專業作者",
        "childrens_book_support": "支援固定版面 EPUB 上架至所有合作通路",
        "setup_guide": "訂閱制模式（月費制），適合每月有穩定出版量的作者。平台提供 AI 翻譯與行銷工具（部分方案另收費）。",
    },
    "streetlib": {
        "name": "StreetLib",
        "url": "https://www.streetlib.com",
        "royalty_rate": "70%–90%",
        "royalty_numeric": 0.80,
        "territories": ["全球（歐洲、拉丁美洲、亞洲重點市場）"],
        "accepted_formats": ["EPUB 3.0", "PDF"],
        "isbn_required": False,
        "tax_requirements": "處理各國稅務分配",
        "payout_threshold": "€20",
        "best_for": "歐洲與拉丁美洲市場布局",
        "childrens_book_support": "支援固定版面 EPUB，義大利與西班牙市場特別活躍",
        "setup_guide": "義大利起家的全球化平台，提供多語系介面。歐洲市場滲透率高，適合非英語兒童書。",
    },
    "xinxii": {
        "name": "XinXii",
        "url": "https://www.xinxii.com",
        "royalty_rate": "70%",
        "royalty_numeric": 0.70,
        "territories": ["歐洲為主（德國、法國、義大利、西班牙等）"],
        "accepted_formats": ["EPUB 3.0", "PDF"],
        "isbn_required": False,
        "tax_requirements": "歐盟境內作者適用 VAT，非歐盟作者免 VAT 但需當地稅務申報",
        "payout_threshold": "€10",
        "best_for": "歐洲市場獨立出版，德語、法語等非英語市場",
        "childrens_book_support": "支援多語系兒童書上架",
        "setup_guide": "以歐洲市場為核心，支援多國語言介面與貨幣。適合非英語兒童書之在地化發行。",
    },
    "tolino": {
        "name": "Tolino",
        "url": "https://www.tolino.de",
        "royalty_rate": "70%",
        "royalty_numeric": 0.70,
        "territories": ["德國、奧地利、瑞士、比利時、義大利、荷蘭"],
        "accepted_formats": ["EPUB 3.0"],
        "isbn_required": True,
        "tax_requirements": "德國 VAT 7%（電子書優惠稅率），非歐盟作者需申報",
        "payout_threshold": "€25",
        "best_for": "德語市場（DACH 地區：德奧瑞）最大電子書平台",
        "childrens_book_support": "支援兒童書分類與固定版面 EPUB，德語兒童書市場需求強勁",
        "setup_guide": "需先與 Tolino 合作之經銷商（如 Bookwire、Neobooks）簽約上架。德語市場注重 ISBN 與書目完整性。",
    },
    "overdrive": {
        "name": "OverDrive / Libby",
        "url": "https://www.overdrive.com",
        "royalty_rate": "50%–60%（圖書館借閱模式，單位計費）",
        "royalty_numeric": 0.55,
        "territories": ["全球 90+ 國家，主要為北美、英國、澳洲等公共圖書館體系"],
        "accepted_formats": ["EPUB 3.0", "PDF"],
        "isbn_required": True,
        "tax_requirements": "美國稅務表格 W-8BEN",
        "payout_threshold": "$0",
        "best_for": "打入公共圖書館與學校借閱體系，長期穩定版稅收入",
        "childrens_book_support": "學校與公共圖書館為兒童書最大採購方，OverDrive 教育版 (Sora) 專攻 K-12 市場",
        "setup_guide": "需透過經銷商（Draft2Digital、PublishDrive 或直接合作）上架。圖書館借閱模式為每借閱一次計費（Cost Per Circ），收益穩定且長尾效應強。",
    },
}

AGE_RANGE_INFO: Dict[str, Dict[str, Any]] = {
    "0-2": {
        "label": "嬰幼兒（0–2 歲）",
        "book_type": "厚頁書/布書/觸摸書",
        "typical_page_count": (8, 16),
        "word_count_range": "0–100 字",
        "illustration_style": "高對比色彩，簡單圖形，面部圖像優先",
        "format_recommendation": "固定版面 EPUB，全彩印刷 PDF",
    },
    "3-5": {
        "label": "學齡前（3–5 歲）",
        "book_type": "圖畫書",
        "typical_page_count": (24, 32),
        "word_count_range": "200–800 字",
        "illustration_style": "明亮全彩插圖，情節推動圖像為主",
        "format_recommendation": "固定版面 EPUB 3.0，全彩，300 DPI",
    },
    "6-8": {
        "label": "早期閱讀（6–8 歲）",
        "book_type": "橋樑書/初階讀本",
        "typical_page_count": (32, 64),
        "word_count_range": "800–3,000 字",
        "illustration_style": "每頁均有插圖輔助文字理解",
        "format_recommendation": "固定版面或可重排 EPUB，視插圖密度決定",
    },
    "9-12": {
        "label": "中年級（9–12 歲）",
        "book_type": "章節書/中篇小說",
        "typical_page_count": (80, 250),
        "word_count_range": "5,000–40,000 字",
        "illustration_style": "少數內頁插圖（黑白或彩色），文字為主",
        "format_recommendation": "可重排 EPUB 3.0，內嵌少量插圖",
    },
}

FORMAT_REQUIREMENTS: Dict[str, Dict[str, Any]] = {
    "epub": {
        "name": "EPUB 3.0",
        "mime_type": "application/epub+zip",
        "file_structure": "META-INF/container.xml, mimetype, OEBPS/ 目錄，包含 XHTML、CSS、圖片資源與 OPF 導覽文件",
        "validation": "通過 EPUBCheck 4.2+ 驗證，無錯誤與警告方為合格",
        "metadata_required": "title, creator (author), language (BCP 47), identifier (ISBN 或 UUID), publisher, date",
        "fixed_layout": "兒童繪本必須使用固定版面（fixed-layout），透過 OPF 中 rendition:layout 與 rendition:orientation 設定",
        "image_requirements": "JPEG/PNG，解析度至少 300 DPI，色彩空間 RGB，單頁不超過 5MB",
        "accessibility": "必須為圖片加上 alt 文字描述（WCAG 2.1 AA 標準）",
        "max_file_size": {
            "amazon_kdp": "650 MB",
            "apple_books": "2 GB",
            "google_play_books": "100 MB",
            "default": "100 MB",
        },
    },
    "mobi": {
        "name": "MOBI / KF8",
        "note": "Amazon Kindle 舊版格式，已逐步被 KPF/EPUB 取代。KDP 自 2021 年起已停止接受 MOBI 新上傳，建議直接上傳 EPUB 由 KDP 自動轉換。",
        "usage": "僅用於舊版 Kindle 裝置之向後相容性",
        "accepted_by": ["amazon_kdp"],
        "deprecated": True,
    },
    "pdf": {
        "name": "PDF",
        "mime_type": "application/pdf",
        "print_requirements": {
            "color_space": "CMYK",
            "resolution": "300 DPI",
            "bleed": "0.125 英吋（3.175 mm）四邊出血",
            "fonts": "所有字型須內嵌子集",
            "page_size": "依書籍開本設定（兒童繪本常見 8.5\"x8.5\" 或 8\"x10\"）",
        },
        "digital_requirements": {
            "color_space": "RGB",
            "resolution": "72–150 DPI（螢幕閱讀用）",
            "page_size": "依裝置螢幕比例最佳化",
        },
        "validation": "通過 PDF/X-1a:2001 或 PDF/X-4 標準驗證以確保印刷品質",
        "accepted_by": ["google_play_books", "bookbaby", "lulu", "ingramspark", "streetlib", "xinxii", "overdrive"],
    },
}


class EbookPublisherOrgan(BrainComponent):
    """電子書上架引擎器官 — 自動化將兒童電子書上架至 15+ 全球出版與經銷平台。

    涵蓋 Amazon KDP、Apple Books、Google Play Books、Kobo、
    Barnes & Noble、Smashwords、Draft2Digital、BookBaby、Lulu、
    IngramSpark、PublishDrive、StreetLib、XinXii、Tolino、OverDrive 等平台，
    提供完整的稿件準備、格式轉換、上架管理與銷售追蹤功能。
    """

    def __init__(self, dna: Optional[dict] = None):
        super().__init__(dna)
        self._books: Dict[str, Dict[str, Any]] = {}
        self._publisher_accounts: Dict[str, Dict[str, Any]] = {}

    # ── 公開方法 ─────────────────────────────────────────────

    @tool(name="prepare_manuscript", description="準備電子書稿件元資料，含書名、作者、語言、分類、年齡範圍與插畫類型")
    def prepare_manuscript(
        self,
        title: str,
        author: str,
        language: str = "zh-TW",
        category: str = "兒童圖書",
        age_range: str = "3-5",
        page_count: int = 28,
        illustration_type: str = "全彩數位插畫",
    ) -> dict:
        """建立並儲存一份兒童電子書的稿件元資料。

        針對兒童書需求，記錄年齡範圍（0–2、3–5、6–8、9–12）、
        頁數範圍、插畫類型等關鍵出版參數，作為後續格式轉換與
        平台上架的基準。

        Args:
            title: 書名
            author: 作者姓名或筆名
            language: 語言代碼，預設 zh-TW（繁體中文）
            category: 書籍分類，預設「兒童圖書」
            age_range: 適合年齡範圍（0-2 / 3-5 / 6-8 / 9-12）
            page_count: 總頁數
            illustration_type: 插畫類型（如：全彩數位插畫、水彩手繪、混合媒材等）

        Returns:
            dict: 含 manuscript_id 與完整稿件元資料。
        """
        if not title.strip():
            raise ValueError("書名不可為空")
        if not author.strip():
            raise ValueError("作者名稱不可為空")
        if not language.strip():
            raise ValueError("語言不可為空")
        if age_range not in AGE_RANGE_INFO:
            raise ValueError(f"不支援的年齡範圍: {age_range}，支援: {list(AGE_RANGE_INFO)}")
        if page_count < 4:
            raise ValueError("頁數至少為 4 頁")

        age_info = AGE_RANGE_INFO[age_range]
        min_pages, max_pages = age_info["typical_page_count"]
        if page_count < min_pages or page_count > max_pages:
            raise ValueError(
                f"年齡範圍 {age_info['label']} 建議頁數為 {min_pages}–{max_pages} 頁，"
                f"當前設定 {page_count} 頁超出建議範圍"
            )

        manuscript_id = str(uuid.uuid4())[:8]
        record = {
            "manuscript_id": manuscript_id,
            "title": title.strip(),
            "author": author.strip(),
            "language": language.strip(),
            "category": category.strip(),
            "age_range": age_range,
            "age_range_label": age_info["label"],
            "book_type": age_info["book_type"],
            "page_count": page_count,
            "word_count_range": age_info["word_count_range"],
            "illustration_type": illustration_type.strip(),
            "illustration_style_recommendation": age_info["illustration_style"],
            "format_recommendation": age_info["format_recommendation"],
            "created_at": datetime.now().isoformat(),
            "status": "draft",
        }
        self._books[manuscript_id] = record

        return {
            "manuscript_id": manuscript_id,
            "title": record["title"],
            "author": record["author"],
            "language": record["language"],
            "category": record["category"],
            "age_range": record["age_range"],
            "age_range_label": record["age_range_label"],
            "book_type": record["book_type"],
            "page_count": record["page_count"],
            "word_count_range": record["word_count_range"],
            "illustration_type": record["illustration_type"],
            "format_recommendation": record["format_recommendation"],
            "status": "draft",
            "next_steps": [
                "使用 format_ebook() 為此稿件進行格式轉換規格設定",
                "選擇目標出版平台後使用 publish_to_platform() 執行上架",
                "確認插畫已完成且解析度符合各平台要求",
            ],
        }

    @tool(name="format_ebook", description="根據指定輸出格式（EPUB/MOBI/PDF），為電子書稿件產出格式轉換需求規格")
    def format_ebook(self, manuscript_id: str, formats: List[str]) -> dict:
        """為指定稿件產出各格式的轉換規格與技術需求清單。

        針對兒童書的特殊需求（固定版面、高解析度圖片），
        提供 EPUB 3.0 固定版面、MOBI/KF8 相容性、PDF 印刷規格
        等詳細技術指引。

        Args:
            manuscript_id: 稿件 ID
            formats: 目標輸出格式清單（epub / mobi / pdf）

        Returns:
            dict: 含各格式技術規格、檔案大小限制與平台相容性對照。
        """
        if manuscript_id not in self._books:
            raise KeyError(f"找不到稿件: {manuscript_id}")
        if not formats or not isinstance(formats, list):
            raise ValueError("formats 必須為非空清單")
        valid_fmts = {"epub", "mobi", "pdf"}
        invalid = [f for f in formats if f not in valid_fmts]
        if invalid:
            raise ValueError(f"不支援的格式: {invalid}，支援: {list(valid_fmts)}")

        book = self._books[manuscript_id]
        age_range = book["age_range"]
        is_childrens_picture_book = age_range in ("0-2", "3-5", "6-8")

        format_specs: Dict[str, Dict[str, Any]] = {}

        for fmt in formats:
            req = FORMAT_REQUIREMENTS[fmt]
            spec = {
                "format": fmt,
                "format_name": req["name"],
                "file_specifications": {},
                "file_size_limits": {},
            }

            if fmt == "epub":
                spec["file_specifications"] = {
                    "版本": "EPUB 3.2",
                    "布局模式": (
                        "固定版面（fixed-layout）" if is_childrens_picture_book else "可重排（reflowable）"
                    ),
                    "XHTML 結構": "每頁一個 XHTML 檔案，使用 viewport meta 標籤設定頁面尺寸",
                    "CSS 樣式": "使用 CSS 2.1 及 EPUB 3 相容屬性，避免 Javascript",
                    "圖片規格": (
                        f"JPEG/PNG，300 DPI 以上，RGB 色彩空間，單頁不超過 5MB。"
                        f"兒童繪本建議每頁圖片尺寸與最終印刷尺寸一致（如 8.5\"x8.5\" 為 2550x2550 px）"
                    ),
                    "無障礙要求": "每個 <img> 元素必須提供 alt 屬性描述圖片內容（WCAG 2.1 AA）",
                    "驗證工具": "EPUBCheck 4.2+，必須零錯誤通過",
                    "中文字型": "須內嵌繁體中文字型或使用系統安全字型（如 Noto Sans TC），確保跨裝置顯示一致",
                }
                spec["file_size_limits"] = {
                    "Amazon KDP": "最大 650 MB",
                    "Apple Books": "最大 2 GB",
                    "Google Play Books": "最大 100 MB",
                    "Kobo": "最大 100 MB",
                }
            elif fmt == "mobi":
                spec["file_specifications"] = {
                    "狀態": "已淘汰格式，KDP 自 2021 年起停止接受 MOBI 新上傳",
                    "替代方案": "直接上傳 EPUB 3.0 至 Amazon KDP，由系統自動轉換為 KF8/KPF 格式",
                    "舊版相容": "若需手動建立 MOBI，使用 Kindle Previewer 3 將 EPUB 轉為 MOBI/KF8",
                }
                spec["file_size_limits"] = {
                    "Amazon KDP": "最大 650 MB（以 EPUB 原始檔計算）",
                }
                spec["note"] = req.get("note", "")
            elif fmt == "pdf":
                if age_range in ("0-2", "3-5"):
                    spec["file_specifications"] = {
                        "印刷用_PDF": {
                            "色彩空間": "CMYK (FOGRA39 或 GRACoL 2013)",
                            "解析度": "300 DPI",
                            "出血": "四邊各 0.125 英吋（3.175 mm）",
                            "字型內嵌": "全部字型必須內嵌子集（subset），包括中文字型",
                            "頁面尺寸": "依繪本開本設定，常見為 8.5\"x8.5\" 方形或 8\"x10\" 直式",
                            "合規標準": "PDF/X-1a:2001 或 PDF/X-4",
                            "條碼區域": "封面須預留 ISBN 條碼區域（建議右下角 2\"x1.25\" 白色區域）",
                        },
                        "數位用_PDF": {
                            "色彩空間": "RGB",
                            "解析度": "150 DPI（兼顧畫質與檔案大小）",
                            "頁面尺寸": "依目標裝置螢幕比例最佳化",
                        },
                    }
                else:
                    spec["file_specifications"] = {
                        "數位用_PDF": {
                            "色彩空間": "RGB",
                            "解析度": "150 DPI",
                            "字型內嵌": "所有字型須內嵌子集",
                        },
                    }
                spec["file_size_limits"] = {
                    "Google Play Books": "最大 100 MB",
                    "IngramSpark": "最大 100 MB（PDF/X-1a 格式）",
                    "Lulu": "最大 100 MB",
                }
                spec["accepted_by_platforms"] = req.get("accepted_by", [])

            format_specs[fmt] = spec

        book["target_formats"] = formats
        book["format_specs"] = format_specs
        book["status"] = "formatted"

        return {
            "manuscript_id": manuscript_id,
            "title": book["title"],
            "age_range": age_range,
            "age_range_label": book["age_range_label"],
            "is_childrens_picture_book": is_childrens_picture_book,
            "target_formats": formats,
            "format_specifications": format_specs,
            "status": "formatted",
            "tip": (
                "兒童繪本（0-2/3-5/6-8 歲）必須使用固定版面 EPUB 3.0。"
                "上傳至 Amazon KDP 時只需提供 EPUB，系統自動轉換為 Kindle 格式。"
                "PDF 印刷檔請確實設定出血與 CMYK 色彩以確保印製品質。"
            ),
        }

    @tool(name="publish_to_platform", description="將電子書稿件模擬上架至指定出版平台，回傳該平台的 ISBN、稅務、版稅等需求清單")
    def publish_to_platform(
        self,
        manuscript_id: str,
        platform: str,
        price: float = 4.99,
        territories: Optional[List[str]] = None,
    ) -> dict:
        """將電子書稿件模擬上架至指定出版平台。

        回傳完整的平台上架需求清單，包含：
        - ISBN 需求（需自行購買或平台提供免費 ISBN）
        - 稅務表單要求（W-8BEN、W-9 等）
        - 版稅計算說明（依定價與平台費率）
        - 檔案格式要求
        - 兒童書分類上架指引

        Args:
            manuscript_id: 稿件 ID
            platform: 目標平台代碼（amazon_kdp / apple_books / google_play_books / kobo /
                      barnes_noble / smashwords / draft2digital / bookbaby / lulu /
                      ingramspark / publishdrive / streetlib / xinxii / tolino / overdrive）
            price: 零售定價（美元），預設 $4.99（兒童書常見定價區間 $2.99–$9.99）
            territories: 銷售地區清單，None 則使用平台預設全球發行

        Returns:
            dict: 含該平台之上架必要條件、預估版稅與注意事項。
        """
        if manuscript_id not in self._books:
            raise KeyError(f"找不到稿件: {manuscript_id}")
        if platform not in PUBLISHER_PLATFORMS:
            raise ValueError(f"不支援的平台: {platform}，支援: {list(PUBLISHER_PLATFORMS)}")
        if price <= 0:
            raise ValueError("定價必須大於 0")

        book = self._books[manuscript_id]
        cfg = PUBLISHER_PLATFORMS[platform]

        royalty_numeric = cfg["royalty_numeric"]
        effective_royalty_rate = royalty_numeric

        if platform == "amazon_kdp" and (price < 2.99 or price > 9.99):
            effective_royalty_rate = 0.35
        if platform == "kobo" and price < 2.99:
            effective_royalty_rate = 0.45

        estimated_royalty_per_sale = round(price * effective_royalty_rate, 2)
        delivery_cost_per_unit = 0.0
        if platform == "amazon_kdp":
            delivery_cost_per_unit = round(0.15 * (book.get("page_count", 32) / 10), 2)

        territory_list = territories if territories else cfg["territories"]

        publish_id = str(uuid.uuid4())[:8]
        record = {
            "publish_id": publish_id,
            "manuscript_id": manuscript_id,
            "title": book["title"],
            "platform": platform,
            "platform_name": cfg["name"],
            "price_usd": price,
            "territories": territory_list,
            "published_at": datetime.now().isoformat(),
            "status": "published",
        }
        self._publisher_accounts.setdefault(platform, {})
        self._publisher_accounts[platform][manuscript_id] = record

        if "published_platforms" not in book:
            book["published_platforms"] = {}
        book["published_platforms"][platform] = {
            "publish_id": publish_id,
            "price": price,
            "royalty_rate_applied": effective_royalty_rate,
            "published_at": record["published_at"],
        }
        book["status"] = "published"

        return {
            "publish_id": publish_id,
            "manuscript_id": manuscript_id,
            "title": book["title"],
            "author": book["author"],
            "platform": platform,
            "platform_name": cfg["name"],
            "url": cfg["url"],
            "price": price,
            "effective_royalty_rate": f"{int(effective_royalty_rate * 100)}%",
            "estimated_royalty_per_sale": estimated_royalty_per_sale,
            "delivery_cost_per_unit": delivery_cost_per_unit,
            "territories": territory_list,
            "requirements_checklist": {
                "isbn_required": cfg["isbn_required"],
                "isbn_note": "需自行購買 Bowker (美國) 或各國 ISBN 機構之 ISBN。兒童書不同版本（EPUB/PDF）需不同 ISBN。" if cfg["isbn_required"] else "平台提供免費 ASIN 或內部識別碼，但建議仍自行購買 ISBN 以保留完整版權控制",
                "tax_forms": cfg["tax_requirements"],
                "accepted_formats": cfg["accepted_formats"],
                "payout_threshold": cfg["payout_threshold"],
                "childrens_book_note": cfg["childrens_book_support"],
            },
            "setup_guide": cfg["setup_guide"],
            "status": "published",
            "published_at": record["published_at"],
        }

    @tool(name="track_sales", description="追蹤指定電子書稿件在所有已上架平台的模擬銷售數據，含銷量、營收與版稅")
    def track_sales(self, manuscript_id: str) -> dict:
        """追蹤指定稿件在所有已上架平台的銷售表現。

        產出各平台的單位銷量、總營收、版稅收入與排名估計，
        以稿件內容特性為基礎計算差異化的平台上表現。

        Args:
            manuscript_id: 稿件 ID

        Returns:
            dict: 含各平台銷售明細、總版稅與最佳表現平台排名。
        """
        if manuscript_id not in self._books:
            raise KeyError(f"找不到稿件: {manuscript_id}")

        book = self._books[manuscript_id]
        published = book.get("published_platforms", {})
        if not published:
            raise RuntimeError(f"稿件 {manuscript_id} 尚未上架至任何平台，請先使用 publish_to_platform")

        platform_sales: List[Dict[str, Any]] = []
        total_units = 0
        total_revenue = 0.0
        total_royalties = 0.0
        title_seed = abs(hash(book["title"] + book["author"]))

        for plat, pub_info in published.items():
            cfg = PUBLISHER_PLATFORMS[plat]
            plat_seed = abs(hash(plat + book["title"]))
            age_factor_map = {"0-2": 1.4, "3-5": 1.6, "6-8": 1.3, "9-12": 1.0}
            age_factor = age_factor_map.get(book["age_range"], 1.0)
            market_size_map = {
                "amazon_kdp": 800, "apple_books": 400, "google_play_books": 250,
                "kobo": 180, "barnes_noble": 150, "smashwords": 80,
                "draft2digital": 90, "bookbaby": 50, "lulu": 60,
                "ingramspark": 120, "publishdrive": 100, "streetlib": 70,
                "xinxii": 40, "tolino": 100, "overdrive": 300,
            }

            base_sales = market_size_map.get(plat, 100)
            units = int(base_sales * age_factor + (title_seed % 50) + (plat_seed % 30))
            price = pub_info["price"]
            royalty_rate = pub_info["royalty_rate_applied"]
            revenue = round(units * price, 2)
            royalty = round(units * price * royalty_rate, 2)

            rank_map = {
                "amazon_kdp": f"#{units % 5000 + 100:,}（兒童書類別）",
                "apple_books": f"#{units % 3000 + 50:,}（兒童與青少年）",
                "google_play_books": f"#{units % 4000 + 200:,}（童書）",
                "kobo": f"#{units % 2000 + 30:,}（Kids）",
                "barnes_noble": f"#{units % 3000 + 80:,}（Nook Kids）",
                "overdrive": f"#{units % 10000 + 500:,}（圖書館借閱次數）",
            }

            total_units += units
            total_revenue += revenue
            total_royalties += royalty

            platform_sales.append({
                "platform": plat,
                "platform_name": cfg["name"],
                "units_sold": units,
                "retail_price": price,
                "gross_revenue": revenue,
                "royalty_rate": f"{int(royalty_rate * 100)}%",
                "royalties_earned": royalty,
                "estimated_rank": rank_map.get(plat, f"#{units % 3000 + 100:,}"),
            })

        platform_sales.sort(key=lambda x: x["units_sold"], reverse=True)

        return {
            "manuscript_id": manuscript_id,
            "title": book["title"],
            "author": book["author"],
            "age_range": book["age_range_label"],
            "published_platforms_count": len(published),
            "total_units_sold": total_units,
            "total_gross_revenue": round(total_revenue, 2),
            "total_royalties_earned": round(total_royalties, 2),
            "average_royalty_per_unit": round(total_royalties / max(1, total_units), 2),
            "platform_breakdown": platform_sales,
            "best_performing_platform": platform_sales[0]["platform_name"] if platform_sales else None,
            "tracked_at": datetime.now().isoformat(),
        }

    @tool(name="list_platforms", description="列出所有 15 個電子書出版平台及其版稅費率、格式要求與平台特色")
    def list_platforms(self) -> dict:
        """列出所有 15 個支援的電子書出版與經銷平台，包含版稅費率、格式要求與兒童書支援程度。

        Returns:
            dict: 含各平台完整資訊與目前已啟用的平台數。
        """
        platforms_list: List[Dict[str, Any]] = []
        active_count = 0

        for key, cfg in PUBLISHER_PLATFORMS.items():
            has_published = key in self._publisher_accounts and len(self._publisher_accounts.get(key, {})) > 0
            if has_published:
                active_count += 1
            platforms_list.append({
                "platform_key": key,
                "platform_name": cfg["name"],
                "url": cfg["url"],
                "royalty_rate": cfg["royalty_rate"],
                "royalty_numeric": cfg["royalty_numeric"],
                "accepted_formats": cfg["accepted_formats"],
                "isbn_required": cfg["isbn_required"],
                "has_published_books": has_published,
                "published_count": len(self._publisher_accounts.get(key, {})),
                "best_for": cfg["best_for"],
                "childrens_book": cfg["childrens_book_support"],
                "territories": cfg["territories"],
            })

        return {
            "total_platforms": len(PUBLISHER_PLATFORMS),
            "active_platforms": active_count,
            "platforms": platforms_list,
        }

    @tool(name="generate_childrens_book_ideas", description="根據主題與年齡範圍產生兒童書創作靈感，含建議書名、故事大綱與插畫方向")
    def generate_childrens_book_ideas(self, theme: str, age_range: str = "3-5") -> dict:
        """根據指定主題與年齡範圍，產出兒童書創作靈感包。

        包含多組建議書名、故事大綱、核心教育價值與插畫風格指引，
        協助作者快速建立兒童書出版方向。

        Args:
            theme: 故事主題（如：友誼、勇氣、自然、太空、海洋、恐龍等）
            age_range: 適合年齡範圍（0-2 / 3-5 / 6-8 / 9-12）

        Returns:
            dict: 含多組書名建議、故事大綱與教育價值說明。
        """
        if age_range not in AGE_RANGE_INFO:
            raise ValueError(f"不支援的年齡範圍: {age_range}，支援: {list(AGE_RANGE_INFO)}")
        if not theme.strip():
            raise ValueError("主題不可為空")

        age_info = AGE_RANGE_INFO[age_range]
        theme_seed = abs(hash(theme.strip() + age_range))

        idea_pools: Dict[str, Dict[str, Any]] = {
            "友誼": {
                "titles": [
                    f"小小熊找朋友",
                    f"不一樣也沒關係",
                    f"彩虹橋上的約定",
                    f"最特別的禮物",
                ],
                "outline": "主角在旅程中認識與自己不同的朋友，學會包容與合作。過程中經歷誤會與和解，最終體會友誼的真正意義。",
                "educational_value": "社交情緒學習（SEL）、同理心、多元包容、衝突解決",
                "illustration_style": "溫暖柔和色調，角色表情豐富，肢體互動場景",
            },
            "勇氣": {
                "titles": [
                    f"第一次上學去",
                    f"黑夜裡的小燈籠",
                    f"小小冒險家的探險日記",
                    f"勇敢的說不",
                ],
                "outline": "主角面對內心的恐懼（第一次上學、怕黑、嘗試新事物），在探索過程中發現自己的勇氣與韌性。",
                "educational_value": "自我認同、克服恐懼、成長心態、解決問題能力",
                "illustration_style": "色彩對比由灰暗漸轉明亮，象徵主角內心的轉變歷程",
            },
            "自然": {
                "titles": [
                    f"種子的秘密旅行",
                    f"森林裡的小小守護者",
                    f"跟著風兒去探險",
                    f"小水滴的奇幻漂流",
                ],
                "outline": "透過自然界中微小事物的視角，帶領小讀者認識生態循環、季節變化與生命奇蹟。",
                "educational_value": "自然科學啟蒙、環境保護意識、生命教育、觀察力培養",
                "illustration_style": "寫實與想像結合的自然場景，豐富的動植物細節",
            },
            "太空": {
                "titles": [
                    f"小火箭的星際旅行",
                    f"月亮上的兔子朋友",
                    f"誰住在火星上？",
                    f"宇宙探險隊：太陽系之旅",
                ],
                "outline": "主角搭乘想像中的太空船造訪太陽系各大行星，認識天文知識的同時展開一段星際友誼冒險。",
                "educational_value": "天文科學啟蒙、好奇心培養、科學思維、團隊合作",
                "illustration_style": "明亮夢幻的宇宙色調，擬人化的星球與太空船",
            },
            "海洋": {
                "titles": [
                    f"小鯨魚的尋家之旅",
                    f"珊瑚礁的秘密花園",
                    f"海龜爺爺說故事",
                    f"沙灘上的寶藏",
                ],
                "outline": "主角潛入海洋世界，結識各種海洋生物，發現海洋生態之美也意識到保護海洋的重要性。",
                "educational_value": "海洋生態教育、環境保護、生物多樣性、家族與歸屬感",
                "illustration_style": "豐富藍色系漸層，細膩的水下光影與海洋生物細節",
            },
            "恐龍": {
                "titles": [
                    f"小暴龍的生日派對",
                    f"三角龍上學去",
                    f"誰偷了恐龍蛋？",
                    f"恐龍幼兒園的一天",
                ],
                "outline": "以擬人化恐龍角色演出幼兒日常情境（上學、交友、分享），讓小讀者在熟悉的恐龍角色中學習生活技能。",
                "educational_value": "生活習慣養成、社交技巧、情緒表達、分享與輪流",
                "illustration_style": "可愛卡通化恐龍造型，明亮活潑色彩，生活場景",
            },
        }

        theme_lower = theme.strip()
        matched_idea = idea_pools.get(theme_lower)
        if not matched_idea:
            generic_titles = [
                f"《{theme}大冒險》",
                f"《小不點的{theme}日記》",
                f"《{theme}的秘密》",
                f"《走進{theme}的世界》",
            ]
            matched_idea = {
                "titles": generic_titles,
                "outline": f"以 {theme} 為核心主題，透過適合 {age_info['label']} 的故事情節與角色互動，引導小讀者認識並喜愛 {theme}。",
                "educational_value": f"{theme} 相關知識啟蒙與價值觀建立",
                "illustration_style": f"適合 {age_info['label']} 的視覺風格，{age_info['illustration_style']}",
            }

        title_count = min(4, theme_seed % 4 + 1)
        selected_titles = matched_idea["titles"][:title_count]

        return {
            "theme": theme.strip(),
            "age_range": age_range,
            "age_range_label": age_info["label"],
            "book_type": age_info["book_type"],
            "word_count_range": age_info["word_count_range"],
            "suggested_titles": selected_titles,
            "story_outline": matched_idea["outline"],
            "educational_value": matched_idea["educational_value"],
            "illustration_direction": matched_idea["illustration_style"],
            "format_recommendation": age_info["format_recommendation"],
            "idea_count": len(selected_titles),
        }

    def status(self) -> dict:
        """回報器官當前狀態。

        Returns:
            dict: 含已出版書籍數、總版稅、啟用平台數及上架概況。
        """
        published_books = [
            b for b in self._books.values() if b.get("status") == "published"
        ]
        total_royalties = 0.0
        book_count = len(published_books)

        for b in published_books:
            for plat, pub_info in b.get("published_platforms", {}).items():
                price = pub_info.get("price", 0)
                royalty_rate = pub_info.get("royalty_rate_applied", 0)
                units_est = 50
                total_royalties += price * royalty_rate * units_est

        platforms_live = [
            plat for plat, acc in self._publisher_accounts.items() if len(acc) > 0
        ]

        return {
            "name": "EbookPublisherOrgan",
            "alive": True,
            "published_books": book_count,
            "total_manuscripts": len(self._books),
            "total_royalties": round(total_royalties, 2),
            "platforms_live": platforms_live,
            "platforms_live_count": len(platforms_live),
            "supported_platforms": list(PUBLISHER_PLATFORMS.keys()),
        }
