"""
Memory Demo — 記憶器官展示

Shows how MemoryManager stores and recalls context.
"""
from ai_bos_core import BOSKernel


def memory_demo():
    bos = BOSKernel()

    conversations = [
        ("My name is Alice", "Nice to meet you, Alice!"),
        ("I like Python programming", "Great, Python is awesome!"),
        ("What is my name?", "Your name is Alice."),
        ("What do I like?", "You like Python programming."),
    ]

    print("Storing memories...")
    for inp, out in conversations[:3]:
        bos.memory.store(inp, out)

    print("\nRecalling context for 'What is my name?':")
    ctx = bos.memory.recall("What is my name?")
    print(f"  Recall result:\n{ctx or '  (none)'}")

    print("\nRecalling context for 'programming':")
    ctx = bos.memory.recall("programming")
    print(f"  Recall result:\n{ctx or '  (none)'}")

    print(f"\nTotal memory entries: {bos.memory.status()['entries']}")


if __name__ == "__main__":
    memory_demo()
