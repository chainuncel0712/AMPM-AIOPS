"""
自成長模組 v2 - 全自主進化
自己找資源、換模型、接工具、升級自己
"""
import os
import sys
import json
import requests
import subprocess
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))


class AutoGrow:
    """自動成長 - 全自主版"""
    
    def __init__(self, obsidian):
        self.obsidian = obsidian
        self.base = Path(__file__).parent.parent
        self.growth_log = self.base.parent / "growth_log.json"
        self._load_log()
    
    def _load_log(self):
        if self.growth_log.exists():
            self.growth_log_data = json.loads(self.growth_log.read_text())
        else:
            self.growth_log_data = {"grown": [], "failed": [], "upgrades": []}
    
    def _save_log(self):
        self.growth_log.write_text(json.dumps(self.growth_log_data, ensure_ascii=False, indent=2))
    
    def think(self, question: str) -> str:
        """🧠 讓 LLM 自己思考決策"""
        prompt = f"""你是黑曜的自我進化模組。根據以下問題做出決策。

問題：{question}

回覆格式：只回覆一個具體的執行動作（一句話），不要解釋。"""
        try:
            return self.obsidian.llm.call([
                {"role": "user", "content": prompt}
            ])
        except:
            return "跳過"
    
    def upgrade_model(self):
        """🔄 自動找更好的免費模型"""
        print("🔄 檢查模型升級...")
        try:
            # 用 OpenRouter 搜尋更好的免費模型
            r = requests.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY', '')}"},
                timeout=10
            )
            if r.status_code == 200:
                models = r.json().get("data", [])
                # 找免費且更強的
                free_models = [
                    m for m in models
                    if "free" in str(m.get("pricing", {})).lower()
                    and m.get("id", "") != ""
                ]
                if free_models:
                    best = free_models[0]
                    print(f"  🆕 找到更強模型: {best['id']}")
                    
                    # 自動更新 llm.py
                    self._update_llm_model(best['id'])
                    self.growth_log_data["upgrades"].append({
                        "type": "model",
                        "model": best['id'],
                        "time": datetime.now().isoformat()
                    })
                    self._save_log()
        except Exception as e:
            print(f"  ⚠️ 模型升級失敗: {e}")
    
    def _update_llm_model(self, model_id):
        """更新 llm.py 中的模型"""
        with open(self.base / "llm.py", "r") as f:
            content = f.read()
        
        # 更新 OpenRouter 模型
        if "OpenRouter" in content:
            content = content.replace(
                '"model": "',
                f'"model": "{model_id}"  # was: "'
            )
            # 只改第一處
            content = content.replace(
                f'"model": "{model_id}"  # was: "',
                '"model": "',
                1
            )
            content = content.replace(
                '"model": "',
                f'"model": "{model_id}"',
                2
            )
        
        with open(self.base / "llm.py", "w") as f:
            f.write(content)
    
    def discover_tools(self):
        """🔍 自動搜尋並安裝新工具"""
        print("🔍 搜尋新工具...")
        
        # 用 LLM 決定需要什麼工具
        need = self.think("黑曜目前缺什麼工具？只回覆一個 pip 套件名稱")
        
        if need and len(need) < 50:
            try:
                print(f"  📦 嘗試安裝: {need}")
                result = subprocess.run(
                    ["pip3", "install", need.strip()],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    print(f"  ✅ {need} 安裝成功")
                    self.growth_log_data["upgrades"].append({
                        "type": "tool",
                        "name": need.strip(),
                        "time": datetime.now().isoformat()
                    })
                    self._save_log()
                    
                    # 生成對應的器官
                    self.generate_organ(f"包裝 {need} 工具，提供 run() 接口")
                else:
                    print(f"  ⚠️ {need} 安裝失敗")
            except:
                pass
    
    def generate_organ(self, need: str) -> bool:
        """🧬 用 LLM 自己寫新零件"""
        print(f"🧬 生成新零件: {need[:50]}...")
        
        prompt = f"""你是 Python 專家。為黑曜系統寫一個新零件。

需求：{need}

規則：
1. 類別名：{self._to_classname(need)}
2. __init__(self)
3. run(self, input_data=None) → 回傳結果
4. status(self) → {{"alive": True}}
5. 檔案名：{self._to_filename(need)}.py
6. 目錄：src/bag/

只輸出 Python 程式碼。"""

        try:
            code = self.obsidian.llm.call([
                {"role": "system", "content": "只輸出 Python 程式碼。"},
                {"role": "user", "content": prompt}
            ])
            code = code.replace("```python", "").replace("```", "").strip()
            
            if "class " in code and "def run" in code:
                filename = self._to_filename(need) + ".py"
                filepath = self.base / "bag" / filename
                filepath.write_text(code, encoding="utf-8")
                
                self.growth_log_data["grown"].append({
                    "name": filename,
                    "need": need[:100],
                    "time": datetime.now().isoformat(),
                })
                self._save_log()
                print(f"  ✅ 新零件: {filepath}")
                return True
            return False
        except Exception as e:
            print(f"  ❌ {e}")
            return False
    
    def daily_growth(self):
        """🌱 每日全自主成長"""
        print("\n🌱 ====== 每日自主成長 ======")
        
        # 1. 檢查模型升級
        self.upgrade_model()
        
        # 2. 搜尋新工具
        self.discover_tools()
        
        # 3. 重新掃描
        from skeleton.assembler import Assembler
        a = Assembler()
        a.scan_and_load()
        
        print(f"🌱 成長完成: {len(a.organs)} 零件")
        print("=" * 40)
    
    def _to_filename(self, name):
        return name.lower().replace(" ", "_")[:30]
    
    def _to_classname(self, name):
        return "".join(w.capitalize() for w in name.split())[:30]
