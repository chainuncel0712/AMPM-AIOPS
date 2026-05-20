"""黑曜產線 v2 — 開源優先，批次處理"""
import os, json, requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

DS_KEY = os.getenv("DEEPSEEK_API_KEY", "")
ATXP_CONN = os.getenv("ATXP_CONNECTION_STRING", "")
ATXP_MODEL = os.getenv("ATXP_MODEL", "gpt-4.1")
NVIDIA_KEY = os.getenv("NVIDIA_API_KEY", "")
BASE = Path(__file__).parent.parent / "outputs"

def call_llm(system_prompt, user_prompt, max_tokens=4000):
    """deepseek-chat (非推理/免費) → ATXP 備援"""
    providers = [
        ("DeepSeek-Chat", "https://api.deepseek.com/v1/chat/completions", DS_KEY, "deepseek-chat"),
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
                timeout=120)
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"], name
            print(f"  {name} {r.status_code}")
        except Exception as e:
            print(f"  {name}: {e}")
    return None, None

def save_md(path, content, title, provider):
    header = f"# {title}\n\n> 生成: {datetime.now().strftime('%Y-%m-%d %H:%M')} | 模型: {provider}\n\n---\n\n"
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write(header + content)
    return len(content)

# ============================================================
BRAND_BOOK = Path(__file__).parent / "enterprise_brand_book.md"
brand_context = BRAND_BOOK.read_text()[:3000] if BRAND_BOOK.exists() else ""

print("=" * 50)
print("產線 v2 — deepseek-chat 優先")
print("=" * 50)

# === Task 1: IP 角色設定書 ===
print("\n📝 [1/4] IP 角色完整設定書...")
ip_prompt = f"""IP角色設計師，根據以下品牌書，寫 PANEY & MONEY 角色設定書（繁體中文，至少1500字）。

品牌書摘要：{brand_context}

輸出：
## 1. PANEY（夜貓）設定
- 外觀細節：純黑短毛、銀灰雙眸、月亮石吊墜
- 性格：沉穩觀察力強、脆弱點
- 10種表情描述（文字描述，供畫師參考）
- 口頭禪與小習慣

## 2. MONEY（日貓）設定  
- 外觀細節：橘虎斑條紋、琥珀眼、耳尖白毛
- 性格：樂觀行動派、何時會洩氣
- 10種表情描述
- 口頭禪與道具

## 3. 互動關係：吵架/和好/合作模式

## 4. 角色比例規範：頭身比/四肢/尾巴"""
ip, ip_p = call_llm("專業IP角色設計師，產出畫師可直接執行的設定書。", ip_prompt, 4000)
if ip:
    n = save_md(BASE / "children_book/ip_design_bible.md", ip, "PANEY & MONEY IP 角色完整設定書", ip_p)
    print(f"  ✅ {n}字 ({ip_p})")

# === Task 2: 插畫風格指引 ===
print("\n🎨 [2/4] 插畫風格指引書...")
il_prompt = f"""插畫藝術總監，為 PANEY & MONEY 童書系列寫風格指引（繁體中文，至少1200字）。

品牌背景：雙貓IP（PANEY黑貓/MONEY橘虎斑），日夜探險主題，對象3-6歲
品牌書摘要：{brand_context[:1500]}

輸出：
## 1. 風格定位：線條粗細、填色方式、風格關鍵字
## 2. 角色造型規範：頭身比、五官比例、不可變元素
## 3. 場景設計：晨昏城視覺、日夜切換、各場景色調
## 4. 色彩調色盤：白天暖色/夜晚冷色/情緒場景
## 5. 年齡層微調：3-5歲 vs 6-10歲畫風差異"""
il, il_p = call_llm("專業插畫藝術總監，產出畫師可直接執行的風格指引。", il_prompt, 4000)
if il:
    n = save_md(BASE / "children_book/illustration_style_guide.md", il, "PANEY & MONEY 插畫風格指引書", il_p)
    print(f"  ✅ {n}字 ({il_p})")

# === Task 3: 品牌視覺手冊 ===
print("\n🎯 [3/4] 品牌視覺使用手冊...")
v_prompt = f"""品牌視覺設計師，寫可交付設計師的使用手冊（繁體中文，至少1000字）。

品牌書摘要：{brand_context[:1500]}

輸出：
## 1. 色票系統（表格：色名/HEX/RGB/CMYK/用途）
#241E1C(主) #FF8C1A(輔) #189FFF(輔) #F7F7F7(中) #FFD966(強)

## 2. 字體層級：H1-H4/內文/圖說 的字體大小行距

## 3. LOGO使用禁則：不可拉伸/改色/變形/最小尺寸/安全邊距

## 4. 社群平台應用：頭像/封面模板規範"""
vh, vh_p = call_llm("專業品牌視覺設計師，產出設計師可直接執行的規範手冊。", v_prompt, 3000)
if vh:
    n = save_md(BASE / "brand_identity/visual_handbook.md", vh, "品牌色彩與字體使用手冊", vh_p)
    print(f"  ✅ {n}字 ({vh_p})")

