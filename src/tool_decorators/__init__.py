"""工具裝飾器模組 — 將類別方法註冊為 AI Agent 可呼叫的工具。"""
import functools
from typing import Any, Callable, Optional


def tool(name: Optional[str] = None, description: Optional[str] = None):
    """@tool 裝飾器：將方法標記為可供 AI Agent 呼叫的工具端點。

    支援兩種用法：
        @tool
        def my_method(self, ...): ...

        @tool(name="自訂名稱", description="工具說明")
        def my_method(self, ...): ...

    被裝飾的方法將獲得 _is_tool、_tool_name、_tool_description 屬性標記，
    框架在掃描器官時會自動發現並註冊這些方法。
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        wrapper._is_tool = True
        wrapper._tool_name = name if name else func.__name__
        wrapper._tool_description = description if description else (func.__doc__ or "")
        return wrapper

    if callable(name):
        func = name
        name = None
        return decorator(func)

    return decorator
