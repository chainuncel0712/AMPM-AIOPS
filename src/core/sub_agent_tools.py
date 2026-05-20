"""
Sub-Agent Tools — 給 AgentCompany 子代理用的真實工具
支援寫檔、跑指令、搜尋、讀檔，讓子代理不只是想，還能真的動手做。
"""
import os
import json
import subprocess
import urllib.request
import urllib.parse
from pathlib import Path

# 輸出的根目錄
OUTPUT_ROOT = Path("/home/pop5057273712_gmail_com/AMPM-AIOPS/outputs")
OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

# 限制：不允許的指令關鍵字
FORBIDDEN_COMMANDS = ["rm -rf", "mkfs", "dd if=", "> /dev/", ":(){", "chmod 777", "wget", "curl"]


def _resolve_path(filepath: str) -> Path:
    """智慧路徑解析：去掉多餘的 outputs/ 前綴，統一到 OUTPUT_ROOT 下。"""
    path = Path(filepath)
    if path.is_absolute():
        return path
    # 去掉可能重複的 "outputs" 或 "outputs/" 前綴
    parts = path.parts
    if parts and parts[0] in ("outputs", "output"):
        path = Path(*parts[1:]) if len(parts) > 1 else Path(".")
    return OUTPUT_ROOT / path


def write_file(filepath: str, content: str) -> str:
    """寫入檔案。路徑自動放在 outputs/ 目錄下。"""
    path = _resolve_path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(content, encoding="utf-8")
        size = len(content.encode("utf-8"))
        return f"✅ 已寫入 {path} ({size} bytes, {len(content)} chars)"
    except Exception as e:
        return f"❌ 寫入失敗: {e}"


def read_file(filepath: str) -> str:
    """讀取檔案內容。"""
    path = _resolve_path(filepath)
    try:
        content = path.read_text(encoding="utf-8")
        if len(content) > 3000:
            return content[:3000] + f"\n...（共 {len(content)} chars，已截斷）"
        return content
    except FileNotFoundError:
        return f"❌ 檔案不存在: {path}"
    except Exception as e:
        return f"❌ 讀取失敗: {e}"


def list_dir(dirpath: str = ".") -> str:
    """列出目錄內容。"""
    path = _resolve_path(dirpath)
    if not path.exists():
        return f"❌ 目錄不存在: {path}（可用 mkdir 建立，或直接用 write_file 會自動建立）"
    try:
        items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
        lines = [f"📁 {path}/"]
        if not items:
            lines.append("  （空目錄）")
        for item in items:
            typ = "📁" if item.is_dir() else "📄"
            size = ""
            if item.is_file():
                try:
                    s = item.stat().st_size
                    size = f" ({s:,} bytes)"
                except:
                    pass
            lines.append(f"  {typ} {item.name}{size}")
        return "\n".join(lines)
    except Exception as e:
        return f"❌ 列目錄失敗: {e}"


def run_command(cmd: str, cwd: str = None) -> str:
    """執行 shell 指令。有安全限制。預設工作目錄為 outputs/。"""
    # 安全檢查
    cmd_lower = cmd.lower()
    for forbidden in FORBIDDEN_COMMANDS:
        if forbidden in cmd_lower:
            return f"❌ 拒絕執行危險指令（包含 '{forbidden}'）"

    work_dir = str(_resolve_path(cwd)) if cwd else str(OUTPUT_ROOT)
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=30, cwd=work_dir,
            env={**os.environ, "PATH": os.environ.get("PATH", "/usr/bin:/bin")}
        )
        output = result.stdout
        if result.stderr:
            output += "\n[stderr]\n" + result.stderr
        if result.returncode != 0:
            output += f"\n[exit code: {result.returncode}]"
        if len(output) > 3000:
            output = output[:3000] + "\n...（已截斷）"
        return output if output.strip() else f"✅ 指令執行成功（無輸出）"
    except subprocess.TimeoutExpired:
        return "❌ 指令執行超時（>30秒）"
    except Exception as e:
        return f"❌ 指令執行失敗: {e}"


