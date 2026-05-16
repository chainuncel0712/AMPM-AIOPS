"""
API Wrapper Generator v1 — 動態 REST API 包裝器
自動探測端點 → 生成工具定義 → 註冊到工具系統
"""
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

sys.path.insert(0, str(Path(__file__).parent.parent))
from skeleton.base_organ import BaseOrgan


class APIWrapper(BaseOrgan):
    """動態 API 包裝器 — 探測、包裝、快取 REST API 端點"""

    def __init__(self, tool_registry=None, auto_builder=None):
        super().__init__("api_wrapper")
        self._registry = tool_registry
        self._builder = auto_builder
        self._wrapped_apis: Dict[str, Dict] = {}
        self._response_cache: Dict[str, Dict] = {}
        self._cache_ttl = 300  # 5 分鐘

    # ── API 註冊 ───────────────────────────────────────────

    def wrap(self, name: str, base_url: str, endpoints: List[Dict]) -> Dict:
        """手動包裝一組 API 端點
        endpoints: [
            {"path": "/users", "method": "GET", "description": "列出使用者"},
            {"path": "/users/{id}", "method": "GET", "description": "取得使用者"},
        ]
        """
        tools = []
        for ep in endpoints:
            tool_def = self._build_single_tool(name, base_url, ep)
            tools.append(tool_def)

            if self._registry and self._builder:
                self._registry.learn_tool(
                    name=tool_def["name"],
                    description=tool_def["description"],
                    category="api_wrapper",
                    code=tool_def["config"],
                )

        api_def = {
            "name": name,
            "base_url": base_url,
            "endpoints": endpoints,
            "tools": [t["name"] for t in tools],
            "wrapped_at": time.time(),
        }
        self._wrapped_apis[name] = api_def
        return api_def

    def wrap_from_openapi(self, name: str, spec_url: str) -> Optional[Dict]:
        """從 OpenAPI spec URL 動態包裝"""
        try:
            import urllib.request

            with urllib.request.urlopen(spec_url, timeout=10) as resp:
                spec = json.loads(resp.read().decode())

            if self._builder:
                base_url = spec.get("servers", [{}])[0].get("url", "")
                tools = self._builder.from_openapi(spec, base_url)

                for tool in tools:
                    if self._registry:
                        self._registry.learn_tool(
                            name=tool["name"],
                            description=tool["description"],
                            category=name,
                            code=tool["config"],
                        )

                api_def = {
                    "name": name,
                    "spec_url": spec_url,
                    "base_url": base_url,
                    "tools": [t["name"] for t in tools],
                    "wrapped_at": time.time(),
                }
                self._wrapped_apis[name] = api_def
                return api_def
        except Exception as e:
            return {"error": str(e)}
        return None

    def _build_single_tool(self, api_name: str, base_url: str, endpoint: Dict) -> Dict:
        path = endpoint["path"]
        method = endpoint.get("method", "GET").upper()
        safe_name = re.sub(r"[^a-zA-Z0-9_]", "_", f"{api_name}_{method.lower()}_{path.strip('/')}")

        return {
            "name": safe_name,
            "description": endpoint.get("description", f"{method} {base_url}{path}"),
            "type": "rest",
            "config": {
                "method": method,
                "path": path,
                "base_url": base_url,
                "headers": endpoint.get("headers", {"Content-Type": "application/json"}),
                "params_schema": endpoint.get("params", {}),
            },
        }

    # ── 動態呼叫 ───────────────────────────────────────────

    def call(self, api_name: str, endpoint: str, method: str = "GET", params: Dict = None, use_cache: bool = True) -> Dict:
        """直接呼叫已包裝的 API 端點"""
        api_def = self._wrapped_apis.get(api_name)
        if not api_def:
            return {"error": f"API '{api_name}' 未註冊"}

        base = api_def["base_url"]
        url = urljoin(base, endpoint)

        if use_cache and method == "GET":
            cache_key = f"{method}:{url}:{json.dumps(params or {})}"
            cached = self._response_cache.get(cache_key)
            if cached and time.time() - cached["ts"] < self._cache_ttl:
                return cached["data"]

        try:
            import urllib.request

            if params and method == "GET":
                from urllib.parse import urlencode
                url += "?" + urlencode(params)

            req = urllib.request.Request(url, method=method)
            req.add_header("Content-Type", "application/json")
            if params and method != "GET":
                req.data = json.dumps(params).encode()

            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())

            result = {"status": resp.status, "data": data, "success": True}

            if method == "GET":
                self._response_cache[cache_key] = {"ts": time.time(), "data": result}

            return result
        except Exception as e:
            return {"error": str(e), "success": False}

    # ── 端點探索 ───────────────────────────────────────────

    def probe(self, base_url: str, common_endpoints: List[str] = None) -> List[str]:
        """探測 API 常見端點是否存在"""
        common = common_endpoints or [
            "/health", "/api/health", "/status",
            "/api/v1/users", "/api/v1/status",
            "/metrics", "/api/docs",
        ]
        found = []
        for ep in common:
            url = urljoin(base_url, ep)
            try:
                import urllib.request
                req = urllib.request.Request(url, method="HEAD")
                with urllib.request.urlopen(req, timeout=5) as resp:
                    if resp.status < 500:
                        found.append(ep)
            except Exception:
                pass
        return found

    def status(self) -> Dict:
        return {
            "name": self.name,
            "alive": self.is_alive(),
            "wrapped_apis": len(self._wrapped_apis),
            "total_endpoints": sum(len(api["endpoints"]) for api in self._wrapped_apis.values()),
            "cached_responses": len(self._response_cache),
        }
