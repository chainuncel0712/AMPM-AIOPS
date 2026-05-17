import os, time, threading, requests, json
from dotenv import load_dotenv
load_dotenv()

class TokenBucket:
    """Token Bucket 速率限制器"""
    def __init__(self, rate: int, per_seconds: int = 60):
        self.rate = rate
        self.per_seconds = per_seconds
        self.tokens = rate
        self.last_refill = time.time()
        self.lock = threading.Lock()

    def consume(self) -> bool:
        with self.lock:
            now = time.time()
            elapsed = now - self.last_refill
            self.tokens = min(self.rate, self.tokens + elapsed * self.rate / self.per_seconds)
            self.last_refill = now
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False

    def wait_time(self) -> float:
        with self.lock:
            if self.tokens >= 1:
                return 0
            return max(0, self.per_seconds / self.rate - (time.time() - self.last_refill))


class LLMClient:
    def __init__(self, breath_system=None):
        self.breath = breath_system
        self.providers = []
        self.rate_limiter = TokenBucket(rate=30, per_seconds=60)  # 每分鐘 30 次

        # 🥇 ATXP LLM Gateway（AI 經濟協議）
        atxp_conn = os.getenv("ATXP_CONNECTION_STRING")
        if atxp_conn:
            atxp_model = os.getenv("ATXP_MODEL", "gpt-4.1")
            self.providers.append({"name":"ATXP","key":atxp_conn,"ep":"https://llm.atxp.ai/v1/chat/completions","model":atxp_model})

        # 🥈 DeepSeek
        ds_key = os.getenv("DEEPSEEK_API_KEY")
        if ds_key:
            self.providers.append({"name":"DeepSeek","key":ds_key,"ep":"https://api.deepseek.com/v1/chat/completions","model":"deepseek-v4-pro"})

        # 🥈 OpenRouter
        or_key = os.getenv("OPENROUTER_API_KEY")
        if or_key:
            self.providers.append({"name":"OR-DeepSeek","key":or_key,"ep":"https://openrouter.ai/api/v1/chat/completions","model":"deepseek/deepseek-v4-pro"})
            self.providers.append({"name":"OR-Gemini","key":or_key,"ep":"https://openrouter.ai/api/v1/chat/completions","model":"google/gemini-2.0-flash-001"})

        # 🥉 NVIDIA
        nv = os.getenv("NVIDIA_API_KEY")
        if nv:
            self.providers.append({"name":"NV-Llama","key":nv,"ep":"https://integrate.api.nvidia.com/v1/chat/completions","model":"meta/llama-3.1-8b-instruct"})

        # 🏠 Ollama 本機
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ollama_ok = sock.connect_ex(('127.0.0.1', 11434)) == 0
        sock.close()
        if ollama_ok:
            ollama_model = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
            self.providers.append({"name":"Ollama","key":"ollama","ep":"http://localhost:11434/v1/chat/completions","model":ollama_model})

        print(f"🤖 {len(self.providers)}層: {' → '.join(p['name'] for p in self.providers)}")
        self.rate_limiter = TokenBucket(rate=int(os.getenv("MAX_API_CALLS_PER_MINUTE", "30")), per_seconds=60)

    def call(self, messages, temperature=0.7):
        # ===== Phase 8: runtime guard — 檢查是否經 ContextAssembler =====
        from runtime.context.persona_builder import RUNTIME_IDENTITY
        has_identity = any(
            isinstance(m, dict) and m.get("role") == "system" and RUNTIME_IDENTITY[:20] in m.get("content", "")
            for m in (messages if isinstance(messages, list) else [])
        )
        if not has_identity and isinstance(messages, list) and len(messages) > 0:
            print("⚠️ [Guard] LLM call bypasses ContextAssembler — 缺少 RUNTIME_IDENTITY")

        if self.breath and not self.breath.can_call_api():
            return "休息中..."
        if self.breath:
            self.breath.record_api_call()

        # 速率限制
        if not self.rate_limiter.consume():
            wait = self.rate_limiter.wait_time()
            if wait > 0:
                time.sleep(wait)

        safe = [m if isinstance(m, dict) else {"role": "user", "content": str(m)} for m in messages]
        if not safe:
            safe = [{"role": "user", "content": str(messages)}]

        for p in self.providers:
            try:
                r = requests.post(
                    p["ep"],
                    headers={"Authorization": f"Bearer {p['key']}", "Content-Type": "application/json"},
                    json={"model": p["model"], "messages": safe, "temperature": temperature, "max_tokens": 4000},
                    timeout=30
                )
                if r.status_code == 200:
                    try:
                        return r.json().get("choices", [{}])[0].get("message", {}).get("content", "")
                    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
                        return "⚠️ API 回應格式異常"
                if r.status_code == 429:
                    print(f"⚠️ {p['name']} 速率限制，等待...")
                    time.sleep(5)
                    continue
                print(f"⚠️ {p['name']} {r.status_code}")
            except Exception as e:
                print(f"⚠️ {p['name']}: {str(e)[:30]}")
        return "⚠️ 錯誤：所有模型不可用"
