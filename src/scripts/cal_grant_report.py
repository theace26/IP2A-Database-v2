# src/scripts/cal_grant_report.py
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

IN_JSON = Path("cal_dashboard.json")


def main() -> int:
    payload = json.loads(IN_JSON.read_text(encoding="utf-8"))
    decisions = payload.get("decisions", [])

    cat_counts = Counter()
    risk_counts = Counter()

    for d in decisions:
        risk_counts[d.get("risk_level", "UNKNOWN")] += 1
        for c in d.get("categories", []):
            cat_counts[c] += 1

    print("IP2A Change Summary (Grant/Compliance Friendly)")
    print(f"- Branch: {payload.get('branch')}")
    print(f"- Policy Env: {payload.get('policy_env')}")
    print("")
    print("Risk counts:")
    for k in ["LOW", "MEDIUM", "HIGH"]:
        print(f"- {k}: {risk_counts.get(k, 0)}")

    print("\nChange categories:")
    for k in ["DATA", "STRUCTURAL", "RELATIONAL", "TOPOLOGICAL"]:
        print(f"- {k}: {cat_counts.get(k, 0)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
