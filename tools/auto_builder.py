"""
Auto Tool Builder v1 — 從 API spec 自動生成工具包裝器
支援: OpenAPI/Swagger spec, 手動 JSON schema, 動態 REST 端點
"""
import json
import os
import re
import textwrap
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


class AutoBuilder:
    """從 API 規格自動生成工具定義與執行器"""

    def __init__(self, tool_registry=None):
        self._registry = tool_registry
        self._built_tools: Dict[str, Dict] = {}

    # ── OpenAPI/Swagger 解析 ──────────────────────────────

    def from_openapi(self, spec: Dict, base_url: str = "") -> List[Dict]:
        """從 OpenAPI 3.x spec 生成工具清單"""
        tools = []
        paths = spec.get("paths", {})
        for path, methods in paths.items():
            for method, detail in methods.items():
                if method not in ("get", "post", "put", "delete", "patch"):
                    continue
                tool = self._build_rest_tool(
                    path=path,
                    method=method.upper(),
                    detail=detail,
                    base_url=base_url,
                )
                tools.append(tool)
        self._built_tools["openapi"] = tools
        return tools

    def _build_rest_tool(
        self, path: str, method: str, detail: Dict, base_url: str
    ) -> Dict:
        operation_id = detail.get("operationId", f"{method.lower()}_{re.sub(r'[^a-zA-Z0-9]', '_', path)}")
        summary = detail.get("summary", detail.get("description", ""))
        params_schema = self._extract_params_schema(detail)

        tool_def = {
            "name": operation_id,
            "description": summary or f"{method} {path}",
            "type": "rest",
            "config": {
                "method": method,
                "path": path,
                "base_url": base_url,
                "params_schema": params_schema,
                "headers": {"Content-Type": "application/json"},
            },
            "executor": self._make_rest_executor(base_url, path, method, params_schema),
        }
        return tool_def

    def _extract_params_schema(self, detail: Dict) -> Dict:
        params = {}
        for p in detail.get("parameters", []):
            name = p.get("name", "")
            params[name] = {
                "type": p.get("schema", {}).get("type", "string"),
                "required": p.get("required", False),
                "in": p.get("in", "query"),
                "description": p.get("description", ""),
            }
        if "requestBody" in detail:
            content = detail["requestBody"].get("content", {})
            json_content = content.get("application/json", {})
            schema = json_content.get("schema", {})
            if schema:
                params["_body"] = {"type": "object", "required": True, "in": "body", "schema": schema}
        return params

    # ── 手動 JSON schema 工具生成 ──────────────────────────

    def from_schema(self, tool_schemas: List[Dict]) -> List[Dict]:
        """從手動 schema 定義生成工具
        schema 格式:
        {
            "name": "tool_name",
            "description": "...",
            "type": "rest" | "bash" | "python",
            "config": { ... },
        }
        """
        tools = []
        for schema in tool_schemas:
            tool_def = {
                "name": schema["name"],
                "description": schema.get("description", ""),
                "type": schema.get("type", "custom"),
                "config": schema.get("config", {}),
            }
            if schema["type"] == "rest":
                tool_def["executor"] = self._make_rest_executor(
                    schema["config"].get("base_url", ""),
                    schema["config"].get("path", ""),
                    schema["config"].get("method", "GET"),
                    schema["config"].get("params_schema", {}),
                )
            elif schema["type"] == "bash":
                tool_def["executor"] = self._make_bash_executor(
                    schema["config"].get("template", ""),
                    schema["config"].get("params", {}),
                )
            tools.append(tool_def)
        self._built_tools["schema"] = tools
        return tools

    # ── 執行器工廠 ─────────────────────────────────────────

    def _make_rest_executor(self, base_url: str, path: str, method: str, params: Dict) -> Callable:
        def executor(**kwargs) -> Dict:
            import http.client
            import urllib.parse

            url = base_url.rstrip("/") + "/" + path.lstrip("/")
            parsed = urllib.parse.urlparse(url)
            conn = http.client.HTTPSConnection(parsed.netloc, timeout=30) if parsed.scheme == "https" else http.client.HTTPConnection(parsed.netloc, timeout=30)

            query_params = {}
            for k, v in kwargs.items():
                p = params.get(k, {})
                if p.get("in") == "query" or (not p and method == "GET"):
                    query_params[k] = v

            full_path = parsed.path
            if query_params:
                full_path += "?" + urllib.parse.urlencode(query_params)

            body = None
            if method in ("POST", "PUT", "PATCH"):
                body_data = {k: v for k, v in kwargs.items() if k not in query_params}
                if body_data:
                    body = json.dumps(body_data)

            conn.request(method, full_path, body=body, headers={"Content-Type": "application/json"})
            resp = conn.getresponse()
            data = resp.read().decode("utf-8")
            conn.close()

            try:
                return {"status": resp.status, "data": json.loads(data)}
            except json.JSONDecodeError:
                return {"status": resp.status, "data": data}

        return executor

    def _make_bash_executor(self, template: str, params: Dict) -> Callable:
        def executor(**kwargs) -> Dict:
            import subprocess

            cmd = template.format(**kwargs)
            try:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                return {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode,
                }
            except subprocess.TimeoutExpired:
                return {"error": "timeout", "stdout": "", "stderr": ""}
            except Exception as e:
                return {"error": str(e), "stdout": "", "stderr": ""}

        return executor

    # ── 工具註冊 ───────────────────────────────────────────

    def register_all(self) -> int:
        """將所有已建工具註冊到 tool_registry"""
        count = 0
        for category, tools in self._built_tools.items():
            for tool in tools:
                if self._registry:
                    self._registry.learn_tool(
                        name=tool["name"],
                        description=tool["description"],
                        category=category,
                        code=tool.get("config", {}),
                    )
                count += 1
        return count

    def get_built_tools(self) -> Dict[str, List[Dict]]:
        return self._built_tools


# ── CLI helper for quick tool generation ──────────────────

def generate_tool_from_curl(curl_command: str) -> Dict:
    """從 curl 命令快速生成工具定義"""
    import shlex

    parts = shlex.split(curl_command)
    method = "GET"
    url = ""
    headers = {}
    data = None

    i = 0
    while i < len(parts):
        p = parts[i]
        if p == "curl":
            i += 1
            continue
        elif p == "-X" or p == "--request":
            i += 1
            method = parts[i].upper()
        elif p.startswith("http"):
            url = p
        elif p == "-H" or p == "--header":
            i += 1
            h = parts[i].split(":", 1)
            headers[h[0].strip()] = h[1].strip()
        elif p == "-d" or p == "--data":
            i += 1
            data = parts[i]
        elif p == "-u" or p == "--user":
            i += 1
            headers["Authorization"] = "Basic " + parts[i]
        i += 1

    from urllib.parse import urlparse

    parsed = urlparse(url) if url else None
    tool_name = re.sub(r"[^a-zA-Z0-9_]", "_", parsed.path.strip("/") if parsed else "custom")

    return {
        "name": tool_name,
        "description": f"{method} {parsed.path if parsed else url}",
        "type": "rest",
        "config": {
            "method": method,
            "path": parsed.path if parsed else "",
            "base_url": f"{parsed.scheme}://{parsed.netloc}" if parsed else "",
            "headers": headers,
            "params_schema": {},
        },
    }
