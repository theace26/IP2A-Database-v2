from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, List

from src.scripts.migration_blast_radius import analyze_migration

# -------------------------------------------------------------------
# Defaults & artifacts
# -------------------------------------------------------------------

DEFAULT_MIGRATIONS_DIR = Path("src/db/migrations/versions")

PR_COMMENT = Path("change_advisory_pr.md")
DASHBOARD_JSON = Path("cal_dashboard.json")


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------


def has_breaking_ok(path: Path) -> bool:
    return "# BREAKING_OK" in path.read_text(encoding="utf-8")


# -------------------------------------------------------------------
# Core policy engine (PURE – no env access)
# -------------------------------------------------------------------


def evaluate(
    *,
    env: str,
    migrations_dir: Path,
) -> List[dict[str, Any]]:
    """
    Evaluate migrations against Change Advisory policy.

    This function is PURE:
    - no environment access
    - no filesystem globals
    - fully testable
    """

    decisions: List[dict[str, Any]] = []

    for path in sorted(migrations_dir.glob("*.py")):
        if path.name.startswith("__"):
            continue

        report = analyze_migration(path)
        risk = report["risk_level"]
        breaking_ok = has_breaking_ok(path)

        allowed = True
        reason = "Allowed"

        if env == "prod" and risk == "HIGH" and not breaking_ok:
            allowed = False
            reason = "HIGH risk migration blocked in prod (no # BREAKING_OK)"

        decisions.append(
            {
                **report,
                "migration": path.name,
                "environment": env,
                "breaking_ok": breaking_ok,
                "allowed": allowed,
                "decision_reason": reason,
            }
        )

    return decisions


# -------------------------------------------------------------------
# Reporting
# -------------------------------------------------------------------


def render_pr_comment(decisions: List[dict[str, Any]]) -> str:
    lines = [
        "## 🛡️ Change Advisory Layer Report",
        "",
        "| Migration | Risk | Categories | BREAKING_OK | Allowed |",
        "|----------|------|------------|-------------|---------|",
    ]

    for d in decisions:
        lines.append(
            f"| `{d['migration']}` "
            f"| **{d['risk_level']}** "
            f"| {', '.join(d['categories']) or '—'} "
            f"| {'Yes' if d['breaking_ok'] else 'No'} "
            f"| {'✅' if d['allowed'] else '⛔'} |"
        )

    blocked = [d for d in decisions if not d["allowed"]]
    lines.append("")
    if blocked:
        lines.append("### 🚨 Blocked Changes")
        for b in blocked:
            lines.append(f"- `{b['migration']}` — {b['decision_reason']}")
    else:
        lines.append("✅ **No blocked changes detected**")

    return "\n".join(lines)


# -------------------------------------------------------------------
# CLI entrypoint (ENV ACCESS IS ALLOWED HERE)
# -------------------------------------------------------------------


def main() -> int:
    env = os.getenv("APP_ENV", "dev").lower()

    migrations_dir = Path(os.getenv("CAL_MIGRATIONS_DIR", str(DEFAULT_MIGRATIONS_DIR)))

    decisions = evaluate(
        env=env,
        migrations_dir=migrations_dir,
    )

    PR_COMMENT.write_text(render_pr_comment(decisions), encoding="utf-8")
    DASHBOARD_JSON.write_text(json.dumps(decisions, indent=2), encoding="utf-8")

    blocked = [d for d in decisions if not d["allowed"]]

    for d in decisions:
        status = "✅ ALLOW" if d["allowed"] else "⛔ BLOCK"
        print(f"{status} {d['migration']} — {d['risk_level']}")

    if blocked:
        print("\n🚨 Change Advisory blocked migrations:")
        for b in blocked:
            print(f"- {b['migration']}: {b['decision_reason']}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
