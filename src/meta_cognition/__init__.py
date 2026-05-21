"""
Meta-Cognition — 元認知層
===========================
Self-observation + strategy suggestion + reflection.
Rules:
  - OBSERVE only: reads event_log, governance stats
  - SUGGEST only: produces text suggestions, never auto-applies
  - REFLECT only: correlates past observations with outcomes
  - Cannot execute tools, cannot make decisions, cannot modify state

All data flows to governance/event_log and governance/scoring for audit.
"""
from meta_cognition.self_observer import SelfObserver
from meta_cognition.strategy_suggester import StrategySuggester
from meta_cognition.reflection_engine import ReflectionEngine


class MetaCognition:
    """
    Top-level meta-cognition organ.
    Call .cycle() periodically to observe → suggest → reflect.
    """

    def __init__(self):
        self.observer = SelfObserver()
        self.suggester = StrategySuggester()
        self.reflector = ReflectionEngine()
        self._cycle_count = 0

    def cycle(self) -> dict:
        """
        Run one full meta-cognition cycle:
        1. Observe current state from governance
        2. Analyze → produce suggestions
        3. Reflect on outcomes
        """
        self._cycle_count += 1

        observation = self.observer.observe()
        suggestions = self.suggester.analyze(observation)
        reflection = self.reflector.reflect(observation, suggestions)

        return {
            "cycle": self._cycle_count,
            "observation": observation,
            "suggestions": suggestions,
            "reflection": reflection,
        }

    @property
    def cycle_count(self) -> int:
        return self._cycle_count
