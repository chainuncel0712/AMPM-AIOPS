"""胎盘 - 母体与子代理之间的信息与资源交换"""
from skeleton.base_organ import BaseOrgan

class Placenta(BaseOrgan):
    def __init__(self, llm_client, memory, tools, executor, birth):
        super().__init__("placenta")
        self.llm = llm_client
        self.memory = memory
        self.tools = tools
        self.executor = executor
        self.birth = birth
        self._children = {}  # id -> agent info

    def send_task(self, child_id: str, task: str) -> str:
        """派任务给子代理，并返回结果"""
        child = self._children.get(child_id)
        if not child:
            return f"找不到子代理: {child_id}"

        # 构建子代理专用的系统提示
        system_prompt = child.get("prompt", "完成分配的任务。")
        tools_allowed = child.get("tools", [])
        tool_list_str = "\n".join([f"- {t}" for t in tools_allowed]) if tools_allowed else "无特殊工具"

        messages = [
            {"role": "system", "content": f"{system_prompt}\n可用工具：{tool_list_str}"},
            {"role": "user", "content": task}
        ]
        response = self.llm.call(messages)
        # 如果回复中包含工具调用，执行工具并二次调用
        return response

    def adopt(self, child_info: dict):
        """登记一个子代理"""
        self._children[child_info["id"]] = child_info

    def remove(self, child_id: str):
        self._children.pop(child_id, None)

    def status(self) -> dict:
        return {
            "name": self.name,
            "alive": self.is_alive(),
            "children_count": len(self._children),
        }