# === Task 4: 童書商品頁（批次處理，每批5本） ===
print("\n📚 [4/4] 童書商品頁（15本，分3批）...")

books = [
    ("day06", "出發！彩虹森林的祕密", "Discovering Rainbow Forest's Secret", "自然探索隊"),
    ("day07", "月光海洋的螢火蟲舞會", "Firefly Ball in the Moonlit Ocean", "自然探索隊"),
    ("day08", "沙漠星沙：發現會發光的石頭", "Desert Stardust: The Glowing Stones", "自然探索隊"),
    ("day09", "極地列車：拜訪企鵝郵差", "Polar Express: Visiting Penguin Postman", "自然探索隊"),
    ("day10", "為什麼天空會換顏色？", "Why Does the Sky Change Color?", "科學解謎團"),
    ("day11", "磁力方塊的飄浮實驗室", "Magnetic Blocks' Floating Lab", "科學解謎團"),
    ("day12", "縮小燈！前進人體細胞城", "Shrink Ray! Into the Cell City", "科學解謎團"),
    ("day13", "機械恐龍失控中：齒輪與槓桿", "Runaway Robot Dino: Gears & Levers", "科學解謎團"),
    ("day14", "牙齒王國的早安歌", "Good Morning Song of Tooth Kingdom", "好習慣童話村"),
    ("day15", "生氣雲，飄走囉！", "Angry Cloud, Float Away!", "好習慣童話村"),
    ("day16", "分享貝殼：小海豚教我的事", "Sharing Shells: What Dolphin Taught Me", "好習慣童話村"),
    ("day17", "睡覺時間到！晚安冒險", "Sleepytime! Goodnight Adventure", "好習慣童話村"),
    ("day18", "巴西嘉年華的神奇羽毛扇", "Magic Feather Fan at Brazil Carnival", "世界文化寶盒"),
    ("day19", "日本狸貓的煎茶道旅行", "Tanuki's Tea Ceremony Journey", "世界文化寶盒"),
    ("day20", "埃及貓神與金字塔拼圖", "Egyptian Cat God & Pyramid Puzzle", "世界文化寶盒"),
]

BATCH = 5
total = 0
for batch_start in range(0, len(books), BATCH):
    batch = books[batch_start:batch_start+BATCH]
    batch_text = "\n".join([f"{i+1}. {cn} / {en}（{series}）" for i, (day, cn, en, series) in enumerate(batch)])
    
    bp = f"""童書編輯。為以下 PANEY & MONEY 系列童書各寫商品頁（繁體中文）。
年齡3-6歲（前12本）/5-8歲（後3本）。口號：白天勇敢出發，晚上安心回家。

書單：
{batch_text}

每本輸出格式（依序，不需書名標題）：

【書名】一句話短介（30字內）
短文（120字，從貓咪視角開場帶情境，結尾附學習點）
賣點（5條簡短）
關鍵字（8個）
FAQ（2則，含親子共讀引導）

直接輸出，用「---」分隔各本。"""
    
    content, provider = call_llm("專業童書編輯，產出可直接上架的完整商品頁。精簡有力。", bp, 4000)
    if content:
        # Split and save
        parts = content.split("---")
        for i, (day, cn, en, series) in enumerate(batch):
            part = parts[i].strip() if i < len(parts) else ""
            if not part:
                continue
            
            day_num = int(day[3:])
            if day_num <= 5: d = "day01-05"
            elif day_num <= 10: d = "day06-10"
            elif day_num <= 15: d = "day11-15"
            else: d = "day16-20"
            
            out_dir = BASE / f"children_book/product_pages/{d}"
            out_dir.mkdir(parents=True, exist_ok=True)
            fname = f"{day}_{en.lower().replace(' ','_').replace(':','').replace('?','').replace('!','')[:40]}.md"
            with open(out_dir / fname, "w") as f:
                f.write(f"# {cn} / {en}\n\n> 系列: {series} | {datetime.now().strftime('%Y-%m-%d')}\n\n{part}")
            total += 1
            print(f"  ✅ {day} {cn}")
    else:
        print(f"  ❌ 批次 {batch_start//BATCH+1} 失敗")
    
    print(f"  批次 {batch_start//BATCH+1}/{(len(books)+BATCH-1)//BATCH} 完成")

print(f"\n📚 童書商品頁: {total}/{len(books)} 本")

print("\n" + "=" * 50)
print("產線完成！所有成品已寫入 outputs/")
print("=" * 50)
