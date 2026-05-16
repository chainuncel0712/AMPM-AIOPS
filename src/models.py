#!/usr/bin/env python3
"""
模型切換系統 - 黑曜和子代理可以動態切換 AI 模型

功能：
1. 多模型支援（NVIDIA NIM、OpenAI、本地模型等）
2. 動態切換 - 根據任務類型選擇最佳模型
3. 子代理獨立模型 - 每個子代理可用不同模型
4. 成本控制 - 簡單任務用便宜模型，複雜任務用強大模型
5. 自動降級 - 模型失敗時自動切換備用
"""

import json
import requests
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

class ModelRegistry:
    """模型註冊表 - 管理所有可用模型"""
    
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.registry_file = self.base_dir / "data" / "models" / "registry.json"
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.models = self._load()
        self.current_model = None
        self.model_stats = {}  # 記錄每個模型的使用情況
    
    def _load(self) -> Dict:
        if self.registry_file.exists():
            try:
                return json.loads(self.registry_file.read_text())
            except:
                return {}
        return {}
    
    def _save(self):
        self.registry_file.write_text(json.dumps(self.models, ensure_ascii=False, indent=2))
    
    def register(self, model_id: str, name: str, endpoint: str, api_key: str = None, 
                 max_tokens: int = 1500, cost_per_call: float = 0.001, 
                 strengths: List[str] = None, is_free: bool = False):
        """註冊新模型"""
        self.models[model_id] = {
            "name": name,
            "endpoint": endpoint,
            "api_key": api_key,
            "max_tokens": max_tokens,
            "cost_per_call": cost_per_call,
            "strengths": strengths or ["general"],
            "is_free": is_free,
            "registered_at": datetime.now().isoformat(),
            "last_used": None,
            "success_count": 0,
            "fail_count": 0
        }
        self._save()
        print(f"✅ 模型已註冊: {name} ({model_id})")
        return True
    
    def register_nvidia_models(self, nvidia_key: str):
        """註冊所有可用的 NVIDIA NIM 模型"""
        nvidia_endpoint = "https://integrate.api.nvidia.com/v1/chat/completions"
        
        models = [
            ("llama3-70b", "meta/llama-3.1-70b-instruct", 1500, 0.001, 
             ["general", "reasoning", "complex"], False),
            ("llama3-8b", "meta/llama-3.1-8b-instruct", 2000, 0.0001,
             ["fast", "simple", "cheap"], False),
            ("mixtral", "mistralai/mixtral-8x7b-instruct-v0.1", 2000, 0.0005,
             ["coding", "analysis"], False),
            ("gemma", "google/gemma-2b-it", 1000, 0.00005,
             ["fast", "tiny"], True),
            ("code-llama", "meta/codellama-70b", 2000, 0.001,
             ["coding", "debug"], False),
        ]
        
        for model_id, model_name, max_tokens, cost, strengths, is_free in models:
            self.register(
                model_id=model_id,
                name=model_name,
                endpoint=nvidia_endpoint,
                api_key=nvidia_key,
                max_tokens=max_tokens,
                cost_per_call=cost,
                strengths=strengths,
                is_free=is_free
            )
        
        print(f"📦 已註冊 {len(models)} 個 NVIDIA 模型")
    
    def get_model(self, model_id: str) -> Dict:
        """取得模型資訊"""
        return self.models.get(model_id)
    
    def list_models(self) -> Dict:
        """列出所有模型"""
        return {mid: {"name": m["name"], "strengths": m["strengths"], "free": m.get("is_free", False)} 
                for mid, m in self.models.items()}
    
    def select_best_model(self, task_type: str, require_free: bool = False) -> str:
        """根據任務類型選擇最佳模型"""
        best = None
        best_score = -1
        
        for mid, m in self.models.items():
            # 如果需要免費模型
            if require_free and not m.get("is_free", False):
                continue
            
            # 計算匹配分數
            score = 0
            if task_type in m["strengths"]:
                score += 10
            if "general" in m["strengths"]:
                score += 2
            if not m.get("is_free", False):
                score -= 1  # 付費模型稍微扣分
            
            if score > best_score:
                best_score = score
                best = mid
        
        return best or list(self.models.keys())[0]
    
    def update_stats(self, model_id: str, success: bool):
        """更新模型使用統計"""
        if model_id in self.models:
            if success:
                self.models[model_id]["success_count"] += 1
            else:
                self.models[model_id]["fail_count"] += 1
            self.models[model_id]["last_used"] = datetime.now().isoformat()
            self._save()


