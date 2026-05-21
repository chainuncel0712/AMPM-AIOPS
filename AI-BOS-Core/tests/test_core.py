def test_import():
    import ai_bos_core
    assert hasattr(ai_bos_core, "__version__")


def test_boot():
    from ai_bos_core import boot
    bos = boot()
    assert bos is not None
    assert bos.registry is not None


def test_baseline():
    from ai_bos_core import run_baseline, BOSKernel
    bos = BOSKernel()
    report = run_baseline(bos)
    assert report["passed"] == report["total"]


def test_memory_store_recall():
    from ai_bos_core import BOSKernel
    bos = BOSKernel()
    bos.memory.store("Hello world", "Hi there")
    bos.memory.store("Python is great", "Yes it is")
    ctx = bos.memory.recall("Hello")
    assert "Hello world" in ctx
    ctx = bos.memory.recall("Python")
    assert "Python" in ctx


def test_demo_import():
    from ai_bos_core.demo import main
    assert callable(main)


def test_custom_organ():
    from ai_bos_core import BOSKernel
    bos = BOSKernel()
    class TestOrgan:
        name = "test_organ"
        def status(self):
            return {"name": self.name, "alive": True}
    bos.registry.register("test_organ", TestOrgan())
    health = bos.registry.health()
    names = [o["name"] for o in health]
    assert "test_organ" in names


def test_pluggable_simple_memory():
    from ai_bos_core import BOSKernel, SimpleMemory
    mem = SimpleMemory()
    bos = BOSKernel(memory=mem)
    assert bos.memory.name == "simple_memory"
    bos.memory.store("hello", "world")
    assert bos.memory.status()["entries"] == 1


def test_base_memory_interface():
    from ai_bos_core import BaseMemory
    m = BaseMemory()
    import pytest
    with pytest.raises(NotImplementedError):
        m.save({})
    with pytest.raises(NotImplementedError):
        m.load()
    with pytest.raises(NotImplementedError):
        m.clear()
    with pytest.raises(NotImplementedError):
        m.store("a", "b")
    with pytest.raises(NotImplementedError):
        m.recall("q")


def test_simple_memory_save_load_clear():
    from organs.memory.simple_memory import SimpleMemory
    m = SimpleMemory()
    m.save({"key": "value"})
    assert m.load() == {"key": "value"}
    m.clear()
    assert m.load() is None
