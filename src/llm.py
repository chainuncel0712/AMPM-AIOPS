import os, time, threading, requests, json, base64
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
    def __init__(self, breath_system=None, thalamus=None):
        self.breath = breath_system
        self.thalamus = thalamus
        self.providers = []
        self.rate_limiter = TokenBucket(rate=30, per_seconds=60)  # 每分鐘 30 次
        self._last_user_msg = ""  # 供 router 分類用

        # 🥇 OpenRouter 免費模型（優先，不燒錢）
        or_key = os.getenv("OPENROUTER_API_KEY")
        if or_key:
            self.providers.append({"name":"OR-Free","key":or_key,"ep":"https://openrouter.ai/api/v1/chat/completions","model":"deepseek/deepseek-v4-flash:free"})
            self.providers.append({"name":"OR-Llama","key":or_key,"ep":"https://openrouter.ai/api/v1/chat/completions","model":"meta-llama/llama-3.3-70b-instruct:free"})

        # 🥈 DeepSeek 直連（備援）
        ds_key = os.getenv("DEEPSEEK_API_KEY")
        if ds_key:
            self.providers.append({"name":"DeepSeek","key":ds_key,"ep":"https://api.deepseek.com/v1/chat/completions","model":"deepseek-v4-pro"})

        # 🥉 Ollama 本機（免費備援）
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ollama_ok = sock.connect_ex(('127.0.0.1', 11434)) == 0
        sock.close()
        if ollama_ok:
            ollama_model = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
            self.providers.append({"name":"Ollama","key":"ollama","ep":"http://localhost:11434/v1/chat/completions","model":ollama_model})

        # 🤗 HuggingFace（已移除 — DNS 無法解析且模型不支援）

        print(f"🤖 {len(self.providers)}層: {' → '.join(p['name'] for p in self.providers)}")
        self.rate_limiter = TokenBucket(rate=int(os.getenv("MAX_API_CALLS_PER_MINUTE", "30")), per_seconds=60)
        default_model = os.getenv("DEFAULT_MODEL", "DeepSeek")
        self.preferred_model = None if default_model.lower() == "auto" else default_model
        if self.preferred_model:
            print(f"🎯 預設模型: {self.preferred_model}")

    def list_models(self) -> list:
        """列出所有可用模型"""
        return [{"name": p["name"], "model": p["model"]} for p in self.providers]

    def switch_model(self, name: str) -> str:
        """切換到指定模型

        Args:
            name: 模型名稱 (大小寫不敏感)，'auto' 恢復自動 fallback
        Returns:
            目前使用的模型名稱
        """
        if name.lower() == "auto":
            self.preferred_model = None
            return "自動 fallback"

        for p in self.providers:
            if name.lower() in p["name"].lower():
                self.preferred_model = p["name"]
                return f"{p['name']} ({p['model']})"

        return f"找不到 {name}，可用: {', '.join(p['name'] for p in self.providers)}"

    def register_model(self, name: str, key: str, endpoint: str, model: str) -> str:
        """動態註冊新模型 — 黑曜可以自己擴充能力"""
        for p in self.providers:
            if p["name"].lower() == name.lower():
                p["model"] = model
                p["key"] = key
                return f"已更新 {name} ({model})"
        self.providers.append({
            "name": name, "key": key, "ep": endpoint, "model": model
        })
        print(f"📡 動態註冊模型: {name} ({model})")
        return f"已註冊 {name} ({model})"

    def discover_models(self, limit: int = 10) -> list:
        """從 OpenRouter 探索可用模型 — 黑曜自主擴充能力"""
        or_key = os.getenv("OPENROUTER_API_KEY")
        if not or_key:
            return []
        try:
            r = requests.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {or_key}"},
                timeout=10
            )
            if r.status_code == 200:
                data = r.json()
                items = data if isinstance(data, list) else data.get("data", [])
                models = []
                for m in items[:limit * 3]:
                    model_id = m.get("id", "")
                    name = m.get("name", model_id)
                    if any(kw in model_id.lower() for kw in ["free", "flash", "nano", "mini", "8b", "7b", "1b"]):
                        models.append({
                            "id": model_id,
                            "name": name,
                            "context_length": m.get("context_length", 0),
                            "pricing": m.get("pricing", {}),
                        })
                        if len(models) >= limit:
                            break
                return models
        except Exception as e:
            print(f"⚠️ 探索模型失敗: {e}")
        return []

    def add_openrouter_model(self, model_id: str, label: str = None) -> str:
        """從 OpenRouter 動態加入一個模型"""
        or_key = os.getenv("OPENROUTER_API_KEY")
        if not or_key:
            return "需要 OPENROUTER_API_KEY"
        name = label or model_id.split("/")[-1][:20]
        return self.register_model(
            name=f"OR-{name}",
            key=or_key,
            endpoint="https://openrouter.ai/api/v1/chat/completions",
            model=model_id,
        )

    def current_model(self) -> str:
        """取得目前模型"""
        if self.preferred_model:
            return self.preferred_model
        return "auto (fallback: " + " → ".join(p["name"] for p in self.providers) + ")"
        self.preferred_model = None  # None = 自動 fallback，設值後優先使用指定模型

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

        # 若有用戶指定模型，優先嘗試
        ordered_providers = list(self.providers)
        if self.preferred_model:
            pref = next((p for p in ordered_providers if p["name"] == self.preferred_model), None)
            if pref:
                ordered_providers.remove(pref)
                ordered_providers.insert(0, pref)

        for p in ordered_providers:
            try:
                r = requests.post(
                    p["ep"],
                    headers={"Authorization": f"Bearer {p['key']}", "Content-Type": "application/json"},
                    json={"model": p["model"], "messages": safe, "temperature": temperature, "max_tokens": 4000},
                    timeout=15
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

    def call_smart(self, user_msg: str, messages, temperature=0.7) -> str:
        """智慧路由呼叫：分類訊息 → 挑最佳模型 → 一條直通（最多 1 次 fallback）"""
        if not self.breath or self.breath.can_call_api():
            if self.breath:
                self.breath.record_api_call()
        else:
            return "休息中..."

        if not self.rate_limiter.consume():
            wait = self.rate_limiter.wait_time()
            if wait > 0:
                time.sleep(wait)

        safe = [m if isinstance(m, dict) else {"role": "user", "content": str(m)} for m in messages]
        if not safe:
            safe = [{"role": "user", "content": str(messages)}]

        # 速率保護
        if self.thalamus:
            if not self.thalamus.acquire(timeout=5.0):
                print("⚠️ [Router] 無法取得 LLM 呼叫權（被自治任務佔用），等待中...")
                self.thalamus.acquire(timeout=15.0)

        try:
            if self.thalamus:
                route = self.thalamus.route(user_msg, self.providers)
                primary = route["provider"]
                category = route["category"]
                print(f"🧠 [Router] 「{user_msg[:30]}」→ {category} → {primary['name'] if primary else '?'}")

                if primary:
                    # 只試主模型 + 一個備援，不盲目 fallback
                    fallback = next((p for p in self.providers if p != primary), None)
                    for p in [primary, fallback]:
                        if p is None:
                            continue
                        try:
                            r = requests.post(
                                p["ep"],
                                headers={"Authorization": f"Bearer {p['key']}", "Content-Type": "application/json"},
                                json={"model": p["model"], "messages": safe, "temperature": temperature, "max_tokens": 4000},
                                timeout=25
                            )
                            if r.status_code == 200:
                                try:
                                    return r.json().get("choices", [{}])[0].get("message", {}).get("content", "")
                                except (KeyError, IndexError, TypeError, json.JSONDecodeError):
                                    continue
                            if r.status_code == 429:
                                print(f"⚠️ {p['name']} 速率限制，換備援")
                                time.sleep(1)
                                continue
                            print(f"⚠️ {p['name']} {r.status_code}，換備援")
                        except Exception as e:
                            print(f"⚠️ {p['name']}: {str(e)[:30]}，換備援")
                            continue
        finally:
            if self.thalamus:
                self.thalamus.release()

        # 路由失敗 → 降級到舊的盲目 fallback
        print("⚠️ [Router] 智慧路由失敗，降級到完整 fallback")
        return self.call(messages, temperature)

    def call_local(self, messages, temperature=0.3):
        """只在 Ollama 本地模型上呼叫（免費，給子代理用）"""
        ollama = next((p for p in self.providers if p["name"] == "Ollama"), None)
        if not ollama:
            return "⚠️ Ollama 不可用（嘗試子代理任務）"

        if self.breath and not self.breath.can_call_api():
            return "休息中..."
        if self.breath:
            self.breath.record_api_call()

        safe = [m if isinstance(m, dict) else {"role": "user", "content": str(m)} for m in messages]
        if not safe:
            safe = [{"role": "user", "content": str(messages)}]

        try:
            r = requests.post(
                ollama["ep"],
                headers={"Authorization": f"Bearer {ollama['key']}", "Content-Type": "application/json"},
                json={"model": ollama["model"], "messages": safe, "temperature": temperature, "max_tokens": 4000},
                timeout=60
            )
            if r.status_code == 200:
                try:
                    return r.json().get("choices", [{}])[0].get("message", {}).get("content", "")
                except (KeyError, IndexError, TypeError, json.JSONDecodeError):
                    return "⚠️ Ollama 回應格式異常"
            return f"⚠️ Ollama {r.status_code}"
        except Exception as e:
            return f"⚠️ Ollama 錯誤: {str(e)[:30]}"

    def call_vision(self, prompt: str, image_url: str = None, image_path: str = None) -> str:
        """視覺理解 — 傳圖片給模型分析

        Args:
            prompt: 文字提示
            image_url: 圖片網址
            image_path: 本地圖片路徑（會轉 base64）

        Returns:
            模型分析結果
        """
        # 準備圖片內容
        if image_path:
            try:
                with open(image_path, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()
                ext = image_path.rsplit(".", 1)[-1].lower()
                mime = f"image/{ext}" if ext in ("png","jpg","jpeg","gif","webp") else "image/png"
                image_content = {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}
            except Exception:
                return "⚠️ 無法讀取圖片"
        elif image_url:
            image_content = {"type": "image_url", "image_url": {"url": image_url}}
        else:
            return "⚠️ 請提供圖片網址或路徑"

        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                image_content,
            ]
        }]

        # 用 Gemini 處理視覺（透過 OpenRouter）
        vision_providers = [p for p in self.providers if "gemini" in p["name"].lower() or "4o" in p.get("model", "").lower()]
        if not vision_providers:
            return "⚠️ 沒有視覺模型可用（需 Gemini 或 GPT-4o）"

        for p in vision_providers:
            try:
                r = requests.post(
                    p["ep"],
                    headers={"Authorization": f"Bearer {p['key']}", "Content-Type": "application/json"},
                    json={"model": p["model"], "messages": messages, "max_tokens": 2000},
                    timeout=60
                )
                if r.status_code == 200:
                    return r.json().get("choices", [{}])[0].get("message", {}).get("content", "⚠️ 無回應")
                print(f"⚠️ vision {p['name']} {r.status_code}")
            except Exception as e:
                print(f"⚠️ vision {p['name']}: {str(e)[:30]}")
        return "⚠️ 所有視覺模型不可用"

    def call_image_gen(self, prompt: str, output_path: str = None) -> str:
        """圖像生成 — 透過 HuggingFace Inference API 產生圖片

        Args:
            prompt: 文字提示詞
            output_path: 儲存路徑（可選，預設 outputs/images/）

        Returns:
            結果描述或錯誤訊息
        """
        hf_key = os.getenv("HUGGINGFACE_TOKEN")
        if not hf_key:
            return "⚠️ 需要 HUGGINGFACE_TOKEN"

        if not output_path:
            ts = int(time.time())
            output_path = f"outputs/images/gen_{ts}.png"

        full_path = Path(output_path)
        if not full_path.is_absolute():
            full_path = Path(__file__).parent.parent / output_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # 用 Stable Diffusion 3.5 (免費 HF Inference API)
        model = "stabilityai/stable-diffusion-3.5-large"
        try:
            r = requests.post(
                f"https://api-inference.huggingface.co/models/{model}",
                headers={"Authorization": f"Bearer {hf_key}"},
                json={"inputs": prompt},
                timeout=120
            )
            if r.status_code == 200:
                full_path.write_bytes(r.content)
                size_kb = len(r.content) // 1024
                return f"✅ 圖片已產生: {full_path.relative_to(Path(__file__).parent.parent)} ({size_kb}KB)"
            if r.status_code == 503:
                return f"⚠️ HF 模型載入中，請稍後再試 ({r.json().get('error','')[:80]})"
            return f"⚠️ HF {r.status_code}"
        except Exception as e:
            return f"⚠️ 圖像生成失敗: {str(e)[:60]}"