class ModelSwitcher:
    """模型切換器 - 給黑曜和子代理使用"""
    
    def __init__(self, base_dir: Path, default_model: str = None):
        self.registry = ModelRegistry(base_dir)
        self.base_dir = base_dir
        self.default_model = default_model or "llama3-70b"
        
        # 每個代理的當前模型
        self.agent_models = {}  # {agent_id: model_id}
        
        # 任務類型到模型的映射（可學習）
        self.task_model_map = self._load_task_map()
    
    def _load_task_map(self) -> Dict:
        map_file = self.base_dir / "data" / "models" / "task_map.json"
        if map_file.exists():
            return json.loads(map_file.read_text())
        return {
            "chat": "llama3-70b",
            "fast_reply": "llama3-8b",
            "coding": "code-llama",
            "analysis": "mixtral",
            "simple": "gemma"
        }
    
    def _save_task_map(self):
        map_file = self.base_dir / "data" / "models" / "task_map.json"
        map_file.parent.mkdir(parents=True, exist_ok=True)
        map_file.write_text(json.dumps(self.task_model_map, ensure_ascii=False, indent=2))
    
    def set_agent_model(self, agent_id: str, model_id: str) -> str:
        """設定某個代理使用的模型"""
        if model_id not in self.registry.models:
            available = list(self.registry.models.keys())
            return f"❌ 模型不存在。可用: {available}"
        
        self.agent_models[agent_id] = model_id
        return f"✅ 代理 {agent_id} 已切換到模型: {model_id}"
    
    def get_agent_model(self, agent_id: str) -> str:
        """取得代理當前使用的模型"""
        return self.agent_models.get(agent_id, self.default_model)
    
    def switch_for_task(self, task_type: str, agent_id: str = None) -> str:
        """根據任務類型切換模型"""
        # 選擇最佳模型
        model_id = self.task_model_map.get(task_type)
        if not model_id:
            model_id = self.registry.select_best_model(task_type)
        
        if agent_id:
            self.set_agent_model(agent_id, model_id)
        
        return model_id
    
    def learn_task_mapping(self, task_type: str, model_id: str, reason: str = ""):
        """學習新的任務-模型映射（黑曜自己可以學習）"""
        self.task_model_map[task_type] = model_id
        self._save_task_map()
        return f"✅ 已學習：{task_type} → {model_id}（{reason}）"
    
    def call_model(self, model_id: str, messages: List[Dict], temperature: float = 0.7) -> tuple:
        """呼叫指定模型"""
        model = self.registry.get_model(model_id)
        if not model:
            return None, f"❌ 模型不存在: {model_id}"
        
        headers = {"Content-Type": "application/json"}
        if model.get("api_key"):
            headers["Authorization"] = f"Bearer {model['api_key']}"
        
        payload = {
            "model": model["name"],
            "messages": messages,
            "max_tokens": model.get("max_tokens", 1500),
            "temperature": temperature
        }
        
        try:
            resp = requests.post(model["endpoint"], json=payload, headers=headers, timeout=60)
            if resp.status_code == 200:
                result = resp.json()["choices"][0]["message"]["content"]
                self.registry.update_stats(model_id, True)
                return result, None
            else:
                self.registry.update_stats(model_id, False)
                return None, f"API錯誤: {resp.status_code}"
        except Exception as e:
            self.registry.update_stats(model_id, False)
            return None, str(e)
    
    def call_with_fallback(self, messages: List[Dict], preferred_model: str = None, 
                           temperature: float = 0.7) -> str:
        """呼叫模型，失敗時自動切換備用"""
        # 優先使用指定模型或默認模型
        models_to_try = [preferred_model] if preferred_model else []
        models_to_try.extend(["llama3-70b", "llama3-8b", "mixtral", "gemma"])
        
        for model_id in models_to_try:
            if model_id not in self.registry.models:
                continue
            
            result, error = self.call_model(model_id, messages, temperature)
            if result:
                return result
            
            print(f"⚠️ 模型 {model_id} 失敗: {error}，切換到下一個")
            time.sleep(0.1)
        
        return "❌ 所有模型都失敗了"
    
    def get_models_status(self) -> str:
        """取得所有模型狀態"""
        lines = ["📊 模型狀態："]
        for mid, m in self.registry.models.items():
            status = f"  - {m['name']}: 成功{m['success_count']}次/失敗{m['fail_count']}次"
            if mid == self.default_model:
                status += " ⭐默認"
            lines.append(status)
        return "\n".join(lines)


# ============================================================
# 整合到黑曜的擴充功能
# ============================================================

