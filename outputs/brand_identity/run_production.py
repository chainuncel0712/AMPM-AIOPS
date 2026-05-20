"""黑曜產線 — 接續品牌書後的自動化內容生產"""
import os, json, requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

DS_KEY = os.getenv("DEEPSEEK_API_KEY", "")
ATXP_CONN = os.getenv("ATXP_CONNECTION_STRING", "")
ATXP_MODEL = os.getenv("ATXP_MODEL", "gpt-4.1")
BASE = Path(__file__).parent.parent / "outputs"

def call_llm(system_prompt, user_prompt, max_tokens=6000):
    """Try DeepSeek first, fallback to ATXP"""
    providers = [
        ("DeepSeek", "https://api.deepseek.com/v1/chat/completions", DS_KEY, "deepseek-v4-pro"),
        ("ATXP", "https://llm.atxp.ai/v1/chat/completions", ATXP_CONN, ATXP_MODEL),
    ]
    for name, ep, key, model in providers:
        if not key:
            continue
        try:
            r = requests.post(ep,
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={"model": model, "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ], "max_tokens": max_tokens, "temperature": 0.7, "stream": False},
                timeout=180)
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"], name
            print(f"  {name} HTTP {r.status_code}: {r.text[:150]}")
        except Exception as e:
            print(f"  {name} error: {e}")
    return None, None

def save_md(path, content, title, provider):
    header = f"# {title}\n\n> 生成: {datetime.now().strftime('%Y-%m-%d %H:%M')} | 模型: {provider}\n\n---\n\n"
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write(header + content)
    return len(content)

# ============================================================
BRAND_BOOK = Path(__file__).parent / "enterprise_brand_book.md"
brand_context = BRAND_BOOK.read_text() if BRAND_BOOK.exists() else ""

print("=" * 60)
print("黑曜產線啟動 — 4 任務並行")
print("=" * 60)

# --- Task 1: IP 角色設定書 ---
print("\n📝 [1/4] IP 角色完整設定書...")
ip_prompt = f"""你是IP角色設計師。根據以下品牌書，撰寫完整的 PANEY & MONEY IP 角色設定書。

=== 品牌書參考 ===
{brand_context[:3000]}

請輸出（繁體中文，至少1500字）：

## 1. PANEY（夜貓）詳細設定
- 外觀：純黑短毛、銀灰雙眸、月亮石吊墜的細節（形狀/大小/光澤）
- 性格：沉穩、觀察力強，但內心有什麼脆弱點？
- 口頭禪與習慣：常說的話、緊張時的小動作
- 10種表情描述：開心、難過、生氣、害怕、好奇、得意、困惑、害羞、疲憊、堅定

## 2. MONEY（日貓）詳細設定
- 外觀：橘虎斑條紋、琥珀眼、耳尖白毛的細節
- 性格：樂觀行動派，但什麼情況會讓他洩氣？
- 口頭禪與習慣：常說的話、隨身攜帶的小道具
- 10種表情描述（同上）

## 3. 雙貓互動關係
- 吵架模式、和好方式、合作默契
- 誰依賴誰比較多？什麼時刻角色會反轉？

## 4. 角色比例圖規範
- 頭身比（幾頭身）
- 四肢比例、尾巴長度
- 不同年齡層的微調建議（Q版 vs 標準版）"""

ip_content, ip_provider = call_llm(
    "你是專業IP角色設計師，為兒童品牌打造可直接交付畫師的角色設定書。內容要具體可執行。",
    ip_prompt, 5000)
if ip_content:
    n = save_md(BASE / "children_book/ip_design_bible.md", ip_content, "PANEY & MONEY IP 角色完整設定書", ip_provider)
    print(f"  ✅ {n}字 (via {ip_provider})")

# --- Task 2: 插畫風格指引 ---
print("\n🎨 [2/4] 插畫風格指引書...")
illust_prompt = f"""你是插畫藝術總監。根據以下品牌書與IP設定，撰寫插畫風格指引書。

=== 品牌書 ===
{brand_context[:2000]}

=== IP設定 ===
{ip_content[:1500] if ip_content else '（參考品牌書第3章）'}

請輸出（繁體中文，至少1200字）：

## 1. 整體風格定位
- 線條風格：粗細、是否保留手繪質感
- 填色方式：平塗/漸層/水彩感
- 風格關鍵字（3-5個，如：溫暖圓潤、美式復古、日系簡約）

## 2. 角色造型規範
- 頭身比、五官比例、簡化規則
- 線稿粗細規範（外輪廓 vs 內細節）
- 不可變更的元素（月亮石/耳尖白毛/條紋方向）

## 3. 場景設計規範
- 晨昏城（Twilight City）視覺設定：建築風格/色調/天空處理
- 日夜切換的視覺語言
- 各冒險場景的氛圍色調建議

## 4. 色彩調色盤（per 場景類型）
- 白天場景調色盤（暖色系為主）
- 夜晚場景調色盤（冷色系為主）
- 情緒場景調色盤（生氣紅/難過藍/開心黃）

## 5. 年齡層畫風微調
- 3-5歲：更大更圓、色彩更飽和、背景簡化
- 6-10歲：細節增加、比例接近寫實、可加入資訊圖表元素"""

illust_content, illust_provider = call_llm(
    "你是專業插畫藝術總監，為兒童品牌產出可直接給畫師執行的風格指引。",
    illust_prompt, 5000)
if illust_content:
    n = save_md(BASE / "children_book/illustration_style_guide.md", illust_content, "PANEY & MONEY 插畫風格指引書", illust_provider)
    print(f"  ✅ {n}字 (via {illust_provider})")

# --- Task 3: 品牌色彩與字體手冊 ---
print("\n🎯 [3/4] 品牌視覺使用手冊...")
visual_prompt = f"""你是品牌視覺設計師。根據品牌書撰寫可交付設計師的完整使用手冊。

=== 品牌書 ===
{brand_context[:2000]}

請輸出（繁體中文，至少1000字）：

## 1. 色票系統
（以表格呈現：色名/HEX/RGB/CMYK/用途）
主色 #241E1C、輔助色 #FF8C1A #189FFF、中性色 #F7F7F7、強調色 #FFD966

## 2. 字體層級規範
- H1-H4 標題：字體/大小/字重/行距
- 內文：字體/大小/行距
- 圖說/註腳
- 童書內頁字體（需較大、友善兒童）

## 3. 三組LOGO使用禁則
- 不可拉伸/變形/改色
- 最小尺寸限制（px）
- 安全邊距規範
- 錯誤使用範例（文字描述）

## 4. 社群平台應用
- Facebook/IG/Twitter 頭像套用規範
- 封面圖模板尺寸建議
- 浮水印使用規則"""

visual_content, visual_provider = call_llm(
    "你是專業品牌視覺設計師，產出可直接交付設計師執行的規範手冊。",
    visual_prompt, 4000)
if visual_content:
    n = save_md(BASE / "brand_identity/visual_handbook.md", visual_content, "品牌色彩與字體使用手冊", visual_provider)
    print(f"  ✅ {n}字 (via {visual_provider})")

# --- Task 4: 童書6-20商品頁 ---
print("\n📚 [4/4] 童書第6-20本商品頁...")

book_series = {
    "A_自然探索隊": [
        ("day06", "出發！彩虹森林的祕密", "Discovering Rainbow Forest's Secret"),
        ("day07", "月光海洋的螢火蟲舞會", "Firefly Ball in the Moonlit Ocean"),
        ("day08", "沙漠星沙：發現會發光的石頭", "Desert Stardust: The Glowing Stones"),
        ("day09", "極地列車：拜訪企鵝郵差", "Polar Express: Visiting Penguin Postman"),
    ],
    "B_科學解謎團": [
        ("day10", "為什麼天空會換顏色？", "Why Does the Sky Change Color?"),
        ("day11", "磁力方塊的飄浮實驗室", "Magnetic Blocks' Floating Lab"),
        ("day12", "縮小燈！前進人體細胞城", "Shrink Ray! Into the Cell City"),
        ("day13", "機械恐龍失控中：齒輪與槓桿", "Runaway Robot Dino: Gears & Levers"),
    ],
    "C_好習慣童話村": [
        ("day14", "牙齒王國的早安歌", "Good Morning Song of Tooth Kingdom"),
        ("day15", "生氣雲，飄走囉！", "Angry Cloud, Float Away!"),
        ("day16", "分享貝殼：小海豚教我的事", "Sharing Shells: What Little Dolphin Taught Me"),
        ("day17", "睡覺時間到！晚安冒險", "Sleepytime! Goodnight Adventure"),
    ],
    "D_世界文化寶盒": [
        ("day18", "巴西嘉年華的神奇羽毛扇", "The Magic Feather Fan at Brazil Carnival"),
        ("day19", "日本狸貓的煎茶道旅行", "Japanese Tanuki's Tea Ceremony Journey"),
        ("day20", "埃及貓神與金字塔拼圖", "Egyptian Cat God & the Pyramid Puzzle"),
    ],
}

total_books = 0
for series_name, books in book_series.items():
    for day, name_cn, name_en in books:
        short_prompt = f"""你是童書編輯。為 PANEY & MONEY 系列寫此書的商品頁，用繁體中文。

書名: {name_cn} / {name_en}
系列: {series_name}
年齡: 3-6歲 (A/B/C系列) 或 5-8歲 (D系列)
IP: PANEY（夜貓/黑）與 MONEY（日貓/橘虎斑）
口號: 白天勇敢出發，晚上安心回家 / Brave by day, cozy by night

請輸出格式（不要開場白，直接輸出內容）:

## {name_cn}
**{name_en}**

### 一句話短介
（30字內）

### 商品頁短文（150字）
（從PANEY或MONEY視角開場，帶入一個情境，結尾附學習點）

### 賣點（5條）
- 

### 關鍵字（10個）
童書、繪本、（主題相關）、親子共讀、3-6歲、PANEY&MONEY

### FAQ（2則）
Q: 
A: 

### 親子共讀引導
- 讀完問孩子："""

        content, provider = call_llm(
            "你是專業童書編輯，產出可直接上架的商品頁文案。精簡有力，每本書控制在300字內。",
            short_prompt, 800)
        
        if content:
            out_dir = BASE / f"children_book/product_pages/{day[:4]}-{int(day[3:])+4:02d}"
            # map to day directories
            day_num = int(day[3:])
            if day_num <= 5:
                d = "day01-05"
            elif day_num <= 10:
                d = f"day06-10"
            elif day_num <= 15:
                d = "day11-15"
            else:
                d = "day16-20"
            out_dir = BASE / f"children_book/product_pages/{d}"
            out_dir.mkdir(parents=True, exist_ok=True)
            
            fname = f"{day}_{name_cn[:12].replace('！','').replace('？','').replace(' ','_')}.md"
            # simpler: use day name
            fname = f"{day}_{name_en.lower().replace(' ','_').replace(':','').replace('?','').replace('!','')[:40]}.md"
            with open(out_dir / fname, "w") as f:
                f.write(f"# {name_cn} / {name_en}\n\n> 系列: {series_name} | 生成: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n---\n\n{content}")
            
            total_books += 1
            print(f"  ✅ {day} {name_cn} ({len(content)}字)")

print(f"\n📚 童書商品頁: {total_books}/15 本完成")

# ============================================================
print("\n" + "=" * 60)
print("黑曜產線完成")
print(f"📁 outputs/brand_identity/visual_handbook.md")
print(f"📁 outputs/children_book/ip_design_bible.md")
print(f"📁 outputs/children_book/illustration_style_guide.md")
print(f"📁 outputs/children_book/product_pages/day06-20/ ({total_books}本)")
print("=" * 60)