def web_search(query: str) -> str:
    """搜尋網頁（使用 DuckDuckGo HTML）。"""
    try:
        url = "https://html.duckduckgo.com/html/?" + urllib.parse.urlencode({"q": query})
        req = urllib.request.Request(url, headers={"User-Agent": "AMPM-Obsidian/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        # 簡單擷取標題和摘要
        import re
        results = []
        for m in re.finditer(r'<a[^>]*class="result__a"[^>]*>(.*?)</a>', html):
            title = re.sub(r'<[^>]+>', '', m.group(1)).strip()
            results.append(title)
        if not results:
            # 嘗試其他方式
            snippets = re.findall(r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>', html)
            results = [re.sub(r'<[^>]+>', '', s).strip()[:200] for s in snippets]
        if results:
            return "搜尋結果：\n" + "\n".join(f"  {i+1}. {r}" for i, r in enumerate(results[:10]))
        return "未找到相關結果"
    except Exception as e:
        return f"❌ 搜尋失敗: {e}"


# 工具定義（傳給 LLM 的格式）
TOOL_DEFINITIONS = """
## 可用工具（⚠️ 你必須呼叫工具來實際操作，禁止只回文字說「已完成」）

1. write_file — 寫入檔案
   格式：{"tool": "write_file", "args": {"filepath": "路徑", "content": "完整內容"}}
   範例路徑：ebooks/chapter-03.md, children_book/research.md, website/index.html
   ⚠️ 產出的內容必須用 write_file 寫入檔案，路徑不要加 outputs/

2. read_file — 讀取檔案
   格式：{"tool": "read_file", "args": {"filepath": "路徑"}}

3. list_dir — 列出目錄
   格式：{"tool": "list_dir", "args": {"dirpath": "路徑"}}

4. run_command — 執行指令
   格式：{"tool": "run_command", "args": {"cmd": "指令"}}
   可用：mkdir, ls, cat, echo, python3, git, cp, mv 等。

5. web_search — 搜尋網頁
   格式：{"tool": "web_search", "args": {"query": "搜尋關鍵字"}}

6. generate_image — 產生圖像（插畫、封面、設計稿）
   格式：{"tool": "generate_image", "args": {"prompt": "詳細的圖片描述（英文效果更好）", "filepath": "images/my_design.png"}}

⚠️ 鐵則（違反視為任務失敗）：
- 必須先搜尋再寫內容（web_search → write_file）
- 寫檔案時 content 必須是完整內容，不能寫「此處省略」
- 每章獨立一個檔案，不要把所有章節塞進一個檔案
- 路徑範例：ebooks/ch03_xxx.md、children_book/research.md、website/index.html
- 路徑不要加 outputs/ 前綴
"""


def generate_image(prompt: str, filepath: str = "images/generated.png") -> str:
    """透過 HuggingFace 產生圖像"""
    hf_key = os.getenv("HUGGINGFACE_TOKEN")
    if not hf_key:
        return "❌ 需要 HUGGINGFACE_TOKEN"
    path = _resolve_path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    model = "stabilityai/stable-diffusion-3.5-large"
    try:
        req = urllib.request.Request(
            f"https://api-inference.huggingface.co/models/{model}",
            data=json.dumps({"inputs": prompt}).encode(),
            headers={"Authorization": f"Bearer {hf_key}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            path.write_bytes(resp.read())
        return f"✅ 圖片已產生: {filepath} ({path.stat().st_size // 1024}KB)"
    except Exception as e:
        return f"❌ 圖像生成失敗: {str(e)[:60]}"


def execute_tool(tool_name: str, args: dict) -> str:
    """執行指定的工具。"""
    tools_map = {
        "write_file": write_file,
        "read_file": read_file,
        "list_dir": list_dir,
        "run_command": run_command,
        "web_search": web_search,
        "generate_image": generate_image,
    }
    fn = tools_map.get(tool_name)
    if not fn:
        return f"❌ 未知工具: {tool_name}，可用工具: {', '.join(tools_map.keys())}"
    try:
        return fn(**args)
    except TypeError as e:
        return f"❌ 工具參數錯誤: {e}。正確參數請參考工具定義。"
    except Exception as e:
        return f"❌ 工具執行錯誤: {e}"
