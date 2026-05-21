#!/usr/bin/env python3
"""
黑曜金鑰管理 CLI
用法:
  python scripts/manage_license.py generate pro
  python scripts/manage_license.py generate enterprise --days 365
  python scripts/manage_license.py validate AMPM-PRO-xxxx-xxxx
  python scripts/manage_license.py list
"""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pro.license import LicenseManager


def cmd_generate(args):
    tier = args[0] if args else "pro"
    if tier not in ("pro", "enterprise"):
        print("❌ 版本請填 pro 或 enterprise"); return
    days = 365
    if "--days" in args:
        idx = args.index("--days")
        if idx + 1 < len(args):
            days = int(args[idx + 1])
    key = LicenseManager.generate_key(tier, days)
    print(f"\n  🗝️  金鑰: {key}")
    print(f"  📋 版本: {LicenseManager.TIER_LABELS.get(tier, tier)}")
    print(f"  ⏳ 有效期: {days} 天")
    print(f"\n  設定方式:")
    print(f"  export AMPM_LICENSE_KEY={key}")


def cmd_validate(args):
    if not args:
        print("❌ 請提供金鑰"); return
    result = LicenseManager.validate_key(args[0])
    if result["valid"]:
        print(f"  ✅ 有效金鑰 — {LicenseManager.TIER_LABELS.get(result['tier'], result['tier'])}")
    else:
        print(f"  ❌ 無效金鑰 — {result['reason']}")


def cmd_list(args):
    print(f"\n  可用版本:")
    for tier, label in LicenseManager.TIER_LABELS.items():
        features = LicenseManager.FEATURES.get(tier, [])
        print(f"  {'🆓' if tier=='community' else '💎' if tier=='pro' else '🏢'} {label}")
        for f in features:
            print(f"    · {f}")
        print()


if __name__ == "__main__":
    cmds = {"generate": cmd_generate, "validate": cmd_validate, "list": cmd_list}
    if len(sys.argv) < 2 or sys.argv[1] not in cmds:
        print(__doc__); sys.exit(1)
    cmds[sys.argv[1]](sys.argv[2:])
