# Plugin Security Policy

## Core Rule

Plugins **must never** hold decision authority over the AI Brain.

## Permanently Forbidden Operations

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

## Allowed Operations

- ✅ Register capabilities
- ✅ Return execution results
- ✅ Provide context candidates (no authority to apply them)
- ✅ Subscribe to public events
- ✅ Use SDK public methods

## Enforcement

1. Plugin manifest **must declare** all capabilities upfront.
2. Runtime **rejects** any plugin attempting forbidden operations.
3. Plugins run in a **sandboxed execution context**.
4. Violation = automatic plugin disable + security log entry.

## Violation Severity

| Level | Action |
|-------|--------|
| **Warn** | Attempted forbidden operation, blocked by runtime |
| **Error** | Repeated violations within 1 hour |
| **Critical** | Attempt to modify governance/routing/permissions |

Critical violations trigger:
- Immediate plugin disable
- Security alert notification
- Permanent block after 3 critical violations
