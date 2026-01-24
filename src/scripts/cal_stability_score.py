# src/scripts/cal_stability_score.py
from __future__ import annotations

import json
from pathlib import Path

IN_JSON = Path("cal_dashboard.json")

CATEGORY_SCORES = {
    "DATA": 1,
    "STRUCTURAL": 3,
    "RELATIONAL": 5,
    "TOPOLOGICAL": 8,
}


def main() -> int:
    payload = json.loads(IN_JSON.read_text(encoding="utf-8"))
    decisions = payload.get("decisions", [])

    score = 0
    for d in decisions:
        for c in d.get("categories", []):
            score += CATEGORY_SCORES.get(c, 0)
        if d.get("risk_level") == "HIGH":
            score += 10

    print(f"Schema Stability Score: {score}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
