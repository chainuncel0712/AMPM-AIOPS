"""
降級模式 - 零件壞了自動找替代
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

class FallbackChain:
    """降級鏈：主零件壞了用備用"""
    
    def __init__(self):
        self.fallbacks = {
            "cortex": self._fallback_cortex,
            "eye": self._fallback_eye,
            "memory": self._fallback_memory,
        }
    
    def _fallback_cortex(self, msg):
        """cortex 掛了 → 用 hypothalamus"""
        try:
            from brain.hypothalamus import Hypothalamus
            h = Hypothalamus(None, None, None, None, None, None, lambda x: x)
            return h.process(msg) if hasattr(h, 'process') else f"[降級] {msg}"
        except:
            return f"[降級模式] 無法處理: {msg[:100]}"
    
    def _fallback_eye(self, query):
        """eye 掛了 → 直接回傳空"""
        return ""
    
    def _fallback_memory(self):
        """memory 掛了 → 回傳 None"""
        return None
    
    def safe_call(self, organ_name: str, method: str, *args, **kwargs):
        """安全呼叫：主零件壞了自動降級"""
        try:
            from skeleton.assembler import Assembler
            a = Assembler()
            a.scan_and_load()
            organ = a.organs.get(organ_name)
            if organ and hasattr(organ, method):
                return getattr(organ, method)(*args, **kwargs)
        except:
            pass
        
        # 降級
        fallback = self.fallbacks.get(organ_name)
        if fallback:
            print(f"⚠️ [{organ_name}] 降級運行")
            return fallback(*args) if args else fallback()
        
        return f"⚠️ [{organ_name}] 不可用"

# 全局降級管理器
fallback = FallbackChain()

def safe_process(msg: str) -> str:
    """安全處理訊息（多層降級）"""
    # 第一層：cortex
    result = fallback.safe_call("cortex", "process", msg)
    if result and "降級" not in str(result):
        return result
    
    # 第二層：直接用 LLM
    try:
        from llm import LLMClient
        llm = LLMClient()
        return llm.call([{"role": "user", "content": msg}])
    except:
        return f"[緊急降級] 系統暫時無法回應"
