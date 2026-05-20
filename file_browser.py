#!/usr/bin/env python3
"""
黑曜作品瀏覽器 — 讓 Hao 在自己電腦上看到黑曜的所有產出
啟動後瀏覽 http://VPS_IP:8888 即可查看 outputs/ 目錄
"""
import http.server
import os
from pathlib import Path
from urllib.parse import unquote

OUTPUTS_DIR = Path(__file__).parent / "outputs"

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>黑曜作品集</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Segoe UI', system-ui, sans-serif; background: #0a0a0a; color: #e0e0e0; min-height: 100vh; }
.header { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding: 24px; text-align: center; border-bottom: 2px solid #7c3aed; }
.header h1 { font-size: 1.5em; color: #a78bfa; }
.header .stats { color: #888; font-size: 0.9em; margin-top: 8px; }
.container { max-width: 800px; margin: 0 auto; padding: 16px; }
.breadcrumb { padding: 12px 0; font-size: 0.85em; color: #666; }
.breadcrumb a { color: #a78bfa; text-decoration: none; }
.breadcrumb a:hover { color: #c4b5fd; }
.file-list { list-style: none; }
.file-item { display: flex; align-items: center; padding: 10px 12px; margin: 2px 0; border-radius: 6px; transition: background 0.2s; }
.file-item:hover { background: rgba(124, 58, 237, 0.1); }
.file-item.dir { border-left: 3px solid #7c3aed; }
.file-item .icon { margin-right: 12px; font-size: 1.3em; }
.file-item .name { flex: 1; }
.file-item .name a { color: #e0e0e0; text-decoration: none; }
.file-item .name a:hover { color: #a78bfa; }
.file-item .size { color: #666; font-size: 0.85em; min-width: 80px; text-align: right; }
.file-item .preview { color: #666; font-size: 0.8em; margin-left: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 200px; }
.empty { text-align: center; padding: 40px; color: #555; }
.refresh { text-align: center; padding: 10px; }
.refresh a { color: #a78bfa; font-size: 0.85em; }
</style>
<script>
setTimeout(function(){location.reload();}, 60000);
</script>
</head>
<body>
<div class="header">
  <h1>黑曜作品集</h1>
  <div class="stats">{stats}</div>
</div>
<div class="container">
  <div class="breadcrumb">
    <a href="/">🏠 首頁</a> {breadcrumb}
  </div>
  <ul class="file-list">
{items}
  </ul>
  <div class="refresh">
    <a href=".">🔄 重新整理（每60秒自動更新）</a>
  </div>
</div>
</body>
</html>"""


class FileBrowser(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(OUTPUTS_DIR), **kwargs)

    def do_GET(self):
        path = unquote(self.path).split("?")[0]
        full_path = OUTPUTS_DIR / path.lstrip("/")

        if full_path.is_dir():
            self._serve_directory(full_path, path)
        elif full_path.is_file() and full_path.suffix in (".md", ".txt", ".html", ".css", ".js", ".py"):
            self._serve_file_with_viewer(full_path)
        elif full_path.is_file():
            super().do_GET()
        else:
            self.send_error(404)

    def _serve_directory(self, dir_path: Path, url_path: str):
        try:
            items = sorted(dir_path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
        except PermissionError:
            self.send_error(403)
            return

        # 統計
        file_count = sum(1 for i in items if i.is_file() and i.suffix != ".gitkeep")
        total_size = sum(i.stat().st_size for i in items if i.is_file() and i.suffix != ".gitkeep")
        stats = f"{file_count} 個檔案 · {self._format_size(total_size)}"

        # 麵包屑
        if url_path == "/" or url_path == "":
            breadcrumb = ""
        else:
            parts = url_path.strip("/").split("/")
            breadcrumb = ""
            cum = ""
            for p in parts:
                cum += f"/{p}"
                breadcrumb += f' / <a href="{cum}">{p}</a>'

        # 檔案列表
        rows = []
        for item in items:
            if item.name == ".gitkeep":
                continue
            rel = item.relative_to(OUTPUTS_DIR)
            url = f"/{rel}"

            if item.is_dir():
                rows.append(f'<li class="file-item dir">'
                           f'<span class="icon">📁</span>'
                           f'<span class="name"><a href="{url}">{item.name}/</a></span>'
                           f'</li>')
            else:
                size_str = self._format_size(item.stat().st_size)
                preview = ""
                if item.suffix in (".md", ".txt"):
                    try:
                        first_line = item.read_text(encoding="utf-8").split("\n")[0][:80]
                        preview = f'<span class="preview">{first_line}</span>'
                    except:
                        pass
                icon = {"md": "📝", "html": "🌐", "css": "🎨", "js": "⚡", "py": "🐍"}.get(item.suffix[1:], "📄")
                rows.append(f'<li class="file-item">'
                           f'<span class="icon">{icon}</span>'
                           f'<span class="name"><a href="{url}">{item.name}</a>{preview}</span>'
                           f'<span class="size">{size_str}</span>'
                           f'</li>')

        if not rows:
            rows.append('<li class="empty">📭 這個目錄還是空的，黑曜正在努力中...</li>')

        html = HTML_TEMPLATE.format(
            stats=stats,
            breadcrumb=breadcrumb,
            items="\n".join(rows)
        )
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def _serve_file_with_viewer(self, file_path: Path):
        try:
            content = file_path.read_text(encoding="utf-8")
        except:
            super().do_GET()
            return

        ext = file_path.suffix[1:]
        lang_map = {"md": "markdown", "html": "html", "css": "css", "js": "javascript", "py": "python"}
        lang = lang_map.get(ext, "plaintext")

        viewer_html = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{file_path.name} - 黑曜作品</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
<style>
body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: #0d1117; color: #c9d1d9; margin: 0; }}
.header {{ background: #161b22; padding: 12px 24px; border-bottom: 1px solid #30363d; display: flex; justify-content: space-between; align-items: center; }}
.header a {{ color: #a78bfa; text-decoration: none; }}
.content {{ max-width: 900px; margin: 24px auto; padding: 0 20px; overflow-x: auto; }}
.content pre {{ background: #161b22; padding: 16px; border-radius: 8px; overflow-x: auto; font-size: 0.9em; }}
.content h1, .content h2, .content h3 {{ color: #a78bfa; margin-top: 24px; }}
.content p {{ line-height: 1.7; margin: 12px 0; }}
.content code {{ background: #21262d; padding: 2px 6px; border-radius: 4px; font-size: 0.9em; }}
.content ul, .content ol {{ padding-left: 24px; }}
.content li {{ margin: 6px 0; }}
.content blockquote {{ border-left: 3px solid #7c3aed; padding-left: 12px; color: #8b949e; margin: 12px 0; }}
</style>
</head>
<body>
<div class="header">
  <a href="/">← 回作品集</a>
  <span>{file_path.name}（{len(content):,} 字）</span>
</div>
<div class="content">
{self._render_markdown(content) if ext == 'md' else f'<pre><code class="language-{lang}">{self._escape_html(content)}</code></pre>'}
</div>
<script>hljs.highlightAll();</script>
</body>
</html>"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(viewer_html.encode("utf-8"))

    def _render_markdown(self, text: str) -> str:
        """簡易 Markdown 轉 HTML"""
        lines = text.split("\n")
        result = []
        in_code = False
        code_lines = []
        code_lang = ""

        for line in lines:
            if line.startswith("```"):
                if in_code:
                    result.append(f'<pre><code class="language-{code_lang}">{"".join(code_lines)}</code></pre>')
                    code_lines = []
                    in_code = False
                else:
                    in_code = True
                    code_lang = line[3:].strip()
                continue

            if in_code:
                code_lines.append(self._escape_html(line) + "\n")
                continue

            if line.startswith("# "):
                result.append(f"<h1>{line[2:]}</h1>")
            elif line.startswith("## "):
                result.append(f"<h2>{line[3:]}</h2>")
            elif line.startswith("### "):
                result.append(f"<h3>{line[4:]}</h3>")
            elif line.startswith("- "):
                result.append(f"<li>{line[2:]}</li>")
            elif line.startswith("> "):
                result.append(f"<blockquote>{line[2:]}</blockquote>")
            elif line.strip() == "":
                result.append("<br>")
            else:
                result.append(f"<p>{self._escape_html(line)}</p>")

        if in_code:
            result.append(f'<pre><code class="language-{code_lang}">{"".join(code_lines)}</code></pre>')

        return "\n".join(result)

    def _escape_html(self, text: str) -> str:
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def _format_size(self, size: int) -> str:
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / 1024 / 1024:.1f} MB"


if __name__ == "__main__":
    import socketserver
    PORT = 8888
    print(f"📂 黑曜作品瀏覽器啟動於 http://0.0.0.0:{PORT}")
    print(f"   在你的電腦瀏覽器打開 http://<VPS_IP>:{PORT}")
    with socketserver.TCPServer(("0.0.0.0", PORT), FileBrowser) as httpd:
        httpd.serve_forever()
