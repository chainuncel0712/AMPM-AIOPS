"""
Orchestrator — 執行編排器
"""


class Orchestrator:
    def __init__(self, kernel):
        self.kernel = kernel

    def run(self, input_text: str) -> str:
        return self.kernel.run(input_text)
