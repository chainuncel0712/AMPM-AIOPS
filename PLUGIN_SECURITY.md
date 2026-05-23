<p align="center"><img src="assets/300.png" width="180"></p>

<h1 align="center" style="color:#e94560; border-bottom:1px solid #30363d; padding-bottom:8px;">Plugin Security Policy</h1>

<h2 align="center" style="color:#58a6ff;">Core Rule</h2>

<p align="center" style="color:#c9d1d9;">
Plugins <strong>must never</strong> hold decision authority over the AI Brain.
</p>

<h2 align="center" style="color:#58a6ff;">Permanently Forbidden Operations</h2>

| Operation | Reason |
|-----------|--------|
| Modify Routing | Routing is Kernel Authority |
| Modify Governance | Governance is Kernel Authority |
| Modify Context Policy | Context Policy is Kernel Authority |
| Modify Memory Ranking | Memory Ranking is Kernel Authority |
| Modify Permissions | Permissions is Kernel Authority |
| Modify Runtime Authority | Runtime Authority is Kernel Authority |
| Access Kernel Directories | Only through Public API |
| Execute Unauthorized Tools | Only registered capabilities allowed |

<h2 align="center" style="color:#58a6ff;">Allowed Operations</h2>

- ✅ Register capabilities
- ✅ Return execution results
- ✅ Provide context candidates (no authority to apply them)
- ✅ Subscribe to public events
- ✅ Use SDK public methods

<h2 align="center" style="color:#58a6ff;">Enforcement</h2>

1. Plugin manifest **must declare** all capabilities upfront.
2. Runtime **rejects** any plugin attempting forbidden operations.
3. Plugins run in a **sandboxed execution context**.
4. Violation = automatic plugin disable + security log entry.

<h2 align="center" style="color:#58a6ff;">Violation Severity</h2>

| Level | Action |
|-------|--------|
| **Warn** | Attempted forbidden operation, blocked by runtime |
| **Error** | Repeated violations within 1 hour |
| **Critical** | Attempt to modify governance/routing/permissions |

<p style="color:#c9d1d9;">
Critical violations trigger:
</p>

- Immediate plugin disable
- Security alert notification
- Permanent block after 3 critical violations

<br>
<hr style="border:1px solid #30363d;">
<p align="center" style="color:#8b949e; font-size:0.85em;">
  <sub>AMPM-AIOPS — AI OS Public Framework</sub>
</p>
