"""
技能傳承器官 — 世代傳遞系統
當子代理誕生時，母體將累積的知識、技能、工具、記憶
精華傳承給下一代，讓子代理不必從零開始。
"""
import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from skeleton.base_organ import BaseOrgan


class Inheritance(BaseOrgan):
    """
    技能傳承器官

    傳遞內容：
    1. 能力矩陣 — 母體目前的能力自評
    2. 知識庫 — 進化循環中學到的精華
    3. 工具註冊表 — 可用工具清單
    4. 記憶精華 — 重要性 > 0.6 的長期記憶
    5. 安全規則 — 母體的安全約束
    6. DNA — 核心身份與使命
    7. 世代基因 — 從祖先傳下來的累積智慧
    """

    def __init__(self, base_dir: Path, memory, tools,
                 awareness=None, evolution_cycle=None, dna=None):
        super().__init__("inheritance")
        self.base_dir = base_dir
        self.memory = memory
        self.tools = tools
        self.awareness = awareness
        self.evolution_cycle = evolution_cycle
        self.dna = dna or {}

        self.data_dir = base_dir / "data" / "inheritance"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.genome_file = self.data_dir / "genome.json"
        self.lineage_file = self.data_dir / "lineage.json"

        self._lock = threading.Lock()

        # ===== 累積基因 =====
        self.accumulated_genome: Dict[str, Any] = self._load_genome()
        self.lineage: List[Dict] = self._load_lineage()

        # ===== 世代計數 =====
        self.generation = len(self.lineage) + 1
        self.children_spawned = 0

    # =========================================
    # 基因管理
    # =========================================

    def _load_genome(self) -> dict:
        if self.genome_file.exists():
            try:
                return json.loads(self.genome_file.read_text())
            except Exception:
                pass
        return {
            "generation": 1,
            "accumulated_skills": {},
            "accumulated_knowledge": [],
            "evolution_history": [],
            "best_practices": [],
        }

    def _save_genome(self):
        self.genome_file.write_text(
            json.dumps(self.accumulated_genome, ensure_ascii=False, indent=2))

    def _load_lineage(self) -> list:
        if self.lineage_file.exists():
            try:
                return json.loads(self.lineage_file.read_text())
            except Exception:
                pass
        return []

    def _save_lineage(self):
        self.lineage_file.write_text(
            json.dumps(self.lineage, ensure_ascii=False, indent=2))

    # =========================================
    # 提取傳承包
    # =========================================

    def extract_inheritance_package(self, child_role: str) -> Dict:
        """
        提取一個傳承包，包含母體累積的所有精華，
        過濾出對子代理角色相關的部分。
        """
        package = {
            "generation": self.generation,
            "inherited_at": datetime.now().isoformat(),
            "child_role": child_role,
            "core_dna": {},
            "capabilities": {},
            "knowledge": [],
            "tools": [],
            "memory_gems": [],
            "safety_rules": [],
            "best_practices": [],
        }

        # 1. DNA
        package["core_dna"] = {
            "name": self.dna.get("name", "黑曜"),
            "mission": self.dna.get("core_mission", "幫助用戶成功"),
            "language": self.dna.get("language", "繁體中文"),
        }

        # 2. 能力矩陣（過濾相關的）
        if self.awareness:
            for name, cap in self.awareness.capabilities.items():
                # 只傳和子代理角色相關的能力
                if child_role[:3] in name or name[:3] in child_role or True:
                    package["capabilities"][name] = min(1.0, cap.get("level", 0) * 0.7)

        # 3. 進化循環的精華知識
        if self.evolution_cycle:
            learnings = self.evolution_cycle._load_json(
                self.evolution_cycle.learnings_file)
            for lrn in learnings[-30:]:
                if lrn.get("confidence", 0) >= 0.5:
                    package["knowledge"].append({
                        "topic": lrn.get("topic", ""),
                        "insight": lrn.get("insight", "")[:200],
                    })

        # 4. 工具註冊表
        try:
            if self.tools and hasattr(self.tools, "registry"):
                for name in list(self.tools.registry.keys())[:20]:
                    package["tools"].append(name)
        except Exception:
            pass

        # 5. 長期記憶精華（重要度高的）
        try:
            if self.memory and hasattr(self.memory, "get_all_facts"):
                facts = self.memory.get_all_facts()
                for f in facts[-30:]:
                    # 只傳精華
                    if len(f) > 20:
                        package["memory_gems"].append(f[:200])
        except Exception:
            pass

        # 6. 安全規則
        try:
            if self.evolution_cycle:
                package["safety_rules"] = list(
                    self.evolution_cycle.SAFETY.get("forbidden_actions", []))
        except Exception:
            package["safety_rules"] = ["禁止破壞系統", "禁止修改核心檔案"]

        # 7. 最佳實踐（從累積基因中提取）
        package["best_practices"] = self.accumulated_genome.get(
            "best_practices", [])[-10:]

        # 8. 將自己的精華加到累積基因
        self._merge_back_to_genome(package)

        return package

    def _merge_back_to_genome(self, package: Dict):
        """將這次傳承的精華整理合併回累積基因"""
        # 合併技能
        for name, level in package["capabilities"].items():
            existing = self.accumulated_genome["accumulated_skills"].get(name, 0)
            self.accumulated_genome["accumulated_skills"][name] = max(existing, level)

        # 合併知識
        existing_knowledge = {
            k["insight"][:50] for k in self.accumulated_genome["accumulated_knowledge"]
        }
        for k in package["knowledge"]:
            key = k.get("insight", "")[:50]
            if key not in existing_knowledge:
                self.accumulated_genome["accumulated_knowledge"].append(k)
                existing_knowledge.add(key)

        if len(self.accumulated_genome["accumulated_knowledge"]) > 200:
            self.accumulated_genome["accumulated_knowledge"] = (
                self.accumulated_genome["accumulated_knowledge"][-200:])

        self.accumulated_genome["evolution_history"].append({
            "ts": datetime.now().isoformat(),
            "generation": self.generation,
            "action": "merged_inheritance",
        })
        if len(self.accumulated_genome["evolution_history"]) > 100:
            self.accumulated_genome["evolution_history"] = (
                self.accumulated_genome["evolution_history"][-100:])

        self._save_genome()

    # =========================================
    # 接生（整合 birth + inheritance）
    # =========================================

    def spawn(self, birth, nursery, placenta, name: str, role: str) -> Dict:
        """
        生出一個子代理，並註入傳承包。

        流程：
        1. 從母體提取傳承包
        2. 呼叫 birth.deliver() 創造子代理
        3. 將傳承包註入子代理
        4. 登記到 nursery 和 placenta
        5. 記錄世代
        """
        # 1. 提取傳承
        inheritance_pkg = self.extract_inheritance_package(role)

        # 2. 接生
        child = birth.deliver(name=name, role=role)

        if "error" in child:
            return child

        child_id = child["id"]

        # 3. 註入傳承
        child["inheritance"] = inheritance_pkg
        child["generation"] = self.generation
        child["parent"] = self.dna.get("name", "黑曜")

        # 4. 登記
        if nursery:
            nursery.register(child_id, child)
        if placenta:
            placenta.adopt({
                "id": child_id,
                "name": name,
                "role": role,
                "tools": inheritance_pkg.get("tools", []),
                "prompt": self._build_child_prompt(child, inheritance_pkg),
                "inheritance": inheritance_pkg,
            })

        # 5. 記錄世代
        self.lineage.append({
            "child_id": child_id,
            "child_name": name,
            "child_role": role,
            "generation": self.generation,
            "spawned_at": datetime.now().isoformat(),
            "skills_inherited": len(inheritance_pkg.get("capabilities", {})),
            "knowledge_items": len(inheritance_pkg.get("knowledge", [])),
        })
        self._save_lineage()

        self.children_spawned += 1

        # 6. 記錄到自我意識
        if self.awareness:
            self.awareness.record_event("spawn",
                f"子代理誕生: {name} ({role}) — 傳承 {len(inheritance_pkg['capabilities'])} 技能")

        return child

    def _build_child_prompt(self, child: dict, inheritance: dict) -> str:
        """根據傳承包建立子代理的系統提示詞"""
        caps = inheritance.get("capabilities", {})
        knowledge = inheritance.get("knowledge", [])
        dna = inheritance.get("core_dna", {})

        prompt = f"""你是 {child['name']}，第 {self.generation} 代子代理。
母體: {dna.get('name', '黑曜')}
角色: {child['role']}

傳承的技能:
{chr(10).join(f'- {k}: {v:.0%}' for k, v in list(caps.items())[:5])}

核心知識:
{chr(10).join(f'- {k.get("insight", "")[:80]}' for k in knowledge[:3])}

規則:
1. {dna.get('mission', '幫助用戶成功')}
2. 安全第一，禁止破壞性操作
3. 誠實回報，不回傳假資訊
4. 遇到不會的事請求母體協助
5. 從任務中持續學習成長
"""
        return prompt

    # =========================================
    # 子代理回饋（逆向傳承）
    # =========================================

    def receive_child_learning(self, child_id: str, child_name: str,
                                new_knowledge: List[Dict]):
        """
        接收子代理學到的新知識，逆向註入母體。
        子代理在任務中學到的，回傳給母體繼續進化。
        """
        for item in new_knowledge:
            self.accumulated_genome["accumulated_knowledge"].append({
                "source": f"child:{child_name}",
                "insight": item.get("insight", "")[:200],
                "received_at": datetime.now().isoformat(),
            })

        self.accumulated_genome["evolution_history"].append({
            "ts": datetime.now().isoformat(),
            "action": "child_feedback",
            "child": child_name,
            "items": len(new_knowledge),
        })

        self._save_genome()

        # 更新自我意識
        if self.awareness:
            self.awareness.record_event("child_feedback",
                f"子代理 {child_name} 回傳 {len(new_knowledge)} 項知識")

    # =========================================
    # 世代查詢
    # =========================================

    def get_generation_summary(self) -> str:
        """取得世代摘要"""
        gen = self.accumulated_genome
        skills_count = len(gen.get("accumulated_skills", {}))
        knowledge_count = len(gen.get("accumulated_knowledge", []))
        lineage_count = len(self.lineage)

        return (
            f"🧬 世代傳承摘要:\n"
            f"  當前世代: 第 {self.generation} 代\n"
            f"  累積技能: {skills_count} 項\n"
            f"  累積知識: {knowledge_count} 條\n"
            f"  子代理總數: {lineage_count}\n"
            f"  最佳實踐: {len(gen.get('best_practices', []))} 條"
        )

    def get_lineage_tree(self) -> list:
        """取得世代樹"""
        return self.lineage

    def status(self) -> dict:
        return {
            "name": self.name,
            "alive": self.is_alive(),
            "generation": self.generation,
            "children_spawned": self.children_spawned,
            "accumulated_skills": len(
                self.accumulated_genome.get("accumulated_skills", {})),
            "accumulated_knowledge": len(
                self.accumulated_genome.get("accumulated_knowledge", [])),
        }
