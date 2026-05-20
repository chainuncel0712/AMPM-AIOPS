"""
黑曜品牌視覺分析腳本 — 分析三張 LOGO，整合童書大方向，產出企業品牌形象書
"""
import os, sys, json, base64, time, requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

BASE = Path(__file__).parent
NVIDIA_KEY = os.getenv("NVIDIA_API_KEY", "")
ATXP_CONN = os.getenv("ATXP_CONNECTION_STRING", "")
ATXP_MODEL = os.getenv("ATXP_MODEL", "gpt-4.1")
DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY", "")

IMAGES = {
    "text_logo": ("0022.png", "文字 LOGO：AM&PM ADVENTURE 品牌標準字"),
    "children_logo": ("children_logo.jpg", "童書封面用 LOGO：動物 IP 角色設計"),
    "web_logo": ("web_logo.png", "網站用 LOGO"),
}

def img_to_b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def mime_type(path):
    ext = Path(path).suffix.lower()
    return {"jpg": "jpeg", "jpeg": "jpeg", "png": "png"}.get(ext, "jpeg")

def call_vision(b64, mime, questions, provider="nvidia"):
    content = [{"type": "text", "text": q} for q in questions]
    content.append({"type": "image_url", "image_url": {"url": f"data:image/{mime};base64,{b64}"}})

    if provider == "nvidia" and NVIDIA_KEY:
        try:
            r = requests.post(
                "https://integrate.api.nvidia.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {NVIDIA_KEY}", "Content-Type": "application/json"},
                json={"model": "meta/llama-3.2-90b-vision-instruct", "messages": [{"role": "user", "content": content}], "max_tokens": 2000},
                timeout=60
            )
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"], "nvidia"
            else:
                print(f"  NVIDIA {r.status_code}: {r.text[:200]}")
        except Exception as e:
            print(f"  NVIDIA error: {e}")

    if provider in ("nvidia", "atxp") and ATXP_CONN:
        try:
            r = requests.post(
                "https://llm.atxp.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {ATXP_CONN}", "Content-Type": "application/json"},
                json={"model": ATXP_MODEL, "messages": [{"role": "user", "content": content}], "max_tokens": 2000},
                timeout=60
            )
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"], "atxp"
        except Exception as e:
            print(f"  ATXP error: {e}")

    return None, None

# ============================================================
# Step 1: 分析三張 LOGO
# ============================================================
print("=" * 60)
print("黑曜品牌視覺分析 — 開始")
print("=" * 60)

analyses = {}
for key, (fname, desc) in IMAGES.items():
    fpath = BASE / fname
    print(f"\n📷 分析 [{key}] {desc}...")
    b64 = img_to_b64(fpath)
    mime = mime_type(fpath)

    questions = [
        f"請詳細描述這張圖片的內容。類型：{desc}。請分析：1) 視覺風格與調性 2) 主要色彩(含hex色碼) 3) 字體風格 4) 構圖特色 5) 品牌感與識別度。用繁體中文回答。"
    ]

    result, provider = call_vision(b64, mime, questions, "nvidia")
    if not result:
        print(f"  ↻ NVIDIA失敗，切換 ATXP...")
        result, provider = call_vision(b64, mime, questions, "atxp")

    if result:
        analyses[key] = {"file": fname, "description": desc, "analysis": result, "provider": provider}
        print(f"  ✅ {provider.upper()} 完成 ({len(result)}字)")
    else:
        analyses[key] = {"file": fname, "description": desc, "analysis": "視覺分析失敗", "provider": "none"}
        print(f"  ❌ 分析失敗")

# Save analysis cache
with open(BASE / "vision_analysis.json", "w") as f:
    json.dump(analyses, f, ensure_ascii=False, indent=2)
print(f"\n📁 視覺分析存檔 → vision_analysis.json")

# ============================================================
# Step 2: 讀取童書大方向
# ============================================================
print("\n📖 讀取品牌方向文件...")
brand_direction = (BASE / "brand_direction.txt").read_text()
print(f"  方向文件: {len(brand_direction)}字")

# ============================================================
# Step 3: DeepSeek 整合產出品牌形象書
# ============================================================
print("\n🧠 DeepSeek 整合產出品牌書...")

vision_summary = "\n\n".join([
    f"## {k}\n{desc}\n分析結果: {v['analysis'][:800]}"
    for k, v in analyses.items()
    for desc in [v['description']]
])

prompt = f"""你是品牌策略師。請根據以下素材，產出一份完整的「企業品牌形象書」。

=== 視覺 LOGO 分析 ===
{vision_summary}

=== 品牌方向（童書大方向） ===
{brand_direction[:5000]}

請用繁體中文，產出一份結構完整的品牌書，包含以下章節：

## 1. 品牌核心
- 品牌名、品牌承諾、一句話定位
- 品牌價值主張

## 2. 視覺識別系統
- LOGO 分析與應用規範（文字LOGO、童書LOGO、網站LOGO 各自用途）
- 色彩系統（主色、輔色、hex色碼）
- 字體規範建議

## 3. IP 角色體系
- PANEY & MONEY 角色設定
- IP 世界觀與故事框架
- IP 衍生可能性（周邊、跨媒體）

## 4. 品牌聲音與文案風格
- 語調定位
- 品牌口號（中英）
- 文案範例

## 5. 產品體系
- 童書系列架構（20本一季）
- 工具書/電子書方向
- 產品線擴張路線圖

## 6. 市場定位
- 目標受眾
- 平台策略
- 競爭優勢

## 7. 品牌執行手冊
- 封面設計規則
- 上架素材標準格式
- 品牌一致性檢查清單

請直接輸出完整內容，不要說「這是一個草案」之類的廢話。這是要直接拿去用的品牌書。
"""

r = requests.post(
    "https://api.deepseek.com/v1/chat/completions",
    headers={"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"},
    json={
        "model": "deepseek-v4-pro",
        "messages": [{"role": "system", "content": "你是品牌策略專家，產出直接可用的完整文件，不閒聊、不廢話、不道歉。"},
                      {"role": "user", "content": prompt}],
        "max_tokens": 8000,
        "temperature": 0.7
    },
    timeout=120
)

if r.status_code == 200:
    brand_book = r.json()["choices"][0]["message"]["content"]
    out_path = BASE / "enterprise_brand_book.md"
    with open(out_path, "w") as f:
        f.write(f"# AMPM-AIOPS 企業品牌形象書\n\n")
        f.write(f"> 生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"> 視覺分析提供者: NVIDIA Llama 3.2 Vision / ATXP gpt-4.1\n")
        f.write(f"> 品牌策略: DeepSeek v4-pro\n\n")
        f.write("---\n\n")
        f.write(brand_book)
    print(f"\n✅ 品牌書已產出: {out_path} ({len(brand_book)}字)")
    # Also save raw
    with open(BASE / "brand_book_raw.txt", "w") as f:
        f.write(brand_book)
else:
    print(f"❌ DeepSeek 失敗: {r.status_code} {r.text[:300]}")

print("\n" + "=" * 60)
print("品牌視覺分析完成")
print(f"輸出目錄: {BASE}")
print("=" * 60)