class ModelCapability:
    """給黑曜的模型能力擴充"""
    
    def __init__(self, base_dir: Path):
        self.switcher = ModelSwitcher(base_dir)
        
        # 註冊 NVIDIA 模型
        nvidia_key = "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"
        self.switcher.registry.register_nvidia_models(nvidia_key)
    
    def get_models_list(self) -> str:
        """取得模型清單（給黑曜顯示）"""
        models = self.switcher.registry.list_models()
        lines = ["🔧 可用模型："]
        for mid, info in models.items():
            lines.append(f"  • {mid}: {info['name'][:30]} - {', '.join(info['strengths'])}")
        return "\n".join(lines)
    
    def switch_model(self, agent_id: str, model_id: str) -> str:
        """切換代理的模型"""
        return self.switcher.set_agent_model(agent_id, model_id)
    
    def auto_switch(self, task_description: str) -> str:
        """根據任務描述自動切換"""
        # 簡單的任務類型判斷
        task_lower = task_description.lower()
        
        if any(kw in task_lower for kw in ["程式", "code", "寫", "除錯", "debug"]):
            model = self.switcher.switch_for_task("coding")
        elif any(kw in task_lower for kw in ["分析", "分析", "思考", "複雜"]):
            model = self.switcher.switch_for_task("analysis")
        elif any(kw in task_lower for kw in ["快", "簡單", "快速"]):
            model = self.switcher.switch_for_task("fast_reply")
        else:
            model = self.switcher.switch_for_task("chat")
        
        return f"🔄 根據任務自動切換到模型: {model}"
    
    def learn_model_for_task(self, task_type: str, model_id: str) -> str:
        """學習哪種任務用哪個模型"""
        return self.switcher.learn_task_mapping(task_type, model_id, "使用者教導")


# 測試
if __name__ == "__main__":
    print("🧠 模型切換系統測試")
    cap = ModelCapability(Path.home() / ".ampm_brain")
    print(cap.get_models_list())
    print("\n" + cap.auto_switch("幫我寫一個 Python 爬蟲"))

    def think_and_choose_model(self, task_description: str, call_ai_func) -> str:
        """思考後自己選擇用哪個模型（不是預設）"""
        
        # 獲取當前可用模型清單
        available = self.switcher.registry.list_models()
        models_info = []
        for mid, info in available.items():
            models_info.append(f"- {mid}: {info['strengths']}")
        
        prompt = f"""任務：{task_description}

可用模型：
{chr(10).join(models_info)}

請思考：
1. 這個任務需要什麼能力？（推理、速度、視覺、長文本、成本）
2. 哪個模型最適合？
3. 為什麼？

輸出 JSON：
{{
    "selected_model": "模型ID",
    "reason": "選擇原因",
    "confidence": 0.0-1.0
}}
"""
        response = call_ai_func(prompt)
        
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                selected = result.get("selected_model")
                reason = result.get("reason", "")
                confidence = result.get("confidence", 0.5)
                
                if selected and selected in [m for m in self.switcher.registry.models.keys()]:
                    self.switcher.set_agent_model("obsidian", selected)
                    return f"🧠 根據任務思考後，選擇 {selected}\n原因：{reason}\n信心度：{confidence:.0%}"
                else:
                    return f"⚠️ 思考後建議 {selected}，但該模型不可用。保持當前模型。"
        except:
            pass
        
        return "⚠️ 無法決定，保持當前模型"
    
    def discover_and_learn_models(self, call_ai_func) -> str:
        """自己發現並學習新模型（主動成長）"""
        # 可以從環境變數、API、或預設列表中探索
        potential_models = [
            "meta/llama-4-scout-17b-16e-instruct",
            "meta/llama-4-maverick-17b-128e-instruct",
            "meta/llama-3.2-11b-vision-instruct",
            "meta/llama-3.2-90b-vision-instruct",
            "deepseek-ai/deepseek-v4-pro",
            "moonshotai/kimi-k2.6",
            "qwen/qwen3.6-27b"
        ]
        
        # 檢查哪些還沒註冊
        registered = self.switcher.registry.models.keys()
        new_models = [m for m in potential_models if m not in registered and "placeholder" not in m]
        
        if not new_models:
            return "📭 沒有發現新模型"
        
        # 讓 AI 思考哪些值得加入
        prompt = f"""我發現了這些新模型：
{new_models}

請分析哪些值得加入，輸出 JSON：
{{
    "to_add": ["模型ID1", "模型ID2"],
    "reasons": {{"模型ID": "為什麼值得加入"}}
}}
"""
        response = call_ai_func(prompt)
        
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                to_add = result.get("to_add", [])
                added = []
                for model_id in to_add:
                    if model_id in new_models:
                        self.switcher.registry.register(
                            model_id=model_id,
                            name=model_id,
                            endpoint=config.nvidia_endpoint,
                            strengths=["general"],
                            is_free=False
                        )
                        added.append(model_id)
                if added:
                    return f"✅ 已探索並加入新模型：{', '.join(added)}"
        except:
            pass
        
        return "⚠️ 探索完成，但無法自動加入"
